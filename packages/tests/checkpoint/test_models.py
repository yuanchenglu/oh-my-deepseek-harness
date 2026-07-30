"""Checkpoint 数据模型测试 — 验证 CompletedStep / Checkpoint / ReviewResult / DictStep。

测试 platform_core.checkpoint.models 中的：
  - CompletedStep Pydantic 模型
  - Checkpoint Pydantic 模型
  - ReviewResult Pydantic 模型
  - DictStep Pydantic 模型
  - CreateCheckpointRequest Pydantic 模型
  - generate_checkpoint_id()
  - now_iso()
"""

import re

from platform_core.checkpoint.models import (
    CompletedStep,
    Checkpoint,
    ReviewResult,
    DictStep,
    CreateCheckpointRequest,
    generate_checkpoint_id,
    now_iso,
)


class TestCompletedStep:
    def test_minimal(self):
        s = CompletedStep(step_id="s1", text="第一步")
        assert s.step_id == "s1"
        assert s.text == "第一步"
        assert s.result == ""

    def test_with_result(self):
        s = CompletedStep(step_id="s1", text="第一步", result="完成")
        assert s.result == "完成"


class TestCheckpoint:
    def test_minimal(self):
        cp = Checkpoint(
            checkpoint_id="cp_abc123",
            plan_id="plan_xyz",
            created_at="2025-01-01T00:00:00",
            checkpoint_number=1,
            current_goal="实现登录",
        )
        assert cp.checkpoint_id == "cp_abc123"
        assert cp.checkpoint_number == 1
        assert cp.unexpected_findings == []
        assert cp.remaining_plan == []
        assert cp.purpose == "step_threshold"

    def test_with_all_fields(self):
        cp = Checkpoint(
            checkpoint_id="cp_1",
            plan_id="plan_1",
            created_at="2025-01-01T00:00:00",
            checkpoint_number=2,
            current_goal="测试",
            completed_steps_summary=[
                CompletedStep(step_id="s1", text="步骤1", result="ok")
            ],
            unexpected_findings=["发现 bug"],
            remaining_plan=["步骤2"],
            purpose="abnormal_event",
        )
        assert len(cp.completed_steps_summary) == 1
        assert len(cp.unexpected_findings) == 1
        assert len(cp.remaining_plan) == 1
        assert cp.purpose == "abnormal_event"


class TestReviewResult:
    def test_minimal(self):
        r = ReviewResult(
            alignment="aligned",
            progress_status="on_track",
            unexpected_impact="none",
        )
        assert r.alignment == "aligned"
        assert r.progress_status == "on_track"
        assert r.unexpected_impact == "none"
        assert r.adjustments == []
        assert r.confidence == 0.5

    def test_with_all_fields(self):
        r = ReviewResult(
            alignment="partial",
            progress_status="at_risk",
            unexpected_impact="medium",
            adjustments=["调整计划"],
            confidence=0.7,
        )
        assert r.confidence == 0.7
        assert len(r.adjustments) == 1


class TestDictStep:
    def test_minimal(self):
        s = DictStep(step_id="s1", text="步骤1", status="pending")
        assert s.step_id == "s1"
        assert s.key == ""


class TestCreateCheckpointRequest:
    def test_minimal(self):
        req = CreateCheckpointRequest(
            plan_id="plan_1",
            plan_steps=[DictStep(step_id="s1", text="步骤1", status="pending")],
            completed_step_ids=[],
        )
        assert req.plan_id == "plan_1"
        assert len(req.plan_steps) == 1


class TestGenerateCheckpointId:
    def test_starts_with_cp(self):
        cpid = generate_checkpoint_id()
        assert cpid.startswith("cp_")

    def test_has_hex_suffix(self):
        cpid = generate_checkpoint_id()
        assert len(cpid) > 3  # cp_ + hex

    def test_unique(self):
        ids = {generate_checkpoint_id() for _ in range(10)}
        assert len(ids) == 10


class TestNowIso:
    def test_returns_string(self):
        s = now_iso()
        assert isinstance(s, str)
        assert "T" in s
