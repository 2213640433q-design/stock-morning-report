#!/usr/bin/env python3
"""
股票晨报 - 专业基本面分析版
包含技术面 + 基本面分析
"""
import json
import os
import urllib.request
import ssl
from datetime import datetime

# 自选股配置
WATCHLIST = [
    {"code": "600111", "name": "北方稀土", "industry": "稀土永磁"},
    {"code": "600900", "name": "长江电力", "industry": "水电"}
]

# 基本面分析数据（静态配置，可定期更新）
FUNDAMENTAL_DATA = {
    "600111": {
        "name": "北方稀土",
        "business": "稀土氧化物、稀土金属、稀土磁性材料",
        "advantage": "中国稀土集团控股，资源垄断优势",
        "risk": "稀土价格波动大，受政策影响",
        "pe_history": "历史PE区间：30-150倍",
        "dividend": "分红较少，资本开支大"
    },
    "600900": {
        "name": "长江电力",
        "business": "水电发电、配售电",
        "advantage": "长江流域水电独家运营，成本优势明显",
        "risk": "来水波动、电价调整",
        "pe_history": "历史PE区间：15-25倍",
        "dividend": "高分红，现金流稳定"
    }
}

def get_stock_quote(code):
    """获取股票行情"""
    market = "sh" if code.startswith(('6', '5', '9')) else "sz"
    url = f"https://qt.gtimg.cn/q={market}{code}"
    
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
            data = response.read().decode('gbk', errors='ignore')
            prefix = f'v_{market}{code}="'
            if prefix in data:
                start = data.find(prefix) + len(prefix)
                end = data.find('"', start)
                fields = data[start:end].split('~')
                if len(fields) >= 55:
                    price = float(fields[3])
                    prev = float(fields[4])
                    change = round(price - prev, 2)
                    volume = int(fields[6]) if fields[6].isdigit() else 0
                    market_cap = round(float(fields[44]) / 100000000, 0) if fields[44] else 0
                    
                    return {
                        "code": code,
                        "name": fields[1],
                        "price": price,
                        "change": change,
                        "change_pct": round(change / prev * 100, 2),
                        "open": float(fields[5]),
                        "high": float(fields[33]),
                        "low": float(fields[34]),
                        "volume": volume,
                        "volume_wan": round(volume / 10000, 2),
                        "turnover": fields[37] if fields[37] else "N/A",
                        "amplitude": round((float(fields[33]) - float(fields[34])) / prev * 100, 2),
                        "pe": fields[52] if fields[52] and fields[52] != "N/A" else "N/A",
                        "pb": fields[45] if fields[45] else "N/A",
                        "market_cap": market_cap,
                    }
    except Exception as e:
        return None
    return None

def analyze_technical(quote):
    """技术面分析"""
    change_pct = quote.get("change_pct", 0)
    amplitude = quote.get("amplitude", 0)
    
    # 趋势判断
    if change_pct >= 9.5:
        trend = "🔥 涨停"
        signal = "强势"
    elif change_pct >= 5:
        trend = "📈 大涨"
        signal = "强势"
    elif change_pct >= 1:
        trend = "📈 上涨"
        signal = "中性偏多"
    elif change_pct > -1:
        trend = "📊 震荡"
        signal = "中性"
    elif change_pct > -5:
        trend = "📉 下跌"
        signal = "中性偏空"
    else:
        trend = "🔴 大跌"
        signal = "弱势"
    
    return trend, signal

def analyze_valuation(quote):
    """估值分析"""
    try:
        pe = float(quote.get("pe", 0)) if quote.get("pe") != "N/A" else 0
        if pe <= 0:
            return "亏损", "无法评估"
        elif pe < 15:
            return f"{pe:.1f}倍", "低估"
        elif pe < 30:
            return f"{pe:.1f}倍", "合理"
        else:
            return f"{pe:.1f}倍", "偏高"
    except:
        return "N/A", "无法评估"

def build_stock_block(q):
    """构建单个股票区块"""
    code = q["code"]
    name = q["name"]
    price = q["price"]
    change = q["change"]
    pct = q["change_pct"]
    trend, signal = analyze_technical(q)
    pe_val, pe_status = analyze_valuation(q)
    
    # 获取基本面数据
    fundamental = FUNDAMENTAL_DATA.get(code, {})
    
    emoji = "🟢" if change >= 0 else "🔴"
    
    content = f"### {emoji} {name} ({code})\n\n"
    
    # 行情数据
    content += f"**现价**: ¥{price} | **涨跌**: {change:+.2f} ({pct:+.2f}%)\n\n"
    content += f"📊 **技术面**: {trend} · 信号: {signal}\n\n"
    content += f"💰 **估值**: PE {pe_val} ({pe_status})\n\n"
    content += f"---\n\n"
    
    # 详细数据
    content += f"**开盘**: ¥{q['open']} | **最高**: ¥{q['high']} | **最低**: ¥{q['low']}\n\n"
    content += f"**成交量**: {q['volume_wan']}万手 | **换手率**: {q['turnover']}% | **振幅**: {q['amplitude']}%\n\n"
    content += f"**市值**: {q['market_cap']}亿\n\n"
    content += f"---\n\n"
    
    # 基本面分析
    content += f"**🏢 主营业务**: {fundamental.get('business', 'N/A')}\n\n"
    content += f"**⭐ 核心优势**: {fundamental.get('advantage', 'N/A')}\n\n"
    content += f"**⚠️ 主要风险**: {fundamental.get('risk', 'N/A')}\n\n"
    content += f"**📈 历史PE**: {fundamental.get('pe_history', 'N/A')}\n\n"
    content += f"**💵 分红**: {fundamental.get('dividend', 'N/A')}"
    
    return content

def build_card(quotes):
    """构建飞书卡片"""
    stock_blocks = []
    for q in quotes:
        if q:
            stock_blocks.append(build_stock_block(q))
    
    content = "### 📈 股票行情 + 基本面分析\n\n"
    content += "\n---\n\n".join(stock_blocks)
    content += f"\n\n---\n\n*更新时间: {datetime.now().strftime('%H:%M')} | 数据: 腾讯财经*"
    
    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "template": "blue",
            "title": {"tag": "plain_text", "content": f"📈 股票晨报 {datetime.now().strftime('%m-%d')}"}
        },
        "elements": [
            {
                "tag": "div",
                "text": {"tag": "lark_md", "content": content}
            }
        ]
    }

def send_to_feishu(card, webhook_url):
    """发送到飞书"""
    message = {"msg_type": "interactive", "card": card}
    
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        data = json.dumps(message).encode('utf-8')
        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get('code') == 0
    except Exception as e:
        print(f"发送失败: {e}")
        return False

def main():
    webhook_url = os.environ.get('FEISHU_WEBHOOK_URL', '')
    if not webhook_url:
        print("错误: 未设置 FEISHU_WEBHOOK_URL")
        return 1
    
    quotes = []
    for stock in WATCHLIST:
        quote = get_stock_quote(stock["code"])
        if quote:
            quotes.append(quote)
    
    if not quotes:
        print("获取行情失败")
        return 1
    
    card = build_card(quotes)
    
    if send_to_feishu(card, webhook_url):
        print("✅ 推送成功")
        return 0
    else:
        print("❌ 推送失败")
        return 1

if __name__ == "__main__":
    exit(main())
