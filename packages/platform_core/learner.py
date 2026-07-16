"""
会话学习总结引擎（Session Learning Summary Engine）— 平台无关核心。

在每次会话结束时记录一条带时间戳的学习条目到 feedback-lessons.md，
实现"每次对话都是一次学习"的持续积累机制。

本模块不依赖任何 Hermes API，所有文件路径和会话数据通过函数参数传入。
"""

import datetime
import logging
import os
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

# 默认持久化路径
DEFAULT_FEEDBACK_FILE = os.path.expanduser("~/.hermes/memories/feedback-lessons.md")


def build_lesson_entry(session_id: str) -> str:
    """生成格式化的时间戳学习条目。

    Args:
        session_id: 当前结束的会话 ID

    Returns:
        格式化的条目文本（不含文件写入）。
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"\n[{now}] Session {session_id} 结束"


def check_skill_proposal(
    conversation_history: Union[List[Dict[str, Any]], None],
    session_id: str,
    min_rounds: int = 10,
) -> Optional[Dict[str, Any]]:
    """I-09: 检查是否满足 Skill 提议条件。

    条件：
      - 对话轮数超过 min_rounds 轮

    不自动创建 Skill（只提议，由 Curator 或用户确认）。

    Args:
        conversation_history: 对话历史列表，用于判断轮数
        session_id: 当前会话 ID
        min_rounds: 触发 Skill 提议的最小对话轮数

    Returns:
        dict with 'skill_proposal' key 包含建议信息，或 None（不满足条件）。
        所有异常静默降级。
    """
    try:
        rounds = (
            len(conversation_history)
            if isinstance(conversation_history, (list, tuple))
            else 0
        )
        if rounds > min_rounds:
            n_tasks = max(1, rounds // min_rounds)
            return {
                "skill_proposal": {
                    "session_id": session_id,
                    "n_tasks": n_tasks,
                    "rounds": rounds,
                }
            }
    except Exception:
        pass
    return None


DEFAULT_MIN_ROUNDS = 10


def handle_session_end(
    session_id: str,
    conversation_history: Union[List[Dict[str, Any]], None] = None,
    feedback_file: str = DEFAULT_FEEDBACK_FILE,
    min_rounds: int = DEFAULT_MIN_ROUNDS,
) -> Optional[Dict[str, Any]]:
    """处理会话结束逻辑：写入学习记录 + 检查 Skill 提议。

    从 kwargs 中提取 session_id，生成时间戳条目追加写入 feedback_file。
    文件不存在时自动创建，写入权限不足时静默跳过并记 warning。

    Args:
        session_id: 当前结束的会话 ID
        conversation_history: 可选，对话历史列表，用于判断轮数
        feedback_file: 反馈文件路径
        min_rounds: 触发 Skill 提议的最小对话轮数

    Returns:
        写入成功时返回 dict（含写入的条目文本）；写入失败时返回 None。
        函数不会抛异常。
    """
    entry = build_lesson_entry(session_id)

    result = None
    try:
        parent_dir = os.path.dirname(feedback_file)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

        with open(feedback_file, "a", encoding="utf-8") as f:
            f.write(entry)

        logger.info("会话学习记录已写入: %s", entry.strip())
        result = {"entry": entry.strip()}
    except PermissionError:
        logger.warning("写入反馈文件权限不足，已静默跳过: %s", feedback_file)
    except OSError as e:
        logger.warning(
            "写入反馈文件时发生 IO 错误，已静默跳过: %s — %s", feedback_file, e
        )

    # ── I-09: Skill 提议（独立于时间戳记录，互不影响） ──
    proposal = check_skill_proposal(conversation_history, session_id, min_rounds)
    if proposal:
        logger.info(
            "[I-09] Skill proposal: session %s "
            "completed %d tasks in %d rounds "
            "\u2014 consider saving as Skill",
            proposal["skill_proposal"]["session_id"],
            proposal["skill_proposal"]["n_tasks"],
            proposal["skill_proposal"]["rounds"],
        )

    return result
