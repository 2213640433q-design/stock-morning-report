#!/usr/bin/env python3
"""
同花顺期货数据接口
获取氧化镨钕期货实时价格
"""

import json
import sys
import os
import urllib.request
import urllib.parse
import ssl
from datetime import datetime
from typing import Dict, Optional

ssl._create_default_https_context = ssl._create_unverified_context

class THSFuturesAPI:
    """同花顺期货API"""
    
    def __init__(self):
        self.base_url = "https://basic.10jqka.com.cn/api/stockph"
        self.quote_url = "http://d.10jqka.com.cn/v4/line/"
        
    def get_futures_quote(self, code: str) -> Dict:
        """
        获取期货实时行情
        
        Args:
            code: 期货代码，如:
                - 氧化镨钕期货: prnd (如果有)
                - 稀土相关期货代码
        """
        # 同花顺期货代码格式: market_code + futures_code
        # 113=上期所, 114=大商所, 115=郑商所
        
        # 尝试获取氧化镨钕相关期货
        # 注意: 目前国内可能没有直接的氧化镨钕期货
        # 但可能有稀土相关期货或相关金属期货
        
        futures_codes = [
            ("115", "PRND"),   # 郑商所 - 尝试氧化镨钕
            ("113", "RE"),     # 上期所 - 尝试稀土
            ("114", "RE"),     # 大商所 - 尝试稀土
        ]
        
        for market, futures_code in futures_codes:
            try:
                result = self._fetch_futures(market, futures_code)
                if result and "error" not in result:
                    return result
            except Exception as e:
                continue
        
        return {"error": "未找到氧化镨钕期货数据"}
    
    def _fetch_futures(self, market: str, code: str) -> Dict:
        """获取特定期货数据"""
        # 同花顺期货数据接口
        secid = f"{market}.{code}"
        url = f"http://d.10jqka.com.cn/v4/line/{secid}/01/last.js"
        
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'http://stockpage.10jqka.com.cn/',
        })
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read().decode('utf-8', errors='ignore')
            
            # 解析返回数据
            # 格式: quotebridge_v4_line_xxx({...})
            if 'quotebridge_' in data:
                start = data.find('{')
                end = data.rfind('}') + 1
                if start > 0 and end > start:
                    json_data = json.loads(data[start:end])
                    
                    # 解析期货数据
                    if 'data' in json_data:
                        lines = json_data['data'].split('\n')
                        if lines:
                            # 最新一条数据
                            latest = lines[-1].split(',')
                            if len(latest) >= 5:
                                return {
                                    "code": code,
                                    "market": market,
                                    "date": latest[0],
                                    "open": float(latest[1]),
                                    "high": float(latest[2]),
                                    "low": float(latest[3]),
                                    "close": float(latest[4]),
                                    "volume": int(latest[5]) if len(latest) > 5 else 0,
                                    "source": "同花顺期货"
                                }
        
        return {"error": "数据解析失败"}
    
    def get_rare_earth_index(self) -> Dict:
        """
        获取稀土板块指数
        作为稀土价格的参考
        """
        try:
            # 稀土板块指数代码: 885343
            # 同花顺板块指数
            url = "http://d.10jqka.com.cn/v4/line/1a/885343/01/last.js"
            
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'http://stockpage.10jqka.com.cn/',
            })
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = response.read().decode('utf-8', errors='ignore')
                
                if 'quotebridge_' in data:
                    start = data.find('{')
                    end = data.rfind('}') + 1
                    if start > 0 and end > start:
                        json_data = json.loads(data[start:end])
                        
                        if 'data' in json_data:
                            lines = json_data['data'].split('\n')
                            if lines:
                                latest = lines[-1].split(',')
                                if len(latest) >= 5:
                                    close = float(latest[4])
                                    prev_close = float(lines[-2].split(',')[4]) if len(lines) > 1 else close
                                    
                                    return {
                                        "index_name": "稀土永磁板块",
                                        "index_code": "885343",
                                        "close": close,
                                        "prev_close": prev_close,
                                        "change": close - prev_close,
                                        "change_pct": (close - prev_close) / prev_close * 100 if prev_close else 0,
                                        "date": latest[0],
                                        "source": "同花顺板块"
                                    }
        except Exception as e:
            print(f"获取稀土板块指数失败: {e}", file=sys.stderr)
        
        return {"error": "获取失败"}
    
    def get_relevant_stocks(self) -> Dict:
        """
        获取稀土相关股票数据
        用于综合判断稀土价格趋势
        """
        stocks = {
            "600111": "北方稀土",
            "600010": "包钢股份",
            "000831": "五矿稀土",
            "600392": "盛和资源",
            "600549": "厦门钨业",
        }
        
        results = {}
        
        for code, name in stocks.items():
            try:
                market = "1" if code.startswith('6') else "0"
                url = f"http://d.10jqka.com.cn/v4/line/{market}{code}/01/last.js"
                
                req = urllib.request.Request(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Referer': 'http://stockpage.10jqka.com.cn/',
                })
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = response.read().decode('utf-8', errors='ignore')
                    
                    if 'quotebridge_' in data:
                        start = data.find('{')
                        end = data.rfind('}') + 1
                        if start > 0 and end > start:
                            json_data = json.loads(data[start:end])
                            
                            if 'data' in json_data:
                                lines = json_data['data'].split('\n')
                                if lines:
                                    latest = lines[-1].split(',')
                                    if len(latest) >= 5:
                                        close = float(latest[4])
                                        prev_close = float(lines[-2].split(',')[4]) if len(lines) > 1 else close
                                        
                                        results[code] = {
                                            "name": name,
                                            "price": close,
                                            "change_pct": (close - prev_close) / prev_close * 100 if prev_close else 0
                                        }
            except Exception as e:
                print(f"获取{name}失败: {e}", file=sys.stderr)
        
        return results
    
    def estimate_prnd_price(self) -> Dict:
        """
        综合多种数据估算氧化镨钕价格
        """
        # 1. 获取稀土板块指数
        index = self.get_rare_earth_index()
        
        # 2. 获取相关股票
        stocks = self.get_relevant_stocks()
        
        # 3. 计算综合变化
        changes = []
        
        if "error" not in index:
            changes.append(index.get("change_pct", 0))
        
        for code, data in stocks.items():
            changes.append(data.get("change_pct", 0))
        
        if changes:
            avg_change = sum(changes) / len(changes)
        else:
            avg_change = 0
        
        # 4. 估算氧化镨钕价格
        # 基准价: 85万/吨
        # 假设股价与稀土价格相关性为0.6
        base_price = 85.0
        estimated_change = avg_change * 0.6
        estimated_price = base_price * (1 + estimated_change / 100)
        
        return {
            "prnd_price": round(estimated_price, 2),
            "prnd_change_pct": round(estimated_change, 2),
            "base_price": base_price,
            "avg_stock_change": round(avg_change, 2),
            "source": "同花顺综合估算",
            "components": {
                "index": index if "error" not in index else None,
                "stocks": stocks
            },
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M")
        }


def main():
    """测试"""
    ths = THSFuturesAPI()
    
    print("="*60)
    print("同花顺稀土数据测试")
    print("="*60)
    
    # 1. 尝试获取期货
    print("\n【1】尝试获取氧化镨钕期货...")
    futures = ths.get_futures_quote("PRND")
    print(json.dumps(futures, ensure_ascii=False, indent=2))
    
    # 2. 获取稀土板块指数
    print("\n【2】获取稀土板块指数...")
    index = ths.get_rare_earth_index()
    print(json.dumps(index, ensure_ascii=False, indent=2))
    
    # 3. 获取相关股票
    print("\n【3】获取稀土相关股票...")
    stocks = ths.get_relevant_stocks()
    print(json.dumps(stocks, ensure_ascii=False, indent=2))
    
    # 4. 综合估算
    print("\n【4】综合估算氧化镨钕价格...")
    estimate = ths.estimate_prnd_price()
    print(json.dumps(estimate, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
