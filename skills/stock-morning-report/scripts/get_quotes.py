#!/usr/bin/env python3
"""
获取自选股实时行情
"""

import json
import urllib.request
import sys

def get_stock_quote(code):
    """获取单只股票行情（使用腾讯API）"""
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
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read().decode('gbk', errors='ignore')
            
            # 解析数据
            # 格式: v_sh600111="1~北方稀土~...";
            prefix = f'v_{market}{code}="'
            if prefix in data:
                start = data.find(prefix) + len(prefix)
                end = data.find('"', start)
                content = data[start:end]
                fields = content.split('~')
                
                if len(fields) >= 35:
                    return {
                        "code": code,
                        "name": fields[1],
                        "price": float(fields[3]),
                        "prev_close": float(fields[4]),
                        "open": float(fields[5]),
                        "high": float(fields[33]),
                        "low": float(fields[34]),
                        "volume": int(fields[6]) if fields[6].isdigit() else 0,
                        "update_time": fields[30] if len(fields) > 30 else "",
                        "change": round(float(fields[3]) - float(fields[4]), 2),
                        "change_pct": round((float(fields[3]) - float(fields[4])) / float(fields[4]) * 100, 2)
                    }
    except Exception as e:
        return {"code": code, "error": str(e)}
    
    return {"code": code, "error": "无法获取数据"}

def get_watchlist_quotes(watchlist):
    """获取自选股列表的行情"""
    results = []
    for stock in watchlist:
        quote = get_stock_quote(stock["code"])
        results.append(quote)
    return results

if __name__ == "__main__":
    # 默认自选股
    watchlist = [
        {"code": "600111", "name": "北方稀土"},
        {"code": "000001", "name": "平安银行"},
    ]
    
    quotes = get_watchlist_quotes(watchlist)
    print(json.dumps(quotes, ensure_ascii=False, indent=2))
