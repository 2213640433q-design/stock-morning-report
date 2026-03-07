# 股票晨报推送

每天自动推送自选股行情和分析到飞书。

## 设置步骤

### 1. 创建飞书机器人

1. 打开飞书，进入一个群聊（或创建个人群）
2. 点击群设置 → 群机器人 → 添加机器人
3. 选择「自定义机器人」
4. 复制 **Webhook 地址**（格式：`https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxx`）

### 2. Fork/创建 GitHub 仓库

1. 登录 GitHub: https://github.com
2. 创建新仓库，命名为 `stock-morning-report`
3. 上传本仓库的所有文件：
   - `.github/workflows/stock-report.yml`
   - `stock_report.py`
   - `README.md`

### 3. 配置 Secrets

1. 进入你的 GitHub 仓库
2. 点击 **Settings** → **Secrets and variables** → **Actions**
3. 点击 **New repository secret**
4. 添加：
   - Name: `FEISHU_WEBHOOK_URL`
   - Value: 你的飞书 Webhook 地址

### 4. 修改自选股（可选）

编辑 `stock_report.py` 文件，修改 `WATCHLIST`：

```python
WATCHLIST = [
    {"code": "600111", "name": "北方稀土"},
    {"code": "000001", "name": "平安银行"},
    {"code": "300750", "name": "宁德时代"},
]
```

### 5. 测试运行

1. 进入 GitHub 仓库的 **Actions** 标签
2. 点击 **Stock Morning Report** 工作流
3. 点击 **Run workflow** 手动触发一次测试

## 定时说明

- **执行时间**: 北京时间每天早上 10:00
- **执行日**: 周一至周五（工作日）
- **时区**: UTC+8（北京时间）

## 推送内容

每条消息包含：
- 📈 股票名称和代码
- 💰 现价、涨跌、涨跌幅
- 📰 AI 趋势分析
- 💡 基本面影响评估
- 💰 估值影响判断

## 注意事项

1. GitHub Actions 免费额度：每月 2000 分钟（足够使用）
2. 飞书 webhook 有效期：如果机器人被删除或重置，需要更新 webhook 地址
3. 股票数据：使用腾讯财经 API，A 股实时数据

## 故障排查

如果收不到推送：

1. 检查 GitHub Actions 运行日志（Actions → 最近运行 → 查看日志）
2. 确认 Secrets 中的 webhook 地址正确
3. 飞书里确认机器人是否正常工作

## License

MIT
