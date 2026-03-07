#!/usr/bin/env python3
"""
推送股票晨报到飞书 - 估值版
"""

import json
import sys
import os

def build_feishu_card(report):
    header = {
        "template": "blue",
        "title": {
            "tag": "plain_text",
            "content": f"📊 北方稀土基本面估值报告 - {report['date']}"
        }
    }
    
    elements = []
    
    for stock in report['stocks']:
        code = stock['code']
        name = stock['name']
        quote = stock.get('quote', {})
        news = stock.get('news', [])
        valuation = stock.get('valuation')
        
        # ========== 股票基本信息 ==========
        price_info = ""
        if 'price' in quote and 'error' not in quote:
            change = quote.get('change', 0)
            change_pct = quote.get('change_pct', 0)
            change_emoji = "🟢" if change >= 0 else "🔴"
            sign = "+" if change >= 0 else ""
            price_info = f"**现价**: ¥{quote['price']} {change_emoji} {sign}{change} ({sign}{change_pct}%)"
            price_info += f"\n开盘: ¥{quote['open']} | 最高: ¥{quote['high']} | 最低: ¥{quote['low']}"
            price_info += f"\n成交量: {quote.get('volume', 0)/10000:.0f}万手"
        
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"## {name} ({code})\n{price_info}"
            }
        })
        
        # ========== 估值结果 ==========
        if valuation:
            rec = valuation.get('recommendation', '中性')
            rec_emoji = valuation.get('recommendation_emoji', '➡️')
            val = valuation.get('valuation', {})
            
            # 估值核心数据
            target = val.get('target_price', 0)
            current = val.get('current_price', 0)
            upside = val.get('upside', 0)
            upside_emoji = "📈" if upside > 0 else "📉" if upside < 0 else "➡️"
            
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"### {rec_emoji} 投资建议: {rec}\n"
                              f"**目标价**: ¥{target} {upside_emoji} (较当前{upside:+.1f}%)\n"
                              f"**当前价**: ¥{current}\n"
                              f"**EPS**: {val.get('base_eps')} → {val.get('adjusted_eps')} (调整后)\n"
                              f"**PE**: {val.get('base_pe')} → {val.get('adjusted_pe')}x (调整后)"
                }
            })
            
            # 四维度评分卡
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "### 📋 四维度基本面评分卡"
                }
            })
            
            dims = valuation.get('dimensions', [])
            for dim in dims:
                dim_name = dim.get('dimension', '')
                weight = dim.get('weight', '')
                score = dim.get('score', 0)
                max_score = dim.get('max_score', 1)
                rating = dim.get('rating', '中性')
                signals = dim.get('signals', [])
                details = dim.get('details', [])
                
                # 根据得分选择颜色
                ratio = score / max_score if max_score else 0
                if ratio >= 0.3:
                    color = "🟢"
                elif ratio >= 0.1:
                    color = "🟡"
                elif ratio > -0.1:
                    color = "⚪"
                elif ratio > -0.3:
                    color = "🟠"
                else:
                    color = "🔴"
                
                # 维度标题
                elements.append({
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**{dim_name}** ({weight}): {color} {score:+d}/{max_score}分 - {rating}"
                    }
                })
                
                # 信号
                if signals:
                    elements.append({
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"信号: {', '.join(signals)}"
                        }
                    })
                
                # 详情（只显示第一条）
                if details:
                    elements.append({
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"• {details[0]}"
                        }
                    })
            
            # 分析摘要
            summary = valuation.get('summary', '')
            if summary:
                elements.append({
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"### 💡 分析摘要\n{summary}"
                    }
                })
        
        # ========== 相关新闻 ==========
        if news:
            news_content = "### 📰 相关新闻\n"
            for j, n in enumerate(news[:5], 1):
                title = n.get('title', '')[:45]
                if len(n.get('title', '')) > 45:
                    title += "..."
                news_content += f"{j}. {title}\n"
            
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": news_content
                }
            })
    
    # 页脚
    elements.append({
        "tag": "note",
        "elements": [
            {
                "tag": "plain_text",
                "content": "📌 本报告基于公开信息自动分析，估值模型仅供参考，不构成投资建议。股市有风险，投资需谨慎。"
            }
        ]
    })
    
    card = {
        "config": {"wide_screen_mode": True},
        "header": header,
        "elements": elements
    }
    
    return card

def main():
    if len(sys.argv) < 2:
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        default_path = os.path.expanduser(f"~/.config/stock-morning-report/reports/{today}.json")
        if os.path.exists(default_path):
            report_path = default_path
        else:
            print("用法: python3 send_to_feishu.py <report.json>", file=sys.stderr)
            sys.exit(1)
    else:
        report_path = sys.argv[1]
    
    if not os.path.exists(report_path):
        print(f"错误: 报告文件不存在: {report_path}", file=sys.stderr)
        sys.exit(1)
    
    with open(report_path, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    card = build_feishu_card(report)
    
    output = {
        "feishu_card": card,
        "report_summary": {
            "date": report['date'],
            "stock_count": len(report['stocks']),
            "stocks": [s['name'] for s in report['stocks']]
        }
    }
    
    print(json.dumps(output, ensure_ascii=False, indent=2))
    
    print(f"\n报告生成完成！", file=sys.stderr)
    for s in report['stocks']:
        val = s.get('valuation')
        if val:
            v = val.get('valuation', {})
            print(f"  - {s['name']}: 目标价¥{v.get('target_price', '-')}, 建议{val.get('recommendation', '-')}", file=sys.stderr)

if __name__ == "__main__":
    main()
