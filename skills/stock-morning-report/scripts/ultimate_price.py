#!/usr/bin/env python3
"""
稀土价格获取 - 终极方案
结合搜索、新闻提取、参考价格
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

class UltimatePriceFetcher:
    """终极价格获取器"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        # 参考价格基准（定期手动更新）
        self.reference_prices = {
            "prnd": 85.0,      # 氧化镨钕
            "dy": 165.0,       # 氧化镝
            "tb": 580.0,       # 氧化铽
        }
    
    def get_prnd_price(self) -> Dict:
        """
        获取氧化镨钕价格
        优先级: 新闻提取 > 搜索 > 参考价格
        """
        # 1. 先获取新闻
        news = self._fetch_news()
        
        # 2. 从新闻中提取价格
        price_from_news = self._extract_price_from_news(news)
        if price_from_news:
            return {
                "product": "氧化镨钕",
                "price": price_from_news,
                "unit": "万元/吨",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "source": "新闻提取",
                "news_count": len(news)
            }
        
        # 3. 尝试搜索
        price_from_search = self._search_price()
        if price_from_search:
            return price_from_search
        
        # 4. 使用参考价格
        return {
            "product": "氧化镨钕",
            "price": self.reference_prices["prnd"],
            "unit": "万元/吨",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "source": "参考价格",
            "note": "自动获取失败，使用参考价格"
        }
    
    def _fetch_news(self) -> List[Dict]:
        """获取稀土相关新闻"""
        news = []
        
        try:
            # 新浪搜索
            url = "https://search.sina.com.cn/?q=%E6%B0%A7%E5%8C%96%E9%95%8F%E9%92%95&c=news&from=channel&ie=utf-8"
            req = urllib.request.Request(url, headers=self.headers)
            
            with urllib.request.urlopen(req, timeout=15) as response:
                html = response.read().decode('utf-8', errors='ignore')
                
                pattern = r'<h2><a[^>]*href="([^"]+)"[^>]*>(.*?)</a></h2>'
                matches = re.findall(pattern, html, re.DOTALL)
                
                for link, title in matches[:10]:
                    title = re.sub(r'<[^>]+>', '', title).strip()
                    if title and len(title) > 10:
                        news.append({
                            "title": title,
                            "url": link,
                            "source": "新浪"
                        })
        except Exception as e:
            print(f"获取新闻失败: {e}", file=sys.stderr)
        
        return news
    
    def _extract_price_from_news(self, news: List[Dict]) -> Optional[float]:
        """从新闻标题中提取价格"""
        for item in news:
            title = item.get("title", "")
            
            # 匹配价格模式
            # 例如: "氧化镨钕价格跌至43.5万元/吨"、"氧化镨钕43-44万元/吨"
            patterns = [
                r'氧化镨钕[\s\S]*?(\d{2,3}\.\d{1,2})\s*[-~]\s*(\d{2,3}\.\d{1,2})\s*万元?/吨',
                r'氧化镨钕[\s\S]*?(\d{2,3}\.\d{1,2})\s*万元?/吨',
                r'氧化镨钕[\s\S]*?(\d{2,3})\s*万/吨',
                r'镨钕氧化物[\s\S]*?(\d{2,3}\.\d{1,2})\s*万元?/吨',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, title)
                if match:
                    try:
                        if len(match.groups()) == 2 and match.group(2):
                            # 价格区间，取平均
                            low = float(match.group(1))
                            high = float(match.group(2))
                            price = (low + high) / 2
                        else:
                            price = float(match.group(1))
                        
                        # 验证价格合理性
                        if 30 <= price <= 150:
                            print(f"✓ 从新闻提取价格: ¥{price}万/吨", file=sys.stderr)
                            print(f"  来源: {title[:50]}...", file=sys.stderr)
                            return round(price, 2)
                    except:
                        pass
        
        return None
    
    def _search_price(self) -> Optional[Dict]:
        """通过搜索获取价格"""
        try:
            # 搜狗搜索
            url = "https://www.sogou.com/web?query=%E6%B0%A7%E5%8C%96%E9%95%8F%E9%92%95%E4%BB%B7%E6%A0%BC"
            req = urllib.request.Request(url, headers=self.headers)
            
            with urllib.request.urlopen(req, timeout=15) as response:
                html = response.read().decode('utf-8', errors='ignore')
                
                # 查找价格
                patterns = [
                    r'(\d{2,3}\.\d{1,2})\s*[-~]\s*(\d{2,3}\.\d{1,2})\s*万元/吨',
                    r'(\d{2,3}\.\d{1,2})\s*万元/吨',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, html)
                    if match:
                        if len(match.groups()) == 2 and match.group(2):
                            low = float(match.group(1))
                            high = float(match.group(2))
                            price = round((low + high) / 2, 2)
                            price_range = f"{low}-{high}"
                        else:
                            price = float(match.group(1))
                            price_range = None
                        
                        if 30 <= price <= 150:
                            return {
                                "product": "氧化镨钕",
                                "price": price,
                                "price_range": price_range,
                                "unit": "万元/吨",
                                "date": datetime.now().strftime("%Y-%m-%d"),
                                "source": "搜狗搜索"
                            }
        except Exception as e:
            print(f"搜索获取失败: {e}", file=sys.stderr)
        
        return None


def main():
    """测试"""
    fetcher = UltimatePriceFetcher()
    
    print("="*60)
    print("终极稀土价格获取测试")
    print("="*60)
    
    result = fetcher.get_prnd_price()
    print("\n最终结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
