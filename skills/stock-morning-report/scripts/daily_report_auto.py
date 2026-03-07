#!/usr/bin/env python3
"""
北方稀土全自动估值日报系统
整合实时数据获取 + 四维度估值模型
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from realtime_data import RealTimeDataFetcher
from nrer_valuation_system import NRERValuationSystem

class NRERDailyReport:
    """北方稀土日报生成器"""
    
    def __init__(self):
        self.data_fetcher = RealTimeDataFetcher()
        self.valuation_system = NRERValuationSystem()
    
    def generate_report(self) -> Dict:
        """生成完整日报"""
        
        print("="*50, file=sys.stderr)
        print("开始生成北方稀土估值日报", file=sys.stderr)
        print("="*50, file=sys.stderr)
        
        # 1. 获取实时数据
        print("\n【1/4】获取实时数据...", file=sys.stderr)
        data = self.data_fetcher.get_all_data("600111")
        
        stock = data.get("stock", {})
        prices = data.get("rare_earth_prices", {})
        news = data.get("news", [])
        
        # 检查数据有效性
        if "error" in stock:
            print(f"错误: 无法获取股票数据 - {stock['error']}", file=sys.stderr)
            return {"error": "数据获取失败"}
        
        current_price = stock.get("price", 0)
        prnd_price = prices.get("prnd", 85.0)
        
        print(f"  股票: {stock.get('name')} ¥{current_price}", file=sys.stderr)
        print(f"  氧化镨钕: ¥{prnd_price}万/吨", file=sys.stderr)
        print(f"  新闻: {len(news)}条", file=sys.stderr)
        
        # 2. 估值计算
        print("\n【2/4】进行四维度估值分析...", file=sys.stderr)
        valuation = self.valuation_system.calculate_valuation(
            current_price=current_price,
            prnd_price=prnd_price,
            news_items=news
        )
        
        # 3. 生成报告
        print("\n【3/4】生成报告...", file=sys.stderr)
        report = {
            "report_title": "北方稀土每日基本面估值报告",
            "generated_at": f"{data['date']} {data['time']}",
            "data_sources": data.get("data_sources", []),
            
            # 市场数据
            "market_data": {
                "stock_name": stock.get("name"),
                "stock_code": stock.get("code"),
                "current_price": current_price,
                "prev_close": stock.get("prev_close"),
                "change": stock.get("change"),
                "change_pct": stock.get("change_pct"),
                "open": stock.get("open"),
                "high": stock.get("high"),
                "low": stock.get("low"),
                "volume": stock.get("volume"),
                "volume_wan": round(stock.get("volume", 0) / 10000, 2),
                "amount": stock.get("amount"),
                "pe_ttm": stock.get("pe_ttm"),
                "pb": stock.get("pb"),
                "market_cap": stock.get("market_cap"),
            },
            
            # 稀土价格
            "rare_earth_prices": {
                "prnd_price": prnd_price,
                "prnd_source": prices.get("source"),
                "prnd_update_time": prices.get("update_time"),
            },
            
            # 估值结果
            "valuation": valuation,
            
            # 新闻列表
            "news": news[:10],  # 只保留前10条
        }
        
        # 4. 生成摘要
        print("\n【4/4】完成!", file=sys.stderr)
        print("="*50, file=sys.stderr)
        
        return report
    
    def format_for_display(self, report: Dict) -> str:
        """格式化为可读文本"""
        if "error" in report:
            return f"报告生成失败: {report['error']}"
        
        md = report['market_data']
        val = report['valuation']
        v = val['valuation']
        
        output = []
        output.append("=" * 60)
        output.append(f"📊 {report['report_title']}")
        output.append(f"生成时间: {report['generated_at']}")
        output.append("=" * 60)
        
        # 股票信息
        output.append(f"\n【股票行情】{md['stock_name']} ({md['stock_code']})")
        change_emoji = "📈" if md['change'] >= 0 else "📉"
        output.append(f"  现价: ¥{md['current_price']} {change_emoji} {md['change']:+.2f} ({md['change_pct']:+.2f}%)")
        output.append(f"  开盘: ¥{md['open']} | 最高: ¥{md['high']} | 最低: ¥{md['low']}")
        output.append(f"  成交: {md['volume_wan']:.0f}万手 | 市值: ¥{md['market_cap']:.0f}亿")
        output.append(f"  PE(TTM): {md['pe_ttm']:.2f} | PB: {md['pb']:.2f}")
        
        # 稀土价格
        re = report['rare_earth_prices']
        output.append(f"\n【稀土价格】氧化镨钕: ¥{re['prnd_price']}万/吨 (来源: {re['prnd_source']})")
        
        # 估值结果
        output.append(f"\n【估值结果】{val['recommendation_emoji']} {val['recommendation']}")
        output.append(f"  目标价: ¥{v['target_price']:.2f} (较当前{v['upside']:+.1f}%)")
        output.append(f"  EPS: {v['base_eps']} → {v['adjusted_eps']:.2f}")
        output.append(f"  PE: {v['base_pe']}x → {v['adjusted_pe']}x")
        
        # 四维度评分
        output.append(f"\n【四维度评分卡】总分: {v['total_score']}/{v['max_score']} ({v['score_ratio']:.0f}%)")
        for dim in val['dimensions']:
            emoji = "🟢" if dim['score'] > 0 else "🔴" if dim['score'] < 0 else "⚪"
            output.append(f"  {emoji} {dim['dimension']}({dim['weight']}): {dim['score']:+.0f}分 - {dim['rating']}")
            if dim['signals']:
                output.append(f"      信号: {', '.join(dim['signals'])}")
        
        # 新闻
        output.append(f"\n【相关新闻】")
        for i, news in enumerate(report['news'][:5], 1):
            output.append(f"  {i}. [{news['keyword']}] {news['title'][:40]}...")
        
        # 数据源
        output.append(f"\n【数据源】")
        for src in report['data_sources']:
            output.append(f"  • {src}")
        
        output.append("\n" + "=" * 60)
        output.append("免责声明: 本报告仅供参考，不构成投资建议")
        output.append("=" * 60)
        
        return "\n".join(output)


def main():
    """主函数"""
    report_generator = NRERDailyReport()
    report = report_generator.generate_report()
    
    # 打印可读版本
    print("\n" + report_generator.format_for_display(report))
    
    # 保存JSON版本
    output_file = f"/Users/Zhuanz/.config/stock-morning-report/reports/{report['generated_at'][:10]}.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n报告已保存: {output_file}", file=sys.stderr)


if __name__ == "__main__":
    main()
