"""reasoning_effort.py 单元测试 — 验证 I-17 推理强度控制逻辑。"""

from deepseek_harness.reasoning_effort import (
    on_pre_llm_call,
    _get_reasoning_effort_level,
)


class TestGetReasoningEffortLevel:
    def test_architecture_returns_max(self):
        assert _get_reasoning_effort_level("architecture") == "max"

    def test_research_returns_max(self):
        assert _get_reasoning_effort_level("research") == "max"

    def test_collaboration_returns_max(self):
        assert _get_reasoning_effort_level("collaboration") == "max"

    def test_refactor_returns_high(self):
        assert _get_reasoning_effort_level("refactor") == "high"

    def test_new_returns_high(self):
        assert _get_reasoning_effort_level("new") == "high"

    def test_medium_returns_high(self):
        assert _get_reasoning_effort_level("medium") == "high"

    def test_simple_returns_none(self):
        assert _get_reasoning_effort_level("simple") is None

    def test_spec_driven_returns_none(self):
        assert _get_reasoning_effort_level("spec_driven") is None

    def test_unknown_intent_returns_none(self):
        assert _get_reasoning_effort_level("unknown") is None

    def test_empty_intent_returns_none(self):
        assert _get_reasoning_effort_level("") is None


class TestOnPreLlmCall:
    def test_non_first_turn_returns_none(self):
        """非首轮应跳过处理。"""
        r = on_pre_llm_call(is_first_turn=False)
        assert r is None

    def test_no_user_message_returns_none(self):
        """无 user_message 应跳过处理。"""
        r = on_pre_llm_call(is_first_turn=True, user_message="")
        assert r is None

    def test_simple_intent_returns_none(self):
        """simple intent 应返回 None（不注入 context）。"""
        r = on_pre_llm_call(
            is_first_turn=True,
            user_message="fix typo in readme",
        )
        assert r is None

    def test_architecture_returns_max_context(self):
        """architecture intent 应返回高复杂度推理指引。"""
        r = on_pre_llm_call(
            is_first_turn=True,
            user_message="design the system architecture",
        )
        assert r is not None
        assert "context" in r
        assert "高复杂度" in r["context"]

    def test_refactor_returns_high_context(self):
        """refactor intent 应返回中等复杂度推理指引。"""
        r = on_pre_llm_call(
            is_first_turn=True,
            user_message="refactor the auth module",
        )
        assert r is not None
        assert "context" in r
        assert "中等复杂度" in r["context"]

    def test_research_returns_max_context(self):
        """research intent 应返回高复杂度推理指引。"""
        r = on_pre_llm_call(
            is_first_turn=True,
            user_message="research the best approach",
        )
        assert r is not None
        assert "context" in r
        assert "高复杂度" in r["context"]
