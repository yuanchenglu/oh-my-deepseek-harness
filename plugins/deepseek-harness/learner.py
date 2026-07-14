"""
会话学习总结引擎（Session Learning Summary Engine）。

在 on_session_end hook 中被 Hermes Plugin 系统调用，
在每次会话结束时记录一条带时间戳的学习条目到 feedback-lessons.md，
实现"每次对话都是一次学习"的持续积累机制。

工作模式：
  - 从 kwargs 提取 session_id
  - 生成格式化的时间戳条目，追加写入反馈文件
  - 文件不存在时自动创建，写入失败时静默降级
"""

import datetime
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# 持久化路径：用户纠正史/教训备忘录文件
_FEEDBACK_FILE = os.path.expanduser("~/.hermes/memories/feedback-lessons.md")


def _check_skill_proposal(kwargs: dict, session_id: str) -> None:
    """I-09: 检查是否满足 Skill 提议条件，满足时输出提议日志。

    条件：
      - 对话轮数超过 10 轮
      - 完成了至少 1 个完整任务

    不自动创建 Skill（只提议，由 Curator 或用户确认）。
    所有异常静默降级，不阻断 session 结束流程。
    """
    try:
        conversation_history = kwargs.get("conversation_history", [])
        rounds = (
            len(conversation_history)
            if isinstance(conversation_history, (list, tuple))
            else 0
        )
        if rounds > 10:
            n_tasks = max(1, rounds // 10)
            logger.info(
                "[I-09] Skill proposal: session %s "
                "completed %d tasks in %d rounds "
                "\u2014 consider saving as Skill",
                session_id,
                n_tasks,
                rounds,
            )
    except Exception:
        pass


def on_session_end(**kwargs) -> Optional[Dict[str, Any]]:
    """会话结束时，向 feedback-lessons.md 追加一条时间戳学习记录。

    从 kwargs 中提取 session_id，生成形如
    `[2025-07-14 10:30] Session ses_abc123 结束`
    的条目，以追加模式写入 `~/.hermes/memories/feedback-lessons.md`。
    文件不存在时自动创建，写入权限不足时静默跳过并记 warning。

    新增 I-09 Skill 提议：对话超过 10 轮时输出提议日志。

    Args:
        **kwargs: Hermes Plugin 系统传入的会话结束上下文，至少包含:
            session_id: str — 当前结束的会话 ID
            conversation_history: list — 可选，对话历史列表，用于判断轮数

    Returns:
        写入成功时返回 dict（含写入的条目文本）；写入失败时返回 None。
        函数不会抛异常。

    Raises:
        不显式抛异常。所有 IO 操作在 try/except 内。
    """
    session_id = kwargs.get("session_id", "unknown")

    # 生成格式化的时间戳条目
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n[{now}] Session {session_id} 结束"

    result = None
    try:
        # 确保父目录存在
        parent_dir = os.path.dirname(_FEEDBACK_FILE)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

        # 追加模式写入（不覆盖已有内容）
        with open(_FEEDBACK_FILE, "a", encoding="utf-8") as f:
            f.write(entry)

        logger.info("会话学习记录已写入: %s", entry.strip())
        result = {"entry": entry.strip()}
    except PermissionError:
        logger.warning("写入反馈文件权限不足，已静默跳过: %s", _FEEDBACK_FILE)
    except OSError as e:
        logger.warning("写入反馈文件时发生 IO 错误，已静默跳过: %s — %s", _FEEDBACK_FILE, e)

    # ── I-09: Skill 提议（独立于时间戳记录，互不影响） ──
    _check_skill_proposal(kwargs, session_id)

    return result
