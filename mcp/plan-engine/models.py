"""Pydantic 数据模型 — Plan Engine

定义 OKRPlanStep 的完整数据模型：
- PlanStatus: 步骤状态枚举（pending / in_progress / completed / pending_review）
- AssociationStrength: 关联强度枚举（strong / moderate / weak）
- OKRPlanStep: 核心步骤数据模型（含 DAG 依赖字段）
- CreatePlanResponse / UpdateStepRequest / CascadeResponse / PlanStatusResponse: API 响应模型
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class PlanStatus(str, Enum):
    """步骤状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PENDING_REVIEW = "pending_review"


class AssociationStrength(str, Enum):
    """关联强度"""
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"


class OKRPlanStep(BaseModel):
    """OKR 增强型 PlanStep 数据模型

    Attributes:
        step_id: 步骤唯一标识（UUID）
        text: 步骤描述
        key: 关键结果/里程碑标识
        status: 当前状态
        parent_id: 父步骤 ID（用于父子层级）
        dependency_ids: 依赖步骤 ID 列表（DAG 边）
        association_strength: 与父/依赖步骤的关联强度
        children: 子步骤列表（不持久化，运行时构建）
    """
    step_id: str = ""
    text: str
    key: str = ""
    status: PlanStatus = PlanStatus.PENDING
    parent_id: Optional[str] = None
    dependency_ids: List[str] = Field(default_factory=list)
    association_strength: AssociationStrength = AssociationStrength.MODERATE
    children: List[OKRPlanStep] = Field(default_factory=list)


# ── API 请求/响应模型 ──────────────────────────────────────


class CreatePlanRequest(BaseModel):
    """创建 Plan 请求"""
    task_description: str


class CreatePlanResponse(BaseModel):
    """创建 Plan 响应"""
    plan_id: str
    steps: List[OKRPlanStep]


class UpdateStepRequest(BaseModel):
    """更新步骤请求"""
    text: Optional[str] = None
    key: Optional[str] = None
    status: Optional[PlanStatus] = None
    parent_id: Optional[str] = None
    dependency_ids: Optional[List[str]] = None
    association_strength: Optional[AssociationStrength] = None


class CascadeRequest(BaseModel):
    """级联修正请求"""
    plan_id: str
    modified_step_id: str


class CascadeResponse(BaseModel):
    """级联修正响应"""
    affected_steps: List[str]
    action: Dict[str, str]


class PlanStatusResponse(BaseModel):
    """Plan 状态响应"""
    plan_id: str
    steps: List[OKRPlanStep]
    adjacency_list: Dict[str, List[str]]
    created_at: str
    updated_at: str


class ErrorResponse(BaseModel):
    """错误响应"""
    detail: str
