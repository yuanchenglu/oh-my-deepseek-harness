"""Plan Engine 数据模型测试 — 验证 OKRPlanStep / PlanStatus / AssociationStrength。

测试 platform_core.plan_engine.models 中的：
  - PlanStatus 枚举
  - AssociationStrength 枚举
  - OKRPlanStep Pydantic 模型
"""

from platform_core.plan_engine.models import (
    OKRPlanStep,
    PlanStatus,
    AssociationStrength,
)


class TestPlanStatus:
    def test_values(self):
        assert PlanStatus.PENDING.value == "pending"
        assert PlanStatus.IN_PROGRESS.value == "in_progress"
        assert PlanStatus.COMPLETED.value == "completed"
        assert PlanStatus.PENDING_REVIEW.value == "pending_review"

    def test_enum_membership(self):
        assert "pending" in {s.value for s in PlanStatus}


class TestAssociationStrength:
    def test_values(self):
        assert AssociationStrength.STRONG.value == "strong"
        assert AssociationStrength.MODERATE.value == "moderate"
        assert AssociationStrength.WEAK.value == "weak"


class TestOKRPlanStep:
    def test_minimal_creation(self):
        step = OKRPlanStep(text="实现登录模块")
        assert step.text == "实现登录模块"
        assert step.status == PlanStatus.PENDING
        assert step.dependency_ids == []
        assert step.association_strength == AssociationStrength.MODERATE

    def test_with_all_fields(self):
        step = OKRPlanStep(
            step_id="step-1",
            text="实现登录模块",
            key="auth",
            status=PlanStatus.IN_PROGRESS,
            parent_id="step-0",
            dependency_ids=["step-0"],
            association_strength=AssociationStrength.STRONG,
        )
        assert step.step_id == "step-1"
        assert step.key == "auth"
        assert step.status == PlanStatus.IN_PROGRESS
        assert step.parent_id == "step-0"
        assert step.dependency_ids == ["step-0"]
        assert step.association_strength == AssociationStrength.STRONG

    def test_children_default(self):
        step = OKRPlanStep(text="test")
        assert step.children == []

    def test_children_custom(self):
        child = OKRPlanStep(text="child step")
        parent = OKRPlanStep(text="parent", children=[child])
        assert len(parent.children) == 1
        assert parent.children[0].text == "child step"
