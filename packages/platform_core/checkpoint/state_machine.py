"""Checkpoint 四维审查状态机

基于 I-11 Checkpoint 快照审查状态机：
1. 目标对齐（aligned / partial / deviated）
2. 进度状态（on_track / at_risk / behind）
3. 意外发现影响（none / low / medium / high）
4. 调整建议生成

所有函数均为确定性纯函数，不依赖任何 I/O 或外部服务。
"""

from __future__ import annotations

import logging
from typing import List

from platform_core.checkpoint.models import Checkpoint, CompletedStep, CreateCheckpointRequest

logger = logging.getLogger(__name__)


# ========================================================================
# 基于完整 Plan 数据的审查函数（需要原始 plan_steps 和 completed_step_ids）
# ========================================================================


def compute_alignment(
    checkpoint: Checkpoint,
    request: CreateCheckpointRequest,
) -> str:
    """检查已完成步骤是否与原始目标一致

    检查维度：
    - 已完成的步骤是否都是 plan_steps 中的子集
    - 是否有步骤完成但不在 plan_steps 中（跑偏）
    """
    plan_step_ids = {s.step_id for s in request.plan_steps}
    completed_ids = set(request.completed_step_ids)

    # 完成但不在 plan 中 → deviated
    extraneous = completed_ids - plan_step_ids
    if extraneous:
        logger.warning("发现 plan 外的完成步骤: %s", extraneous)
        return "deviated"

    # 无已完成的步骤，不需要判定
    if not completed_ids:
        return "aligned"

    # 全部在 plan 范围内 → aligned
    return "aligned"


def compute_progress(
    checkpoint: Checkpoint,
    request: CreateCheckpointRequest,
) -> str:
    """评估进度状态

    - 已完成步骤数 / 总步骤数 >= 0.5 → on_track
    - 0.25 ~ 0.5 → at_risk
    - < 0.25 → behind
    """
    total = len(request.plan_steps)
    done = len(request.completed_step_ids)
    if total == 0:
        return "on_track"

    ratio = done / total
    if ratio >= 0.5:
        return "on_track"
    elif ratio >= 0.25:
        return "at_risk"
    else:
        return "behind"


def compute_unexpected_impact(
    checkpoint: Checkpoint,
) -> str:
    """评估意外发现的影响程度

    - 无意外发现 → none
    - 发现条数 >= 3 或包含关键关键词 → high
    - 发现条数 >= 1 → medium/low 折中
    """
    findings = checkpoint.unexpected_findings or []
    if not findings:
        return "none"

    # 检查严重关键词
    severe_keywords = {"security", "vulnerability", "crash", "data loss",
                       "安全", "漏洞", "崩溃", "数据丢失"}
    combined = " ".join(f.lower() for f in findings)
    for kw in severe_keywords:
        if kw.lower() in combined:
            return "high"

    if len(findings) >= 3:
        return "medium"

    return "low"


def compute_adjustments(
    checkpoint: Checkpoint,
    request: CreateCheckpointRequest,
) -> List[str]:
    """根据审查情况生成剩余计划调整建议"""
    adjustments: List[str] = []

    alignment = compute_alignment(checkpoint, request)
    progress = compute_progress(checkpoint, request)
    impact = compute_unexpected_impact(checkpoint)

    if alignment == "deviated":
        adjustments.append("存在偏离原始目标的步骤，建议检查已完成步骤与 Plan 的对应关系")

    if progress == "behind":
        adjustments.append("进度严重落后于预期，建议评估是否需要缩减范围或追加资源")

    if impact == "high":
        adjustments.append("意外发现影响重大，建议暂停当前 Plan 并优先处理安全问题")
    elif impact == "medium":
        adjustments.append("有多项意外发现，建议在继续前先评估这些发现的影响")

    if checkpoint.remaining_plan:
        adjustments.append(
            f"剩余 {len(checkpoint.remaining_plan)} 步待完成: "
            f"{'; '.join(checkpoint.remaining_plan[:3])}"
            f"{'...' if len(checkpoint.remaining_plan) > 3 else ''}"
        )

    return adjustments


def build_completed_summary(
    request: CreateCheckpointRequest,
) -> List[CompletedStep]:
    """从请求中提取已完成的步骤摘要"""
    step_map = {s.step_id: s for s in request.plan_steps}
    summary: List[CompletedStep] = []
    for sid in request.completed_step_ids:
        step = step_map.get(sid)
        if step:
            summary.append(CompletedStep(
                step_id=sid,
                text=step.text,
                result="",
            ))
    return summary


def build_remaining_plan(request: CreateCheckpointRequest) -> List[str]:
    """提取剩余 Plan 步骤描述"""
    completed_set = set(request.completed_step_ids)
    return [
        f"[{s.step_id}] {s.text}" for s in request.plan_steps
        if s.step_id not in completed_set
    ]


def build_current_goal(request: CreateCheckpointRequest) -> str:
    """推断当前目标

    取第一个未完成的步骤作为当前目标；如果全部完成则返回最后一步。
    """
    completed_set = set(request.completed_step_ids)
    for s in request.plan_steps:
        if s.step_id not in completed_set:
            return s.text
    # 全部完成 → 取最后一步的文本
    if request.plan_steps:
        return request.plan_steps[-1].text
    return ""


# ========================================================================
# 基于快照的审查函数（无原始 plan_steps，仅从 Checkpoint 快照判断）
# ========================================================================


def check_alignment_from_snapshot(checkpoint: Checkpoint) -> str:
    """基于快照检查目标对齐

    无原始 plan_steps 时，用 completed_steps 的数量和内容判断：
    - 有 completed_steps 但无 remaining_plan → 全部完成 → aligned
    - 有 completed_steps 且有 remaining_plan → 正在执行 → aligned
    - 有 unexpected_findings 可能暗示偏离 → 降级为 partial
    """
    if not checkpoint.completed_steps_summary:
        return "aligned"  # 还没开始，无所谓偏离

    if checkpoint.unexpected_findings:
        # 有意外发现 → 可能走偏了
        return "partial"

    return "aligned"


def check_progress_from_snapshot(checkpoint: Checkpoint) -> str:
    """基于快照检查进度

    用 remaining_plan 和 completed_steps 的比率估算。
    """
    done = len(checkpoint.completed_steps_summary)
    remaining = len(checkpoint.remaining_plan)
    total = done + remaining

    if total == 0:
        return "on_track"

    ratio = done / total
    if ratio >= 0.5:
        return "on_track"
    elif ratio >= 0.25:
        return "at_risk"
    else:
        return "behind"


def adjustments_from_snapshot(
    checkpoint: Checkpoint,
    alignment: str,
    progress: str,
    impact: str,
) -> List[str]:
    """从快照生成调整建议"""
    adjustments: List[str] = []

    if alignment == "partial":
        adjustments.append("部分步骤可能偏离原始目标，建议复审已完成的步骤内容")

    if progress == "behind":
        adjustments.append("进度落后，建议考虑缩减范围或增加资源")

    if impact == "high":
        adjustments.append("安全/合规风险较高，建议暂停并优先处理意外发现")
    elif impact == "medium":
        adjustments.append("存在多项意外发现，建议评估后再继续")

    if checkpoint.remaining_plan:
        adjustments.append(
            f"剩余 {len(checkpoint.remaining_plan)} 步: "
            f"{'; '.join(checkpoint.remaining_plan[:3])}"
            f"{'...' if len(checkpoint.remaining_plan) > 3 else ''}"
        )

    return adjustments


def compute_confidence(
    alignment: str,
    progress: str,
    impact: str,
) -> float:
    """基于快照信息完整度计算审查置信度

    基准 0.85，以下情况递减：
    - 没有 completed_steps → 0.60（没足够数据）
    - aligned + none impact → 0.90（一切顺利，置信度高）
    - partial + high impact → 0.70（情况复杂，信息不足）
    """
    if alignment == "aligned" and impact == "none":
        return 0.90
    if alignment == "partial" and impact == "high":
        return 0.70
    if alignment == "deviated":
        return 0.60
    return 0.85
