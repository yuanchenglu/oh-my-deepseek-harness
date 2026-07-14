"""Checkpoint Review 数据模型 — Pydantic v2

基于 I-11 Checkpoint 快照审查状态机概念：
- 快照提取 (§3.1)：从 Plan 状态提取结构化 Checkpoint
- 上下文递减性质 (§3.3)：仅读快照摘要，不读完整执行日志
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field


class CompletedStep(BaseModel):
    """已完成的步骤摘要"""
    step_id: str = Field(..., description="步骤唯一标识")
    text: str = Field(..., description="步骤描述文本")
    result: str = Field(default="", description="步骤执行结果摘要（≤ 3 句话）")


class Checkpoint(BaseModel):
    """结构化 Checkpoint 快照"""
    checkpoint_id: str = Field(..., description="Checkpoint 唯一标识 (cp_xxx)")
    plan_id: str = Field(..., description="所属 Plan 唯一标识 (plan_xxx)")
    created_at: str = Field(..., description="创建时间 (ISO-8601)")
    checkpoint_number: int = Field(..., ge=1, description="Plan 内的 Checkpoint 编号（从 1 递增）")
    current_goal: str = Field(..., description="当前正在执行的目标描述")
    completed_steps_summary: List[CompletedStep] = Field(
        default_factory=list,
        description="已完成步骤的摘要列表",
    )
    unexpected_findings: List[str] = Field(
        default_factory=list,
        description="非预期发现（如 API 与文档不一致）",
    )
    remaining_plan: List[str] = Field(
        default_factory=list,
        description="剩余 Plan 步骤描述",
    )
    purpose: str = Field(
        default="step_threshold",
        description=(
            "触发目的: step_threshold | abnormal_event | phase_boundary"
        ),
    )


class CreateCheckpointRequest(BaseModel):
    """POST /checkpoint/create 请求体"""
    plan_id: str = Field(..., description="Plan 唯一标识")
    plan_steps: List[DictStep] = Field(
        ...,
        description="Plan 的完整步骤列表",
    )
    completed_step_ids: List[str] = Field(
        ...,
        description="已完成的步骤 ID 列表",
    )
    unexpected_findings: List[str] = Field(
        default_factory=list,
        description="执行过程中发现的非预期信息",
    )


class DictStep(BaseModel):
    """Plan 步骤的扁平结构（从外部传入）"""
    step_id: str = Field(..., description="步骤唯一标识")
    text: str = Field(..., description="步骤描述文本")
    status: str = Field(..., description="步骤状态")
    key: str = Field(default="", description="步骤关键词/主题")


class CreateCheckpointResponse(BaseModel):
    """POST /checkpoint/create 响应体"""
    checkpoint: Checkpoint


class ReviewRequest(BaseModel):
    """POST /checkpoint/review/{checkpoint_id} 请求体（目前为空，可用作未来扩展）"""
    pass


class ReviewResult(BaseModel):
    """Checkpoint 审查结果"""
    alignment: str = Field(
        ...,
        description="目标对齐程度: aligned | partial | deviated",
    )
    progress_status: str = Field(
        ...,
        description="进度状态: on_track | at_risk | behind",
    )
    unexpected_impact: str = Field(
        ...,
        description="意外发现影响: none | low | medium | high",
    )
    adjustments: List[str] = Field(
        default_factory=list,
        description="剩余计划调整建议",
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0, le=1.0,
        description="审查置信度 (0~1)",
    )


class ReviewResponse(BaseModel):
    """POST /checkpoint/review/{checkpoint_id} 响应体"""
    checkpoint_id: str
    review_result: ReviewResult


class ChainResponse(BaseModel):
    """GET /checkpoint/chain/{plan_id} 响应体"""
    plan_id: str
    checkpoints: List[Checkpoint]
    total: int


class ErrorResponse(BaseModel):
    """统一错误响应"""
    error: str
    detail: Optional[str] = None


def generate_checkpoint_id() -> str:
    """生成唯一 Checkpoint ID (cp_xxx)"""
    import uuid
    return f"cp_{uuid.uuid4().hex[:12]}"


def now_iso() -> str:
    """返回当前 UTC 时间 ISO-8601 字符串"""
    return datetime.now(timezone.utc).isoformat()
