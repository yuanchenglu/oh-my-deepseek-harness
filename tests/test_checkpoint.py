"""CP-001 Checkpoint 归属/编号/审查/链测试。

覆盖 TC-CP-001~006。
测 storage 层不变量（plan 归属、completed ids、唯一编号、幂等、链排序）
与 models validator。用临时 SQLite 与合成 Plan，不触碰真实数据。
"""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

from harness_server.models import (
    Checkpoint,
    CompletedStep,
    CreateCheckpointRequest,
    DictStep,
    OKRPlanStep,
    PlanStatus,
)
from harness_server.storage import HarnessStorage


@pytest.fixture(autouse=True)
def _isolate_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """隔离 HOME，避免 import app 时模块级副作用污染真实 ~/.hermes。"""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))


def _step(step_id: str) -> OKRPlanStep:
    return OKRPlanStep(step_id=step_id, text=f"步骤 {step_id}")


def _checkpoint(plan_id: str, number: int, cp_id: str = "") -> Checkpoint:
    return Checkpoint(
        checkpoint_id=cp_id or f"cp_{plan_id}_{number}",
        plan_id=plan_id,
        created_at="2026-08-04T00:00:00+00:00",
        checkpoint_number=number,
        current_goal="目标",
        completed_steps_summary=[CompletedStep(step_id="s1", text="完成", result="ok")],
    )


# ════════════════════════════════════════════════════════════════
# TC-CP-001/002: 合法 Plan 快照成功 / Plan 不存在 not_found
# ════════════════════════════════════════════════════════════════


def test_checkpoint_requires_existing_plan(tmp_path: Path) -> None:
    """TC-CP-002: plan 不存在时创建 Checkpoint 被拒绝。"""
    store = HarnessStorage(str(tmp_path / "cp.db"))
    with pytest.raises(ValueError):
        store.insert_checkpoint(_checkpoint("ghost-plan", 1))


def test_checkpoint_valid_plan_snapshot_succeeds(tmp_path: Path) -> None:
    """TC-CP-001: 合法 Plan 的 Checkpoint 快照创建成功。"""
    store = HarnessStorage(str(tmp_path / "cp.db"))
    store.create_plan_with_steps("p1", [_step("s1")])
    cp_id = store.insert_checkpoint(_checkpoint("p1", 1))
    assert store.get_checkpoint(cp_id) is not None


# ════════════════════════════════════════════════════════════════
# TC-CP-003: completed ID 不属于 Plan → conflict
# ════════════════════════════════════════════════════════════════


def test_completed_step_ids_must_belong_to_plan(tmp_path: Path) -> None:
    """TC-CP-003: completed_step_ids 不属于 Plan 的步骤时被拒绝。"""
    store = HarnessStorage(str(tmp_path / "cp.db"))
    store.create_plan_with_steps("p1", [_step("s1")])

    # completed_step_ids 含不属于 plan 的 id → 校验失败
    with pytest.raises(ValueError):
        CreateCheckpointRequest(
            plan_id="p1",
            plan_steps=[DictStep(step_id="s1", text="x", status="pending")],
            completed_step_ids=["ghost-step"],
        )


# ════════════════════════════════════════════════════════════════
# TC-CP-004: 并发编号不重复
# ════════════════════════════════════════════════════════════════


def test_concurrent_checkpoint_numbering_unique(tmp_path: Path) -> None:
    """TC-CP-004: 同 Plan 并发创建 Checkpoint 编号不重复。"""
    store = HarnessStorage(str(tmp_path / "cp.db"))
    store.create_plan_with_steps("p1", [_step("s1")])

    inserted: list[int] = []
    lock = threading.Lock()

    def worker():
        num = store._get_next_checkpoint_number("p1")
        try:
            # 用唯一 cp_id 避免并发 id 冲突（编号唯一性才是被测点）
            store.insert_checkpoint(
                _checkpoint("p1", num, cp_id=f"cp_{threading.get_ident()}_{num}")
            )
            with lock:
                inserted.append(num)
        except Exception:
            # 并发冲突（唯一索引兜底）：该编号已被占用，忽略
            pass

    threads = [threading.Thread(target=worker) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(inserted) == len(set(inserted))  # 无重复编号


# ════════════════════════════════════════════════════════════════
# TC-CP-005: 同规则重复 Review 幂等
# ════════════════════════════════════════════════════════════════


def test_review_is_idempotent_per_rule_version(tmp_path: Path) -> None:
    """TC-CP-005: 同 Checkpoint 同规则重复 Review 结果一致。"""
    from harness_server.app import (
        _adjustments_from_snapshot,
        _check_alignment_from_snapshot,
        _check_progress_from_snapshot,
        _compute_confidence,
        _compute_unexpected_impact,
    )

    store = HarnessStorage(str(tmp_path / "cp.db"))
    store.create_plan_with_steps("p1", [_step("s1")])
    cp = _checkpoint("p1", 1)

    # review 是确定性纯函数：同输入同输出（幂等）
    def _review(cp):
        a = _check_alignment_from_snapshot(cp)
        p = _check_progress_from_snapshot(cp)
        i = _compute_unexpected_impact(cp)
        adj = _adjustments_from_snapshot(cp, a, p, i)
        return (a, p, i, adj, _compute_confidence(a, p, i))

    assert _review(cp) == _review(cp)


# ════════════════════════════════════════════════════════════════
# TC-CP-006: Chain 按编号升序
# ════════════════════════════════════════════════════════════════


def test_chain_ordered_by_number_ascending(tmp_path: Path) -> None:
    """TC-CP-006: Chain 按 checkpoint_number 升序返回。"""
    store = HarnessStorage(str(tmp_path / "cp.db"))
    store.create_plan_with_steps("p1", [_step("s1")])
    # 乱序插入
    store.insert_checkpoint(_checkpoint("p1", 3))
    store.insert_checkpoint(_checkpoint("p1", 1))
    store.insert_checkpoint(_checkpoint("p1", 2))

    chain = store.get_checkpoint_chain("p1")
    nums = [c.checkpoint_number for c in chain]
    assert nums == sorted(nums)
    assert nums == [1, 2, 3]