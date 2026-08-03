"""SES-001: Session 策略状态隔离存储。

替换 gate.py 中模块级 _current_hard_constraints 全局集合，
按 session_id 隔离硬约束状态。线程安全。

FR-POLICY-001: 约束按 session_id 隔离
FR-POLICY-002: 约束保留原文、来源 Session/Turn、创建时间
FR-POLICY-003: 用户可显式新增/取消约束，不因后续消息未重述而自动删除
FR-POLICY-006: Session 结束时清理内存状态
"""

from __future__ import annotations

import datetime
import threading
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Constraint:
    """单条硬约束的完整生命周期记录。

    active=False 表示被用户显式取消；记录保留用于审计（FR-POLICY-002）。
    cancel_turn_id 记录取消发生在哪个 turn，None 表示仍活跃。
    """
    text: str
    session_id: str
    turn_id: str
    created_at: datetime.datetime = field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    active: bool = True
    cancel_turn_id: Optional[str] = None
    cancelled_constraints: set[str] = field(default_factory=set)


class SessionPolicyStore:
    """按 session_id 隔离的硬约束存储。线程安全单例。

    用 _lock 保护 _sessions 字典的读写。
    每个 session 维护一个 Constraint 列表（活跃+已取消），
    get_active_constraints 返回 active=True 且 text 不在 cancelled 集合中的约束文本。
    """

    _instance: Optional["SessionPolicyStore"] = None
    _instance_lock = threading.Lock()

    def __init__(self) -> None:
        self._sessions: dict[str, list[Constraint]] = {}
        self._lock = threading.RLock()

    @classmethod
    def get_instance(cls) -> "SessionPolicyStore":
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """测试用：重置单例，清除所有 session 状态。"""
        with cls._instance_lock:
            cls._instance = None

    def add_constraints(
        self, session_id: str, constraints: set[str], turn_id: str = ""
    ) -> None:
        """为 session 添加约束。

        FR-POLICY-003: 已取消的约束不会被同名新约束复活。
        重复添加的活跃约束不重复记录。
        空集合调用不产生任何效果（不删除已有约束）。
        """
        with self._lock:
            session_list = self._sessions.setdefault(session_id, [])
            cancelled_set = self._cancelled_set(session_list)
            for text in constraints:
                if text in cancelled_set:
                    continue  # 已显式取消，不复活
                if any(c.text == text and c.active for c in session_list):
                    continue  # 已存在且活跃
                session_list.append(
                    Constraint(text=text, session_id=session_id, turn_id=turn_id)
                )

    def cancel_constraint(self, session_id: str, text: str, turn_id: str = "") -> bool:
        """显式取消一条约束。返回是否找到并取消了。

        FR-POLICY-003: 取消后该约束标记 inactive，后续 add 同名约束不复活。
        """
        with self._lock:
            session_list = self._sessions.get(session_id, [])
            for c in session_list:
                if c.text == text and c.active:
                    c.active = False
                    c.cancel_turn_id = turn_id
                    return True
            return False

    def get_active_constraints(self, session_id: str) -> set[str]:
        """返回 session 的活跃约束文本集合。"""
        with self._lock:
            session_list = self._sessions.get(session_id, [])
            return {c.text for c in session_list if c.active}

    def end_session(self, session_id: str) -> None:
        """FR-POLICY-006: 清理 session 内存状态。

        审计事件独立持久化，不属于本方法职责。
        """
        with self._lock:
            self._sessions.pop(session_id, None)

    @staticmethod
    def _cancelled_set(session_list: list[Constraint]) -> set[str]:
        """返回已取消的约束文本集合。"""
        return {c.text for c in session_list if not c.active}
