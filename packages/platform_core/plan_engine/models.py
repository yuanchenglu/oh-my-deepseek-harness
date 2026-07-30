"""Pydantic 数据模型 — Plan Engine（纯业务层）

定义 OKRPlanStep 的核心数据模型：
- PlanStatus: 步骤状态枚举
- AssociationStrength: 关联强度枚举
- OKRPlanStep: 核心步骤数据模型（含 DAG 依赖字段）
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
