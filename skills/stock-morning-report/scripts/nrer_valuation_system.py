#!/usr/bin/env python3
"""
北方稀土估值系统 - 配置版
支持手动输入关键价格数据 + 自动新闻分析
"""

import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Tuple

class NRERValuationSystem:
    """北方稀土估值系统"""
    
    def __init__(self):
        # 基准数据
        self.base_data = {
            "total_shares": 36.15,      # 总股本 36.15亿股
            "base_eps": 1.57,            # 基准EPS
            "base_pe": 35,               # 基准PE
            "base_price": 55.38,         # 基准价格
            "prnd_base_price": 85.0,     # 氧化镨钕基准价格(万元/吨)
        }
        
        # 估值参数
        self.params = {
            "pe_bull": 45,
            "pe_base": 35,
            "pe_bear": 25,
            "eps_sensitivity": 0.15,     # 价格每变化1万/吨，EPS变化
        }
        
        # 关键词库
        self.keywords = {
            "supply_positive": ["停产", "减产", "检修", "进口受阻", "供给收缩", "配额收紧"],
            "supply_negative": ["复产", "复工", "增产", "扩产", "产能释放", "供给增加"],
            "demand_positive": ["订单", "补库", "招标", "排产", "旺季", "新能源车", "风电", "机器人"],
            "policy_positive": ["出口管制", "管理条例", "打黑", "收储", "产业整合"],
            "price_positive": ["价格上涨", "涨价", "突破", "企稳", "反弹"],
            "price_negative": ["价格下跌", "跌破", "下行", "库存累积"],
        }
    
    def calculate_valuation(self, 
                          current_price: float,
                          prnd_price: float,
                          news_items: List[Dict]) -> Dict:
        """
        计算估值
        
        Args:
            current_price: 当前股价
            prnd_price: 氧化镨钕当前价格(万元/吨)
            news_items: 新闻列表
        """
        all_text = " ".join([n.get("title", "") for n in news_items])
        
        # ========== 维度1: 利润核心 (价差) ==========
        profit_score = 0
        profit_signals = []
        profit_details = []
        
        # 氧化镨钕价格变化
        prnd_change = prnd_price - self.base_data["prnd_base_price"]
        prnd_change_pct = (prnd_change / self.base_data["prnd_base_price"]) * 100
        
        if prnd_change_pct > 2:
            profit_score += 15
            profit_signals.append("产品价格上涨")
            profit_details.append(f"氧化镨钕价格{prnd_price}万/吨，较基准上涨{prnd_change_pct:.1f}%")
        elif prnd_change_pct < -2:
            profit_score -= 15
            profit_signals.append("产品价格下跌")
            profit_details.append(f"氧化镨钕价格{prnd_price}万/吨，较基准下跌{abs(prnd_change_pct):.1f}%")
        else:
            profit_details.append(f"氧化镨钕价格{prnd_price}万/吨，基本持平")
        
        # 股价验证
        stock_change = ((current_price - self.base_data["base_price"]) 
                       / self.base_data["base_price"] * 100)
        if stock_change > 3:
            profit_score += 10
            profit_signals.append("股价强势")
        elif stock_change < -3:
            profit_score -= 10
            profit_signals.append("股价弱势")
        
        # EPS调整
        eps_adjustment = (prnd_change * self.params["eps_sensitivity"])
        adjusted_eps = self.base_data["base_eps"] + eps_adjustment
        
        profit_analysis = {
            "dimension": "利润核心",
            "weight": "40%",
            "score": profit_score,
            "max_score": 40,
            "rating": self._get_rating(profit_score, 40),
            "signals": profit_signals,
            "details": profit_details,
            "prnd_price": prnd_price,
            "prnd_change_pct": round(prnd_change_pct, 2),
            "eps_adjustment": round(eps_adjustment, 3),
            "adjusted_eps": round(adjusted_eps, 2)
        }
        
        # ========== 维度2: 供需边际 ==========
        supply_score = 0
        supply_signals = []
        supply_details = []
        
        supply_pos = sum(1 for k in self.keywords["supply_positive"] if k in all_text)
        supply_neg = sum(1 for k in self.keywords["supply_negative"] if k in all_text)
        
        if supply_pos > supply_neg:
            supply_score += 15
            supply_signals.append("供给收缩")
            supply_details.append("检测到供给端扰动信号")
        elif supply_neg > supply_pos:
            supply_score -= 15
            supply_signals.append("供给放松")
            supply_details.append("检测到供给增加信号")
        else:
            supply_details.append("供给端暂无重大变化")
        
        demand_pos = sum(1 for k in self.keywords["demand_positive"] if k in all_text)
        if demand_pos > 0:
            supply_score += 10
            supply_signals.append("需求向好")
            supply_details.append("检测到需求增长信号")
        
        supply_analysis = {
            "dimension": "供需边际",
            "weight": "30%",
            "score": supply_score,
            "max_score": 30,
            "rating": self._get_rating(supply_score, 30),
            "signals": supply_signals,
            "details": supply_details
        }
        
        # ========== 维度3: 政策情绪 ==========
        policy_score = 0
        policy_signals = []
        policy_details = []
        
        policy_pos = sum(1 for k in self.keywords["policy_positive"] if k in all_text)
        if policy_pos > 0:
            policy_score += 15
            policy_signals.append("政策利好")
            policy_details.append("检测到政策面积极信号")
        
        geo_keywords = ["地缘", "冲突", "战争", "军事", "国防"]
        geo_count = sum(1 for k in geo_keywords if k in all_text)
        if geo_count > 0:
            policy_score += 10
            policy_signals.append("地缘溢价")
            policy_details.append("地缘冲突强化稀土战略属性")
        
        if policy_score == 0:
            policy_details.append("政策面无重大变化")
        
        policy_analysis = {
            "dimension": "政策情绪",
            "weight": "20%",
            "score": policy_score,
            "max_score": 20,
            "rating": self._get_rating(policy_score, 20),
            "signals": policy_signals,
            "details": policy_details
        }
        
        # ========== 维度4: 资金市场 ==========
        market_score = 0
        market_signals = []
        market_details = []
        
        if stock_change > 5:
            market_score += 5
            market_signals.append("强势上涨")
        elif stock_change > 0:
            market_score += 2
            market_signals.append("上涨")
        elif stock_change < -5:
            market_score -= 5
            market_signals.append("大幅下跌")
        elif stock_change < 0:
            market_score -= 2
            market_signals.append("下跌")
        
        market_details.append(f"股价较基准{stock_change:+.1f}%")
        
        market_analysis = {
            "dimension": "资金市场",
            "weight": "10%",
            "score": market_score,
            "max_score": 10,
            "rating": self._get_rating(market_score, 10),
            "signals": market_signals,
            "details": market_details
        }
        
        # ========== 综合计算 ==========
        dimensions = [profit_analysis, supply_analysis, policy_analysis, market_analysis]
        total_score = sum(d["score"] for d in dimensions)
        max_total = sum(d["max_score"] for d in dimensions)
        
        # PE调整
        score_ratio = total_score / max_total
        if score_ratio > 0.3:
            adjusted_pe = self.params["pe_bull"]
        elif score_ratio > 0.1:
            adjusted_pe = self.params["pe_base"] + 5
        elif score_ratio > -0.1:
            adjusted_pe = self.params["pe_base"]
        elif score_ratio > -0.3:
            adjusted_pe = self.params["pe_base"] - 5
        else:
            adjusted_pe = self.params["pe_bear"]
        
        # 目标价
        target_price = adjusted_eps * adjusted_pe
        upside = (target_price - current_price) / current_price * 100
        
        # 投资建议
        if upside > 20:
            recommendation = "强烈看好"
            rec_emoji = "🔥"
        elif upside > 10:
            recommendation = "看好"
            rec_emoji = "📈"
        elif upside > -10:
            recommendation = "持有"
            rec_emoji = "➡️"
        elif upside > -20:
            recommendation = "谨慎"
            rec_emoji = "⚠️"
        else:
            recommendation = "回避"
            rec_emoji = "📉"
        
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "stock_code": "600111",
            "stock_name": "北方稀土",
            "current_price": current_price,
            "base_price": self.base_data["base_price"],
            "dimensions": dimensions,
            "valuation": {
                "base_eps": self.base_data["base_eps"],
                "adjusted_eps": round(adjusted_eps, 2),
                "base_pe": self.params["pe_base"],
                "adjusted_pe": adjusted_pe,
                "target_price": round(target_price, 2),
                "upside": round(upside, 1),
                "total_score": total_score,
                "max_score": max_total,
                "score_ratio": round(score_ratio * 100, 1)
            },
            "recommendation": recommendation,
            "recommendation_emoji": rec_emoji,
            "summary": f"基于四维度分析，给予【{recommendation}】评级。目标价¥{round(target_price, 2)}（较当前{upside:+.1f}%）。"
        }
    
    def _get_rating(self, score: int, max_score: int) -> str:
        """获取评级"""
        ratio = score / max_score if max_score else 0
        if ratio >= 0.3:
            return "变好"
        elif ratio >= 0.1:
            return "偏正面"
        elif ratio > -0.1:
            return "中性"
        elif ratio > -0.3:
            return "偏谨慎"
        else:
            return "变差"


def main():
    """测试"""
    # 示例数据
    current_price = 54.3  # 当前股价
    prnd_price = 84.5     # 氧化镨钕价格(万元/吨)
    
    # 示例新闻
    news_items = [
        {"title": "缅甸稀土进口通道受阻，中重稀土供给紧张"},
        {"title": "氧化镨钕价格企稳，下游磁材企业开始补库"},
        {"title": "新能源车销量超预期，稀土需求向好"},
        {"title": "商务部发布稀土出口管制新规"}
    ]
    
    system = NRERValuationSystem()
    result = system.calculate_valuation(current_price, prnd_price, news_items)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
