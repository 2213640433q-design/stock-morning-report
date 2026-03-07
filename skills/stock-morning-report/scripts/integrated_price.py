#!/usr/bin/env python3
"""
百川盈孚稀土价格获取
通过网页爬取或API
"""

import json
import sys
import os
import urllib.request
import urllib.parse
import re
import ssl
from datetime import datetime
from typing import Dict, Optional

ssl._create_default_https_context = ssl._create_unverified_context

class BaiChuanCrawler:
    """百川盈孚爬虫"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
    
    def get_prnd_price(self) -> Dict:
        """
        获取氧化镨钕价格
        百川盈孚: https://www.baiinfo.com/
        """
        try:
            # 尝试获取百川盈孚首页的稀土数据
            url = "https://www.baiinfo.com/"
            
            req = urllib.request.Request(url, headers=self.headers)
            
            with urllib.request.urlopen(req, timeout=15) as response:
                html = response.read().decode('utf-8', errors='ignore')
                
                # 查找稀土相关价格
                # 百川盈孚页面通常是JSON格式
                
                # 尝试提取价格数据
                result = self._parse_price_from_html(html)
                if result.get("price"):
                    return result
                    
        except Exception as e:
            print(f"百川盈孚获取失败: {e}", file=sys.stderr)
        
        return {"error": "获取失败", "source": "百川盈孚"}
    
    def _parse_price_from_html(self, html: str) -> Dict:
        """从HTML解析价格"""
        result = {
            "product": "氧化镨钕",
            "price": None,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "source": "百川盈孚"
        }
        
        # 查找稀土相关数据
        # 百川盈孚数据通常在JavaScript变量中
        
        # 尝试匹配价格模式
        patterns = [
            r'氧化镨钕[\s\S]{0,50}?(\d{2,3}\.\d{1,2})\s*万元/吨',
            r'镨钕氧化物[\s\S]{0,50}?(\d{2,3}\.\d{1,2})\s*万元/吨',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                price = float(match.group(1))
                if 30 < price < 200:
                    result["price"] = price
                    break
        
        return result


class MetalOnlineCrawler:
    """金属在线爬虫"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
    
    def get_prnd_price(self) -> Dict:
        """
        从亚洲金属网获取
        https://www.asianmetal.cn/
        """
        try:
            url = "https://www.asianmetal.cn/price/PrNdOxide.cn.html"
            
            req = urllib.request.Request(url, headers=self.headers)
            
            with urllib.request.urlopen(req, timeout=15) as response:
                html = response.read().decode('utf-8', errors='ignore')
                
                result = {
                    "product": "氧化镨钕",
                    "price": None,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "source": "亚洲金属网"
                }
                
                # 提取价格
                patterns = [
                    r'(\d{2,3}\.\d{1,2})\s*[-~]\s*(\d{2,3}\.\d{1,2})\s*万元/吨',
                    r'(\d{2,3}\.\d{1,2})\s*万元/吨',
                ]
                
                for pattern in patterns:
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
                
                if result["price"]:
                    return result
                    
        except Exception as e:
            print(f"亚洲金属网获取失败: {e}", file=sys.stderr)
        
        return {"error": "获取失败", "source": "亚洲金属网"}


class IntegratedPriceFetcher:
    """整合多个数据源的获取器"""
    
    def __init__(self):
        self.sources = [
            ("百川盈孚", BaiChuanCrawler()),
            ("亚洲金属网", MetalOnlineCrawler()),
        ]
    
    def get_prnd_price(self) -> Dict:
        """
        尝试多个数据源获取氧化镨钕价格
        """
        for name, crawler in self.sources:
            try:
                print(f"尝试从{name}获取...", file=sys.stderr)
                result = crawler.get_prnd_price()
                if result.get("price") and "error" not in result:
                    print(f"✓ 成功从{name}获取: ¥{result['price']}万/吨", file=sys.stderr)
                    return result
            except Exception as e:
                print(f"✗ {name}失败: {e}", file=sys.stderr)
            
            # 短暂延迟，避免请求过快
            import time
            time.sleep(0.5)
        
        # 所有源都失败，使用参考价格
        print("⚠ 所有数据源失败，使用参考价格", file=sys.stderr)
        return {
            "product": "氧化镨钕",
            "price": 85.0,
            "unit": "万元/吨",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "source": "参考价格",
            "note": "所有数据源获取失败"
        }


def main():
    """测试"""
    fetcher = IntegratedPriceFetcher()
    
    print("="*60)
    print("整合稀土价格获取测试")
    print("="*60)
    
    result = fetcher.get_prnd_price()
    print("\n最终结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
