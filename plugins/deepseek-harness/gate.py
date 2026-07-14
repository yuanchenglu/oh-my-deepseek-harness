"""
认知门控引擎（Cognitive Gate Engine）。

在 pre_llm_call hook 中被 Hermes Plugin 系统调用，
在每轮 LLM 调用前注入认知检查提醒和 MAP.md 记忆导航。

工作模式：
  - 首轮：注入完整 MAP.md + L1/L2 认知提醒
  - 后续轮：仅注入 L1/L2 简短提醒（避免上下文膨胀）
"""

import os
from typing import Any, Dict, Optional


def on_pre_llm_call(**kwargs) -> Optional[Dict[str, Any]]:
    """注入认知检查提醒 + MAP 导航到 user message。

    首轮注入完整 MAP.md + L1/L2 提醒。
    后续轮仅注入 L1/L2 简短提醒（避免上下文膨胀）。

    Args:
        **kwargs: 包含 is_first_turn, session_id 等上下文。
            kwargs 上下文（来自 turn_context.py:468-479）:
                session_id: str — 当前会话 ID
                task_id: str — 当前任务 ID
                turn_id: str — 当前轮次 ID
                user_message: str — 用户消息原文
                conversation_history: list — 对话历史列表
                is_first_turn: bool — 是否为首轮调用
                model: str — 当前使用的模型名称
                platform: str — 对话平台标识
                sender_id: str — 发送者 ID

    Returns:
        dict with 'context' key containing the injection text。
        至少包含 L1/L2 认知提醒，首轮额外包含 MAP.md 导航内容。
        所有文件读取异常都会被静默捕获，不会阻断流程。
        不会返回 None — 至少返回纯 L1/L2 的 dict。

    Raises:
        不显式抛异常。所有 IO 操作在 try/except 内。
    """
    is_first = kwargs.get("is_first_turn", False)
    parts: list[str] = []

    # L1 荣辱观 + L2 思维方式（每轮必注，保持简短以避免膨胀）
    parts.append(
        "[L1] 荣辱观：以知道自己的不足为荣、以提升认知为荣、以告诉实情为荣。"
        "回应前请用工具验证每个论断，不确定就说不确定。"
    )
    parts.append(
        "[L2] 思维方式：第一性原理、Step by Step、假设先行、找盲区、科研严谨。"
        "拆解到最小任务，假设先行验证。"
    )

    # MAP 导航：首轮注入完整 MAP.md，后续轮跳过以避免上下文膨胀
    if is_first:
        try:
            map_path = os.path.expanduser("~/.hermes/MAP.md")
            if os.path.exists(map_path):
                with open(map_path, "r", encoding="utf-8") as f:
                    map_content = f.read().strip()
                if map_content:
                    parts.append(f"[MAP]\n{map_content}")
        except Exception:
            # 任何文件读取失败都不阻断流程，静默降级
            pass

    return {"context": "\n".join(parts)}
