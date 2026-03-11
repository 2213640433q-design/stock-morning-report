#!/usr/bin/env python3
"""
价值投资学习 - GitHub Actions 专用版
每日学习巴菲特/芒格/段永平投资理念
"""
import json
import os
import urllib.request
import ssl
from datetime import datetime

def send_to_feishu(webhook_url, title, content):
    """发送到飞书"""
    message = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "green",
                "title": {"tag": "plain_text", "content": title}
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": content}
                }
            ]
        }
    }
    
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
                if len(fields) >= 35:
                    return {
                        "code": code,
                        "name": fields[1],
                        "price": float(fields[3]),
                        "change": round(float(fields[3]) - float(fields[4]), 2),
                        "change_pct": round((float(fields[3]) - float(fields[4])) / float(fields[4]) * 100, 2)
                    }
    except Exception as e:
        return None
    return None

# 今日学习内容
LEARNING_CONTENT = """
## 📚 价值投资每日一课

### 今日主题：护城河理论 (Economic Moat)

> "关键是找到那些拥有宽阔护城河的企业，然后一直持有。"
—— 沃伦·巴菲特

**护城河的5种类型：**

1. **成本优势** - 规模经济、独特资源
2. **网络效应** - 用户越多越有价值
3. **无形资产** - 品牌、专利、牌照
4. **转换成本** - 客户不想换
5. **有效规模** - 新进入者无利可图

---

### 💡 今日思考

你的自选股（北方稀土、长江电力）有什么护城河？

**北方稀土** ⚡
- 资源优势：稀土资源稀缺，中国主导
- 风险：大宗商品价格波动

**长江电力** 🌊
- 成本优势：水电成本远低于火电
- 资源垄断：长江流域水电独家运营
- 稳定现金流：类债券资产

---

*每日积累一小点，长期复利的力量*
"""

def main():
    webhook_url = os.environ.get('FEISHU_WEBHOOK_URL', '')
    if not webhook_url:
        print("错误: 未设置 FEISHU_WEBHOOK_URL")
        return 1
    
    # 获取股票行情
    stocks = []
    for code in ["600111", "600900"]:
        quote = get_stock_quote(code)
        if quote:
            stocks.append(quote)
    
    # 构建股票行情摘要
    stock_summary = "### 📈 今日行情\n\n"
    for s in stocks:
        emoji = "🟢" if s['change'] >= 0 else "🔴"
        stock_summary += f"- {emoji} **{s['name']}**({s['code']}): ¥{s['price']} {s['change']:+.2f} ({s['change_pct']:+.2f}%)\n"
    
    # 完整内容
    full_content = LEARNING_CONTENT + "\n\n" + stock_summary
    full_content += f"\n\n*更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*"
    
    title = f"📚 价值投资学习 - {datetime.now().strftime('%m-%d')}"
    
    if send_to_feishu(webhook_url, title, full_content):
        print("✅ 推送成功")
        return 0
    else:
        print("❌ 推送失败")
        return 1

if __name__ == "__main__":
    exit(main())
