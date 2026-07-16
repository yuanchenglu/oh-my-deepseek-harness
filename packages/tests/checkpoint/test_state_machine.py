"""Checkpoint 四维审查状态机测试 — 验证所有审查函数。

测试 platform_core.checkpoint.state_machine 中的：
  - compute_alignment()
  - compute_progress()
  - compute_unexpected_impact()
  - compute_adjustments()
  - build_completed_summary()
  - build_remaining_plan()
  - build_current_goal()
  - check_alignment_from_snapshot()
  - check_progress_from_snapshot()
  - adjustments_from_snapshot()
  - compute_confidence()
"""

from platform_core.checkpoint.models import (
    Checkpoint,
    CompletedStep,
    DictStep,
    CreateCheckpointRequest,
)
from platform_core.checkpoint.state_machine import (
    compute_alignment,
    compute_progress,
    compute_unexpected_impact,
    compute_adjustments,
    build_completed_summary,
    build_remaining_plan,
    build_current_goal,
    check_alignment_from_snapshot,
    check_progress_from_snapshot,
    adjustments_from_snapshot,
    compute_confidence,
)


# ── Helpers ──────────────────────────────────────────────


def make_cp(**overrides) -> Checkpoint:
    """创建 Checkpoint 实例。"""
    defaults = dict(
        checkpoint_id="cp_1",
        plan_id="plan_1",
        created_at="2025-01-01T00:00:00",
        checkpoint_number=1,
        current_goal="实现登录模块",
    )
    defaults.update(overrides)
    return Checkpoint(**defaults)


def make_req(**overrides) -> CreateCheckpointRequest:
    """创建 CreateCheckpointRequest。"""
    defaults = dict(
        plan_id="plan_1",
        plan_steps=[
            DictStep(step_id="s1", text="步骤1", status="completed"),
            DictStep(step_id="s2", text="步骤2", status="in_progress"),
            DictStep(step_id="s3", text="步骤3", status="pending"),
        ],
        completed_step_ids=["s1"],
    )
    defaults.update(overrides)
    return CreateCheckpointRequest(**defaults)


# ========= compute_alignment =========


class TestComputeAlignment:
    def test_all_aligned(self):
        cp = make_cp()
        req = make_req(completed_step_ids=["s1"])
        assert compute_alignment(cp, req) == "aligned"

    def test_deviated(self):
        """已完成但不在 plan_steps 中的步骤 → deviated。"""
        cp = make_cp()
        req = make_req(completed_step_ids=["s1", "extraneous"])
        assert compute_alignment(cp, req) == "deviated"

    def test_no_completed_steps(self):
        cp = make_cp()
        req = make_req(completed_step_ids=[])
        assert compute_alignment(cp, req) == "aligned"

    def test_empty_plan(self):
        cp = make_cp()
        req = make_req(plan_steps=[], completed_step_ids=[])
        assert compute_alignment(cp, req) == "aligned"


# ========= compute_progress =========


class TestComputeProgress:
    def test_on_track(self):
        cp = make_cp()
        req = make_req(completed_step_ids=["s1"])  # 1/3 ≈ 0.33
        assert compute_progress(cp, req) == "at_risk"

    def test_on_track_high_ratio(self):
        cp = make_cp()
        req = make_req(completed_step_ids=["s1", "s2"])  # 2/3 ≈ 0.67
        assert compute_progress(cp, req) == "on_track"

    def test_behind(self):
        cp = make_cp()
        req = make_req(
            plan_steps=[
                DictStep(step_id="s1", text="1", status="pending"),
                DictStep(step_id="s2", text="2", status="pending"),
                DictStep(step_id="s3", text="3", status="pending"),
                DictStep(step_id="s4", text="4", status="pending"),
                DictStep(step_id="s5", text="5", status="pending"),
            ],
            completed_step_ids=["s1"],  # 1/5 = 0.2
        )
        assert compute_progress(cp, req) == "behind"

    def test_zero_total(self):
        cp = make_cp()
        req = make_req(plan_steps=[], completed_step_ids=[])
        assert compute_progress(cp, req) == "on_track"


# ========= compute_unexpected_impact =========


class TestComputeUnexpectedImpact:
    def test_no_findings(self):
        cp = make_cp(unexpected_findings=[])
        assert compute_unexpected_impact(cp) == "none"

    def test_low_impact_single_finding(self):
        cp = make_cp(unexpected_findings=["发现 API 文档过时"])
        assert compute_unexpected_impact(cp) == "low"

    def test_medium_impact_three_findings(self):
        cp = make_cp(unexpected_findings=["a", "b", "c"])
        assert compute_unexpected_impact(cp) == "medium"

    def test_high_impact_security(self):
        cp = make_cp(unexpected_findings=["存在 security 漏洞"])
        assert compute_unexpected_impact(cp) == "high"

    def test_high_impact_chinese(self):
        cp = make_cp(unexpected_findings=["发现安全漏洞，可能导致数据丢失"])
        assert compute_unexpected_impact(cp) == "high"

    def test_none_findings_none(self):
        cp = make_cp(unexpected_findings=[])
        assert compute_unexpected_impact(cp) == "none"


# ========= compute_adjustments =========


class TestComputeAdjustments:
    def test_deviated_has_correction(self):
        cp = make_cp(remaining_plan=["步骤2"])
        req = make_req(completed_step_ids=["extraneous"])
        adj = compute_adjustments(cp, req)
        assert any("偏离" in a for a in adj)

    def test_behind_has_suggestion(self):
        cp = make_cp(remaining_plan=["步骤3"])
        req = make_req(
            plan_steps=[DictStep(step_id="s1", text="1", status="pending") for _ in range(5)],
            completed_step_ids=["s1"],
        )
        adj = compute_adjustments(cp, req)
        assert any("落后" in a for a in adj)

    def test_high_impact_stop_suggestion(self):
        cp = make_cp(unexpected_findings=["security vulnerability"])
        req = make_req(completed_step_ids=[])
        adj = compute_adjustments(cp, req)
        assert any("暂停" in a for a in adj)

    def test_remaining_plan_summary(self):
        cp = make_cp(remaining_plan=["步骤2", "步骤3"])
        req = make_req(completed_step_ids=["s1"])
        adj = compute_adjustments(cp, req)
        assert any("剩余" in a for a in adj)

    def test_no_remaining_plan(self):
        cp = make_cp(remaining_plan=[])
        req = make_req(completed_step_ids=["s1"])
        adj = compute_adjustments(cp, req)
        # 不应包含剩余步数字样
        assert not any("剩余" in a for a in adj)


# ========= build_completed_summary =========


class TestBuildCompletedSummary:
    def test_builds_summary(self):
        req = make_req(completed_step_ids=["s1", "s2"])
        summary = build_completed_summary(req)
        assert len(summary) == 2
        assert summary[0].step_id == "s1"
        assert summary[1].step_id == "s2"

    def test_unknown_step_ids_skipped(self):
        req = make_req(completed_step_ids=["nonexistent"])
        summary = build_completed_summary(req)
        assert len(summary) == 0

    def test_empty(self):
        req = make_req(completed_step_ids=[])
        assert build_completed_summary(req) == []


# ========= build_remaining_plan =========


class TestBuildRemainingPlan:
    def test_returns_uncompleted_steps(self):
        req = make_req(completed_step_ids=["s1"])
        remaining = build_remaining_plan(req)
        assert len(remaining) == 2  # s2, s3
        assert all("s1" not in r for r in remaining)

    def test_all_completed(self):
        req = make_req(completed_step_ids=["s1", "s2", "s3"])
        assert build_remaining_plan(req) == []

    def test_empty_plan(self):
        req = make_req(plan_steps=[], completed_step_ids=[])
        assert build_remaining_plan(req) == []


# ========= build_current_goal =========


class TestBuildCurrentGoal:
    def test_first_uncompleted(self):
        req = make_req(completed_step_ids=["s1"])
        assert build_current_goal(req) == "步骤2"

    def test_all_completed_returns_last(self):
        req = make_req(completed_step_ids=["s1", "s2", "s3"])
        assert build_current_goal(req) == "步骤3"

    def test_empty_plan(self):
        req = make_req(plan_steps=[], completed_step_ids=[])
        assert build_current_goal(req) == ""


# ========= Snapshot-based functions =========


class TestCheckAlignmentFromSnapshot:
    def test_no_completed(self):
        cp = make_cp(completed_steps_summary=[])
        assert check_alignment_from_snapshot(cp) == "aligned"

    def test_aligned_with_completed_and_remaining(self):
        cp = make_cp(
            completed_steps_summary=[CompletedStep(step_id="s1", text="1")],
            remaining_plan=["2"],
        )
        assert check_alignment_from_snapshot(cp) == "aligned"

    def test_partial_with_findings(self):
        cp = make_cp(
            completed_steps_summary=[CompletedStep(step_id="s1", text="1")],
            unexpected_findings=["发现异常"],
        )
        assert check_alignment_from_snapshot(cp) == "partial"


class TestCheckProgressFromSnapshot:
    def test_on_track(self):
        cp = make_cp(
            completed_steps_summary=[CompletedStep(step_id="s1", text="1")],
            remaining_plan=["2"],
        )
        assert check_progress_from_snapshot(cp) == "on_track"  # 1/2 = 0.5

    def test_behind(self):
        cp = make_cp(
            completed_steps_summary=[CompletedStep(step_id="s1", text="1")],
            remaining_plan=["2", "3", "4", "5"],
        )
        assert check_progress_from_snapshot(cp) == "behind"  # 1/5 = 0.2

    def test_zero_total(self):
        cp = make_cp(completed_steps_summary=[], remaining_plan=[])
        assert check_progress_from_snapshot(cp) == "on_track"


class TestAdjustmentsFromSnapshot:
    def test_partial(self):
        adj = adjustments_from_snapshot(make_cp(), "partial", "on_track", "none")
        assert any("偏离" in a for a in adj)

    def test_behind(self):
        adj = adjustments_from_snapshot(make_cp(), "aligned", "behind", "none")
        assert any("落后" in a for a in adj)

    def test_high_impact(self):
        adj = adjustments_from_snapshot(make_cp(), "aligned", "on_track", "high")
        assert any("暂停" in a for a in adj)

    def test_no_remaining_plan(self):
        cp = make_cp(remaining_plan=[])
        adj = adjustments_from_snapshot(cp, "aligned", "on_track", "none")
        assert not any("剩余" in a for a in adj)


# ========= compute_confidence =========


class TestComputeConfidence:
    def test_aligned_none_is_high(self):
        assert compute_confidence("aligned", "on_track", "none") == 0.90

    def test_partial_high_is_lower(self):
        assert compute_confidence("partial", "at_risk", "high") == 0.70

    def test_deviated_is_lowest(self):
        assert compute_confidence("deviated", "behind", "medium") == 0.60

    def test_default(self):
        assert compute_confidence("aligned", "at_risk", "low") == 0.85
