"""Memory Tagger 数据模型 — Pydantic v2（纯业务层）"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class MemoryLayer(str, Enum):
    """记忆层级：对应 I-12 §3.1–3.2 中的分层标记"""
    CONSTRAINT = "constraint"      # 全局约束，不可遗忘（如安全/合规）
    PREFERENCE = "preference"      # 技术偏好与习惯
    STYLE = "style"                # 风格偏好，写作/表达方式
    DECISION = "decision"          # 历史决策与结论
    PATTERN = "pattern"            # 成功模式与经验规律


class MemoryEntry(BaseModel):
    """单条记忆记录"""
    content: str = Field(..., description="记忆内容原文")
    tags: List[str] = Field(default_factory=list, description="关键词标签列表")
    layer: MemoryLayer = Field(..., description="记忆所属层级")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="创建时间（UTC ISO-8601）",
    )

    model_config = {"from_attributes": True}
