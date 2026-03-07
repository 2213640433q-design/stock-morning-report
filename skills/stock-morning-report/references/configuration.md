# 股票晨报配置指南

## 自选股配置

编辑 `~/.config/stock-morning-report/watchlist.json`：

```json
[
  {"code": "600111", "name": "北方稀土"},
  {"code": "000001", "name": "平安银行"},
  {"code": "300750", "name": "宁德时代"},
  {"code": "00700", "name": "腾讯控股"}
]
```

## 飞书推送配置

### 方式1: Webhook 机器人

1. 在飞书群中添加「自定义机器人」
2. 获取 Webhook URL
3. 设置环境变量：
   ```bash
   export FEISHU_WEBHOOK_URL="https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx"
   ```

### 方式2: 通过 OpenClaw Agent 推送

使用 OpenClaw 的 `message` 工具直接发送消息到用户。

## 定时任务配置

### 使用 OpenClaw Cron

```bash
openclaw cron add \
  --name "stock-morning-report" \
  --schedule "0 10 * * 1-5" \
  --command "python3 ~/.openclaw/skills/stock-morning-report/scripts/daily_task.sh"
```

### 使用系统 Cron

```bash
# 编辑 crontab
crontab -e

# 添加（工作日早上10点执行）
0 10 * * 1-5 /bin/bash ~/.openclaw/skills/stock-morning-report/scripts/daily_task.sh
```

## 新闻数据源

当前使用新浪财经搜索，如需更优质数据源，可考虑：

- **AkShare**: 免费财经数据接口
- **Tushare**: 专业金融数据（需积分）
- **东方财富**: 爬虫获取

## AI 分析说明

晨报的核心价值在于 AI 对新闻的分析。当前流程：

1. 获取股票新闻
2. 调用 OpenClaw Agent 进行分析
3. 生成基本面影响评估
4. 判断估值影响

分析维度：
- 新闻类型（政策/业绩/行业/公司）
- 影响方向（利好/利空/中性）
- 影响程度（重大/一般/轻微）
- 估值影响（上调/下调/维持）
