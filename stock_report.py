#!/usr/bin/env python3
"""
股票晨报 - 完整版
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
                if len(fields) >= 45:
                    price = float(fields[3])
                    prev = float(fields[4])
                    change = round(price - prev, 2)
                    return {
                        "code": code,
                        "name": fields[1],
                        "price": price,
                        "change": change,
                        "change_pct": round(change / prev * 100, 2),
                        "open": float(fields[5]),
                        "high": float(fields[33]),
                        "low": float(fields[34]),
                        "volume": int(fields[6]) if fields[6].isdigit() else 0,
                        "turnover": fields[37] if len(fields) > 37 else "N/A",
                    }
    except Exception as e:
        return None
    return None

def analyze_stock(quote):
    """分析股票"""
    change_pct = quote.get("change_pct", 0)
    
    if change_pct >= 5:
        trend = "强势上涨"
        suggestion = "注意回调风险"
    elif change_pct > 0:
        trend = "小幅上涨"
        suggestion = "持股待涨"
    elif change_pct > -5:
        trend = "小幅回调"
        suggestion = "逢低关注"
    else:
        trend = "明显下跌"
        suggestion = "注意风险"
    
    return trend, suggestion

def build_card(quotes):
    """构建飞书卡片"""
    elements = []
    
    for q in quotes:
        if not q:
            continue
        name = q["name"]
        code = q["code"]
        price = q["price"]
        change = q["change"]
        pct = q["change_pct"]
        trend, suggestion = analyze_stock(q)
        
        emoji = "🟢" if change >= 0 else "🔴"
        
        content = f"**{emoji} {name} ({code})**\n"
        content += f"¥{price} {change:+.2f} ({pct:+.2f}%)\n"
        content += f"📊 {trend} · {suggestion}"
        
        elements.append({
            "tag": "div",
            "text": {"tag": "lark_md", "content": content}
        })
        elements.append({"tag": "hr"})
    
    elements.append({
        "tag": "div",
        "text": {"tag": "lark_md", "content": f"*更新时间: {datetime.now().strftime('%H:%M')} | 数据: 腾讯财经*"}
    })
    
    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "template": "blue",
            "title": {"tag": "plain_text", "content": f"📈 股票行情 {datetime.now().strftime('%m-%d')}"}
        },
        "elements": elements
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
