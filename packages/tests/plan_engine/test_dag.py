"""Plan Engine DAG 单元测试 — 验证级联修正、循环检测和邻接表构建。

测试 platform_core.plan_engine.dag 中的：
  - cascade_correct()
  - detect_cycle()
  - build_adjacency_list()
  - PlanStorageProtocol
"""

from unittest import mock

from platform_core.plan_engine.models import (
    OKRPlanStep,
    PlanStatus,
    AssociationStrength,
)
from platform_core.plan_engine.dag import (
    cascade_correct,
    detect_cycle,
    build_adjacency_list,
)


# ── Helpers ──────────────────────────────────────────────


def make_step(sid, text, deps=None, strength=None, parent=None):
    """便捷创建 OKRPlanStep。"""
    return OKRPlanStep(
        step_id=sid,
        text=text,
        dependency_ids=deps or [],
        association_strength=strength or AssociationStrength.MODERATE,
        parent_id=parent,
    )


# ========= cascade_correct =========


class TestCascadeCorrect:
    def test_no_affected_steps(self):
        """无依赖关系时仅返回空结果。"""
        steps = {
            "s1": make_step("s1", "第一步"),
        }
        storage = mock.MagicMock()
        r = cascade_correct("plan-1", "s1", steps, storage)
        assert r["affected_steps"] == []
        assert r["action"] == {}

    def test_strong_dependency_flagged_pending_review(self):
        """STRONG 依赖应标记为 pending_review。"""
        steps = {
            "s1": make_step("s1", "第一步"),
            "s2": make_step("s2", "第二步", deps=["s1"], strength=AssociationStrength.STRONG),
        }
        storage = mock.MagicMock()
        r = cascade_correct("plan-1", "s1", steps, storage)
        assert "s2" in r["affected_steps"]
        assert r["action"]["s2"] == "pending_review"

    def test_weak_dependency_flagged_notify(self):
        """WEAK 依赖应标记为 notify。"""
        steps = {
            "s1": make_step("s1", "第一步"),
            "s2": make_step("s2", "第二步", deps=["s1"], strength=AssociationStrength.WEAK),
        }
        storage = mock.MagicMock()
        r = cascade_correct("plan-1", "s1", steps, storage)
        assert r["action"]["s2"] == "notify"

    def test_calls_storage_update(self):
        """存储层被正确调用。"""
        steps = {
            "s1": make_step("s1", "第一步"),
            "s2": make_step("s2", "第二步", deps=["s1"], strength=AssociationStrength.STRONG),
        }
        storage = mock.MagicMock()
        cascade_correct("plan-1", "s1", steps, storage)
        storage.update_step_statuses.assert_called_once()
        storage.update_plan_timestamp.assert_called_once_with("plan-1")

    def test_child_steps_notified(self):
        """父步骤修改时，子步骤应收到 notify。"""
        steps = {
            "s1": make_step("s1", "父步骤"),
            "s2": make_step("s2", "子步骤", parent="s1"),
        }
        storage = mock.MagicMock()
        r = cascade_correct("plan-1", "s1", steps, storage)
        assert "s2" in r["affected_steps"]
        assert r["action"]["s2"] == "notify"

    def test_chain_cascade(self):
        """链式依赖应全部级联。"""
        steps = {
            "s1": make_step("s1", "1"),
            "s2": make_step("s2", "2", deps=["s1"], strength=AssociationStrength.STRONG),
            "s3": make_step("s3", "3", deps=["s2"], strength=AssociationStrength.STRONG),
        }
        storage = mock.MagicMock()
        r = cascade_correct("plan-1", "s1", steps, storage)
        assert "s2" in r["affected_steps"]
        assert "s3" in r["affected_steps"]


# ========= detect_cycle =========


class TestDetectCycle:
    def test_no_cycle_returns_false(self):
        steps = [
            make_step("s1", "1"),
            make_step("s2", "2", deps=["s1"]),
            make_step("s3", "3", deps=["s2"]),
        ]
        assert detect_cycle(steps) is False

    def test_simple_cycle_returns_true(self):
        steps = [
            make_step("s1", "1", deps=["s2"]),
            make_step("s2", "2", deps=["s1"]),
        ]
        assert detect_cycle(steps) is True

    def test_self_cycle_returns_true(self):
        steps = [
            make_step("s1", "1", deps=["s1"]),
        ]
        assert detect_cycle(steps) is True

    def test_complex_cycle(self):
        steps = [
            make_step("s1", "1", deps=["s3"]),
            make_step("s2", "2", deps=["s1"]),
            make_step("s3", "3", deps=["s2"]),
        ]
        assert detect_cycle(steps) is True

    def test_empty_steps_no_cycle(self):
        assert detect_cycle([]) is False


# ========= build_adjacency_list =========


class TestBuildAdjacencyList:
    def test_no_dependencies(self):
        steps = [make_step("s1", "1"), make_step("s2", "2")]
        adj = build_adjacency_list(steps)
        assert "s1" in adj
        assert "s2" in adj
        assert adj["s1"] == []
        assert adj["s2"] == []

    def test_with_dependencies(self):
        steps = [
            make_step("s1", "1"),
            make_step("s2", "2", deps=["s1"]),
        ]
        adj = build_adjacency_list(steps)
        assert "s1" in adj
        assert adj["s1"] == ["s2"]

    def test_multiple_dependents(self):
        steps = [
            make_step("s1", "1"),
            make_step("s2", "2", deps=["s1"]),
            make_step("s3", "3", deps=["s1"]),
        ]
        adj = build_adjacency_list(steps)
        assert set(adj["s1"]) == {"s2", "s3"}
