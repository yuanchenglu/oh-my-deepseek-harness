"""
I-14 Reasoning Content 剥离器。

在 pre_llm_call hook 中从 conversation_history 剥离 reasoning 字段，
减少 API 请求的 token 消耗（尤其是 DeepSeek 等推理模型的 chain-of-thought tokens）。

核心原则：
  - DeepSeek/OpenAI 等模型：剥离 reasoning（不计入 cache，纯浪费）
  - Claude/Anthropic 模型：保留 reasoning（signed thinking blocks 需回传以保证
    tool call 连续性，且已被 Anthropic 缓存覆盖不会额外计费）
  - 仅剥离发送给 API 的消息副本，不修改 session 本地存储

关联: docs/innovations/14-reasoning-content-stripping.md
参考: https://github.com/khizix/reasonix 中 openai.go buildRequest() 的实现
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# 每轮 reasoning 内容的平均 token 估算值（来自 DeepSeek 实测经验）
ESTIMATED_TOKENS_PER_REASONING = 500


def strip_reasoning_from_history(
    conversation_history: List[Dict[str, Any]],
    model: str = "",
) -> Tuple[List[Dict[str, Any]], int]:
    """从消息历史中剥离 assistant 消息的 reasoning 字段。

    注意：Hermes 内部存储用 `reasoning` 字段名（而非 `reasoning_content`）。
    `reasoning_content` 是发送 API 前转换的字段名，hook 运行时尚未转换。

    Args:
        conversation_history: 对话历史消息列表，每条消息为 dict。
        model: 模型名称字符串，用于推断 provider 类型。

    Returns:
        (stripped_history, stripped_count)：
        - stripped_history: 剥离后的新消息列表（不修改原始列表）。
        - stripped_count: 实际剥离的 reasoning 消息条数。
    """
    stripped_count = 0
    stripped_history: List[Dict[str, Any]] = []

    for msg in conversation_history:
        if not isinstance(msg, dict):
            # 非 dict 消息（极少见边界情况），原样保留
            stripped_history.append(msg)
            continue

        role = msg.get("role", "")
        has_reasoning = "reasoning" in msg

        if role == "assistant" and has_reasoning:
            if _is_anthropic_model(model):
                # Anthropic: 保留 signed thinking blocks
                stripped_history.append(msg)
            else:
                # DeepSeek/OpenAI: 剥离 reasoning
                clean_msg = {k: v for k, v in msg.items() if k != "reasoning"}
                stripped_history.append(clean_msg)
                stripped_count += 1
        else:
            stripped_history.append(msg)

    return stripped_history, stripped_count


def _is_anthropic_model(model: str) -> bool:
    """判断是否 Anthropic/Claude 系列模型。

    Anthropic 的 signed thinking blocks 必须回传以保证 tool call 连续性，
    且已被 Anthropic 缓存覆盖，不会产生额外计费。
    """
    model_lower = model.lower().strip()
    return any(keyword in model_lower for keyword in ["claude", "anthropic"])


def on_pre_llm_call(**kwargs) -> Optional[Dict[str, Any]]:
    """pre_llm_call hook：剥离 reasoning 并记录 token 节省量。

    直接原地替换 kwargs 中的 conversation_history 列表内容，
    使下游 API 请求构建时使用剥离后的消息历史。

    返回 None（不注入 context，只修改 conversation_history）。

    Args:
        **kwargs: 包含 conversation_history, model 等上下文。
    """
    conversation_history = kwargs.get("conversation_history")
    model = kwargs.get("model", "")

    if not conversation_history or not isinstance(conversation_history, list):
        return None

    new_history, stripped_count = strip_reasoning_from_history(
        conversation_history, model
    )

    if stripped_count > 0:
        # 原地替换列表内容，使修改对下游 API 请求构建可见
        conversation_history[:] = new_history

        estimated_tokens = stripped_count * ESTIMATED_TOKENS_PER_REASONING
        # 提取 provider 前缀用于日志（如 "deepseek/deepseek-chat" → "deepseek"）
        provider = model.split("/")[0] if "/" in model else model or "unknown"
        logger.info(
            "[I-14] Stripped %d reasoning messages for provider=%s, "
            "estimated ~%d tokens saved",
            stripped_count,
            provider,
            estimated_tokens,
        )

    return None
