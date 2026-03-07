#!/usr/bin/env python3
"""
东方财富数据接口
免费获取股票、期货、大宗商品数据
"""

import json
import sys
import os
import urllib.request
import urllib.parse
import ssl
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# 忽略SSL证书验证
ssl._create_default_https_context = ssl._create_unverified_context

class EastMoneyAPI:
    """东方财富API封装"""
    
    def __init__(self):
        self.base_url = "https://push2.eastmoney.com/api"
        self.quote_url = "https://push2.eastmoney.com/api/qt/stock/get"
        self.futures_url = "https://push2.eastmoney.com/api/qt/futures/get"
        
    def get_stock_quote(self, code: str, market: str = "1") -> Dict:
        """
        获取股票实时行情
        
        Args:
            code: 股票代码
            market: 1=上海, 0=深圳
        """
        params = {
            "ut": "fa5fd1943c7b386f172d6893dbfba10b",
            "fltt": "2",
            "invt": "2",
            "v": "0",
            "fields": "f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f57,f58,f60,f61,f116,f117,f162,f163,f164,f165,f167,f170,f171,f173,f177,f183,f184,f185,f186,f187,f188,f189,f190",
            "secid": f"{market}.{code}"
        }
        
        try:
            url = f"{self.quote_url}?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://quote.eastmoney.com/',
            })
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                if 'data' in data and data['data']:
                    d = data['data']
                    # 东方财富字段需要除以100
                    price = d.get('f43', 0)
                    if price and price > 10000:  # 价格已经是以分为单位
                        divisor = 100
                    else:
                        divisor = 1
                    
                    return {
                        "code": code,
                        "name": d.get('f58', ''),
                        "price": d.get('f43', 0) / divisor if d.get('f43') else 0,
                        "open": d.get('f46', 0) / divisor if d.get('f46') else 0,
                        "high": d.get('f44', 0) / divisor if d.get('f44') else 0,
                        "low": d.get('f45', 0) / divisor if d.get('f45') else 0,
                        "prev_close": d.get('f60', 0) / divisor if d.get('f60') else 0,
                        "volume": d.get('f47', 0),
                        "amount": d.get('f48', 0),
                        "change": (d.get('f43', 0) - d.get('f60', 0)) / divisor if d.get('f43') and d.get('f60') else 0,
                        "change_pct": d.get('f170', 0) / 100 if d.get('f170') and isinstance(d.get('f170'), (int, float)) else 0,
                        "pe_ttm": d.get('f162', 0) / 100 if d.get('f162') and isinstance(d.get('f162'), (int, float)) else 35,
                        "pb": d.get('f167', 0) / 100 if d.get('f167') and isinstance(d.get('f167'), (int, float)) else 0,
                        "market_cap": d.get('f116', 0) / 100000000 if d.get('f116') else 0,
                        "source": "东方财富"
                    }
                    
        except Exception as e:
            print(f"东方财富股票接口错误: {e}", file=sys.stderr)
        
        return {"code": code, "error": "获取失败"}
    
    def get_futures_quote(self, code: str, market: str = "113") -> Dict:
        """
        获取期货实时行情
        
        Args:
            code: 期货代码
            market: 113=上期所, 114=大商所, 115=郑商所, 142=中金所
        """
        params = {
            "ut": "fa5fd1943c7b386f172d6893dbfba10b",
            "fltt": "2",
            "invt": "2",
            "v": "0",
            "fields": "f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f57,f58,f60,f61,f170",
            "secid": f"{market}.{code}"
        }
        
        try:
            url = f"{self.futures_url}?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://quote.eastmoney.com/',
            })
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                if 'data' in data and data['data']:
                    d = data['data']
                    return {
                        "code": code,
                        "name": d.get('f58', ''),
                        "price": d.get('f43', 0) / 100 if d.get('f43') else 0,
                        "open": d.get('f46', 0) / 100 if d.get('f46') else 0,
                        "high": d.get('f44', 0) / 100 if d.get('f44') else 0,
                        "low": d.get('f45', 0) / 100 if d.get('f45') else 0,
                        "prev_close": d.get('f60', 0) / 100 if d.get('f60') else 0,
                        "change_pct": d.get('f170', 0) / 100 if d.get('f170') else 0,
                        "source": "东方财富期货"
                    }
                    
        except Exception as e:
            print(f"东方财富期货接口错误: {e}", file=sys.stderr)
        
        return {"code": code, "error": "获取失败"}
    
    def get_rare_earth_prices(self) -> Dict:
        """
        获取稀土相关价格
        通过相关股票和期货推算
        """
        prices = {
            "prnd": None,
            "prnd_change_pct": None,
            "source": None,
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        # 尝试获取北方稀土股价作为参考
        nrer = self.get_stock_quote("600111", "1")
        if "error" not in nrer:
            prices["nrer_price"] = nrer.get("price")
            prices["nrer_change_pct"] = nrer.get("change_pct")
        
        # 尝试获取稀土ETF作为行业指数
        etf = self.get_stock_quote("516780", "1")  # 稀土ETF
        if "error" not in etf:
            prices["etf_price"] = etf.get("price")
            prices["etf_change_pct"] = etf.get("change_pct")
        
        # 基于股价变化估算氧化镨钕价格
        # 这是一个简化的估算模型
        base_prnd = 85.0  # 基准价格
        
        if prices.get("nrer_change_pct") is not None:
            # 假设股价变化与稀土价格变化相关性为0.7
            estimated_change = prices["nrer_change_pct"] * 0.7
            prices["prnd"] = round(base_prnd * (1 + estimated_change/100), 2)
            prices["prnd_change_pct"] = round(estimated_change, 2)
            prices["source"] = "基于股价估算"
        else:
            prices["prnd"] = base_prnd
            prices["prnd_change_pct"] = 0.0
            prices["source"] = "基准价格"
        
        return prices


class EastMoneyDataFetcher:
    """整合东方财富数据获取"""
    
    def __init__(self):
        self.em = EastMoneyAPI()
    
    def get_all_data(self, stock_code: str = "600111") -> Dict:
        """获取所有数据"""
        
        print("正在从东方财富获取数据...", file=sys.stderr)
        
        # 1. 获取股票行情
        stock = self.em.get_stock_quote(stock_code, "1")
        
        # 2. 获取稀土价格估算
        prices = self.em.get_rare_earth_prices()
        
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M"),
            "stock": stock,
            "rare_earth_prices": prices,
            "data_source": "东方财富"
        }


def main():
    """测试"""
    fetcher = EastMoneyDataFetcher()
    data = fetcher.get_all_data("600111")
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
