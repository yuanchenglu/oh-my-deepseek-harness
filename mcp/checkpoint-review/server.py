"""Checkpoint Review MCP Server — FastAPI HTTP Server

基于 I-11 Checkpoint 快照审查状态机概念，提供 3 个 REST API 端点：
1. POST /checkpoint/create       — 从 Plan 状态提取结构化 Checkpoint 快照
2. POST /checkpoint/review/{id}  — 对 Checkpoint 执行独立审查
3. GET  /checkpoint/chain/{plan} — 获取 Plan 的完整 Checkpoint 链

触发规则（见文档）：
- 每 3 个 PlanStep 完成触发一次
- 异常事件立即触发
- 阶段边界强制触发

数据持久化：SQLite (~/.hermes/mcp/checkpoint-review.db)
"""

from __future__ import annotations

import logging
import os
import sys
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import (
    ChainResponse,
    Checkpoint,
    CompletedStep,
    CreateCheckpointRequest,
    CreateCheckpointResponse,
    ErrorResponse,
    ReviewRequest,
    ReviewResponse,
    ReviewResult,
    generate_checkpoint_id,
    now_iso,
)
from storage import CheckpointStorage

# ── 日志 ────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("checkpoint-review")

# ── 存储层初始化 ─────────────────────────────────────────────

DB_PATH = os.environ.get(
    "CHECKPOINT_DB_PATH",
    os.path.expanduser("~/.hermes/mcp/checkpoint-review.db"),
)
storage = CheckpointStorage(db_path=DB_PATH)

# ── FastAPI 应用 ────────────────────────────────────────────

app = FastAPI(
    title="Checkpoint Review MCP Server",
    description=(
        "基于 I-11 Checkpoint 快照审查状态机。"
        "从 Plan 状态提取结构化快照，执行轻量上下文审查。"
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========================================================================
# 审查核心逻辑（不对 LLM 做外部调用，而是基于结构化快照做确定性评判）
# ========================================================================


def _compute_alignment(
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

    # 完成数 < plan 步骤数且存在部分完成
    if not completed_ids:
        return "aligned"  # 无已完成的步骤，不需要判定

    # 全部在 plan 范围内 → aligned
    return "aligned"


def _compute_progress(
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


def _compute_unexpected_impact(
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


def _compute_adjustments(
    checkpoint: Checkpoint,
    request: CreateCheckpointRequest,
) -> List[str]:
    """根据审查情况生成剩余计划调整建议"""
    adjustments: List[str] = []

    alignment = _compute_alignment(checkpoint, request)
    progress = _compute_progress(checkpoint, request)
    impact = _compute_unexpected_impact(checkpoint)

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


def _build_completed_summary(
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


def _build_remaining_plan(request: CreateCheckpointRequest) -> List[str]:
    """提取剩余 Plan 步骤描述"""
    completed_set = set(request.completed_step_ids)
    return [
        f"[{s.step_id}] {s.text}" for s in request.plan_steps
        if s.step_id not in completed_set
    ]


def _build_current_goal(request: CreateCheckpointRequest) -> str:
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


# ========== API 端点 ==========


@app.post(
    "/checkpoint/create",
    response_model=CreateCheckpointResponse,
    responses={422: {"model": ErrorResponse}},
    summary="从 Plan 状态提取结构化 Checkpoint 快照",
    description=(
        "输入 Plan 步骤列表和已完成步骤 ID，生成结构化 Checkpoint 快照。"
        "自动递增 checkpoint_number。"
    ),
)
async def create_checkpoint(req: CreateCheckpointRequest):
    """POST /checkpoint/create — 创建 Checkpoint 快照"""
    try:
        if not req.plan_id:
            raise HTTPException(status_code=422, detail="plan_id 不能为空")

        # 自动计算编号
        next_num = storage._get_next_number(req.plan_id)

        # 构建摘要
        completed_summary = _build_completed_summary(req)
        remaining = _build_remaining_plan(req)
        current_goal = _build_current_goal(req)

        # 构建 Checkpoint
        checkpoint = Checkpoint(
            checkpoint_id=generate_checkpoint_id(),
            plan_id=req.plan_id,
            created_at=now_iso(),
            checkpoint_number=next_num,
            current_goal=current_goal,
            completed_steps_summary=completed_summary,
            unexpected_findings=req.unexpected_findings or [],
            remaining_plan=remaining,
            purpose="step_threshold",
        )

        # 持久化
        storage.insert(checkpoint)

        logger.info(
            "Checkpoint 创建成功: %s (plan=%s, #%d)",
            checkpoint.checkpoint_id,
            checkpoint.plan_id,
            checkpoint.checkpoint_number,
        )

        return CreateCheckpointResponse(checkpoint=checkpoint)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("create_checkpoint 错误: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/checkpoint/review/{checkpoint_id}",
    response_model=ReviewResponse,
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
    summary="对 Checkpoint 执行轻量上下文审查",
    description=(
        "从存储读取 Checkpoint 快照，对其执行四维审查："
        "目标对齐、进度偏差、意外发现影响、剩余计划调整建议。"
        "仅读快照，不读完整执行日志。"
    ),
)
async def review_checkpoint(checkpoint_id: str, req: ReviewRequest):  # noqa: ARG001
    """POST /checkpoint/review/{checkpoint_id} — 审查 Checkpoint"""
    try:
        checkpoint = storage.get(checkpoint_id)
        if checkpoint is None:
            raise HTTPException(
                status_code=404,
                detail=f"Checkpoint 不存在: {checkpoint_id}",
            )

        # 审查需要原始请求信息，但不读完整日志
        # 从存储的 data_json 中无法回溯 plan_steps，这里直接从快照做确定性判断
        alignment = _check_alignment_from_snapshot(checkpoint)
        progress = _check_progress_from_snapshot(checkpoint)
        impact = _compute_unexpected_impact(checkpoint)
        adjustments = _adjustments_from_snapshot(checkpoint, alignment, progress, impact)

        review_result = ReviewResult(
            alignment=alignment,
            progress_status=progress,
            unexpected_impact=impact,
            adjustments=adjustments,
            confidence=_compute_confidence(alignment, progress, impact),
        )

        logger.info(
            "审查完成: %s → alignment=%s, progress=%s, impact=%s",
            checkpoint_id,
            alignment,
            progress,
            impact,
        )

        return ReviewResponse(
            checkpoint_id=checkpoint_id,
            review_result=review_result,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("review_checkpoint 错误: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/checkpoint/chain/{plan_id}",
    response_model=ChainResponse,
    responses={422: {"model": ErrorResponse}},
    summary="获取 Plan 的完整 Checkpoint 链",
    description="返回按 checkpoint_number 升序排列的 Checkpoint 列表",
)
async def get_checkpoint_chain(plan_id: str):
    """GET /checkpoint/chain/{plan_id} — 获取 Checkpoint 链"""
    try:
        checkpoints = storage.get_chain(plan_id)
        return ChainResponse(
            plan_id=plan_id,
            checkpoints=checkpoints,
            total=len(checkpoints),
        )
    except Exception as e:
        logger.error("get_checkpoint_chain 错误: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/health",
    summary="健康检查",
    description="返回服务状态和存储统计",
)
async def health_check():
    """GET /health — 健康检查"""
    return {
        "status": "ok",
        "total_checkpoints": storage.count_all(),
        "db_path": storage.db_path,
    }


# ========================================================================
# 审查辅助函数（基于快照的确定性逻辑，不调用 LLM）
# ========================================================================


def _check_alignment_from_snapshot(checkpoint: Checkpoint) -> str:
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


def _check_progress_from_snapshot(checkpoint: Checkpoint) -> str:
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


def _adjustments_from_snapshot(
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


def _compute_confidence(
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


# ── 入口 ────────────────────────────────────────────────────


def main():
    """启动 FastAPI 服务"""
    import uvicorn

    host = os.environ.get("CHECKPOINT_HOST", "127.0.0.1")
    port = int(os.environ.get("CHECKPOINT_PORT", "8300"))

    logger.info("启动 Checkpoint Review MCP Server — %s:%d", host, port)
    logger.info("数据库路径: %s", storage.db_path)

    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
