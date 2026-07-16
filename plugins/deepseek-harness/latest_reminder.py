"""
I-18 时效信息注入（Latest Reminder）。

在 pre_llm_call hook 中注入当前日期和时效信息到 LLM 上下文。
作为 latest_reminder 角色被 API 拒绝后的降级方案。

Spike 验证结论：
- DeepSeek API 不接受 role="latest_reminder"（400 InvalidParameter）
- 降级方案：将时效信息注入 system prompt 末尾

注入方式：
- 首轮：注入完整时效信息（当前日期、时间）到 context
- 后续轮：不注入（避免上下文膨胀）
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def _build_reminder_text() -> str:
    """构建当前时效信息文本。

    Returns:
        格式化的时效信息字符串。
    """
    now = datetime.now()
    return (
        f"[I-18] Current time: {now.strftime('%Y-%m-%d %H:%M %Z')}. "
        f"This information is provided for temporal awareness."
    )


def on_pre_llm_call(**kwargs: Any) -> Optional[Dict[str, Any]]:
    """pre_llm_call hook：注入时效信息到 LLM 上下文。

    仅在首轮调用时注入当前日期和时间信息。
    通过 context 注入到 system prompt，让模型感知当前时间。

    Args:
        **kwargs: Hermes Plugin 系统传入的上下文。
            关键字段：
            - is_first_turn: bool — 是否为首轮调用

    Returns:
        dict with 'context' key 包含时效信息，或 None（非首轮时跳过）。
    """
    is_first = kwargs.get("is_first_turn", False)

    if not is_first:
        return None

    reminder = _build_reminder_text()
    logger.debug("[I-18] Injecting reminder: %s", reminder)

    return {"context": reminder}
