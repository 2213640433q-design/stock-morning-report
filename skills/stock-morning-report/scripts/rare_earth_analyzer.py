#!/usr/bin/env python3
"""
北方稀土专业分析系统 - 基于五维评分卡框架
"""

import json
import sys
import os
import urllib.request
import urllib.parse
import re
from datetime import datetime
from typing import Dict, List, Tuple

class RareEarthAnalyzer:
    """稀土行业专业分析器"""
    
    def __init__(self):
        # 五维评分卡权重
        self.weights = {
            "supply_demand": 0.30,    # 供需平衡表
            "price_profit": 0.25,      # 价格与利润
            "policy_geo": 0.20,        # 政策与地缘
            "company_ops": 0.15,       # 公司经营
            "market_sentiment": 0.10   # 市场情绪
        }
        
        # 关键词库
        self.keywords = {
            "supply_positive": [
                "停产", "减产", "检修", "进口受阻", "通道受阻", "供给收缩",
                "配额收紧", "开采指标", "零增长", "限量", "管控"
            ],
            "supply_negative": [
                "复产", "复工", "增产", "扩产", "产能释放", "供给增加",
                "指标放松", "配额增加", "新矿", "投产"
            ],
            "demand_positive": [
                "订单", "补库", "招标", "排产", "旺季", "需求增长",
                "新能源汽车", "风电", "人形机器人", "低空经济", "军工",
                "地缘冲突", "国防", "战略储备"
            ],
            "demand_negative": [
                "库存", "消化库存", "订单不足", "淡季", "需求疲软",
                "下游观望", "采购谨慎"
            ],
            "policy_positive": [
                "出口管制", "管理条例", "高质量发展", "战略资源", "收储",
                "产业整合", "集中度提升", "政策利好", "补贴"
            ],
            "price_positive": [
                "价格上涨", "涨价", "突破", "企稳", "反弹", "成交量放大",
                "库存低位", "供不应求"
            ],
            "price_negative": [
                "价格下跌", "跌破", "震荡下行", "库存累积", "供过于求",
                "价格承压"
            ]
        }
    
    def analyze_supply_demand(self, news_items: List[Dict], quote: Dict) -> Tuple[int, str, List[str]]:
        """
        维度1: 供需平衡表分析
        评分: -10 ~ +10
        """
        score = 0
        signals = []
        details = []
        
        all_text = " ".join([n.get("title", "") for n in news_items])
        
        # 供给端分析
        supply_pos = sum(1 for k in self.keywords["supply_positive"] if k in all_text)
        supply_neg = sum(1 for k in self.keywords["supply_negative"] if k in all_text)
        
        if supply_pos > supply_neg:
            score += 3
            signals.append("供给端收紧")
            details.append("检测到供给收缩信号（停产/减产/进口受阻）")
        elif supply_neg > supply_pos:
            score -= 2
            signals.append("供给端放松")
            details.append("检测到供给增加信号（复产/扩产）")
        
        # 需求端分析
        demand_pos = sum(1 for k in self.keywords["demand_positive"] if k in all_text)
        demand_neg = sum(1 for k in self.keywords["demand_negative"] if k in all_text)
        
        if demand_pos > demand_neg:
            score += 3
            signals.append("需求端向好")
            details.append("检测到需求增长信号（订单/补库/新兴应用）")
        elif demand_neg > demand_pos:
            score -= 2
            signals.append("需求端疲软")
            details.append("检测到需求疲软信号（库存消化/订单不足）")
        
        # 价格趋势验证
        if quote and 'change_pct' in quote:
            change = quote['change_pct']
            if change > 3:
                score += 2
                signals.append("价格强势")
            elif change < -3:
                score -= 2
                signals.append("价格弱势")
        
        # 默认中性
        if score == 0:
            details.append("供需面暂无重大变化，维持中性判断")
        
        return score, "、".join(signals) if signals else "供需平衡", details
    
    def analyze_price_profit(self, quote: Dict) -> Tuple[int, str, List[str]]:
        """
        维度2: 价格与利润分析
        评分: -10 ~ +10
        """
        score = 0
        signals = []
        details = []
        
        if not quote or 'error' in quote:
            return 0, "数据缺失", ["无法获取行情数据"]
        
        change_pct = quote.get('change_pct', 0)
        
        # 价格变动分析
        if change_pct > 5:
            score += 4
            signals.append("价格大涨")
            details.append(f"今日大涨{change_pct}%，显示市场做多情绪强烈")
        elif change_pct > 2:
            score += 2
            signals.append("价格上涨")
            details.append(f"今日上涨{change_pct}%，走势偏强")
        elif change_pct > -2:
            score += 0
            signals.append("价格平稳")
            details.append(f"今日波动{change_pct}%，处于正常区间")
        elif change_pct > -5:
            score -= 2
            signals.append("价格下跌")
            details.append(f"今日下跌{abs(change_pct)}%，走势偏弱")
        else:
            score -= 4
            signals.append("价格大跌")
            details.append(f"今日大跌{abs(change_pct)}%，需关注支撑位")
        
        # 日内走势分析
        open_price = quote.get('open', 0)
        high_price = quote.get('high', 0)
        low_price = quote.get('low', 0)
        current_price = quote.get('price', 0)
        prev_close = quote.get('prev_close', 0)
        
        if current_price > open_price and current_price > prev_close:
            signals.append("收于开盘和昨收之上")
            details.append("日内走势偏强，收盘站稳关键位置")
        elif current_price < open_price and current_price < prev_close:
            signals.append("收于开盘和昨收之下")
            details.append("日内走势偏弱，收盘跌破关键位置")
        
        return score, "、".join(signals), details
    
    def analyze_policy_geo(self, news_items: List[Dict]) -> Tuple[int, str, List[str]]:
        """
        维度3: 政策与地缘政治分析
        评分: -10 ~ +10
        """
        score = 0
        signals = []
        details = []
        
        all_text = " ".join([n.get("title", "") for n in news_items])
        
        # 政策面分析
        policy_pos = sum(1 for k in self.keywords["policy_positive"] if k in all_text)
        
        if policy_pos > 0:
            score += 4
            signals.append("政策利好")
            details.append("检测到政策面积极信号（出口管制/产业支持）")
        
        # 地缘冲突分析
        geo_keywords = ["地缘", "冲突", "战争", "军事", "国防", "战略"]
        geo_count = sum(1 for k in geo_keywords if k in all_text)
        
        if geo_count > 0:
            score += 3
            signals.append("地缘溢价")
            details.append("地缘冲突强化稀土战略属性，提升估值溢价")
        
        if score == 0:
            details.append("政策面无重大变化")
        
        return score, "、".join(signals) if signals else "政策中性", details
    
    def analyze_company_ops(self, news_items: List[Dict]) -> Tuple[int, str, List[str]]:
        """
        维度4: 公司经营分析
        评分: -10 ~ +10
        """
        score = 0
        signals = []
        details = []
        
        all_text = " ".join([n.get("title", "") for n in news_items])
        
        # 公司经营相关
        company_positive = ["业绩", "增长", "投产", "新材料", "高端", "转型"]
        company_negative = ["亏损", "下滑", "产能利用率", "库存高企"]
        
        pos_count = sum(1 for k in company_positive if k in all_text)
        neg_count = sum(1 for k in company_negative if k in all_text)
        
        if pos_count > neg_count:
            score += 2
            signals.append("经营向好")
            details.append("公司经营层面有积极信号")
        elif neg_count > pos_count:
            score -= 2
            signals.append("经营承压")
            details.append("公司经营层面存在压力")
        else:
            details.append("公司经营层面暂无重大变化")
        
        return score, "、".join(signals) if signals else "经营平稳", details
    
    def analyze_market_sentiment(self, quote: Dict) -> Tuple[int, str, List[str]]:
        """
        维度5: 市场情绪分析
        评分: -10 ~ +10
        """
        score = 0
        signals = []
        details = []
        
        if not quote or 'error' in quote:
            return 0, "数据缺失", ["无法获取行情数据"]
        
        # 成交量分析
        volume = quote.get('volume', 0)
        if volume > 1000000:  # 100万手以上
            signals.append("成交活跃")
            details.append(f"成交量{volume/10000:.0f}万手，市场关注度高")
        elif volume < 300000:
            signals.append("成交清淡")
            details.append(f"成交量{volume/10000:.0f}万手，市场参与度低")
        
        # 涨跌分析
        change_pct = quote.get('change_pct', 0)
        if change_pct > 0:
            score += 1
        elif change_pct < 0:
            score -= 1
        
        if score == 0:
            details.append("市场情绪中性")
        
        return score, "、".join(signals) if signals else "情绪中性", details
    
    def generate_scorecard(self, stock_code: str, stock_name: str, 
                          news_items: List[Dict], quote: Dict) -> Dict:
        """生成完整的评分卡"""
        
        # 五维分析
        supply_score, supply_signal, supply_details = self.analyze_supply_demand(news_items, quote)
        price_score, price_signal, price_details = self.analyze_price_profit(quote)
        policy_score, policy_signal, policy_details = self.analyze_policy_geo(news_items)
        company_score, company_signal, company_details = self.analyze_company_ops(news_items)
        sentiment_score, sentiment_signal, sentiment_details = self.analyze_market_sentiment(quote)
        
        # 计算加权总分
        total_score = (
            supply_score * self.weights["supply_demand"] +
            price_score * self.weights["price_profit"] +
            policy_score * self.weights["policy_geo"] +
            company_score * self.weights["company_ops"] +
            sentiment_score * self.weights["market_sentiment"]
        )
        
        # 确定评级
        if total_score >= 5:
            rating = "看好"
            rating_emoji = "📈"
        elif total_score >= 2:
            rating = "偏正面"
            rating_emoji = "↗️"
        elif total_score > -2:
            rating = "中性"
            rating_emoji = "➡️"
        elif total_score > -5:
            rating = "偏谨慎"
            rating_emoji = "↘️"
        else:
            rating = "谨慎"
            rating_emoji = "📉"
        
        return {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "total_score": round(total_score, 2),
            "rating": rating,
            "rating_emoji": rating_emoji,
            "dimensions": {
                "supply_demand": {
                    "name": "供需平衡表",
                    "weight": f"{self.weights['supply_demand']*100:.0f}%",
                    "score": supply_score,
                    "signal": supply_signal,
                    "details": supply_details
                },
                "price_profit": {
                    "name": "价格与利润",
                    "weight": f"{self.weights['price_profit']*100:.0f}%",
                    "score": price_score,
                    "signal": price_signal,
                    "details": price_details
                },
                "policy_geo": {
                    "name": "政策与地缘",
                    "weight": f"{self.weights['policy_geo']*100:.0f}%",
                    "score": policy_score,
                    "signal": policy_signal,
                    "details": policy_details
                },
                "company_ops": {
                    "name": "公司经营",
                    "weight": f"{self.weights['company_ops']*100:.0f}%",
                    "score": company_score,
                    "signal": company_signal,
                    "details": company_details
                },
                "market_sentiment": {
                    "name": "市场情绪",
                    "weight": f"{self.weights['market_sentiment']*100:.0f}%",
                    "score": sentiment_score,
                    "signal": sentiment_signal,
                    "details": sentiment_details
                }
            },
            "summary": self._generate_summary(supply_signal, price_signal, policy_signal, 
                                             company_signal, sentiment_signal, total_score)
        }
    
    def _generate_summary(self, supply: str, price: str, policy: str, 
                         company: str, sentiment: str, total: float) -> str:
        """生成综合分析摘要"""
        
        if total >= 5:
            return f"基本面整体向好。{supply}，{price}，{policy}，建议积极关注。"
        elif total >= 2:
            return f"基本面偏正面。{supply}，{price}，可适当关注。"
        elif total > -2:
            return f"基本面中性。{supply}，{price}，建议观望。"
        elif total > -5:
            return f"基本面偏谨慎。{supply}，{price}，建议控制仓位。"
        else:
            return f"基本面承压。{supply}，{price}，{policy}，建议谨慎对待。"


def main():
    """测试分析器"""
    analyzer = RareEarthAnalyzer()
    
    # 模拟数据
    news_items = [
        {"title": "缅甸稀土进口通道持续受阻，中重稀土供给紧张"},
        {"title": "氧化镨钕价格企稳，下游磁材企业开始补库"},
        {"title": "商务部发布稀土出口管制新规"}
    ]
    
    quote = {
        "price": 54.3,
        "change_pct": -1.95,
        "volume": 891206
    }
    
    result = analyzer.generate_scorecard("600111", "北方稀土", news_items, quote)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
