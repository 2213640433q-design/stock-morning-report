#!/usr/bin/env python3
"""
北方稀土基本面估值计算器
基于利润核心、供需边际、政策情绪、资金市场四个维度
"""

import json
import sys
import os
import urllib.request
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional

class NRERValuationModel:
    """北方稀土估值模型"""
    
    def __init__(self):
        # 基准数据（需要根据最新财报更新）
        # 北方稀土当前股价约55元，按PE=35倒推，EPS约1.57
        self.base_data = {
            "total_shares": 36.15,  # 总股本 36.15亿股
            "base_eps": 1.57,       # 基准EPS（按当前股价55/PE35估算）
            "base_pe": 35,          # 基准PE（行业平均）
            "base_price": 55.38,    # 基准价格（昨收）
            "prnd_price": 85.0,     # 氧化镨钕参考价格（万元/吨）
        }
        
        # 估值参数
        self.valuation_params = {
            "pe_bull": 45,      # 牛市PE
            "pe_base": 35,      # 基准PE
            "pe_bear": 25,      # 熊市PE
            "eps_sensitivity": 0.15,  # EPS对价格敏感度（每涨1万/吨，EPS变化）
        }
    
    def fetch_prnd_price(self) -> Tuple[Optional[float], List[str]]:
        """
        获取氧化镨钕最新价格
        尝试多个数据源
        """
        signals = []
        
        # 尝试上海有色网
        try:
            url = "https://www.smm.cn/cixitu/oxidized_praseodymium_neodymium"
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            })
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8', errors='ignore')
                # 查找价格数据
                price_match = re.search(r'(\d+\.?\d*)\s*万元/吨', html)
                if price_match:
                    price = float(price_match.group(1))
                    signals.append(f"氧化镨钕价格: {price}万元/吨（上海有色网）")
                    return price, signals
        except Exception as e:
            signals.append(f"上海有色网获取失败: {e}")
        
        # 尝试百川盈孚
        try:
            url = "https://www.baiinfo.com/"
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            })
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8', errors='ignore')
                # 简单匹配
                if '氧化镨钕' in html:
                    signals.append("百川盈孚: 检测到稀土相关数据")
        except Exception as e:
            signals.append(f"百川盈孚获取失败: {e}")
        
        # 使用参考价格
        signals.append(f"使用参考价格: {self.base_data['prnd_price']}万元/吨")
        return self.base_data['prnd_price'], signals
    
    def analyze_profit_core(self, news_items: List[Dict], quote: Dict) -> Dict:
        """
        维度1: 利润核心 (价差)
        权重: 40%
        """
        score = 0
        max_score = 40
        signals = []
        details = []
        
        all_text = " ".join([n.get("title", "") for n in news_items])
        
        # 1. 氧化镨钕价格变动
        price_change_keywords = {
            "positive": ["价格上涨", "涨价", "突破", "创新高", "强势"],
            "negative": ["价格下跌", "降价", "跌破", "走弱", "回调"]
        }
        
        pos_count = sum(1 for k in price_change_keywords["positive"] if k in all_text)
        neg_count = sum(1 for k in price_change_keywords["negative"] if k in all_text)
        
        if pos_count > neg_count:
            score += 15
            signals.append("产品价格上涨")
            details.append("氧化镨钕价格上涨信号，利好毛利空间")
        elif neg_count > pos_count:
            score -= 15
            signals.append("产品价格下跌")
            details.append("氧化镨钕价格下跌信号，压缩毛利空间")
        else:
            details.append("氧化镨钕价格暂无重大变化")
        
        # 2. 精矿采购价格
        concentrate_keywords = {
            "positive": ["精矿价格稳定", "成本可控", "自给率提升"],
            "negative": ["精矿涨价", "成本上升", "精矿补涨"]
        }
        
        if any(k in all_text for k in concentrate_keywords["positive"]):
            score += 10
            signals.append("成本端稳定")
            details.append("精矿采购价格稳定或涨幅小于产品涨幅，剪刀差扩大")
        elif any(k in all_text for k in concentrate_keywords["negative"]):
            score -= 10
            signals.append("成本端压力")
            details.append("精矿采购价格上涨，压缩利润空间")
        else:
            details.append("精矿价格暂无重大变化")
        
        # 3. 股价验证（价格→毛利→EPS传导）
        if quote and 'change_pct' in quote:
            change = quote['change_pct']
            if change > 3:
                score += 10
                signals.append("股价强势")
                details.append(f"股价上涨{change}%，市场认可盈利改善预期")
            elif change < -3:
                score -= 10
                signals.append("股价弱势")
                details.append(f"股价下跌{abs(change)}%，市场担忧盈利下滑")
        
        # 计算估值影响
        eps_impact = score / max_score * self.valuation_params["eps_sensitivity"]
        
        return {
            "dimension": "利润核心",
            "weight": "40%",
            "score": score,
            "max_score": max_score,
            "rating": self._get_rating(score, max_score),
            "signals": signals,
            "details": details,
            "eps_impact": round(eps_impact, 3)
        }
    
    def analyze_supply_demand(self, news_items: List[Dict]) -> Dict:
        """
        维度2: 供需边际 (驱动)
        权重: 30%
        """
        score = 0
        max_score = 30
        signals = []
        details = []
        
        all_text = " ".join([n.get("title", "") for n in news_items])
        
        # 供给端分析
        supply_positive = ["缅甸停产", "进口受阻", "口岸关闭", "莱纳斯减产", "检修", "供给收缩"]
        supply_negative = ["缅甸复产", "进口恢复", "口岸开放", "莱纳斯复工", "产能释放"]
        
        supply_pos = sum(1 for k in supply_positive if k in all_text)
        supply_neg = sum(1 for k in supply_negative if k in all_text)
        
        if supply_pos > supply_neg:
            score += 12
            signals.append("供给收缩")
            details.append("检测到供给端扰动（缅甸/澳洲/国内），利好价格")
        elif supply_neg > supply_pos:
            score -= 12
            signals.append("供给放松")
            details.append("供给端扰动解除或产能释放，价格承压")
        else:
            details.append("供给端暂无重大变化")
        
        # 需求端分析
        demand_positive = ["订单增加", "补库", "招标", "排产", "设备更新", "机器人", "新能源车销量"]
        demand_negative = ["订单不足", "库存高企", "下游观望", "销量不及预期"]
        
        demand_pos = sum(1 for k in demand_positive if k in all_text)
        demand_neg = sum(1 for k in demand_negative if k in all_text)
        
        if demand_pos > demand_neg:
            score += 12
            signals.append("需求向好")
            details.append("下游需求回暖或政策刺激，拉动稀土消费")
        elif demand_neg > demand_pos:
            score -= 12
            signals.append("需求疲软")
            details.append("下游需求不振，稀土消费承压")
        else:
            details.append("需求端暂无重大变化")
        
        # 库存水平
        if "库存低位" in all_text or "库存紧张" in all_text:
            score += 6
            signals.append("库存低位")
            details.append("行业库存处于低位，价格弹性大")
        elif "库存累积" in all_text:
            score -= 6
            signals.append("库存累积")
            details.append("行业库存累积，价格承压")
        
        return {
            "dimension": "供需边际",
            "weight": "30%",
            "score": score,
            "max_score": max_score,
            "rating": self._get_rating(score, max_score),
            "signals": signals,
            "details": details
        }
    
    def analyze_policy_sentiment(self, news_items: List[Dict]) -> Dict:
        """
        维度3: 政策情绪 (溢价)
        权重: 20%
        """
        score = 0
        max_score = 20
        signals = []
        details = []
        
        all_text = " ".join([n.get("title", "") for n in news_items])
        
        # 国内政策
        policy_positive = ["出口管制", "管理条例", "打黑", "收储", "产业整合", "高质量发展"]
        policy_negative = ["保供稳价", "约谈", "价格干预", "产能扩张"]
        
        pol_pos = sum(1 for k in policy_positive if k in all_text)
        pol_neg = sum(1 for k in policy_negative if k in all_text)
        
        if pol_pos > pol_neg:
            score += 10
            signals.append("政策利好")
            details.append("出台出口管制、产业支持等政策，强化战略属性")
        elif pol_neg > pol_pos:
            score -= 10
            signals.append("政策谨慎")
            details.append("官方表态保供稳价或约谈企业，压制价格预期")
        else:
            details.append("政策面无重大变化")
        
        # 地缘政治
        geo_positive = ["地缘冲突", "战争", "军事", "国防", "战略储备", "贸易摩擦"]
        geo_negative = ["关系缓和", "合作", "谈判成功"]
        
        geo_pos = sum(1 for k in geo_positive if k in all_text)
        geo_neg = sum(1 for k in geo_negative if k in all_text)
        
        if geo_pos > geo_neg:
            score += 10
            signals.append("地缘溢价")
            details.append("地缘冲突强化稀土战略地位，提升估值溢价")
        elif geo_neg > geo_pos:
            score -= 5
            signals.append("地缘缓和")
            details.append("国际关系缓和，地缘溢价回落")
        else:
            details.append("地缘因素暂无重大变化")
        
        return {
            "dimension": "政策情绪",
            "weight": "20%",
            "score": score,
            "max_score": max_score,
            "rating": self._get_rating(score, max_score),
            "signals": signals,
            "details": details
        }
    
    def analyze_market_sentiment(self, quote: Dict) -> Dict:
        """
        维度4: 资金与市场 (交易)
        权重: 10%
        """
        score = 0
        max_score = 10
        signals = []
        details = []
        
        if not quote or 'error' in quote:
            return {
                "dimension": "资金市场",
                "weight": "10%",
                "score": 0,
                "max_score": max_score,
                "rating": "中性",
                "signals": [],
                "details": ["无法获取行情数据"]
            }
        
        change_pct = quote.get('change_pct', 0)
        volume = quote.get('volume', 0)
        
        # 价格表现
        if change_pct > 5:
            score += 4
            signals.append("强势上涨")
            details.append(f"股价大涨{change_pct}%，领涨板块")
        elif change_pct > 2:
            score += 2
            signals.append("上涨")
            details.append(f"股价上涨{change_pct}%")
        elif change_pct < -5:
            score -= 4
            signals.append("大幅下跌")
            details.append(f"股价大跌{abs(change_pct)}%，领跌板块")
        elif change_pct < -2:
            score -= 2
            signals.append("下跌")
            details.append(f"股价下跌{abs(change_pct)}%")
        else:
            details.append(f"股价波动{change_pct}%，表现平稳")
        
        # 成交量分析
        if volume > 1500000:
            if change_pct > 0:
                score += 3
                signals.append("放量上涨")
                details.append(f"成交量{volume/10000:.0f}万手，资金积极入场")
            else:
                score -= 3
                signals.append("放量下跌")
                details.append(f"成交量{volume/10000:.0f}万手，资金出逃")
        elif volume > 800000:
            score += 1
            signals.append("成交活跃")
            details.append(f"成交量{volume/10000:.0f}万手，市场关注度高")
        elif volume < 300000:
            score -= 1
            signals.append("成交清淡")
            details.append(f"成交量{volume/10000:.0f}万手，市场参与度低")
        
        return {
            "dimension": "资金市场",
            "weight": "10%",
            "score": score,
            "max_score": max_score,
            "rating": self._get_rating(score, max_score),
            "signals": signals,
            "details": details
        }
    
    def _get_rating(self, score: int, max_score: int) -> str:
        """根据分数获取评级"""
        ratio = score / max_score
        if ratio >= 0.5:
            return "变好"
        elif ratio >= 0.2:
            return "偏正面"
        elif ratio > -0.2:
            return "中性"
        elif ratio > -0.5:
            return "偏谨慎"
        else:
            return "变差"
    
    def calculate_valuation(self, dimensions: List[Dict]) -> Dict:
        """
        计算估值
        传导路径: 价格 → 毛利 → EPS → 股价
        """
        # 计算总分
        total_score = sum(d["score"] for d in dimensions)
        max_total = sum(d["max_score"] for d in dimensions)
        
        # EPS调整
        profit_dim = next((d for d in dimensions if d["dimension"] == "利润核心"), None)
        eps_adjustment = profit_dim["eps_impact"] if profit_dim else 0
        adjusted_eps = self.base_data["base_eps"] + eps_adjustment
        
        # PE调整（基于总分）
        score_ratio = total_score / max_total
        if score_ratio > 0.3:
            adjusted_pe = self.valuation_params["pe_bull"]
        elif score_ratio > 0.1:
            adjusted_pe = self.valuation_params["pe_base"] + 5
        elif score_ratio > -0.1:
            adjusted_pe = self.valuation_params["pe_base"]
        elif score_ratio > -0.3:
            adjusted_pe = self.valuation_params["pe_base"] - 5
        else:
            adjusted_pe = self.valuation_params["pe_bear"]
        
        # 计算目标价
        target_price = adjusted_eps * adjusted_pe
        
        # 与当前价格比较
        current_price = self.base_data["base_price"]
        upside = (target_price - current_price) / current_price * 100
        
        return {
            "base_eps": self.base_data["base_eps"],
            "adjusted_eps": round(adjusted_eps, 2),
            "base_pe": self.valuation_params["pe_base"],
            "adjusted_pe": adjusted_pe,
            "target_price": round(target_price, 2),
            "current_price": current_price,
            "upside": round(upside, 1),
            "total_score": total_score,
            "max_score": max_total,
            "score_ratio": round(score_ratio * 100, 1)
        }
    
    def generate_report(self, stock_code: str, stock_name: str, 
                       news_items: List[Dict], quote: Dict) -> Dict:
        """生成完整估值报告"""
        
        # 四维度分析
        profit_analysis = self.analyze_profit_core(news_items, quote)
        supply_analysis = self.analyze_supply_demand(news_items)
        policy_analysis = self.analyze_policy_sentiment(news_items)
        market_analysis = self.analyze_market_sentiment(quote)
        
        dimensions = [profit_analysis, supply_analysis, policy_analysis, market_analysis]
        
        # 计算估值
        valuation = self.calculate_valuation(dimensions)
        
        # 生成投资建议
        upside = valuation["upside"]
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
            "stock_code": stock_code,
            "stock_name": stock_name,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "dimensions": dimensions,
            "valuation": valuation,
            "recommendation": recommendation,
            "recommendation_emoji": rec_emoji,
            "summary": self._generate_summary(dimensions, valuation, recommendation)
        }
    
    def _generate_summary(self, dimensions: List[Dict], valuation: Dict, rec: str) -> str:
        """生成分析摘要"""
        profit = next((d for d in dimensions if d["dimension"] == "利润核心"), None)
        supply = next((d for d in dimensions if d["dimension"] == "供需边际"), None)
        
        summary = f"基于四维度分析，给予【{rec}】评级。"
        summary += f"目标价¥{valuation['target_price']}（较当前{valuation['upside']:+.1f}%）。"
        
        if profit and profit["signals"]:
            summary += f"利润端: {profit['rating']}。"
        if supply and supply["signals"]:
            summary += f"供需面: {supply['rating']}。"
        
        return summary


def main():
    """测试估值模型"""
    model = NRERValuationModel()
    
    # 模拟数据
    news_items = [
        {"title": "缅甸稀土进口通道受阻，中重稀土供给紧张"},
        {"title": "氧化镨钕价格企稳，下游磁材企业开始补库"},
        {"title": "新能源车销量超预期，稀土需求向好"}
    ]
    
    quote = {
        "price": 54.3,
        "change_pct": -1.95,
        "volume": 891206
    }
    
    report = model.generate_report("600111", "北方稀土", news_items, quote)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
