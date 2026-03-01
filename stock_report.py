#!/usr/bin/env python3
import json
import urllib.request
import os
from datetime import datetime
import ssl

WATCHLIST = [{"code": "600111", "name": "北方稀土"}]

def get_stock_quote(code):
    market = "sh" if code.startswith(('6','5','9')) else "sz" if code.startswith(('0','3','2')) else "bj"
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
                if len(fields) >= 35:
                    price = float(fields[3])
                    prev = float(fields[4])
                    change = round(price - prev, 2)
                    return {
                        "code": code, "name": fields[1], "price": price,
                        "change": change, "change_pct": round(change/prev*100, 2),
                        "open": float(fields[5]), "high": float(fields[33]),
                        "low": float(fields[34]), "volume": fields[6]
                    }
    except Exception as e:
        return {"code": code, "error": str(e)}
    return {"code": code, "error": "无数据"}

def analyze(change_pct):
    if change_pct > 5: return "强势上涨", "短期情绪积极", "估值修复中"
    elif change_pct > 0: return "小幅上涨", "情绪平稳", "估值稳定"
    elif change_pct > -5: return "小幅回调", "短期调整", "或存机会"
    else: return "大幅下跌", "短期承压", "谨慎观望"

def build_card(quotes):
    elements = []
    for q in quotes:
        if "error" in q: continue
        name, code = q["name"], q["code"]
        price, change, pct = q["price"], q["change"], q["change_pct"]
        trend, impact, val = analyze(pct)
        emoji = "📈" if change >= 0 else "📉"
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": f"**{emoji} {name} ({code})**  ¥{price}  {change:+.2f} ({pct:+.2f}%)"}})
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": f"💡 **{trend}**｜{impact}｜{val}"}})
        elements.append({"tag": "hr"})
    elements.append({"tag": "div", "text": {"tag": "lark_md", "content": "*数据来源: 腾讯财经 | 仅供参考*"}})
    return {"config": {"wide_screen_mode": True}, "header": {"template": "blue", "title": {"tag": "plain_text", "content": f"📊 晨报 {datetime.now().strftime('%m-%d')}"}}, "elements": elements}

def send(card):
    url = os.environ.get('FEISHU_WEBHOOK_URL', '')
    if not url: print("错误: 未设置 WEBHOOK"); return False
    try:
        data = json.dumps({"msg_type": "interactive", "card": card}).encode()
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
            result = json.loads(r.read().decode())
            return result.get('code') == 0
    except Exception as e: print(f"错误: {e}"); return False

if __name__ == "__main__":
    quotes = [get_stock_quote(s["code"]) for s in WATCHLIST]
    if send(build_card(quotes)): print("✅ 推送成功")
    else: print("❌ 推送失败"); exit(1)
