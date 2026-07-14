"""Memory Tagger 数据模型 — Pydantic v2"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

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


class TagRequest(BaseModel):
    """POST /memory/tag 请求体"""
    content: str = Field(..., min_length=1, description="需要打标签的记忆内容")


class TagResponse(BaseModel):
    """POST /memory/tag 响应体"""
    content: str
    tags: List[str]
    layer: MemoryLayer
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="分类置信度（0~1）",
    )


class QueryRequest(BaseModel):
    """POST /memory/query 请求体"""
    tags: Optional[List[str]] = Field(default=None, description="按标签筛选")
    layer: Optional[MemoryLayer] = Field(default=None, description="按层级筛选")
    limit: int = Field(default=50, ge=1, le=500, description="返回条数上限")


class QueryResponse(BaseModel):
    """POST /memory/query 响应体"""
    entries: List[MemoryEntry]
    total: int


class FilterRequest(BaseModel):
    """POST /memory/filter 请求体"""
    lambda_value: float = Field(
        alias="lambda",
        ge=0.0, le=1.0,
        description="Memory 强度参数 λ ∈ [0, 1]",
    )
    limit: int = Field(default=50, ge=1, le=500, description="返回条数上限")


class FilterResponse(BaseModel):
    """POST /memory/filter 响应体"""
    entries: List[MemoryEntry]
    total: int
    lambda_value: float
    included_layers: List[str]


class LambdaResponse(BaseModel):
    """GET /memory/lambda/{task_type} 响应体"""
    task_type: str
    suggested_lambda: float
    label: str
    entries: List[MemoryEntry]
    total: int


class ImportResponse(BaseModel):
    """POST /memory/import 响应体"""
    imported: int
    skipped: int
    total_files: int


class ErrorResponse(BaseModel):
    """统一错误响应"""
    error: str
    detail: Optional[str] = None
