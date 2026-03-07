#!/usr/bin/env python3
"""
生意社稀土价格爬虫
https://www.100ppi.com
"""

import json
import sys
import os
import urllib.request
import urllib.parse
import re
import ssl
import time
from datetime import datetime
from typing import Dict, List, Optional

ssl._create_default_https_context = ssl._create_unverified_context

class ShengyisheCrawler:
    """生意社爬虫"""
    
    def __init__(self):
        self.base_url = "https://www.100ppi.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        
    def get_prnd_price(self) -> Dict:
        """
        获取氧化镨钕价格
        生意社页面: https://www.100ppi.com/vane/detail-959.html
        """
        try:
            # 先获取主页建立session
            self._get_homepage()
            
            # 获取氧化镨钕详情页
            url = "https://www.100ppi.com/vane/detail-959.html"
            
            req = urllib.request.Request(url, headers=self.headers)
            
            with urllib.request.urlopen(req, timeout=20) as response:
                html = response.read().decode('utf-8', errors='ignore')
                
                result = self._parse_prnd_page(html)
                if result.get("price"):
                    return result
                    
        except Exception as e:
            print(f"生意社获取失败: {e}", file=sys.stderr)
        
        return {"error": "获取失败", "source": "生意社"}
    
    def _get_homepage(self):
        """获取主页建立session"""
        try:
            url = "https://www.100ppi.com/"
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                response.read()
        except:
            pass
    
    def _parse_prnd_page(self, html: str) -> Dict:
        """解析氧化镨钕页面"""
        result = {
            "product": "氧化镨钕",
            "price": None,
            "price_range": None,
            "change": None,
            "change_pct": None,
            "date": None,
            "source": "生意社",
            "url": "https://www.100ppi.com/vane/detail-959.html"
        }
        
        # 提取价格 - 多种模式尝试
        # 模式1: 价格区间 43.25-43.75 万元/吨
        patterns = [
            # 价格区间模式
            r'氧化镨钕[\s\S]{0,100}?(\d{2,3}\.\d{1,2})\s*[-~]\s*(\d{2,3}\.\d{1,2})\s*万元/吨',
            # 单一价格模式
            r'氧化镨钕[\s\S]{0,100}?(\d{2,3}\.\d{1,2})\s*万元/吨',
            # 表格中的价格
            r'<td[^>]*>[\s\S]*?氧化镨钕[\s\S]*?</td>[\s\S]*?<td[^>]*>(\d{2,3}\.\d{1,2})</td>',
            # 最新价格
            r'最新价[\s\S]{0,50}?(\d{2,3}\.\d{1,2})',
            # 日均价
            r'日均价[\s\S]{0,50}?(\d{2,3}\.\d{1,2})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    # 价格区间
                    low = float(match.group(1))
                    high = float(match.group(2))
                    result["price"] = round((low + high) / 2, 2)
                    result["price_range"] = f"{low}-{high}"
                else:
                    # 单一价格
                    price = float(match.group(1))
                    if 30 < price < 150:  # 合理价格范围
                        result["price"] = price
                break
        
        # 提取涨跌
        change_patterns = [
            r'较昨日[\s\S]{0,30}?([+-]?\d+\.?\d*)[\s\S]{0,10}万元/吨',
            r'涨跌[\s\S]{0,30}?([+-]?\d+\.?\d*)',
            r'([+-]?\d+\.?\d*)%',
        ]
        
        for pattern in change_patterns:
            match = re.search(pattern, html)
            if match:
                change_str = match.group(1)
                try:
                    if '%' in html[match.start():match.end()+10]:
                        result["change_pct"] = float(change_str)
                    else:
                        result["change"] = float(change_str)
                    break
                except:
                    pass
        
        # 提取日期
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{4}年\d{2}月\d{2}日)',
            r'更新时间[\s\S]{0,20}?(\d{2}-\d{2})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, html)
            if match:
                date_str = match.group(1)
                if len(date_str) == 5:  # MM-DD格式
                    result["date"] = f"{datetime.now().year}-{date_str}"
                else:
                    result["date"] = date_str.replace('年', '-').replace('月', '-').replace('日', '')
                break
        
        if not result["date"]:
            result["date"] = datetime.now().strftime("%Y-%m-%d")
        
        return result
    
    def get_all_rare_earth_prices(self) -> Dict:
        """
        获取所有稀土价格
        """
        products = {
            "prnd": {"name": "氧化镨钕", "id": "959"},
            "dy": {"name": "氧化镝", "id": "960"},
            "tb": {"name": "氧化铽", "id": "961"},
        }
        
        results = {}
        
        for key, info in products.items():
            try:
                url = f"https://www.100ppi.com/vane/detail-{info['id']}.html"
                req = urllib.request.Request(url, headers=self.headers)
                
                with urllib.request.urlopen(req, timeout=15) as response:
                    html = response.read().decode('utf-8', errors='ignore')
                    
                    # 提取价格
                    match = re.search(rf'{info["name"]}[\s\S]{{0,100}}?(\d{{2,3}}\.\d{{1,2}})\s*[-~]?\s*(\d{{2,3}}\.\d{{1,2}})?\s*万元/吨', html, re.IGNORECASE)
                    if match:
                        if match.group(2):
                            price = (float(match.group(1)) + float(match.group(2))) / 2
                            price_range = f"{match.group(1)}-{match.group(2)}"
                        else:
                            price = float(match.group(1))
                            price_range = None
                        
                        if 30 < price < 200:
                            results[key] = {
                                "name": info["name"],
                                "price": round(price, 2),
                                "price_range": price_range,
                                "unit": "万元/吨",
                                "date": datetime.now().strftime("%Y-%m-%d"),
                                "source": "生意社"
                            }
            except Exception as e:
                print(f"获取{info['name']}失败: {e}", file=sys.stderr)
        
        return results


def main():
    """测试"""
    crawler = ShengyisheCrawler()
    
    print("="*60)
    print("生意社稀土价格爬虫测试")
    print("="*60)
    
    # 获取氧化镨钕价格
    print("\n【1】获取氧化镨钕价格...")
    prnd = crawler.get_prnd_price()
    print(json.dumps(prnd, ensure_ascii=False, indent=2))
    
    # 获取所有稀土价格
    print("\n【2】获取所有稀土价格...")
    all_prices = crawler.get_all_rare_earth_prices()
    print(json.dumps(all_prices, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
