#!/usr/bin/env python3
"""
股票晨报 - 专业完整版
获取股票行情并推送到飞书
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
                    # 计算市值（亿）
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
                        "high_52w": float(fields[43]) if fields[43] else 0,
                        "low_52w": float(fields[44]) if fields[44] else 0,
                    }
    except Exception as e:
        return None
    return None

def analyze_stock(quote):
    """分析股票"""
    change_pct = quote.get("change_pct", 0)
    amplitude = quote.get("amplitude", 0)
    pe = quote.get("pe", "N/A")
    
    # 趋势判断
    if change_pct >= 9.5:
        trend = "🔥 涨停"
        suggestion = "注意获利回吐"
    elif change_pct >= 5:
        trend = "📈 大涨"
        suggestion = "关注持续性"
    elif change_pct >= 1:
        trend = "📈 上涨"
        suggestion = "持股待涨"
    elif change_pct > -1:
        trend = "📉 震荡"
        suggestion = "观望为主"
    elif change_pct > -5:
        trend = "📉 下跌"
        suggestion = "注意风险"
    else:
        trend = "🔴 大跌"
        suggestion = "谨慎观望"
    
    # 估值参考
    try:
        pe_val = float(pe) if pe != "N/A" else None
        if pe_val:
            if pe_val < 0:
                pe_status = "亏损"
            elif pe_val < 15:
                pe_status = "低估"
            elif pe_val < 30:
                pe_status = "合理"
            else:
                pe_status = "高估"
        else:
            pe_status = "N/A"
    except:
        pe_status = "N/A"
    
    return trend, suggestion, pe_status

def build_stock_block(q):
    """构建单个股票区块"""
    name = q["name"]
    code = q["code"]
    price = q["price"]
    change = q["change"]
    pct = q["change_pct"]
    trend, suggestion, pe_status = analyze_stock(q)
    
    emoji = "🟢" if change >= 0 else "🔴"
    
    content = f"### {emoji} {name} ({code})\n\n"
    content += f"**现价**: ¥{price} | **涨跌**: {change:+.2f} ({pct:+.2f}%)\n\n"
    content += f"📊 **技术面**: {trend} · {suggestion}\n\n"
    content += f"---|---|---\n"
    content += f"今开|最高|最低\n"
    content += f"¥{q['open']}|¥{q['high']}|¥{q['low']}\n\n"
    content += f"---|---|---\n"
    content += f"成交量|成交额|换手\n"
    content += f"{q['volume_wan']}万手|{q['turnover']}%|{q['amplitude']}%\n\n"
    content += f"---|---|---\n"
    content += f"市盈率|市净率|总市值\n"
    content += f"{q['pe']}|{q['pb']}|{q['market_cap']}亿"
    
    return content

def build_card(quotes):
    """构建飞书卡片"""
    stock_blocks = []
    for q in quotes:
        if q:
            stock_blocks.append(build_stock_block(q))
    
    content = "### 📈 今日行情\n\n"
    content += "\n---\n\n".join(stock_blocks)
    content += f"\n\n---\n\n*更新时间: {datetime.now().strftime('%H:%M')} | 数据: 腾讯财经*"
    
    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "template": "blue",
            "title": {"tag": "plain_text", "content": f"📈 股票行情 {datetime.now().strftime('%m-%d')}"}
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
