"""SES-001: SessionPolicyStore 单元测试。

TC-POLICY-001: Session 隔离 -- A 有约束 B 无约束，B 不继承 A
TC-POLICY-002: 同 Session 新增约束 -- 集合累积更新
TC-POLICY-003: 用户明确取消约束 -- 对应约束失效
TC-POLICY-004: Session end -- 内存状态清理
TC-POLICY-005: 两线程并发 Session -- 无交叉污染
"""

from __future__ import annotations

import threading

import pytest

from deepseek_harness.session_policy import SessionPolicyStore, Constraint


@pytest.fixture(autouse=True)
def _fresh_store():
    """每个测试用例拿到干净的单例。"""
    SessionPolicyStore.reset_instance()
    yield
    SessionPolicyStore.reset_instance()


# ── TC-POLICY-001: Session 隔离 ──────────────────────────


class TestSessionIsolation:
    """A Session 有约束，B 无约束 -> B 不继承 A。"""

    def test_b_does_not_inherit_a_constraints(self):
        store = SessionPolicyStore.get_instance()
        store.add_constraints("session-a", {"不能删除数据库"}, turn_id="t1")
        # B 从未设置约束
        assert store.get_active_constraints("session-b") == set()

    def test_a_constraints_persist_when_b_has_none(self):
        store = SessionPolicyStore.get_instance()
        store.add_constraints("session-a", {"不能删除数据库"}, turn_id="t1")
        store.add_constraints("session-b", set(), turn_id="t1")
        assert store.get_active_constraints("session-a") == {"不能删除数据库"}
        assert store.get_active_constraints("session-b") == set()

    def test_missing_session_id_returns_empty(self):
        store = SessionPolicyStore.get_instance()
        assert store.get_active_constraints("nonexistent") == set()


# ── TC-POLICY-002: 同 Session 新增约束 ────────────────────


class TestConstraintAccumulation:
    """同 Session 新增约束 -> 集合累积更新，不替换。"""

    def test_add_second_constraint_retains_first(self):
        store = SessionPolicyStore.get_instance()
        store.add_constraints("s1", {"不能删除数据库"}, turn_id="t1")
        store.add_constraints("s1", {"不能修改配置文件"}, turn_id="t2")
        active = store.get_active_constraints("s1")
        assert "不能删除数据库" in active
        assert "不能修改配置文件" in active

    def test_duplicate_constraint_not_double_counted(self):
        store = SessionPolicyStore.get_instance()
        store.add_constraints("s1", {"不能删除数据库"}, turn_id="t1")
        store.add_constraints("s1", {"不能删除数据库"}, turn_id="t2")
        assert store.get_active_constraints("s1") == {"不能删除数据库"}

    def test_constraint_persists_across_turns(self):
        """FR-POLICY-003: 不能因后续消息未重述而自动删除。"""
        store = SessionPolicyStore.get_instance()
        store.add_constraints("s1", {"不能删除数据库"}, turn_id="t1")
        # 后续 turn 没有约束
        store.add_constraints("s1", set(), turn_id="t2")
        assert "不能删除数据库" in store.get_active_constraints("s1")


# ── TC-POLICY-003: 用户明确取消约束 ──────────────────────


class TestConstraintCancellation:
    """用户明确取消约束 -> 对应约束失效。"""

    def test_cancel_single_constraint(self):
        store = SessionPolicyStore.get_instance()
        store.add_constraints("s1", {"不能删除数据库", "不能修改配置"}, turn_id="t1")
        cancelled = store.cancel_constraint("s1", "不能删除数据库")
        assert cancelled is True
        active = store.get_active_constraints("s1")
        assert "不能删除数据库" not in active
        assert "不能修改配置" in active

    def test_cancel_nonexistent_returns_false(self):
        store = SessionPolicyStore.get_instance()
        store.add_constraints("s1", {"不能删除数据库"}, turn_id="t1")
        cancelled = store.cancel_constraint("s1", "不存在的约束")
        assert cancelled is False

    def test_cancel_in_wrong_session_returns_false(self):
        store = SessionPolicyStore.get_instance()
        store.add_constraints("s1", {"不能删除数据库"}, turn_id="t1")
        assert store.cancel_constraint("s2", "不能删除数据库") is False

    def test_cancelled_constraint_not_re_added_by_subsequent_message(self):
        """FR-POLICY-003: 显式取消后，后续消息提取的相同约束不应复活。"""
        store = SessionPolicyStore.get_instance()
        store.add_constraints("s1", {"不能删除数据库"}, turn_id="t1")
        store.cancel_constraint("s1", "不能删除数据库")
        # 后续消息又提到了同样的约束
        store.add_constraints("s1", {"不能删除数据库"}, turn_id="t2")
        assert "不能删除数据库" not in store.get_active_constraints("s1")


# ── TC-POLICY-004: Session End Cleanup ───────────────────


class TestSessionEndCleanup:
    """Session end -> 内存状态清理。"""

    def test_end_session_clears_constraints(self):
        store = SessionPolicyStore.get_instance()
        store.add_constraints("s1", {"不能删除数据库"}, turn_id="t1")
        store.end_session("s1")
        assert store.get_active_constraints("s1") == set()

    def test_end_session_does_not_affect_others(self):
        store = SessionPolicyStore.get_instance()
        store.add_constraints("s1", {"不能删除数据库"}, turn_id="t1")
        store.add_constraints("s2", {"不能修改配置"}, turn_id="t1")
        store.end_session("s1")
        assert store.get_active_constraints("s2") == {"不能修改配置"}

    def test_end_nonexistent_session_no_error(self):
        store = SessionPolicyStore.get_instance()
        store.end_session("nonexistent")  # 不应抛异常


# ── TC-POLICY-005: 两线程并发 Session ────────────────────


class TestConcurrentSessions:
    """两线程并发 Session -> 无交叉污染。"""

    def test_two_threads_no_cross_contamination(self):
        """使用 barrier 确保两线程真正并发写入。"""
        store = SessionPolicyStore.get_instance()
        barrier = threading.Barrier(2)
        errors: list[Exception] = []

        def worker(session_id: str, constraint: str):
            try:
                barrier.wait(timeout=5)
                store.add_constraints(session_id, {constraint}, turn_id="t1")
                barrier.wait(timeout=5)
                # 验证自己的约束在，对方的约束不在
                active = store.get_active_constraints(session_id)
                assert constraint in active, f"{session_id} lost its constraint"
            except Exception as e:
                errors.append(e)

        t1 = threading.Thread(
            target=worker, args=("thread-a", "不能删除数据库A")
        )
        t2 = threading.Thread(
            target=worker, args=("thread-b", "不能修改配置B")
        )
        t1.start()
        t2.start()
        t1.join(timeout=10)
        t2.join(timeout=10)

        assert not errors, f"线程错误: {errors}"
        # 最终验证隔离
        assert store.get_active_constraints("thread-a") == {"不能删除数据库A"}
        assert store.get_active_constraints("thread-b") == {"不能修改配置B"}

    def test_concurrent_add_and_end_session(self):
        """一个线程添加约束，另一个线程结束 session，互不干扰。"""
        store = SessionPolicyStore.get_instance()
        store.add_constraints("s1", {"不能删除数据库"}, turn_id="t1")
        barrier = threading.Barrier(2)
        errors: list[Exception] = []

        def adder():
            try:
                barrier.wait(timeout=5)
                store.add_constraints("s2", {"不能修改配置"}, turn_id="t1")
            except Exception as e:
                errors.append(e)

        def ender():
            try:
                barrier.wait(timeout=5)
                store.end_session("s1")
            except Exception as e:
                errors.append(e)

        t1 = threading.Thread(target=adder)
        t2 = threading.Thread(target=ender)
        t1.start()
        t2.start()
        t1.join(timeout=10)
        t2.join(timeout=10)

        assert not errors, f"线程错误: {errors}"
        assert store.get_active_constraints("s1") == set()
        assert store.get_active_constraints("s2") == {"不能修改配置"}


# ── Constraint 数据模型 ──────────────────────────────────


class TestConstraintModel:
    """验证 Constraint 数据模型保留 FR-POLICY-002 元数据。"""

    def test_constraint_retains_metadata(self):
        store = SessionPolicyStore.get_instance()
        store.add_constraints("s1", {"不能删除数据库"}, turn_id="turn-42")
        with store._lock:
            constraints = store._sessions.get("s1", [])
            assert len(constraints) == 1
            c = constraints[0]
            assert c.text == "不能删除数据库"
            assert c.session_id == "s1"
            assert c.turn_id == "turn-42"
            assert c.created_at is not None
            assert c.active is True

    def test_cancelled_constraint_marked_inactive_not_removed(self):
        """取消的约束标记为 inactive，不从内存中物理删除（审计需要）。"""
        store = SessionPolicyStore.get_instance()
        store.add_constraints("s1", {"不能删除数据库"}, turn_id="t1")
        store.cancel_constraint("s1", "不能删除数据库")
        with store._lock:
            constraints = store._sessions.get("s1", [])
            assert len(constraints) == 1  # 仍在内存
            assert constraints[0].active is False
