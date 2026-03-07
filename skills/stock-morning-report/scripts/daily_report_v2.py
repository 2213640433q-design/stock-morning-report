#!/usr/bin/env python3
"""
北方稀土估值系统 - 正确逻辑版
氧化镨钕价格 → 合理股价 → 对比当前股价
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime
from typing import Dict, List

from eastmoney_api import EastMoneyDataFetcher
from price_search import RareEarthPriceSearch
from realtime_data import RealTimeDataFetcher

class NRERCorrectValuation:
    """北方稀土正确估值模型"""
    
    def __init__(self):
        # 估值参数
        self.params = {
            "base_prnd_price": 85.0,     # 氧化镨钕基准价格(万元/吨)
            "base_stock_price": 55.0,     # 对应基准股价
            "sensitivity": 0.8,            # 价格敏感度: 稀土价格每变化1%, 股价变化0.8%
            "pe_normal": 35,              # 正常PE
            "pe_bull": 45,                # 牛市PE
            "pe_bear": 25,                # 熊市PE
        }
    
    def calculate_fair_price(self, prnd_price: float, market_sentiment: str = "normal") -> Dict:
        """
        基于氧化镨钕价格计算合理股价
        
        逻辑:
        1. 计算稀土价格变化率
        2. 根据敏感度计算股价变化率
        3. 应用PE调整
        """
        base_prnd = self.params["base_prnd_price"]
        base_stock = self.params["base_stock_price"]
        sensitivity = self.params["sensitivity"]
        
        # 1. 稀土价格变化
        prnd_change_pct = (prnd_price - base_prnd) / base_prnd * 100
        
        # 2. 股价理论变化（考虑敏感度）
        stock_change_pct = prnd_change_pct * sensitivity
        
        # 3. 基础合理股价
        fair_price_base = base_stock * (1 + stock_change_pct / 100)
        
        # 4. 根据市场情绪调整PE
        if market_sentiment == "bull":
            pe = self.params["pe_bull"]
            pe_adjustment = 1.15  # 牛市溢价15%
        elif market_sentiment == "bear":
            pe = self.params["pe_bear"]
            pe_adjustment = 0.85  # 熊市折价15%
        else:
            pe = self.params["pe_normal"]
            pe_adjustment = 1.0
        
        # 5. 最终合理股价
        fair_price = fair_price_base * pe_adjustment
        
        return {
            "prnd_price": prnd_price,
            "base_prnd_price": base_prnd,
            "prnd_change_pct": round(prnd_change_pct, 2),
            "stock_change_pct": round(stock_change_pct, 2),
            "fair_price_base": round(fair_price_base, 2),
            "pe": pe,
            "pe_adjustment": pe_adjustment,
            "fair_price": round(fair_price, 2),
        }
    
    def calculate_valuation(self, 
                          current_stock_price: float,
                          prnd_price: float,
                          news_items: List[Dict]) -> Dict:
        """
        完整估值分析
        """
        # 分析新闻判断市场情绪
        all_text = " ".join([n.get("title", "") for n in news_items])
        
        # 情绪关键词
        bullish_words = ["上涨", "利好", "突破", "订单", "增长", "涨价", "供应紧张"]
        bearish_words = ["下跌", "利空", "跌破", "库存", "下降", "降价", "供应过剩"]
        
        bullish_count = sum(1 for w in bullish_words if w in all_text)
        bearish_count = sum(1 for w in bearish_words if w in all_text)
        
        if bullish_count > bearish_count + 2:
            sentiment = "bull"
            sentiment_desc = "偏多"
        elif bearish_count > bullish_count + 2:
            sentiment = "bear"
            sentiment_desc = "偏空"
        else:
            sentiment = "normal"
            sentiment_desc = "中性"
        
        # 计算合理股价
        fair_value = self.calculate_fair_price(prnd_price, sentiment)
        fair_price = fair_value["fair_price"]
        
        # 计算溢价/折价
        premium = (current_stock_price - fair_price) / fair_price * 100
        
        # 投资建议
        if premium > 15:
            recommendation = "高估"
            rec_emoji = "⚠️"
            action = "考虑减仓"
        elif premium > 5:
            recommendation = "偏贵"
            rec_emoji = "📊"
            action = "持有观望"
        elif premium > -5:
            recommendation = "合理"
            rec_emoji = "➡️"
            action = "持有"
        elif premium > -15:
            recommendation = "偏低"
            rec_emoji = "📈"
            action = "逢低关注"
        else:
            recommendation = "低估"
            rec_emoji = "🔥"
            action = "积极关注"
        
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "current_price": current_stock_price,
            "prnd_price": prnd_price,
            "fair_price": fair_price,
            "premium": round(premium, 1),
            "sentiment": sentiment_desc,
            "recommendation": recommendation,
            "recommendation_emoji": rec_emoji,
            "action": action,
            "details": fair_value,
            "summary": f"当前股价¥{current_stock_price}，合理价¥{fair_price}，溢价{premium:+.1f}%。建议{action}。"
        }


class NRERDailyReportV2:
    """北方稀土日报生成器V2 - 正确逻辑"""
    
    def __init__(self):
        self.em_fetcher = EastMoneyDataFetcher()
        self.price_searcher = RareEarthPriceSearch()
        self.sina_fetcher = RealTimeDataFetcher()
        self.valuation = NRERCorrectValuation()
    
    def generate_report(self) -> Dict:
        """生成日报"""
        
        print("="*60, file=sys.stderr)
        print("北方稀土估值日报[正确逻辑版]", file=sys.stderr)
        print("="*60, file=sys.stderr)
        
        # 1. 获取氧化镨钕价格（基本面）
        print("\n【1/4】获取氧化镨钕价格...", file=sys.stderr)
        prnd_data = self.price_searcher.search_prnd_price()
        prnd_price = prnd_data.get("price", 85.0)
        print(f"  氧化镨钕: ¥{prnd_price}万/吨 (来源: {prnd_data.get('source')})", file=sys.stderr)
        
        # 2. 获取股票行情
        print("\n【2/4】获取股票行情...", file=sys.stderr)
        em_data = self.em_fetcher.get_all_data("600111")
        stock = em_data.get("stock", {})
        current_price = stock.get("price", 0)
        print(f"  北方稀土: ¥{current_price}", file=sys.stderr)
        
        # 3. 获取新闻
        print("\n【3/4】获取行业新闻...", file=sys.stderr)
        news = self.sina_fetcher.get_industry_news(limit=15)
        print(f"  获取到 {len(news)} 条新闻", file=sys.stderr)
        
        # 4. 估值计算
        print("\n【4/4】计算估值...", file=sys.stderr)
        valuation = self.valuation.calculate_valuation(
            current_stock_price=current_price,
            prnd_price=prnd_price,
            news_items=news
        )
        
        print("\n" + "="*60, file=sys.stderr)
        print("完成!", file=sys.stderr)
        print("="*60, file=sys.stderr)
        
        return {
            "report_title": "北方稀土估值日报[基本面驱动版]",
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
        
        output = []
        output.append("=" * 70)
        output.append(f"📊 {report['report_title']}")
        output.append(f"生成时间: {report['generated_at']}")
        output.append("=" * 70)
        
        # 基本面
        output.append(f"\n【基本面】氧化镨钕价格")
        output.append(f"  当前: ¥{prnd['price']}万/吨")
        if prnd.get('price_range'):
            output.append(f"  区间: {prnd['price_range']}万/吨")
        output.append(f"  基准: ¥{det['base_prnd_price']}万/吨")
        output.append(f"  变化: {det['prnd_change_pct']:+.2f}%")
        output.append(f"  来源: {prnd.get('source', '未知')}")
        
        # 股票行情
        output.append(f"\n【股票行情】{stock.get('name')} ({stock.get('code')})")
        change_emoji = "📈" if stock.get('change', 0) >= 0 else "📉"
        output.append(f"  现价: ¥{stock.get('price')} {change_emoji} {stock.get('change', 0):+.2f}")
        output.append(f"  成交: {stock.get('volume', 0)/10000:.0f}万手")
        
        # 估值结果
        output.append(f"\n【估值分析】{val['recommendation_emoji']} {val['recommendation']}")
        output.append(f"  合理股价: ¥{val['fair_price']:.2f}")
        output.append(f"  当前股价: ¥{val['current_price']:.2f}")
        output.append(f"  溢价率: {val['premium']:+.1f}%")
        output.append(f"  市场情绪: {val['sentiment']}")
        output.append(f"  操作建议: {val['action']}")
        
        # 计算过程
        output.append(f"\n【计算逻辑】")
        output.append(f"  稀土价格变化: {det['prnd_change_pct']:+.2f}%")
        if det['prnd_change_pct'] != 0:
            sensitivity_ratio = det['stock_change_pct'] / det['prnd_change_pct']
            output.append(f"  → 股价理论变化: {det['stock_change_pct']:+.2f}% (敏感度{sensitivity_ratio:.1f}x)")
        else:
            output.append(f"  → 股价理论变化: {det['stock_change_pct']:+.2f}%")
        output.append(f"  → 基础合理价: ¥{det['fair_price_base']:.2f}")
        output.append(f"  → PE调整({det['pe']}x): ¥{val['fair_price']:.2f}")
        
        # 新闻
        output.append(f"\n【相关新闻】")
        for i, news in enumerate(report['news'][:5], 1):
            title = news['title'][:40] + "..." if len(news['title']) > 40 else news['title']
            output.append(f"  {i}. {title}")
        
        output.append("\n" + "=" * 70)
        output.append("免责声明: 本报告基于公开数据估算，仅供参考，不构成投资建议")
        output.append("=" * 70)
        
        return "\n".join(output)


def main():
    """主函数"""
    generator = NRERDailyReportV2()
    report = generator.generate_report()
    
    print("\n" + generator.format_for_display(report))
    
    # 保存
    output_file = f"/Users/Zhuanz/.config/stock-morning-report/reports/{datetime.now().strftime('%Y-%m-%d')}_v2.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n报告已保存: {output_file}", file=sys.stderr)


if __name__ == "__main__":
    main()
