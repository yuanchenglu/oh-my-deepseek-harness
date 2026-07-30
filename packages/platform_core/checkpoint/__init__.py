"""Checkpoint — 四维审查状态机

基于 I-11 Checkpoint 快照审查状态机概念：
- 快照提取 (§3.1)：从 Plan 状态提取结构化 Checkpoint
- 上下文递减性质 (§3.3)：仅读快照摘要，不读完整执行日志
"""

from platform_core.checkpoint.models import (
    CompletedStep, Checkpoint, ReviewResult,
    DictStep, CreateCheckpointRequest,
    generate_checkpoint_id, now_iso,
)
from platform_core.checkpoint.state_machine import (
    compute_alignment, compute_progress, compute_unexpected_impact,
    compute_adjustments, build_completed_summary, build_remaining_plan,
    build_current_goal,
    check_alignment_from_snapshot, check_progress_from_snapshot,
    adjustments_from_snapshot, compute_confidence,
)

# ── 类名别名（兼容期望模块级类名的调用方） ──
import platform_core.checkpoint.state_machine as CheckpointStateMachine  # noqa: F401

__all__ = [
    "CompletedStep",
    "Checkpoint",
    "ReviewResult",
    "DictStep",
    "CreateCheckpointRequest",
    "generate_checkpoint_id",
    "now_iso",
    "compute_alignment",
    "compute_progress",
    "compute_unexpected_impact",
    "compute_adjustments",
    "build_completed_summary",
    "build_remaining_plan",
    "build_current_goal",
    "check_alignment_from_snapshot",
    "check_progress_from_snapshot",
    "adjustments_from_snapshot",
    "compute_confidence",
    "CheckpointStateMachine",
]
