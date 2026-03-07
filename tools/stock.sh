#!/bin/bash
# 股票查询工具 - 使用腾讯 API
# 用法: ./stock.sh 600111 或 ./stock.sh 000001

CODE="$1"

if [ -z "$CODE" ]; then
    echo "用法: stock <股票代码>"
    echo "示例: stock 600111 (北方稀土)"
    echo "      stock 000001 (平安银行)"
    exit 1
fi

# 判断市场
if [[ $CODE == 6* ]] || [[ $CODE == 5* ]] || [[ $CODE == 9* ]]; then
    MARKET="sh"  # 上海
elif [[ $CODE == 0* ]] || [[ $CODE == 3* ]] || [[ $CODE == 2* ]]; then
    MARKET="sz"  # 深圳
elif [[ $CODE == 43* ]] || [[ $CODE == 83* ]] || [[ $CODE == 87* ]]; then
    MARKET="bj"  # 北京
else
    MARKET="sh"
fi

# 获取数据
URL="https://qt.gtimg.cn/q=${MARKET}${CODE}"
DATA=$(curl -s "$URL" | iconv -f GBK -t UTF-8 2>/dev/null || curl -s "$URL")

# 解析数据
# 腾讯返回格式: v_sh600111="1~北方稀土~...~最新价~...";
if [[ $DATA =~ v_${MARKET}${CODE}=\"([^\"]+)\" ]]; then
    IFS='~' read -ra FIELDS <<< "${BASH_REMATCH[1]}"
    
    NAME="${FIELDS[1]}"
    PRICE="${FIELDS[3]}"
    PREV_CLOSE="${FIELDS[4]}"
    OPEN="${FIELDS[5]}"
    VOLUME="${FIELDS[6]}"
    HIGH="${FIELDS[33]}"
    LOW="${FIELDS[34]}"
    UPDATE_TIME="${FIELDS[30]}"  # 格式: YYYYMMDDhhmmss
    
    # 格式化时间 YYYYMMDDhhmmss -> YYYY-MM-DD hh:mm:ss
    if [ ${#UPDATE_TIME} -eq 14 ]; then
        FORMATTED_TIME="${UPDATE_TIME:0:4}-${UPDATE_TIME:4:2}-${UPDATE_TIME:6:2} ${UPDATE_TIME:8:2}:${UPDATE_TIME:10:2}:${UPDATE_TIME:12:2}"
    else
        FORMATTED_TIME=$(date '+%Y-%m-%d %H:%M:%S')
    fi
    
    # 计算涨跌
    if command -v bc >/dev/null 2>&1; then
        CHANGE=$(echo "scale=2; $PRICE - $PREV_CLOSE" | bc)
        CHANGE_PCT=$(echo "scale=2; ($CHANGE / $PREV_CLOSE) * 100" | bc)
    else
        CHANGE="N/A"
        CHANGE_PCT="N/A"
    fi
    
    echo "📈 $NAME ($CODE)"
    echo "━━━━━━━━━━━━━━━━"
    echo "现价: ¥$PRICE"
    echo "涨跌: $CHANGE ($CHANGE_PCT%)"
    echo "今开: ¥$OPEN | 最高: ¥$HIGH | 最低: ¥$LOW"
    echo "━━━━━━━━━━━━━━━━"
    echo "更新时间: $FORMATTED_TIME"
    echo "数据来源: 腾讯财经"
else
    echo "无法获取股票 $CODE 的数据，请检查代码是否正确"
fi
