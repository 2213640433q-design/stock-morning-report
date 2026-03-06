#!/usr/bin/env python3
"""
股票晨报 - GitHub Actions 专用版
直接获取行情并推送到飞书，不依赖 OpenClaw
"""

import json
import os
import requests
from datetime import datetime

# 自选股配置
WATCHLIST = [
    {"code": "600111", "name": "北方稀土", "industry": "稀土永磁"}
]

def get_stock_quote(code):
    """获取股票行情（腾讯财经API）"""
    # 判断市场
    if code.startswith(('6', '5', '9')):
        market = "sh"
    elif code.startswith(('0', '3', '2')):
        market = "sz"
    elif code.startswith(('43', '83', '87')):
        market = "bj"
    else:
        market = "sh"
    
    url = f"https://qt.gtimg.cn/q={market}{code}"
    
    try:
        response = requests.get(url, timeout=15)
        response.encoding = 'gbk'
        data = response.text
        
        prefix = f'v_{market}{code}="'
        if prefix in data:
            start = data.find(prefix) + len(prefix)
            end = data.find('"', start)
            content = data[start:end]
            fields = content.split('~')
            
            if len(fields) >= 45:
                price = float(fields[3])
                prev = float(fields[4])
                change = round(price - prev, 2)
                change_pct = round(change / prev * 100, 2)
                volume = int(fields[6]) if fields[6].isdigit() else 0
                
                return {
                    "code": code,
                    "name": fields[1],
                    "price": price,
                    "prev_close": prev,
                    "open": float(fields[5]),
                    "high": float(fields[33]),
                    "low": float(fields[34]),
                    "volume": volume,
                    "volume_wan": round(volume / 10000, 2),
                    "change": change,
                    "change_pct": change_pct,
                    "amplitude": round((float(fields[33]) - float(fields[34])) / prev * 100, 2),
                    "turnover": fields[37] if len(fields) > 37 else "N/A",
                    "pe": fields[52] if len(fields) > 52 else "N/A",
                    "pb": fields[45] if len(fields) > 45 else "N/A",
                    "market_cap": round(float(fields[44]) / 100000000, 2) if len(fields) > 44 and fields[44] else 0,
                }
    except Exception as e:
        print(f"获取 {code} 行情失败: {e}")
        return {"code": code, "error": str(e)}
    
    return {"code": code, "error": "无法解析数据"}

def analyze_stock(quote):
    """分析股票并生成报告内容"""
    change_pct = quote.get("change_pct", 0)
    amplitude = quote.get("amplitude", 0)
    name = quote.get("name", "")
    
    # 趋势判断
    if change_pct >= 9.5:
        trend = "🔥 涨停"
        trend_desc = "今日涨停，资金抢筹明显，短期强势。"
    elif change_pct >= 5:
        trend = "📈 大涨"
        trend_desc = "今日大幅上涨，突破关键位置，短期趋势向好。"
    elif change_pct >= 3:
        trend = "📊 明显上涨"
        trend_desc = "今日涨幅可观，量能配合较好。"
    elif change_pct > 0:
        trend = "📈 小幅上涨"
        trend_desc = "今日小幅走高，走势稳健。"
    elif change_pct > -3:
        trend = "📉 小幅回调"
        trend_desc = "今日小幅回落，正常技术性调整。"
    elif change_pct > -5:
        trend = "📊 明显下跌"
        trend_desc = "今日跌幅较大，注意支撑。"
    else:
        trend = "🔴 大跌"
        trend_desc = "今日大幅下跌，短期承压。"
    
    # 行业特定分析
    if "稀土" in name:
        if change_pct > 0:
            fundamental = "✅ 稀土价格企稳，新能源需求支撑，行业景气度向好。"
            valuation = "💰 估值合理，若稀土涨价有修复空间。"
        else:
            fundamental = "⚠️ 短期受大宗商品价格影响，但供需格局未改。"
            valuation = "💰 回调后估值更具吸引力。"
        
        keywords = ["稀土价格", "新能源需求", "供给指标"]
        
        if change_pct > 3:
            suggestion = "💡 持有观望，不宜追高。"
        elif change_pct > 0:
            suggestion = "💡 持股待涨，关注量能。"
        else:
            suggestion = "💡 逢低关注，分批布局。"
    else:
        fundamental = "✅ 公司基本面正常。"
        valuation = "💰 估值合理。"
        keywords = ["行业政策", "业绩预期"]
        suggestion = "💡 根据大盘走势操作。"
    
    # 风险提示
    if change_pct > 7:
        risk = "⚡ 涨幅较大，注意获利回吐。"
    elif change_pct < -7:
        risk = "⚡ 跌幅较大，注意止损。"
    elif amplitude > 8:
        risk = "⚡ 振幅大，多空分歧明显。"
    else:
        risk = "⚡ 正常波动，关注大盘风险。"
    
    return {
        "trend": trend,
        "trend_desc": trend_desc,
        "fundamental": fundamental,
        "valuation": valuation,
        "suggestion": suggestion,
        "risk": risk,
        "keywords": keywords
    }

def build_feishu_card(quote, analysis):
    """构建飞书卡片"""
    if "error" in quote:
        return {
            "msg_type": "text",
            "content": {"text": f"❌ 获取 {quote.get('code', '股票')} 数据失败"}
        }
    
    name = quote["name"]
    code = quote["code"]
    price = quote["price"]
    change = quote["change"]
    change_pct = quote["change_pct"]
    
    emoji = "🟢" if change >= 0 else "🔴"
    
    content = f"**{emoji} {name} ({code})**\n"
    content += f"**现价**: ¥{price}  **涨跌**: {change:+.2f} ({change_pct:+.2f}%)\n"
    content += f"**今开**: ¥{quote['open']}  **最高**: ¥{quote['high']}  **最低**: ¥{quote['low']}\n"
    content += f"**振幅**: {quote['amplitude']}%  **换手**: {quote['turnover']}%  **成交**: {quote['volume_wan']}万手\n"
    content += f"**市值**: {quote['market_cap']}亿  **PE**: {quote['pe']}  **PB**: {quote['pb']}\n\n"
    
    content += f"**📊 技术面**: {analysis['trend_desc']}\n\n"
    content += f"**📰 基本面**: {analysis['fundamental']}\n"
    content += f"**相关**: {', '.join(analysis['keywords'])}\n\n"
    content += f"**💎 估值**: {analysis['valuation']}\n\n"
    content += f"**🎯 建议**: {analysis['suggestion']}\n\n"
    content += f"**⚠️ 风险**: {analysis['risk']}\n\n"
    content += f"*更新时间: {datetime.now().strftime('%H:%M')} | 数据: 腾讯财经*"
    
    return {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "blue" if change >= 0 else "red",
                "title": {
                    "tag": "plain_text",
                    "content": f"📊 晨报 {name}"
                }
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": content
                    }
                }
            ]
        }
    }

def send_to_feishu(message):
    """发送到飞书"""
    webhook_url = os.environ.get('FEISHU_WEBHOOK_URL', '')
    
    if not webhook_url:
        print("❌ 错误: 未设置 FEISHU_WEBHOOK_URL")
        return False
    
    try:
        response = requests.post(
            webhook_url,
            json=message,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        result = response.json()
        
        if result.get('code') == 0:
            print("✅ 飞书推送成功")
            return True
        else:
            print(f"❌ 飞书推送失败: {result}")
            return False
    except Exception as e:
        print(f"❌ 发送错误: {e}")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print(f"📊 股票晨报 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)
    
    all_success = True
    
    for stock in WATCHLIST:
        code = stock["code"]
        name = stock["name"]
        
        print(f"\n📈 分析 {name} ({code})...")
        
        quote = get_stock_quote(code)
        
        if "error" in quote:
            print(f"❌ 获取数据失败: {quote['error']}")
            all_success = False
            continue
        
        print(f"💰 现价: ¥{quote['price']} ({quote['change_pct']:+.2f}%)")
        
        analysis = analyze_stock(quote)
        message = build_feishu_card(quote, analysis)
        
        if send_to_feishu(message):
            print(f"✅ {name} 推送成功")
        else:
            print(f"❌ {name} 推送失败")
            all_success = False
    
    print("\n" + "=" * 50)
    if all_success:
        print("✅ 所有股票晨报推送完成")
    else:
        print("⚠️ 部分推送失败")
    print("=" * 50)
    
    return 0 if all_success else 1

if __name__ == "__main__":
    exit(main())
