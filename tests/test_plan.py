"""PLAN-001 Plan DAG 与级联不变量测试。

覆盖 TC-PLAN-003~007、TC-PLAN-009。
测 storage 层 DAG 校验（自依赖/缺失/跨 Plan/循环）与 cascade 影响集合。
用临时 SQLite 与生成 DAG fixture，不触碰真实用户数据。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from harness_server.models import AssociationStrength, MemoryLayer, OKRPlanStep, PlanStatus
from harness_server.storage import HarnessStorage


def _step(step_id: str, deps: list[str] | None = None, **kw) -> OKRPlanStep:
    """构造一条 Plan 步骤。"""
    return OKRPlanStep(
        step_id=step_id,
        text=f"步骤 {step_id}",
        dependency_ids=deps or [],
        **kw,
    )


def _make_plan(store: HarnessStorage, plan_id: str, steps: list[OKRPlanStep]) -> None:
    """创建 Plan 并插入步骤。"""
    store.create_plan(plan_id)
    store.insert_steps(plan_id, steps)


# ════════════════════════════════════════════════════════════════
# TC-PLAN-003: 自依赖 → conflict
# ════════════════════════════════════════════════════════════════


def test_self_dependency_rejected(tmp_path: Path) -> None:
    """TC-PLAN-003: 步骤依赖自身被拒绝。"""
    store = HarnessStorage(str(tmp_path / "plan.db"))
    store.create_plan("p1")
    with pytest.raises(ValueError):
        store.insert_steps("p1", [_step("s1", deps=["s1"])])


# ════════════════════════════════════════════════════════════════
# TC-PLAN-004: 不存在依赖 → conflict
# ════════════════════════════════════════════════════════════════


def test_missing_dependency_rejected(tmp_path: Path) -> None:
    """TC-PLAN-004: 依赖不存在的步骤被拒绝。"""
    store = HarnessStorage(str(tmp_path / "plan.db"))
    store.create_plan("p1")
    with pytest.raises(ValueError):
        store.insert_steps("p1", [_step("s1", deps=["ghost"])])


# ════════════════════════════════════════════════════════════════
# TC-PLAN-005: 跨 Plan 依赖 → conflict
# ════════════════════════════════════════════════════════════════


def test_cross_plan_dependency_rejected(tmp_path: Path) -> None:
    """TC-PLAN-005: 依赖其他 Plan 的步骤被拒绝。"""
    store = HarnessStorage(str(tmp_path / "plan.db"))
    store.create_plan("p1")
    store.create_plan("p2")
    store.insert_steps("p1", [_step("s1")])
    # p2 的步骤依赖 p1 的 s1 → 跨 Plan 拒绝
    with pytest.raises(ValueError):
        store.insert_steps("p2", [_step("s2", deps=["s1"])])


# ════════════════════════════════════════════════════════════════
# TC-PLAN-006: 创建环 → conflict
# ════════════════════════════════════════════════════════════════


def test_cycle_on_create_rejected(tmp_path: Path) -> None:
    """TC-PLAN-006: 创建时存在循环依赖被拒绝。"""
    store = HarnessStorage(str(tmp_path / "plan.db"))
    store.create_plan("p1")
    with pytest.raises(ValueError):
        store.insert_steps(
            "p1",
            [
                _step("s1", deps=["s2"]),
                _step("s2", deps=["s3"]),
                _step("s3", deps=["s1"]),  # 环
            ],
        )


# ════════════════════════════════════════════════════════════════
# TC-PLAN-007: 更新形成环 → rollback
# ════════════════════════════════════════════════════════════════


def test_update_creating_cycle_rolls_back(tmp_path: Path) -> None:
    """TC-PLAN-007: 更新步骤形成环时回滚，不产生半状态。"""
    store = HarnessStorage(str(tmp_path / "plan.db"))
    store.create_plan("p1")
    store.insert_steps("p1", [_step("s1"), _step("s2")])

    # 更新 s2 依赖 s1，再更新 s1 依赖 s2 → 形成环
    store.update_step("s2", dependency_ids=["s1"])
    with pytest.raises(ValueError):
        store.update_step("s1", dependency_ids=["s2"])

    # 回滚后 s1 不应有依赖 s2
    s1 = store.get_step("s1")
    assert "s2" not in s1.dependency_ids


# ════════════════════════════════════════════════════════════════
# TC-PLAN-009: Cascade 影响集合正确
# ════════════════════════════════════════════════════════════════


def test_cascade_impact_set_and_reasons(tmp_path: Path) -> None:
    """TC-PLAN-009: cascade 返回正确的受影响集合与原因。"""
    from harness_server.app import cascade_correct

    store = HarnessStorage(str(tmp_path / "plan.db"))
    store.create_plan("p1")
    store.insert_steps(
        "p1",
        [
            _step("s1"),
            _step("s2", deps=["s1"], association_strength=AssociationStrength.STRONG),
            _step("s3", deps=["s1"], association_strength=AssociationStrength.WEAK),
        ],
    )

    steps = {s.step_id: s for s in store.get_steps("p1")}
    result = cascade_correct("p1", "s1", steps, store)

    assert "s2" in result["action"]
    assert "s3" in result["action"]
    # s2 STRONG → pending_review；s3 WEAK → notify
    assert result["action"]["s2"] == "pending_review"
    assert result["action"]["s3"] == "notify"


def test_cascade_never_alters_completed(tmp_path: Path) -> None:
    """TC-PLAN-009: cascade 不静默修改已完成步骤。"""
    from harness_server.app import cascade_correct

    store = HarnessStorage(str(tmp_path / "plan.db"))
    store.create_plan("p1")
    store.insert_steps(
        "p1",
        [
            _step("s1"),
            _step("s2", deps=["s1"], association_strength=AssociationStrength.STRONG),
        ],
    )
    # 将 s2 标记为 completed
    store.update_step("s2", status=PlanStatus.COMPLETED)

    steps = {s.step_id: s for s in store.get_steps("p1")}
    result = cascade_correct("p1", "s1", steps, store)

    # s2 已完成 → 不应被改为 pending_review
    s2_row = store.get_step("s2")
    assert s2_row.status == PlanStatus.COMPLETED


# ════════════════════════════════════════════════════════════════
# PLAN-002: 状态机 + 原子变更 + 并发（TC-PLAN-001/002/008/010）
# ════════════════════════════════════════════════════════════════


def test_plan_create_is_atomic(tmp_path: Path) -> None:
    """TC-PLAN-001: Plan + Steps 单事务，失败无半状态。"""
    store = HarnessStorage(str(tmp_path / "plan.db"))
    # 原子创建：插入非法步骤（自依赖）→ 整体回滚，不残留 plan
    with pytest.raises(ValueError):
        store.create_plan_with_steps("p1", [_step("s1", deps=["s1"])])
    # plan 元数据不应残留（无半状态）
    assert store.get_plan_meta("p1") is None


def test_illegal_state_transition_rejected(tmp_path: Path) -> None:
    """TC-PLAN-008: 非法状态转换被拒绝（conflict）。"""
    store = HarnessStorage(str(tmp_path / "plan.db"))
    store.create_plan("p1")
    store.insert_steps("p1", [_step("s1")])

    # pending → completed 是合法（跳过中间态）
    store.update_step("s1", status=PlanStatus.COMPLETED)

    # completed → pending 非法（已完成不能再回退到待执行）
    with pytest.raises(ValueError):
        store.update_step("s1", status=PlanStatus.PENDING)


def test_legal_state_transition_accepted(tmp_path: Path) -> None:
    """TC-PLAN-008: 合法状态转换通过。"""
    store = HarnessStorage(str(tmp_path / "plan.db"))
    store.create_plan("p1")
    store.insert_steps("p1", [_step("s1")])

    # pending → in_progress → completed 合法路径
    store.update_step("s1", status=PlanStatus.IN_PROGRESS)
    assert store.get_step("s1").status == PlanStatus.IN_PROGRESS
    store.update_step("s1", status=PlanStatus.COMPLETED)
    assert store.get_step("s1").status == PlanStatus.COMPLETED


def test_concurrent_update_no_half_state(tmp_path: Path) -> None:
    """TC-PLAN-010: 并发更新无半状态。"""
    import threading

    store = HarnessStorage(str(tmp_path / "plan.db"))
    store.create_plan("p1")
    store.insert_steps("p1", [_step("s1")])

    results: list[bool] = []
    errors: list[str] = []

    def worker():
        try:
            results.append(store.update_step("s1", status=PlanStatus.IN_PROGRESS))
        except ValueError as e:
            errors.append(str(e))

    threads = [threading.Thread(target=worker) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # 最终状态必须一致（无半状态）
    final = store.get_step("s1").status
    assert final in (PlanStatus.IN_PROGRESS, PlanStatus.COMPLETED)