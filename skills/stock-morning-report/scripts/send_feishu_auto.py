#!/usr/bin/env python3
"""
发送北方稀土日报到飞书
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from daily_report_auto import NRERDailyReport

def build_feishu_card(report: dict) -> dict:
    """构建飞书卡片"""
    
    md = report['market_data']
    val = report['valuation']
    v = val['valuation']
    
    # 涨跌颜色
    change_color = "green" if md['change'] >= 0 else "red"
    change_emoji = "📈" if md['change'] >= 0 else "📉"
    
    elements = [
        # 股票基本信息
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"## {md['stock_name']} ({md['stock_code']})\n"
                          f"**现价**: ¥{md['current_price']} {change_emoji} {md['change']:+.2f} ({md['change_pct']:+.2f}%)\n"
                          f"开盘: ¥{md['open']} | 最高: ¥{md['high']} | 最低: ¥{md['low']}\n"
                          f"成交: {md['volume_wan']:.0f}万手 | 市值: ¥{md['market_cap']:.0f}亿"
            }
        },
        # 稀土价格
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"**氧化镨钕价格**: ¥{report['rare_earth_prices']['prnd_price']}万/吨\n"
                          f"*来源: {report['rare_earth_prices']['prnd_source']}*"
            }
        },
        {"tag": "hr"},
        # 估值结果
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"### {val['recommendation_emoji']} 投资建议: {val['recommendation']}\n"
                          f"**目标价**: ¥{v['target_price']:.2f} (较当前{v['upside']:+.1f}%)\n"
                          f"EPS: {v['base_eps']} → {v['adjusted_eps']:.2f} | PE: {v['base_pe']}x → {v['adjusted_pe']}x"
            }
        },
        # 四维度评分
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"**四维度评分**: {v['total_score']}/{v['max_score']}分 ({v['score_ratio']:.0f}%)"
            }
        }
    ]
    
    # 添加各维度详情
    for dim in val['dimensions']:
        emoji = "🟢" if dim['score'] > 0 else "🔴" if dim['score'] < 0 else "⚪"
        content = f"{emoji} **{dim['dimension']}** ({dim['weight']}): {dim['score']:+d}分 - {dim['rating']}"
        if dim['signals']:
            content += f"\n  信号: {', '.join(dim['signals'])}"
        
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": content
            }
        })
    
    # 新闻
    elements.append({"tag": "hr"})
    elements.append({
        "tag": "div",
        "text": {
            "tag": "lark_md",
            "content": "### 📰 相关新闻"
        }
    })
    
    for i, news in enumerate(report['news'][:5], 1):
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"{i}. [{news['keyword']}] {news['title'][:45]}..."
            }
        })
    
    # 页脚
    elements.append({
        "tag": "note",
        "elements": [
            {
                "tag": "plain_text",
                "content": f"📊 数据来源: {', '.join(report['data_sources'])}\n"
                          f"⏰ 生成时间: {report['generated_at']}\n"
                          f"⚠️ 免责声明: 本报告仅供参考，不构成投资建议"
            }
        ]
    })
    
    card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "template": "blue",
            "title": {
                "tag": "plain_text",
                "content": f"📊 北方稀土基本面估值日报 - {report['generated_at'][:10]}"
            }
        },
        "elements": elements
    }
    
    return card


def main():
    """生成并发送报告"""
    print("正在生成北方稀土日报...", file=sys.stderr)
    
    generator = NRERDailyReport()
    report = generator.generate_report()
    
    if "error" in report:
        print(f"错误: {report['error']}", file=sys.stderr)
        sys.exit(1)
    
    # 构建飞书卡片
    card = build_feishu_card(report)
    
    # 输出JSON格式（供调用方使用）
    output = {
        "feishu_card": card,
        "report_summary": {
            "date": report['generated_at'][:10],
            "stock": report['market_data']['stock_name'],
            "recommendation": report['valuation']['recommendation'],
            "target_price": report['valuation']['valuation']['target_price'],
            "upside": report['valuation']['valuation']['upside']
        }
    }
    
    print(json.dumps(output, ensure_ascii=False, indent=2))
    
    print("\n日报生成完成!", file=sys.stderr)
    print(f"建议: {report['valuation']['recommendation']}", file=sys.stderr)
    print(f"目标价: ¥{report['valuation']['valuation']['target_price']:.2f}", file=sys.stderr)


if __name__ == "__main__":
    main()
