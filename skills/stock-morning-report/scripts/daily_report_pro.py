#!/usr/bin/env python3
"""
北方稀土估值系统 - 专业版
基于真实业绩弹性和估值溢价
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime
from typing import Dict, List

from eastmoney_api import EastMoneyDataFetcher
from ultimate_price import UltimatePriceFetcher
from realtime_data import RealTimeDataFetcher

class NRERProfessionalValuation:
    """北方稀土专业估值模型"""
    
    def __init__(self):
        # 专业估值参数
        self.params = {
            # 业绩弹性: 稀土价格每变化1%，EPS变化约2.3%
            "earnings_elasticity": 2.3,
            
            # 基准数据（基于2025年预期业绩）
            "base_prnd_price": 85.0,      # 氧化镨钕基准价格(万元/吨)
            "base_eps": 1.50,              # 基准EPS（2025年预期，对应85万/吨稀土价格）
            "base_stock_price": 52.5,      # 对应基准股价（1.5*35=52.5）
            "base_pe": 35,                 # 基准PE
            
            # 估值区间
            "pe_normal": 35,               # 正常估值
            "pe_bull": 50,                 # 牛市估值（战略溢价）
            "pe_bear": 25,                 # 熊市估值
            "pe_high_risk": 78,            # 高风险估值（如2024年Q3的78倍）
            
            # 成本端风险
            "concentrate_price_base": 100, # 精矿基准价格（假设）
        }
    
    def calculate_eps(self, prnd_price: float, concentrate_change_pct: float = 0) -> Dict:
        """
        计算EPS
        
        逻辑:
        1. 稀土价格变化 → 收入变化
        2. 考虑精矿成本变化 → 毛利变化
        3. 扣除税费 → EPS
        """
        base_prnd = self.params["base_prnd_price"]
        base_eps = self.params["base_eps"]
        elasticity = self.params["earnings_elasticity"]
        
        # 稀土价格变化
        prnd_change_pct = (prnd_price - base_prnd) / base_prnd * 100
        
        # 收入端变化（价格变化 × 弹性）
        revenue_change_pct = prnd_change_pct * elasticity
        
        # 成本端冲击（精矿价格变化）
        # 2025年Q4案例: 精矿价格大涨37%，稀土价格回落，利润被挤压
        cost_impact = concentrate_change_pct * 0.5  # 成本影响系数
        
        # 净利润变化 = 收入变化 - 成本冲击
        profit_change_pct = revenue_change_pct - cost_impact
        
        # 新EPS
        new_eps = base_eps * (1 + profit_change_pct / 100)
        
        return {
            "base_eps": base_eps,
            "prnd_change_pct": round(prnd_change_pct, 2),
            "revenue_change_pct": round(revenue_change_pct, 2),
            "cost_impact_pct": round(cost_impact, 2),
            "profit_change_pct": round(profit_change_pct, 2),
            "new_eps": round(new_eps, 2),
        }
    
    def calculate_fair_price(self, 
                           prnd_price: float,
                           concentrate_change_pct: float = 0,
                           market_sentiment: str = "normal") -> Dict:
        """
        计算合理股价
        
        股价 = EPS × PE
        
        其中:
        - EPS由稀土价格和成本决定
        - PE由市场情绪决定（正常/牛市/熊市）
        """
        # 1. 计算EPS
        eps_data = self.calculate_eps(prnd_price, concentrate_change_pct)
        new_eps = eps_data["new_eps"]
        
        # 2. 确定PE（基于市场情绪）
        if market_sentiment == "bull":
            pe = self.params["pe_bull"]
            pe_desc = "牛市估值（战略溢价）"
        elif market_sentiment == "bear":
            pe = self.params["pe_bear"]
            pe_desc = "熊市估值"
        elif market_sentiment == "high_risk":
            pe = self.params["pe_high_risk"]
            pe_desc = "高风险估值（需警惕）"
        else:
            pe = self.params["pe_normal"]
            pe_desc = "正常估值"
        
        # 3. 计算合理股价
        fair_price = new_eps * pe
        
        # 4. 风险提示
        risks = []
        if pe > 60:
            risks.append("估值过高，需业绩消化")
        if concentrate_change_pct > 20:
            risks.append("成本端压力大，利润空间被挤压")
        if eps_data["prnd_change_pct"] < -10:
            risks.append("稀土价格大幅下跌，业绩承压")
        
        return {
            "eps_data": eps_data,
            "pe": pe,
            "pe_desc": pe_desc,
            "fair_price": round(fair_price, 2),
            "risks": risks,
        }
    
    def calculate_valuation(self,
                          current_stock_price: float,
                          current_pe: float,
                          prnd_price: float,
                          news_items: List[Dict]) -> Dict:
        """
        完整估值分析
        """
        # 分析新闻判断市场情绪和成本端变化
        all_text = " ".join([n.get("title", "") for n in news_items])
        
        # 情绪判断
        bullish_words = ["上涨", "利好", "突破", "订单", "增长", "涨价", "供应紧张", "收储"]
        bearish_words = ["下跌", "利空", "跌破", "库存", "下降", "降价", "供应过剩"]
        cost_rise_words = ["精矿涨价", "成本上升", "成本上涨"]
        cost_fall_words = ["精矿降价", "成本下降"]
        
        bullish_count = sum(1 for w in bullish_words if w in all_text)
        bearish_count = sum(1 for w in bearish_words if w in all_text)
        cost_rise_count = sum(1 for w in cost_rise_words if w in all_text)
        cost_fall_count = sum(1 for w in cost_fall_words if w in all_text)
        
        # 市场情绪
        if bullish_count > bearish_count + 2:
            sentiment = "bull"
            sentiment_desc = "偏多（战略资源溢价）"
        elif bearish_count > bullish_count + 2:
            sentiment = "bear"
            sentiment_desc = "偏空"
        else:
            sentiment = "normal"
            sentiment_desc = "中性"
        
        # 成本端变化估算
        if cost_rise_count > cost_fall_count:
            concentrate_change = 15  # 假设成本上涨15%
        elif cost_fall_count > cost_rise_count:
            concentrate_change = -10  # 假设成本下降10%
        else:
            concentrate_change = 0
        
        # 计算合理股价
        fair_value = self.calculate_fair_price(
            prnd_price=prnd_price,
            concentrate_change_pct=concentrate_change,
            market_sentiment=sentiment
        )
        
        fair_price = fair_value["fair_price"]
        
        # 计算溢价/折价
        premium = (current_stock_price - fair_price) / fair_price * 100
        
        # PE估值风险判断
        pe_risk = ""
        if current_pe > 70:
            pe_risk = "⚠️ PE过高，估值泡沫风险"
        elif current_pe > 50:
            pe_risk = "⚡ PE偏高，需业绩验证"
        elif current_pe < 30:
            pe_risk = "💎 PE偏低，可能存在机会"
        
        # 投资建议
        if premium > 30 or current_pe > 70:
            recommendation = "高估"
            rec_emoji = "⚠️"
            action = "减仓/回避"
        elif premium > 10 or current_pe > 50:
            recommendation = "偏贵"
            rec_emoji = "📊"
            action = "谨慎持有"
        elif premium > -10:
            recommendation = "合理"
            rec_emoji = "➡️"
            action = "持有"
        elif premium > -30:
            recommendation = "偏低"
            rec_emoji = "📈"
            action = "逢低买入"
        else:
            recommendation = "低估"
            rec_emoji = "🔥"
            action = "积极买入"
        
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "current_price": current_stock_price,
            "current_pe": current_pe,
            "prnd_price": prnd_price,
            "fair_price": fair_price,
            "premium": round(premium, 1),
            "sentiment": sentiment_desc,
            "pe_risk": pe_risk,
            "recommendation": recommendation,
            "recommendation_emoji": rec_emoji,
            "action": action,
            "details": fair_value,
            "summary": f"当前股价¥{current_stock_price}(PE{current_pe:.1f})，合理价¥{fair_price}，溢价{premium:+.1f}%。{pe_risk}建议{action}。"
        }


class NRERDailyReportPro:
    """北方稀土日报生成器 - 专业版"""
    
    def __init__(self):
        self.em_fetcher = EastMoneyDataFetcher()
        self.price_fetcher = UltimatePriceFetcher()
        self.sina_fetcher = RealTimeDataFetcher()
        self.valuation = NRERProfessionalValuation()
    
    def generate_report(self) -> Dict:
        """生成日报"""
        
        print("="*70, file=sys.stderr)
        print("北方稀土估值日报[专业版 - 基于业绩弹性]", file=sys.stderr)
        print("="*70, file=sys.stderr)
        
        # 1. 获取氧化镨钕价格
        print("\n【1/4】获取氧化镨钕价格...", file=sys.stderr)
        prnd_data = self.price_fetcher.get_prnd_price()
        prnd_price = prnd_data.get("price", 85.0)
        print(f"  氧化镨钕: ¥{prnd_price}万/吨 (来源: {prnd_data.get('source')})", file=sys.stderr)
        
        # 2. 获取股票行情
        print("\n【2/4】获取股票行情...", file=sys.stderr)
        em_data = self.em_fetcher.get_all_data("600111")
        stock = em_data.get("stock", {})
        current_price = stock.get("price", 0)
        current_pe = stock.get("pe_ttm", 35)
        # 如果PE异常，使用默认值
        if current_pe < 5 or current_pe > 200:
            current_pe = 35
        print(f"  北方稀土: ¥{current_price}, PE: {current_pe:.2f}", file=sys.stderr)
        
        # 3. 获取新闻
        print("\n【3/4】获取行业新闻...", file=sys.stderr)
        news = self.sina_fetcher.get_industry_news(limit=15)
        print(f"  获取到 {len(news)} 条新闻", file=sys.stderr)
        
        # 4. 估值计算
        print("\n【4/4】专业估值分析...", file=sys.stderr)
        valuation = self.valuation.calculate_valuation(
            current_stock_price=current_price,
            current_pe=current_pe,
            prnd_price=prnd_price,
            news_items=news
        )
        
        print("\n" + "="*70, file=sys.stderr)
        print("完成!", file=sys.stderr)
        print("="*70, file=sys.stderr)
        
        return {
            "report_title": "北方稀土估值日报[专业版]",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "prnd_data": prnd_data,
            "stock": stock,
            "valuation": valuation,
            "news": news[:10],
        }
    
    def format_for_display(self, report: Dict) -> str:
        """格式化显示"""
        if "error" in report:
            return f"报告生成失败: {report['error']}"
        
        prnd = report['prnd_data']
        stock = report['stock']
        val = report['valuation']
        det = val['details']
        eps = det['eps_data']
        
        output = []
        output.append("=" * 70)
        output.append(f"📊 {report['report_title']}")
        output.append(f"生成时间: {report['generated_at']}")
        output.append("=" * 70)
        
        # 基本面
        output.append(f"\n【基本面】氧化镨钕价格")
        output.append(f"  当前价格: ¥{prnd['price']}万/吨")
        if prnd.get('price_range'):
            output.append(f"  价格区间: {prnd['price_range']}万/吨")
        output.append(f"  来源: {prnd.get('source', '未知')}")
        
        # 股票行情
        output.append(f"\n【股票行情】{stock.get('name')} ({stock.get('code')})")
        change_emoji = "📈" if stock.get('change', 0) >= 0 else "📉"
        output.append(f"  当前股价: ¥{stock.get('price')} {change_emoji} {stock.get('change', 0):+.2f}")
        # 使用修正后的PE
        display_pe = stock.get('pe_ttm', 35)
        if display_pe < 5 or display_pe > 200:
            display_pe = 35
        output.append(f"  当前PE: {display_pe:.2f}倍")
        output.append(f"  成交量: {stock.get('volume', 0)/10000:.0f}万手")
        
        # 估值结果
        output.append(f"\n【估值分析】{val['recommendation_emoji']} {val['recommendation']}")
        output.append(f"  合理股价: ¥{val['fair_price']:.2f}")
        output.append(f"  当前股价: ¥{val['current_price']:.2f}")
        output.append(f"  溢价率: {val['premium']:+.1f}%")
        output.append(f"  市场情绪: {val['sentiment']}")
        if val['pe_risk']:
            output.append(f"  {val['pe_risk']}")
        output.append(f"  操作建议: {val['action']}")
        
        # EPS计算过程
        output.append(f"\n【业绩弹性分析】")
        output.append(f"  基准EPS: ¥{eps['base_eps']}")
        output.append(f"  稀土价格变化: {eps['prnd_change_pct']:+.2f}%")
        output.append(f"  → 收入端变化: {eps['revenue_change_pct']:+.2f}% (弹性系数{det['eps_data'].get('elasticity', 2.3)}x)")
        if eps['cost_impact_pct'] != 0:
            output.append(f"  → 成本端冲击: {eps['cost_impact_pct']:+.2f}%")
        output.append(f"  → 净利润变化: {eps['profit_change_pct']:+.2f}%")
        output.append(f"  预测EPS: ¥{eps['new_eps']}")
        output.append(f"  应用PE: {det['pe']}x ({det['pe_desc']})")
        
        # 风险提示
        if det['risks']:
            output.append(f"\n【风险提示】")
            for risk in det['risks']:
                output.append(f"  ⚠️ {risk}")
        
        # 新闻
        output.append(f"\n【相关新闻】")
        for i, news in enumerate(report['news'][:5], 1):
            title = news['title'][:40] + "..." if len(news['title']) > 40 else news['title']
            output.append(f"  {i}. {title}")
        
        output.append("\n" + "=" * 70)
        output.append("免责声明: 本报告基于公开数据和专业模型估算，仅供参考，不构成投资建议")
        output.append("=" * 70)
        
        return "\n".join(output)


def main():
    """主函数"""
    generator = NRERDailyReportPro()
    report = generator.generate_report()
    
    print("\n" + generator.format_for_display(report))
    
    # 保存
    output_file = f"/Users/Zhuanz/.config/stock-morning-report/reports/{datetime.now().strftime('%Y-%m-%d')}_pro.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n报告已保存: {output_file}", file=sys.stderr)


if __name__ == "__main__":
    main()
