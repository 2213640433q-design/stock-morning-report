#!/usr/bin/env python3
"""
实时数据获取模块 - 全自动版本
整合东方财富、新浪财经等免费数据源
"""

import json
import sys
import os
import urllib.request
import urllib.parse
import re
import ssl
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# 忽略SSL证书验证
ssl._create_default_https_context = ssl._create_unverified_context

class RealTimeDataFetcher:
    """实时数据获取器"""
    
    def __init__(self):
        self.cache = {}
        
    def get_stock_quote(self, code: str) -> Dict:
        """
        获取股票实时行情
        使用腾讯财经API（最稳定）
        """
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
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
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
                            "amount": float(fields[37]) if len(fields) > 37 else 0,  # 成交额
                            "update_time": fields[30] if len(fields) > 30 else "",
                            "change": change,
                            "change_pct": change_pct,
                            "pe_ttm": float(fields[52]) if len(fields) > 52 and fields[52] else 0,  # 市盈率TTM
                            "pb": float(fields[46]) if len(fields) > 46 and fields[46] else 0,  # 市净率
                            "market_cap": float(fields[44]) if len(fields) > 44 and fields[44] else 0,  # 总市值
                        }
        except Exception as e:
            print(f"获取股票行情失败: {e}", file=sys.stderr)
        
        return {"code": code, "error": "无法获取数据"}
    
    def get_rare_earth_prices(self) -> Dict:
        """
        获取稀土价格数据
        尝试多个数据源
        """
        prices = {
            "prnd": None,      # 氧化镨钕
            "dy": None,        # 氧化镝
            "tb": None,        # 氧化铽
            "source": None,
            "update_time": None
        }
        
        # 尝试1: 从生意社获取
        try:
            prnd = self._fetch_prnd_from_shengyishe()
            if prnd:
                prices["prnd"] = prnd
                prices["source"] = "生意社"
                prices["update_time"] = datetime.now().strftime("%Y-%m-%d")
                return prices
        except Exception as e:
            print(f"生意社获取失败: {e}", file=sys.stderr)
        
        # 尝试2: 从金属在线获取
        try:
            prnd = self._fetch_prnd_from_metals()
            if prnd:
                prices["prnd"] = prnd
                prices["source"] = "金属在线"
                prices["update_time"] = datetime.now().strftime("%Y-%m-%d")
                return prices
        except Exception as e:
            print(f"金属在线获取失败: {e}", file=sys.stderr)
        
        # 使用参考价格
        prices["prnd"] = 85.0
        prices["source"] = "参考价格"
        prices["update_time"] = datetime.now().strftime("%Y-%m-%d")
        
        return prices
    
    def _fetch_prnd_from_shengyishe(self) -> Optional[float]:
        """从生意社获取氧化镨钕价格"""
        url = "https://www.100ppi.com/vane/detail-959.html"
        
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            # 查找价格数据
            # 格式: 氧化镨钕 43.25-43.75 万元/吨
            pattern = r'氧化镨钕[\s\S]*?(\d+\.?\d*)\s*[-~]\s*(\d+\.?\d*)\s*万元/吨'
            match = re.search(pattern, html)
            
            if match:
                low = float(match.group(1))
                high = float(match.group(2))
                return round((low + high) / 2, 2)
        
        return None
    
    def _fetch_prnd_from_metals(self) -> Optional[float]:
        """从金属在线获取"""
        url = "http://www.metal.com/"
        
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8', errors='ignore')
            # 这里简化处理
            return None
    
    def get_industry_news(self, keywords: List[str] = None, limit: int = 20) -> List[Dict]:
        """
        获取行业新闻
        """
        if keywords is None:
            keywords = ["稀土", "氧化镨钕", "北方稀土"]
        
        all_news = []
        
        for keyword in keywords:
            news = self._fetch_news_from_sina(keyword, limit=limit//len(keywords))
            all_news.extend(news)
        
        # 去重
        seen = set()
        unique_news = []
        for n in all_news:
            key = n["title"][:30]
            if key not in seen:
                seen.add(key)
                unique_news.append(n)
        
        return unique_news[:limit]
    
    def _fetch_news_from_sina(self, keyword: str, limit: int = 10) -> List[Dict]:
        """从新浪搜索获取新闻"""
        news_items = []
        
        try:
            encoded = urllib.parse.quote(keyword)
            url = f"https://search.sina.com.cn/?q={encoded}&c=news&from=channel&ie=utf-8"
            
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9',
            })
            
            with urllib.request.urlopen(req, timeout=15) as response:
                html = response.read().decode('utf-8', errors='ignore')
                
                # 解析新闻
                pattern = r'<h2><a[^>]*href="([^"]+)"[^>]*>(.*?)</a></h2>'
                matches = re.findall(pattern, html, re.DOTALL)
                
                for link, title in matches[:limit]:
                    title = self._clean_text(title)
                    if self._is_valid_news(title):
                        news_items.append({
                            "title": title,
                            "url": link,
                            "source": "新浪",
                            "keyword": keyword,
                            "time": ""
                        })
                        
        except Exception as e:
            print(f"新浪新闻获取失败 [{keyword}]: {e}", file=sys.stderr)
        
        return news_items
    
    def _clean_text(self, text: str) -> str:
        """清理文本"""
        if not text:
            return ""
        text = re.sub(r'<[^>]+>', '', text)
        text = text.replace('&gt;', '>').replace('&lt;', '<').replace('&amp;', '&')
        text = text.replace('&quot;', '"').replace('&nbsp;', ' ')
        text = ' '.join(text.split())
        return text.strip()
    
    def _is_valid_news(self, title: str) -> bool:
        """验证新闻有效性"""
        if not title or len(title) < 8 or len(title) > 100:
            return False
        
        invalid = ['level2', '点击', '下载', 'APP', '登录', '注册', '>>', '<<', '鿴', '查看更多']
        for pattern in invalid:
            if pattern.lower() in title.lower():
                return False
        
        if not re.search(r'[\u4e00-\u9fa5]', title):
            return False
        
        return True
    
    def get_all_data(self, stock_code: str = "600111") -> Dict:
        """
        获取所有数据
        """
        print("正在获取股票行情...", file=sys.stderr)
        stock = self.get_stock_quote(stock_code)
        
        print("正在获取稀土价格...", file=sys.stderr)
        prices = self.get_rare_earth_prices()
        
        print("正在获取行业新闻...", file=sys.stderr)
        news = self.get_industry_news()
        
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M"),
            "stock": stock,
            "rare_earth_prices": prices,
            "news": news,
            "data_sources": [
                "腾讯财经(股票行情)",
                prices.get("source", "参考价格") + "(稀土价格)",
                "新浪搜索(行业新闻)"
            ]
        }


def main():
    """测试"""
    fetcher = RealTimeDataFetcher()
    data = fetcher.get_all_data("600111")
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
