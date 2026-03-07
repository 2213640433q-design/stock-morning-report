#!/bin/bash
# 股票晨报每日任务脚本
# 由 cron 定时调用

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$HOME/.config/stock-morning-report"
REPORT_DIR="$CONFIG_DIR/reports"
LOG_FILE="$CONFIG_DIR/cron.log"

# 创建目录
mkdir -p "$REPORT_DIR"

# 记录日志
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "========== 开始生成股票晨报 =========="

# 1. 获取自选股列表
WATCHLIST_FILE="$CONFIG_DIR/watchlist.json"
if [ ! -f "$WATCHLIST_FILE" ]; then
    log "创建默认自选股列表..."
    cat > "$WATCHLIST_FILE" << 'EOF'
[
  {"code": "600111", "name": "北方稀土"},
  {"code": "000001", "name": "平安银行"}
]
EOF
fi

# 2. 获取行情
log "获取行情数据..."
python3 "$SCRIPT_DIR/get_quotes.py" > "$REPORT_DIR/quotes_$(date +%Y%m%d).json"

# 3. 生成报告（这里调用OpenClaw Agent进行AI分析）
log "生成报告..."
REPORT_JSON=$(python3 "$SCRIPT_DIR/generate_report.py" 2>/dev/null)

# 4. 保存报告
REPORT_FILE="$REPORT_DIR/$(date +%Y-%m-%d).json"
echo "$REPORT_JSON" > "$REPORT_FILE"
log "报告已保存: $REPORT_FILE"

# 5. 发送通知（可选）
# python3 "$SCRIPT_DIR/send_to_feishu.py" "$REPORT_FILE"

log "========== 股票晨报生成完成 =========="

# 输出报告路径供调用者使用
echo "$REPORT_FILE"
