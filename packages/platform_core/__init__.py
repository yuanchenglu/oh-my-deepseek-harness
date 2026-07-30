"""platform_core — 平台无关的 Harness 核心逻辑。

从 deepseek-harness Hermes Plugin 中提取的纯逻辑模块，
不依赖任何特定 Agent 框架 API。

可用模块：
  - gate: 认知门控引擎（I-02 双向原语 + I-08 范围控制 + L1/L2 提醒）
  - assessor: 工具调用质量评估（I-01 约束违反检测 + 内容完整性检查）
  - intent_router: 7+1 意图分类 + 策略绑定
  - reasoning_strip: Provider 感知的 reasoning 剥离（I-14）
  - learner: 会话学习总结（I-09 Skill 提议）
  - adapter: PlatformAdapter ABC — 多平台适配器统一接口
"""

from .adapter import PlatformAdapter

from .gate import (
    extract_hard_constraints,
    set_hard_constraints,
    get_hard_constraints,
    core_reminders,
    build_map_navigation,
    build_gate_context,
)

from .assessor import (
    extract_keywords,
    check_path_against_constraint,
    check_command_against_constraint,
    record_violation,
    check_constraint_violation,
    assess_tool_call,
    DEFAULT_VIOLATIONS_FILE,
)

from .intent_router import (
    keyword_match_score,
    load_strategies,
    classify_intent,
    get_strategy,
    generate_exclusion_list,
    build_context_injection,
)

from .reasoning_strip import (
    is_anthropic_model,
    strip_reasoning_from_history,
    estimate_tokens_saved,
    ESTIMATED_TOKENS_PER_REASONING,
)

from .learner import (
    build_lesson_entry,
    check_skill_proposal,
    handle_session_end,
    DEFAULT_FEEDBACK_FILE,
)

# ── I-06 Plan Engine — DAG 级联修正 ──
from .plan_engine import (
    OKRPlanStep,
    PlanStatus,
    AssociationStrength,
    cascade_correct,
    detect_cycle,
    build_adjacency_list,
)

# ── I-12 Memory Tagger — 5 层关键词分类 ──
from .memory_tagger import (
    classify,
    extract_tags,
    detect_task_type,
    resolve_layers,
    resolve_task_config,
    MemoryLayer,
    LAMBDA_LEVELS,
    TASK_TYPE_MAPPINGS,
    DEFAULT_LAMBDA,
)

# ── I-11 Checkpoint — 四维审查状态机 ──
from .checkpoint import (
    CompletedStep,
    Checkpoint,
    ReviewResult,
    generate_checkpoint_id,
    now_iso,
    compute_alignment,
    compute_progress,
    compute_unexpected_impact,
    compute_adjustments,
    build_completed_summary,
    build_remaining_plan,
    build_current_goal,
    check_alignment_from_snapshot,
    check_progress_from_snapshot,
    adjustments_from_snapshot,
    compute_confidence,
)

__all__ = [
    # adapter
    "PlatformAdapter",
    # gate
    "extract_hard_constraints",
    "set_hard_constraints",
    "get_hard_constraints",
    "core_reminders",
    "build_map_navigation",
    "build_gate_context",
    # assessor
    "extract_keywords",
    "check_path_against_constraint",
    "check_command_against_constraint",
    "record_violation",
    "check_constraint_violation",
    "assess_tool_call",
    "DEFAULT_VIOLATIONS_FILE",
    # intent_router
    "keyword_match_score",
    "load_strategies",
    "classify_intent",
    "get_strategy",
    "generate_exclusion_list",
    "build_context_injection",
    # reasoning_strip
    "is_anthropic_model",
    "strip_reasoning_from_history",
    "estimate_tokens_saved",
    "ESTIMATED_TOKENS_PER_REASONING",
    # learner
    "build_lesson_entry",
    "check_skill_proposal",
    "handle_session_end",
    "DEFAULT_FEEDBACK_FILE",
    # plan_engine
    "OKRPlanStep",
    "PlanStatus",
    "AssociationStrength",
    "cascade_correct",
    "detect_cycle",
    "build_adjacency_list",
    # memory_tagger
    "classify",
    "extract_tags",
    "detect_task_type",
    "resolve_layers",
    "resolve_task_config",
    "MemoryLayer",
    "LAMBDA_LEVELS",
    "TASK_TYPE_MAPPINGS",
    "DEFAULT_LAMBDA",
    # checkpoint
    "CompletedStep",
    "Checkpoint",
    "ReviewResult",
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
]

# ── 类名别名，兼容期望模块名导入的调用方 ──
import platform_core.gate as Gate
import platform_core.assessor as Assessor
import platform_core.intent_router as IntentRouter
import platform_core.reasoning_strip as ReasoningStripper
import platform_core.learner as Learner

__version__ = "0.1.0"
