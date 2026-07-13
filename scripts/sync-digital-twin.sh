#!/bin/bash
# AIPC → MacBook Air 单向主从同步脚本
# 同步数字分身的 SOUL.md、记忆文件、插件到 MacBook Air
set -euo pipefail

LOCK_FILE="/tmp/digital-twin-sync.lock"
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
    echo "错误: 已有同步进程在运行 (锁文件: $LOCK_FILE)"
    exit 1
fi

SOURCE_HOST="AIPC"
SOURCE_BASE="~/.hermes"
DEST_BASE="$HOME/.hermes"

# 需要同步的路径
SYNC_PATHS=("SOUL.md" "memories/" "plugins/digital-twin/")

# 排除敏感文件和目录
EXCLUDES=("--exclude=.env" "--exclude=config.yaml" "--exclude=state.db" "--exclude=sessions/" "--exclude=.git/" "--exclude=__pycache__/")

for path in "${SYNC_PATHS[@]}"; do
    # --backup --suffix=.local: 目标已有文件备份为 {file}.local
    rsync -avz --backup --suffix=".local" "${EXCLUDES[@]}" \
        "$SOURCE_HOST:$SOURCE_BASE/$path" \
        "$DEST_BASE/$path"
done

echo "同步完成于 $(date)"
