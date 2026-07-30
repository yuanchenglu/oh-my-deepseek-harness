"""
I-17 推理强度控制（Reasoning Effort Control）。

在 pre_llm_call hook 中根据 I-10 意图路由的分类结果，
通过文本提示注入推理深度指引，控制 DeepSeek V4 模型的推理深度。

设计限制：Hermes pre_llm_call hook 协议仅支持通过返回 {"context": "..."}
注入文本到 user message，无法直接设置 API 端的 reasoning_effort 参数。
因此本插件改为通过上下文文本指引模型调整推理强度，而非直接操作 API 参数。

Spike 验证结论：
- DeepSeek API 接受 reasoning_effort 参数（"max"/"high"/"medium"）
- 设 "max" 时推理 token 约 3x 于不设时（282 vs 91）
- 因 Hermes hook 架构限制，改为文本提示注入

映射规则（意图类型 → 推理强度指引）：
  - architecture / research / collaboration → 高复杂度提示
  - refactor / new / medium → 中等复杂度提示
  - simple / spec_driven → 不注入

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

        if effort == "max":
            hint = "本任务属于高复杂度类型（架构/研究/协作），请进行充分的深度推理，考虑多种方案、边界情况和长期影响。"
        elif effort == "high":
            hint = "本任务属于中等复杂度类型（重构/新功能/功能修改），请进行细致的逐步推理，确保逻辑正确。"
        else:
            return None

        return {"context": f"[I-17 推理强度] {hint}"}

    except ImportError:
        logger.debug("[I-17] intent_router not available, skipping")
    except Exception as e:
        logger.error("[I-17] Error: %s", e, exc_info=True)

    return None
