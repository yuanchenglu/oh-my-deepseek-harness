"""
I-14 Reasoning Content 剥离器 — 平台无关核心。

从消息历史中剥离 assistant 消息的 reasoning 字段，
减少 API 请求的 token 消耗（尤其是 DeepSeek 等推理模型的 chain-of-thought tokens）。

核心原则：
  - DeepSeek/OpenAI 等模型：剥离 reasoning（不计入 cache，纯浪费）
  - Claude/Anthropic 模型：保留 reasoning（signed thinking blocks 需回传以保证
    tool call 连续性，且已被 Anthropic 缓存覆盖不会额外计费）
  - 仅剥离发送给 API 的消息副本，不修改 session 本地存储

本模块不依赖任何 Hermes API，消息历史和模型名通过函数参数传入。

参考: https://github.com/khizix/reasonix 中 openai.go buildRequest() 的实现
"""

import logging
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

# 每轮 reasoning 内容的平均 token 估算值（来自 DeepSeek 实测经验）
ESTIMATED_TOKENS_PER_REASONING = 500


def is_anthropic_model(model: str) -> bool:
    """判断是否 Anthropic/Claude 系列模型。

    Anthropic 的 signed thinking blocks 必须回传以保证 tool call 连续性，
    且已被 Anthropic 缓存覆盖，不会产生额外计费。
    """
    model_lower = model.lower().strip()
    return any(keyword in model_lower for keyword in ["claude", "anthropic"])


def strip_reasoning_from_history(
    conversation_history: List[Dict[str, Any]],
    model: str = "",
) -> Tuple[List[Dict[str, Any]], int]:
    """从消息历史中剥离 assistant 消息的 reasoning 字段。

    注意：内部存储用 `reasoning` 字段名（而非 `reasoning_content`）。
    `reasoning_content` 是发送 API 前转换的字段名。

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
            stripped_history.append(msg)
            continue

        role = msg.get("role", "")
        has_reasoning = "reasoning" in msg

        if role == "assistant" and has_reasoning:
            if is_anthropic_model(model):
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


def estimate_tokens_saved(stripped_count: int) -> int:
    """估算剥离 reasoning 节省的 token 数。

    Args:
        stripped_count: 已剥离的 reasoning 消息条数

    Returns:
        估算的 token 节省数
    """
    return stripped_count * ESTIMATED_TOKENS_PER_REASONING
