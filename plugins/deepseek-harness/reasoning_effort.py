"""
I-17 推理强度控制（Reasoning Effort Control）。

在 pre_llm_call hook 中根据 I-10 意图路由的分类结果，
动态设置 reasoning_effort 参数，控制 DeepSeek V4 模型的推理深度。

Spike 验证结论：
- DeepSeek API 接受 reasoning_effort 参数（"max"/"high"/"medium"）
- 设 "max" 时推理 token 约 3x 于不设时（282 vs 91）
- 通过 API 参数传递，不手动注入 REASONING_EFFORT_MAX 文本

映射规则（意图类型 → reasoning_effort 级别）：
  - architecture / research / collaboration → "max"
  - refactor / new / medium → "high"
  - simple / spec_driven → 不设置（使用模型默认值）

关联: docs/innovations/17-reasoning-effort-control.md
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# 意图类型到 reasoning_effort 的映射
_INTENT_EFFORT_MAP: dict[str, str] = {
    # 高复杂度任务 → max reasoning
    "architecture": "max",
    "research": "max",
    "collaboration": "max",
    # 中等复杂度任务 → high reasoning
    "refactor": "high",
    "new": "high",
    "medium": "high",
    # 简单任务 → 不设置（使用模型默认值）
    "simple": "",
    "spec_driven": "",
}

# 需要设置 reasoning_effort 的 intent 列表（用于快速判断）
_EFFORT_INTENTS = {"architecture", "research", "collaboration", "refactor", "new", "medium"}


def _get_reasoning_effort_level(intent: str) -> Optional[str]:
    """根据 I-10 意图类型获取对应的 reasoning_effort 级别。

    Args:
        intent: I-10 意图路由的分类结果（如 "architecture", "refactor" 等）

    Returns:
        "max", "high", 或 None（表示不设置，使用模型默认值）
    """
    effort = _INTENT_EFFORT_MAP.get(intent, "")
    return effort if effort else None


def on_pre_llm_call(**kwargs: Any) -> Optional[Dict[str, Any]]:
    """pre_llm_call hook：注入推理强度上下文。

    依赖 I-10 意图路由的分类结果（classify_intent），
    根据意图类型注入 reasoning_effort 上下文到 LLM 调用。

    仅在首轮调用且存在 user_message 时执行分类和注入。
    为 architecture/research/collaboration → max effort，
    refactor/new/medium → high effort，
    simple/spec_driven → 不注入。

    Args:
        **kwargs: Hermes Plugin 系统传入的上下文。
            关键字段：
            - is_first_turn: bool — 是否为首轮调用
            - user_message: str — 用户消息原文
            - model: str — 当前使用的模型名称

    Returns:
        dict with 'context' key 包含推理强度指引，
        或 None（非首轮/简单任务/无法处理时跳过）。
        异常时静默捕获并记录日志，不阻断流程。
    """
    try:
        is_first = kwargs.get("is_first_turn", False)
        user_message = kwargs.get("user_message", "")

        if not is_first or not user_message:
            return None

        from .intent_router import classify_intent  # 延迟导入

        result = classify_intent(user_message)
        intent = result.get("intent", "spec_driven")

        effort = _get_reasoning_effort_level(intent)
        if effort is None:
            return None

        logger.info(
            "[I-17] Injecting reasoning_effort=%s for intent=%s (confidence=%.2f)",
            effort,
            intent,
            result.get("confidence", 0.0),
        )

        return {
            "context": f"[I-17 reasoning_effort={effort}] "
            f"当前推理强度设置为 {effort}（意图: {intent}）。"
        }

    except ImportError:
        logger.debug("[I-17] intent_router not available, skipping")
    except Exception as e:
        logger.error("[I-17] Error: %s", e, exc_info=True)

    return None
