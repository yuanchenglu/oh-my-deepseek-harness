#!/bin/bash
# 数字分身一键安装/备份/迁移脚本
# 用法: bash scripts/install.sh [--dry-run]
set -euo pipefail

DRY_RUN="${1:-}"
BACKUP_SUFFIX=$(date '+%Y%m%dT%H%M%S')
HERMES_HOME="${HOME}/.hermes"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "=========================================="
echo "数字分身安装脚本"
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "模式: $([ "$DRY_RUN" = "--dry-run" ] && echo "DRY-RUN (预览)" || echo "实际执行")"
echo "=========================================="

# ─── 步骤 1: 检测+备份 ────────────────────────────────
echo ""
echo "【步骤 1/4】检测已有数字分身文件..."

BACKUP_FILES=(
    "$HERMES_HOME/SOUL.md"
    "$HERMES_HOME/memories/MEMORY.md"
    "$HERMES_HOME/memories/USER.md"
)

for f in "${BACKUP_FILES[@]}"; do
    if [ -f "$f" ]; then
        bak="$f.bak.$BACKUP_SUFFIX"
        echo "  发现: $f"
        echo "  备份: $bak"
        if [ "$DRY_RUN" != "--dry-run" ]; then
            cp "$f" "$bak"
        fi
    else
        echo "  未发现: $f (跳过)"
    fi
done

# ─── 步骤 2: 迁移分析 ────────────────────────────────
echo ""
echo "【步骤 2/4】迁移分析..."

MEMORY_FILE="$HERMES_HOME/memories/MEMORY.md"
if [ -f "$MEMORY_FILE" ]; then
    LINE_COUNT=$(wc -l < "$MEMORY_FILE")
    echo "  MEMORY.md 现有 $LINE_COUNT 行"
    echo "  分类规则: 操作类/铁律→Layer1, 参考类→Layer3, 上下文→archive"
else
    echo "  无现有 MEMORY.md，跳过迁移分析"
fi

# 输出迁移计划
cat > /tmp/migration-plan-$$.md << MIGEOF
# 数字分身安装迁移报告

安装时间: $(date '+%Y-%m-%d %H:%M:%S')

## 备份清单
MIGEOF

for f in "${BACKUP_FILES[@]}"; do
    if [ -f "$f" ]; then
        echo "- $f → $f.bak.$BACKUP_SUFFIX" >> /tmp/migration-plan-$$.md
    fi
done

cat >> /tmp/migration-plan-$$.md << MIGEOF

## 迁移摘要
- Layer 0 (身份): SOUL.md → 已就位
- Layer 1 (导航): MAP.md → 已创建
- Layer 2 (活跃记忆): MEMORY.md + USER.md → 已备份
- Layer 3 (参考): memories/*.md → 已就位

## 插件安装
- deepseek-harness → 将安装到 ~/.hermes/plugins/deepseek-harness/
MIGEOF

echo "  迁移计划已生成到: /tmp/migration-plan-$$.md"

# ─── 步骤 3: 安装文件 ────────────────────────────────
echo ""
echo "【步骤 3/4】安装插件文件..."

PLUGIN_SRC="$PROJECT_ROOT/plugins/deepseek-harness"
PLUGIN_DST="$HERMES_HOME/plugins/deepseek-harness"

if [ -d "$PLUGIN_SRC" ]; then
    echo "  源: $PLUGIN_SRC"
    echo "  目标: $PLUGIN_DST"
    if [ "$DRY_RUN" != "--dry-run" ]; then
        mkdir -p "$PLUGIN_DST"
        cp -r "$PLUGIN_SRC"/* "$PLUGIN_DST/"
        echo "  ✅ 插件文件已复制"
    else
        echo "  [DRY-RUN] 将复制: $(ls "$PLUGIN_SRC")"
    fi
else
    echo "  ⚠️ 插件源目录不存在: $PLUGIN_SRC"
fi

# ─── 步骤 4: 启用插件 ────────────────────────────────
echo ""
echo "【步骤 4/4】启用插件..."

if [ "$DRY_RUN" != "--dry-run" ]; then
    if command -v hermes &> /dev/null; then
        hermes plugins enable deepseek-harness 2>&1 || echo "  ⚠️ enable 失败，可能已经启用或 Hermes 未运行"
        echo "  检查插件状态:"
        hermes plugins list 2>&1 | grep -i digital || echo "  ⚠️ 未在插件列表中找到 deepseek-harness"
    else
        echo "  ⚠️ hermes 命令未找到，请手动运行: hermes plugins enable deepseek-harness"
    fi
else
    echo "  [DRY-RUN] 将执行: hermes plugins enable deepseek-harness"
fi

# ─── 完成 ──────────────────────────────────────────
echo ""
echo "=========================================="
if [ "$DRY_RUN" = "--dry-run" ]; then
    echo "DRY-RUN 完成 — 未实际修改任何文件"
    echo "如果要实际执行，运行: bash scripts/install.sh"
else
    # 复制迁移报告
    cp /tmp/migration-plan-$$.md "$PROJECT_ROOT/migration-report.md" 2>/dev/null || true
    echo "✅ 安装完成！迁移报告: migration-report.md"
    echo "请检查: hermes plugins list"
fi
echo "=========================================="
