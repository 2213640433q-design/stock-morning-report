#!/usr/bin/env python3
"""
股票晨报生成器 - 集成基本面估值模型
"""

import json
import sys
import os
import urllib.request
import urllib.parse
import re
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from nrer_valuation import NRERValuationModel

DEFAULT_WATCHLIST = [
    {"code": "600111", "name": "北方稀土"},
]

def get_watchlist():
    config_path = os.path.expanduser("~/.config/stock-morning-report/watchlist.json")
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    return DEFAULT_WATCHLIST

def get_stock_quote(code):
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
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read().decode('gbk', errors='ignore')
            
            prefix = f'v_{market}{code}="'
            if prefix in data:
                start = data.find(prefix) + len(prefix)
                end = data.find('"', start)
                content = data[start:end]
                fields = content.split('~')
                
                if len(fields) >= 35:
                    price = float(fields[3])
                    prev_close = float(fields[4])
                    change = round(price - prev_close, 2)
                    change_pct = round(change / prev_close * 100, 2)
                    
                    return {
                        "code": code,
                        "name": fields[1],
                        "price": price,
                        "prev_close": prev_close,
                        "open": float(fields[5]),
                        "high": float(fields[33]),
                        "low": float(fields[34]),
                        "volume": int(fields[6]) if fields[6].isdigit() else 0,
                        "update_time": fields[30] if len(fields) > 30 else "",
                        "change": change,
                        "change_pct": change_pct
                    }
    except Exception as e:
        return {"code": code, "error": str(e)}
    
    return {"code": code, "error": "无法获取数据"}

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&gt;', '>').replace('&lt;', '<').replace('&amp;', '&')
    text = text.replace('&quot;', '"').replace('&nbsp;', ' ')
    text = ' '.join(text.split())
    return text.strip()

def is_valid_news(title):
    if not title:
        return False
    if len(title) < 8 or len(title) > 100:
        return False
    invalid_patterns = ['level2', '点击', '下载', 'APP', '登录', '注册', '>>', '<<', '鿴', '查看更多']
    for pattern in invalid_patterns:
        if pattern.lower() in title.lower():
            return False
    if not re.search(r'[\u4e00-\u9fa5]', title):
        return False
    return True

def fetch_news_from_sina_search(stock_name, limit=15):
    try:
        encoded_name = urllib.parse.quote(stock_name)
        url = f"https://search.sina.com.cn/?q={encoded_name}&c=news&from=channel&ie=utf-8"
        
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            news_items = []
            pattern = r'<h2><a[^>]*href="([^"]+)"[^>]*>(.*?)</a></h2>'
            matches = re.findall(pattern, html, re.DOTALL)
            
            for link, title in matches[:limit]:
                title = clean_text(title)
                if is_valid_news(title):
                    news_items.append({
                        "title": title,
                        "url": link,
                        "source": "新浪",
                        "time": ""
                    })
            
            return news_items
            
    except Exception as e:
        print(f"新浪搜索获取失败: {e}", file=sys.stderr)
        return []

def fetch_all_news(stock_code, stock_name, limit=15):
    return fetch_news_from_sina_search(stock_name, limit)

def generate_report(watchlist):
    report = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M"),
        "stocks": []
    }
    
    for stock in watchlist:
        code = stock["code"]
        name = stock["name"]
        
        print(f"正在处理: {name} ({code})...", file=sys.stderr)
        
        quote = get_stock_quote(code)
        if 'error' not in quote:
            print(f"  行情: ¥{quote.get('price', '-')} ({quote.get('change_pct', 0)}%)", file=sys.stderr)
        
        print(f"  获取新闻...", file=sys.stderr)
        news = fetch_all_news(code, name, limit=15)
        print(f"  获取到 {len(news)} 条有效新闻", file=sys.stderr)
        
        # 使用估值模型进行分析
        if code == "600111":
            print(f"  进行基本面估值分析...", file=sys.stderr)
            model = NRERValuationModel()
            valuation_report = model.generate_report(code, name, news, quote)
        else:
            valuation_report = None
        
        stock_report = {
            "code": code,
            "name": name,
            "quote": quote,
            "news": news,
            "valuation": valuation_report
        }
        report["stocks"].append(stock_report)
    
    return report

def save_report(report):
    report_dir = os.path.expanduser("~/.config/stock-morning-report/reports")
    os.makedirs(report_dir, exist_ok=True)
    
    filename = f"{report['date']}.json"
    filepath = os.path.join(report_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    return filepath

def main():
    watchlist = get_watchlist()
    
    print(f"开始生成 {datetime.now().strftime('%Y-%m-%d')} 股票晨报...", file=sys.stderr)
    print(f"自选股数量: {len(watchlist)}", file=sys.stderr)
    
    report = generate_report(watchlist)
    filepath = save_report(report)
    
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\n报告已保存: {filepath}", file=sys.stderr)

if __name__ == "__main__":
    main()
