---
name: stock-morning-report
description: 每日定时生成自选股晨报，获取新闻、AI分析基本面影响、评估估值变化，并推送到飞书。Use when: (1) 用户需要每日股票监控和新闻追踪，(2) 需要AI分析股票新闻对基本面的影响，(3) 需要定时推送股票报告到飞书，(4) 管理自选股列表和定时任务。
---

# 股票晨报 (Stock Morning Report)

每日定时生成自选股晨报，包含行情数据、新闻摘要、AI 基本面分析和估值影响评估。

## 功能概述

1. **定时推送**: 每天早上 10 点（工作日）自动执行
2. **自选股管理**: 支持自定义关注股票列表
3. **新闻获取**: 获取自选股相关新闻
4. **AI 分析**: 分析新闻对基本面的影响
5. **估值评估**: 判断对股票估值的影响方向
6. **飞书推送**: 以卡片形式推送到飞书

## 使用方法

### 1. 配置自选股

```bash
# 编辑自选股列表
mkdir -p ~/.config/stock-morning-report
cat > ~/.config/stock-morning-report/watchlist.json << 'EOF'
[
  {"code": "600111", "name": "北方稀土"},
  {"code": "000001", "name": "平安银行"},
  {"code": "300750", "name": "宁德时代"}
]
EOF
```

### 2. 设置定时任务

使用 OpenClaw Cron 设置每天早上 10 点执行：

```bash
openclaw config set cron.jobs.stock-morning-report '{
  "schedule": "0 10 * * 1-5",
  "enabled": true,
  "task": "生成并推送股票晨报"
}'
```

或使用系统 cron：

```bash
crontab -e
# 添加：
0 10 * * 1-5 python3 skills/stock-morning-report/scripts/generate_report.py
```

### 3. 手动执行

```bash
# 获取行情
python3 scripts/get_quotes.py

# 生成报告（需要 AI 分析新闻）
python3 scripts/generate_report.py

# 发送飞书消息
python3 scripts/send_to_feishu.py ~/.config/stock-morning-report/reports/2026-03-01.json
```

## 脚本说明

### scripts/get_quotes.py
获取自选股实时行情，使用腾讯财经 API。

输出示例：
```json
[
  {
    "code": "600111",
    "name": "北方稀土",
    "price": 62.40,
    "change": 3.30,
    "change_pct": 5.58
  }
]
```

### scripts/generate_report.py
生成晨报 JSON 文件。

**注意**: 此脚本需要配合 AI 分析流程使用。新闻分析和基本面评估需要调用 LLM 完成。

### scripts/send_to_feishu.py
构建并发送飞书卡片消息。

### scripts/daily_task.sh
完整的每日任务脚本，可被 cron 调用。

## AI 分析流程

完整的晨报生成需要以下步骤：

1. **获取行情**: `get_quotes.py`
2. **获取新闻**: 需要接入新闻 API（新浪财经/东方财富等）
3. **AI 分析**: 使用 LLM 分析每条新闻：
   - 新闻类型分类
   - 基本面影响判断
   - 估值影响评估
4. **生成报告**: 汇总分析结果
5. **推送消息**: 发送到飞书

## 新闻数据源

当前实现使用简化的新浪财经搜索。如需更完整的数据，建议集成：

- **AkShare**: `ak.stock_news_em()` 东方财富新闻
- **Tushare**: `pro.major_news()` 重大新闻
- **爬虫**: 针对特定财经网站的定向抓取

## 飞书推送配置

### 方式1: 使用 OpenClaw message 工具

由 Agent 直接调用 `message` 工具发送，无需额外配置。

### 方式2: Webhook 机器人

1. 在飞书群添加「自定义机器人」
2. 复制 Webhook URL
3. 设置环境变量：
   ```bash
   export FEISHU_WEBHOOK_URL="https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxx"
   ```

## 示例：完整工作流

```bash
# 1. 配置自选股
vim ~/.config/stock-morning-report/watchlist.json

# 2. 获取今日行情
python3 scripts/get_quotes.py > quotes.json

# 3. 获取新闻并 AI 分析
# （此处需要调用 LLM 分析新闻）

# 4. 生成报告
python3 scripts/generate_report.py

# 5. 推送到飞书
python3 scripts/send_to_feishu.py reports/2026-03-01.json
```

## 参考文档

详细配置说明见 [references/configuration.md](references/configuration.md)
