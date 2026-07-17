"""合并后的 Pydantic 数据模型 — Harness Server

本文件合并了 3 个原服务的所有数据模型：
1. Plan Engine（I-06 OKR PlanStep DAG + 级联修正）
2. Memory Tagger（I-12 Memory 标签 + λ 过滤）
3. Checkpoint Review（I-11 Checkpoint 快照审查）

模型按服务分块组织，每块用分隔线隔开，方便查找。
"""

from __future__ import annotations

# `from __future__ import annotations` 让所有类型注解变成字符串，
# 这样即使类 A 引用了后面才定义的类 B，也不会报错。
# Pydantic 会在模型首次使用时自动解析这些字符串注解。

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ════════════════════════════════════════════════════════════════
# 第一部分：Plan Engine 模型（I-06 OKR PlanStep DAG + 级联修正）
# ════════════════════════════════════════════════════════════════


class PlanStatus(str, Enum):
    """步骤状态枚举

    一个 PlanStep 在生命周期中会经历以下状态：
    - PENDING: 待执行（刚创建时的默认状态）
    - IN_PROGRESS: 执行中
    - COMPLETED: 已完成
    - PENDING_REVIEW: 待审查（级联修正时被标记，需人工确认）
    """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PENDING_REVIEW = "pending_review"


class AssociationStrength(str, Enum):
    """步骤间的关联强度枚举

    用于级联修正时判断影响传播范围：
    - STRONG: 强关联（相邻步骤），状态变更需立即审查
    - MODERATE: 中等关联，需浅审查
    - WEAK: 弱关联，仅需通知
    """

    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"


class OKRPlanStep(BaseModel):
    """OKR 增强型 PlanStep 数据模型

    这是 Plan Engine 的核心数据结构，每个步骤代表一个可执行单元。
    通过 parent_id 和 dependency_ids 构建 DAG（有向无环图）。

    Attributes:
        step_id: 步骤唯一标识（UUID 字符串）
        text: 步骤描述文本（比如 "实现用户登录接口"）
        key: 关键结果/里程碑标识（比如 "S1"、"KR-A"）
        status: 当前状态（见 PlanStatus 枚举）
        parent_id: 父步骤 ID，用于构建父子层级（顶层步骤为 None）
        dependency_ids: 依赖的步骤 ID 列表（DAG 的边：我依赖谁）
        association_strength: 与父/依赖步骤的关联强度
        children: 子步骤列表（不存入数据库，运行时从 parent_id 构建）
    """

    step_id: str = ""
    text: str
    key: str = ""
    status: PlanStatus = PlanStatus.PENDING
    parent_id: Optional[str] = None
    dependency_ids: List[str] = Field(default_factory=list)
    association_strength: AssociationStrength = AssociationStrength.MODERATE
    children: List[OKRPlanStep] = Field(default_factory=list)


# ── Plan Engine API 请求/响应模型 ──────────────────────────


class CreatePlanRequest(BaseModel):
    """POST /plan/create 的请求体

    Attributes:
        task_description: 任务描述文本，服务会自动分解为 3-8 个步骤
    """

    task_description: str


class CreatePlanResponse(BaseModel):
    """POST /plan/create 的响应体

    Attributes:
        plan_id: 新创建的 Plan 唯一标识（UUID）
        steps: 分解出的步骤列表
    """

    plan_id: str
    steps: List[OKRPlanStep]


class UpdateStepRequest(BaseModel):
    """PUT /plan/step/{step_id} 的请求体

    所有字段都是可选的——只更新传入的字段。
    如果更新了 status 或 text，会自动触发级联修正。

    Attributes:
        text: 新的步骤描述
        key: 新的关键结果标识
        status: 新的状态
        parent_id: 新的父步骤 ID
        dependency_ids: 新的依赖列表
        association_strength: 新的关联强度
    """

    text: Optional[str] = None
    key: Optional[str] = None
    status: Optional[PlanStatus] = None
    parent_id: Optional[str] = None
    dependency_ids: Optional[List[str]] = None
    association_strength: Optional[AssociationStrength] = None


class CascadeRequest(BaseModel):
    """POST /plan/cascade 的请求体

    Attributes:
        plan_id: Plan 唯一标识
        modified_step_id: 被修改的步骤 ID（级联修正的起点）
    """

    plan_id: str
    modified_step_id: str


class CascadeResponse(BaseModel):
    """POST /plan/cascade 的响应体

    Attributes:
        affected_steps: 受影响的步骤 ID 列表
        action: 步骤 ID → 处理动作的映射（"pending_review" 或 "notify"）
    """

    affected_steps: List[str]
    action: Dict[str, str]


class PlanStatusResponse(BaseModel):
    """GET /plan/status/{plan_id} 的响应体

    返回 Plan 的完整步骤列表和依赖图邻接表。

    Attributes:
        plan_id: Plan 唯一标识
        steps: 所有步骤列表
        adjacency_list: 依赖图邻接表（step_id → 依赖于它的步骤列表）
        created_at: Plan 创建时间（ISO-8601）
        updated_at: Plan 最后更新时间（ISO-8601）
    """

    plan_id: str
    steps: List[OKRPlanStep]
    adjacency_list: Dict[str, List[str]]
    created_at: str
    updated_at: str


# ════════════════════════════════════════════════════════════════
# 第二部分：Memory Tagger 模型（I-12 Memory 标签 + λ 过滤）
# ════════════════════════════════════════════════════════════════


class MemoryLayer(str, Enum):
    """记忆层级枚举

    对应 I-12 文档 §3.1–3.2 中的分层标记。
    不同层级的记忆在注入 LLM 上下文时有不同优先级。

    取值说明：
    - CONSTRAINT: 全局约束，不可遗忘（如安全规则、合规要求）
    - PREFERENCE: 技术偏好与习惯（如 "喜欢用 pytest"）
    - STYLE: 风格偏好，写作/表达方式（如 "注释用中文"）
    - DECISION: 历史决策与结论（如 "决定用 PostgreSQL"）
    - PATTERN: 成功模式与经验规律（如 "每次部署前要跑测试"）
    """

    CONSTRAINT = "constraint"
    PREFERENCE = "preference"
    STYLE = "style"
    DECISION = "decision"
    PATTERN = "pattern"


class MemoryEntry(BaseModel):
    """单条记忆记录

    Attributes:
        content: 记忆内容原文
        tags: 关键词标签列表（用于检索）
        layer: 记忆所属层级（见 MemoryLayer 枚举）
        created_at: 创建时间（UTC ISO-8601）
    """

    content: str = Field(..., description="记忆内容原文")
    tags: List[str] = Field(default_factory=list, description="关键词标签列表")
    layer: MemoryLayer = Field(..., description="记忆所属层级")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="创建时间（UTC ISO-8601）",
    )

    model_config = {"from_attributes": True}


class TagRequest(BaseModel):
    """POST /memory/tag 的请求体

    Attributes:
        content: 需要打标签的记忆内容（不能为空）
    """

    content: str = Field(..., min_length=1, description="需要打标签的记忆内容")


class TagResponse(BaseModel):
    """POST /memory/tag 的响应体

    Attributes:
        content: 原始内容
        tags: 提取到的关键词标签列表
        layer: 分类结果（记忆层级）
        confidence: 分类置信度（0~1，越高越确定）
    """

    content: str
    tags: List[str]
    layer: MemoryLayer
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="分类置信度（0~1）",
    )


class QueryRequest(BaseModel):
    """POST /memory/query 的请求体

    tags 和 layer 都是可选的筛选条件，同时使用时取交集。

    Attributes:
        tags: 按标签筛选（匹配任意一个标签即可）
        layer: 按层级筛选
        limit: 返回条数上限（1~500）
    """

    tags: Optional[List[str]] = Field(default=None, description="按标签筛选")
    layer: Optional[MemoryLayer] = Field(default=None, description="按层级筛选")
    limit: int = Field(default=50, ge=1, le=500, description="返回条数上限")


class QueryResponse(BaseModel):
    """POST /memory/query 的响应体

    Attributes:
        entries: 查询到的记忆条目列表
        total: 返回的条目数
    """

    entries: List[MemoryEntry]
    total: int


class FilterRequest(BaseModel):
    """POST /memory/filter 的请求体

    λ（lambda）是 Memory 强度参数，决定注入哪些层级的记忆：
    - λ ∈ [0.0, 0.3]: 仅 constraint 层（发散任务/创意场景）
    - λ ∈ [0.4, 0.7]: constraint + preference + decision（混合任务）
    - λ ∈ [0.8, 1.0]: 全部层级（收敛任务/工程场景）

    Attributes:
        lambda_value: λ 值（在 API 中用 "lambda" 作为别名）
        limit: 返回条数上限
    """

    # alias="lambda" 让 API 接收 {"lambda": 0.5}，
    # 但 Python 中用 req.lambda_value 访问（因为 lambda 是保留字）
    lambda_value: float = Field(
        alias="lambda",
        ge=0.0, le=1.0,
        description="Memory 强度参数 λ ∈ [0, 1]",
    )
    limit: int = Field(default=50, ge=1, le=500, description="返回条数上限")


class FilterResponse(BaseModel):
    """POST /memory/filter 的响应体

    Attributes:
        entries: 过滤后的记忆条目列表
        total: 返回的条目数
        lambda_value: 使用的 λ 值
        included_layers: 包含的层级名称列表
    """

    entries: List[MemoryEntry]
    total: int
    lambda_value: float
    included_layers: List[str]


# ════════════════════════════════════════════════════════════════
# 第三部分：Checkpoint Review 模型（I-11 Checkpoint 快照审查）
# ════════════════════════════════════════════════════════════════


class CompletedStep(BaseModel):
    """已完成的步骤摘要

    Attributes:
        step_id: 步骤唯一标识
        text: 步骤描述文本
        result: 步骤执行结果摘要（≤ 3 句话，可为空）
    """

    step_id: str = Field(..., description="步骤唯一标识")
    text: str = Field(..., description="步骤描述文本")
    result: str = Field(default="", description="步骤执行结果摘要（≤ 3 句话）")


class Checkpoint(BaseModel):
    """结构化 Checkpoint 快照

    这是 Checkpoint Review 的核心数据结构。
    快照在特定时机（每 3 步完成 / 异常事件 / 阶段边界）触发创建，
    用于在不读取完整执行日志的情况下审查 Plan 进展。

    Attributes:
        checkpoint_id: Checkpoint 唯一标识 (格式: cp_xxxxxxxxxxxx)
        plan_id: 所属 Plan 唯一标识
        created_at: 创建时间 (ISO-8601)
        checkpoint_number: Plan 内的 Checkpoint 编号（从 1 递增）
        current_goal: 当前正在执行的目标描述
        completed_steps_summary: 已完成步骤的摘要列表
        unexpected_findings: 非预期发现（如 API 与文档不一致）
        remaining_plan: 剩余 Plan 步骤描述列表
        purpose: 触发目的 (step_threshold / abnormal_event / phase_boundary)
    """

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
        description="触发目的: step_threshold | abnormal_event | phase_boundary",
    )


class DictStep(BaseModel):
    """Plan 步骤的扁平结构（从外部请求传入）

    与 OKRPlanStep 不同，这是外部请求传入的简化版本，
    只包含创建 Checkpoint 时需要的基本字段。

    注意：这个类必须在 CreateCheckpointRequest 之前定义，
    因为 CreateCheckpointRequest 引用了它。

    Attributes:
        step_id: 步骤唯一标识
        text: 步骤描述文本
        status: 步骤状态（字符串形式）
        key: 步骤关键词/主题
    """

    step_id: str = Field(..., description="步骤唯一标识")
    text: str = Field(..., description="步骤描述文本")
    status: str = Field(..., description="步骤状态")
    key: str = Field(default="", description="步骤关键词/主题")


class CreateCheckpointRequest(BaseModel):
    """POST /checkpoint/create 的请求体

    Attributes:
        plan_id: Plan 唯一标识
        plan_steps: Plan 的完整步骤列表（扁平结构）
        completed_step_ids: 已完成的步骤 ID 列表
        unexpected_findings: 执行过程中发现的非预期信息
    """

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


class CreateCheckpointResponse(BaseModel):
    """POST /checkpoint/create 的响应体

    Attributes:
        checkpoint: 新创建的 Checkpoint 快照
    """

    checkpoint: Checkpoint


class ReviewRequest(BaseModel):
    """POST /checkpoint/review/{checkpoint_id} 的请求体

    目前为空，预留用于未来扩展（比如传入审查策略参数）。
    """

    pass


class ReviewResult(BaseModel):
    """Checkpoint 审查结果

    审查从四个维度评估 Checkpoint 快照：
    - alignment: 目标对齐程度（已完成的步骤是否偏离原始 Plan）
    - progress_status: 进度状态（是否落后于预期）
    - unexpected_impact: 意外发现的影响程度
    - adjustments: 剩余计划调整建议列表
    - confidence: 审查置信度（0~1）

    Attributes:
        alignment: 目标对齐程度，取值: aligned | partial | deviated
        progress_status: 进度状态，取值: on_track | at_risk | behind
        unexpected_impact: 意外发现影响，取值: none | low | medium | high
        adjustments: 剩余计划调整建议列表
        confidence: 审查置信度 (0~1)
    """

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
    """POST /checkpoint/review/{checkpoint_id} 的响应体

    Attributes:
        checkpoint_id: 被审查的 Checkpoint ID
        review_result: 审查结果
    """

    checkpoint_id: str
    review_result: ReviewResult


class ChainResponse(BaseModel):
    """GET /checkpoint/chain/{plan_id} 的响应体

    Attributes:
        plan_id: Plan 唯一标识
        checkpoints: Checkpoint 列表（按编号升序）
        total: Checkpoint 总数
    """

    plan_id: str
    checkpoints: List[Checkpoint]
    total: int


# ════════════════════════════════════════════════════════════════
# 第四部分：通用模型 + 工具函数
# ════════════════════════════════════════════════════════════════


class ErrorResponse(BaseModel):
    """统一错误响应模型

    所有端点出错时都返回这个结构。
    原来三个服务各有自己的 ErrorResponse，这里合并为一个。

    Attributes:
        detail: 错误详情（简短描述）
    """

    detail: str


def generate_checkpoint_id() -> str:
    """生成唯一 Checkpoint ID

    格式: cp_ + 12 位十六进制随机字符串
    例如: cp_a1b2c3d4e5f6

    Returns:
        形如 "cp_xxxxxxxxxxxx" 的唯一标识
    """
    import uuid

    return f"cp_{uuid.uuid4().hex[:12]}"


def now_iso() -> str:
    """返回当前 UTC 时间的 ISO-8601 字符串

    用于给 Checkpoint 打时间戳。

    Returns:
        形如 "2025-01-15T08:30:00+00:00" 的时间字符串
    """
    return datetime.now(timezone.utc).isoformat()
