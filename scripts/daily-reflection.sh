#!/bin/bash
# 三省吾身 — 每日反思脚本
# 读取 Hermes state.db 昨日 session 记录，生成反思报告
set -euo pipefail

LOCK_FILE="/tmp/digital-twin-reflection.lock"
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
    echo "错误: 已有进程在运行 (锁文件: $LOCK_FILE)"
    exit 1
fi

REFLECTIONS_DIR="$HOME/.hermes/reflections"
mkdir -p "$REFLECTIONS_DIR"

DATE_TAG=$(date '+%Y-%m-%d')
OUTPUT_FILE="$REFLECTIONS_DIR/$DATE_TAG.md"
DB_PATH="$HOME/.hermes/state.db"

# state.db 不存在时生成空报告
if [ ! -f "$DB_PATH" ]; then
    cat > "$OUTPUT_FILE" << EOF
# 三省吾身 — $DATE_TAG

昨日无活动（state.db 不存在）。

EOF
    echo "state.db 不存在，已生成空报告"
    exit 0
fi

# 查询昨日 session 统计
SQL_RESULT=$(sqlite3 -readonly "$DB_PATH" "
SELECT date(started_at) as day,
       COUNT(*) as session_count,
       COALESCE(SUM(message_count), 0) as total_messages,
       COALESCE(SUM(tool_call_count), 0) as total_tool_calls,
       COALESCE(GROUP_CONCAT(DISTINCT model), 'N/A') as models_used
FROM sessions
WHERE date(started_at) = date('now', '-1 day')
GROUP BY date(started_at);
")

if [ -z "$SQL_RESULT" ]; then
    # 昨日无 activity
    cat > "$OUTPUT_FILE" << EOF
# 三省吾身 — $DATE_TAG

昨日无活动记录。

EOF
else
    # 解析 SQL 结果（sqlite3 默认 | 分隔）
    IFS='|' read -r day sessions msgs tools models <<< "$SQL_RESULT"
    cat > "$OUTPUT_FILE" << EOF
# 三省吾身 — $DATE_TAG

## 昨日概要
- Session 数: $sessions
- 消息总数: $msgs
- 工具调用数: $tools
- 使用模型: $models

## 工具使用统计
（待后续扩展）

## 关键模式
（待后续扩展）

## 改进建议
（待后续扩展）
EOF
fi

echo "反思报告已生成: $OUTPUT_FILE"
