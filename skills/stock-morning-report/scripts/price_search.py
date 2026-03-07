#!/usr/bin/env python3
"""
稀土价格获取 - 综合多源
通过搜索获取最新价格信息
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

class RareEarthPriceSearch:
    """稀土价格搜索器"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
    
    def search_prnd_price(self) -> Dict:
        """
        通过搜索获取氧化镨钕价格
        """
        # 搜索关键词
        keywords = ["氧化镨钕价格", "氧化镨钕最新价格", "氧化镨钕今日价格"]
        
        for keyword in keywords:
            try:
                result = self._search_from_baidu(keyword)
                if result.get("price"):
                    return result
            except Exception as e:
                print(f"百度搜索失败: {e}", file=sys.stderr)
            
            try:
                result = self._search_from_sogou(keyword)
                if result.get("price"):
                    return result
            except Exception as e:
                print(f"搜狗搜索失败: {e}", file=sys.stderr)
        
        # 使用参考价格
        return {
            "product": "氧化镨钕",
            "price": 85.0,
            "unit": "万元/吨",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "source": "参考价格",
            "note": "搜索获取失败，使用参考价格"
        }
    
    def _search_from_baidu(self, keyword: str) -> Dict:
        """从百度搜索获取"""
        encoded = urllib.parse.quote(keyword)
        url = f"https://www.baidu.com/s?wd={encoded}"
        
        req = urllib.request.Request(url, headers=self.headers)
        
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            # 查找价格模式
            # 常见格式: 43.5万元/吨、43-44万元/吨、435000元/吨
            patterns = [
                r'(\d+\.?\d*)\s*[-~]\s*(\d+\.?\d*)\s*万元/吨',
                r'(\d+\.?\d*)\s*万元/吨',
                r'(\d{2,3})\s*万/吨',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html)
                if match:
                    if len(match.groups()) == 2:
                        low = float(match.group(1))
                        high = float(match.group(2))
                        price = round((low + high) / 2, 2)
                        price_range = f"{low}-{high}"
                    else:
                        price = float(match.group(1))
                        price_range = None
                    
                    return {
                        "product": "氧化镨钕",
                        "price": price,
                        "price_range": price_range,
                        "unit": "万元/吨",
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "source": "百度搜索",
                        "keyword": keyword
                    }
        
        return {}
    
    def _search_from_sogou(self, keyword: str) -> Dict:
        """从搜狗搜索获取"""
        encoded = urllib.parse.quote(keyword)
        url = f"https://www.sogou.com/web?query={encoded}"
        
        req = urllib.request.Request(url, headers=self.headers)
        
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            patterns = [
                r'(\d+\.?\d*)\s*[-~]\s*(\d+\.?\d*)\s*万元/吨',
                r'(\d+\.?\d*)\s*万元/吨',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html)
                if match:
                    if len(match.groups()) == 2:
                        low = float(match.group(1))
                        high = float(match.group(2))
                        price = round((low + high) / 2, 2)
                        price_range = f"{low}-{high}"
                    else:
                        price = float(match.group(1))
                        price_range = None
                    
                    return {
                        "product": "氧化镨钕",
                        "price": price,
                        "price_range": price_range,
                        "unit": "万元/吨",
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "source": "搜狗搜索",
                        "keyword": keyword
                    }
        
        return {}
    
    def get_prnd_from_news(self, news_items: List[Dict]) -> Optional[float]:
        """
        从新闻标题中提取氧化镨钕价格
        """
        for news in news_items:
            title = news.get("title", "")
            
            # 查找价格模式
            # 例如: "氧化镨钕价格跌至43.5万元/吨"
            patterns = [
                r'氧化镨钕.*?([\d\.]+)\s*[-~]?\s*([\d\.]+)?\s*万元/吨',
                r'氧化镨钕.*?([\d\.]+)\s*万/吨',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, title)
                if match:
                    if match.group(2):
                        price = (float(match.group(1)) + float(match.group(2))) / 2
                    else:
                        price = float(match.group(1))
                    
                    if 30 < price < 150:  # 合理价格范围
                        return round(price, 2)
        
        return None


def main():
    """测试"""
    searcher = RareEarthPriceSearch()
    
    print("="*60)
    print("稀土价格搜索测试")
    print("="*60)
    
    result = searcher.search_prnd_price()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
