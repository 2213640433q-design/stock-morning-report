#!/usr/bin/env python3
"""
生意社稀土价格爬虫
获取氧化镨钕等稀土现货价格
"""

import json
import sys
import os
import urllib.request
import urllib.parse
import re
import ssl
from datetime import datetime
from typing import Dict, List, Optional

ssl._create_default_https_context = ssl._create_unverified_context

class ShengyisheCrawler:
    """生意社爬虫"""
    
    def __init__(self):
        self.base_url = "https://www.100ppi.com"
        
    def get_prnd_price(self) -> Dict:
        """
        获取氧化镨钕价格
        """
        try:
            # 氧化镨钕页面
            url = "https://www.100ppi.com/vane/detail-959.html"
            
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9',
            })
            
            with urllib.request.urlopen(req, timeout=15) as response:
                html = response.read().decode('utf-8', errors='ignore')
                
                result = {
                    "product": "氧化镨钕",
                    "price": None,
                    "change": None,
                    "change_pct": None,
                    "date": None,
                    "source": "生意社",
                    "url": url
                }
                
                # 提取最新价格
                # 格式: 氧化镨钕 43.25-43.75 万元/吨 或 氧化镨钕 43.5 万元/吨
                price_patterns = [
                    r'氧化镨钕[\s\S]*?(\d+\.?\d*)\s*[-~]\s*(\d+\.?\d*)\s*万元/吨',
                    r'氧化镨钕[\s\S]*?(\d+\.?\d*)\s*万元/吨',
                ]
                
                for pattern in price_patterns:
                    match = re.search(pattern, html)
                    if match:
                        if len(match.groups()) == 2:
                            low = float(match.group(1))
                            high = float(match.group(2))
                            result["price"] = round((low + high) / 2, 2)
                            result["price_range"] = f"{low}-{high}"
                        else:
                            result["price"] = float(match.group(1))
                        break
                
                # 提取涨跌
                change_patterns = [
                    r'较昨日[\s\S]*?([+-]?\d+\.?\d*)',
                    r'涨跌[\s\S]*?([+-]?\d+\.?\d*)',
                    r'([+-]?\d+\.?\d*)%',
                ]
                
                for pattern in change_patterns:
                    match = re.search(pattern, html)
                    if match:
                        change_str = match.group(1)
                        if '%' in html[match.start():match.end()+5]:
                            result["change_pct"] = float(change_str)
                        else:
                            result["change"] = float(change_str)
                        break
                
                # 提取日期
                date_pattern = r'(\d{4}-\d{2}-\d{2}|\d{4}年\d{2}月\d{2}日)'
                match = re.search(date_pattern, html)
                if match:
                    result["date"] = match.group(1)
                else:
                    result["date"] = datetime.now().strftime("%Y-%m-%d")
                
                if result["price"]:
                    return result
                    
        except Exception as e:
            print(f"生意社获取失败: {e}", file=sys.stderr)
        
        return {"error": "获取失败", "source": "生意社"}
    
    def get_rare_earth_prices(self) -> Dict:
        """
        获取多种稀土价格
        """
        products = {
            "prnd": {"name": "氧化镨钕", "id": "959"},
            "dy": {"name": "氧化镝", "id": "960"},
            "tb": {"name": "氧化铽", "id": "961"},
            "gd": {"name": "氧化钆", "id": "962"},
        }
        
        results = {}
        
        for key, info in products.items():
            try:
                url = f"https://www.100ppi.com/vane/detail-{info['id']}.html"
                
                req = urllib.request.Request(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                })
                
                with urllib.request.urlopen(req, timeout=15) as response:
                    html = response.read().decode('utf-8', errors='ignore')
                    
                    # 提取价格
                    match = re.search(rf'{info["name"]}[\s\S]*?(\d+\.?\d*)\s*[-~]?\s*(\d+\.?\d*)?\s*万元/吨', html)
                    if match:
                        if match.group(2):
                            price = (float(match.group(1)) + float(match.group(2))) / 2
                        else:
                            price = float(match.group(1))
                        
                        results[key] = {
                            "name": info["name"],
                            "price": round(price, 2),
                            "unit": "万元/吨",
                            "date": datetime.now().strftime("%Y-%m-%d")
                        }
            except Exception as e:
                print(f"获取{info['name']}失败: {e}", file=sys.stderr)
        
        return results
    
    def get_price_trend(self, days: int = 7) -> List[Dict]:
        """
        获取价格走势
        """
        try:
            url = "https://www.100ppi.com/vane/detail-959.html"
            
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            })
            
            with urllib.request.urlopen(req, timeout=15) as response:
                html = response.read().decode('utf-8', errors='ignore')
                
                # 尝试提取历史价格数据
                # 生意社页面通常有图表数据
                trend = []
                
                # 查找价格数据模式
                # 格式可能是JSON或表格
                json_match = re.search(r'var\s+chart_data\s*=\s*(\[.*?\]);', html, re.DOTALL)
                if json_match:
                    try:
                        data = json.loads(json_match.group(1))
                        for item in data[-days:]:
                            trend.append({
                                "date": item.get("date"),
                                "price": item.get("price")
                            })
                    except:
                        pass
                
                return trend
                
        except Exception as e:
            print(f"获取价格走势失败: {e}", file=sys.stderr)
        
        return []


def main():
    """测试"""
    crawler = ShengyisheCrawler()
    
    print("="*60)
    print("生意社稀土价格爬虫测试")
    print("="*60)
    
    # 1. 获取氧化镨钕价格
    print("\n【1】获取氧化镨钕价格...")
    prnd = crawler.get_prnd_price()
    print(json.dumps(prnd, ensure_ascii=False, indent=2))
    
    # 2. 获取多种稀土价格
    print("\n【2】获取多种稀土价格...")
    all_prices = crawler.get_rare_earth_prices()
    print(json.dumps(all_prices, ensure_ascii=False, indent=2))
    
    # 3. 获取价格走势
    print("\n【3】获取价格走势...")
    trend = crawler.get_price_trend(7)
    print(json.dumps(trend, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
