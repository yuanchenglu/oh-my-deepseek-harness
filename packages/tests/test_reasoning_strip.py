"""reasoning_strip.py 单元测试 — 验证 I-14 reasoning 剥离逻辑。

测试 platform_core.reasoning_strip 中所有纯函数：
  - is_anthropic_model()
  - strip_reasoning_from_history()
  - estimate_tokens_saved()
"""

from platform_core.reasoning_strip import (
    is_anthropic_model,
    strip_reasoning_from_history,
    estimate_tokens_saved,
    ESTIMATED_TOKENS_PER_REASONING,
)


# ========= is_anthropic_model =========


class TestIsAnthropicModel:
    def test_claude_is_anthropic(self):
        assert is_anthropic_model("claude-sonnet-4-20250514") is True

    def test_anthropic_provider(self):
        assert is_anthropic_model("anthropic/claude-sonnet-4") is True

    def test_deepseek_is_not_anthropic(self):
        assert is_anthropic_model("deepseek/deepseek-chat") is False

    def test_openai_is_not_anthropic(self):
        assert is_anthropic_model("openai/gpt-4o") is False

    def test_empty_string_is_not_anthropic(self):
        assert is_anthropic_model("") is False

    def test_case_insensitive(self):
        assert is_anthropic_model("CLAUDE-OPUS") is True


# ========= strip_reasoning_from_history =========


class TestStripReasoningFromHistory:
    def test_deepseek_strips_reasoning(self):
        history = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello", "reasoning": "思考中..."},
        ]
        stripped, count = strip_reasoning_from_history(history, model="deepseek/deepseek-chat")
        assert count == 1
        assert "reasoning" not in stripped[1]

    def test_anthropic_keeps_reasoning(self):
        history = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello", "reasoning": "Claude thinking..."},
        ]
        stripped, count = strip_reasoning_from_history(history, model="claude-sonnet-4")
        assert count == 0
        assert "reasoning" in stripped[1]

    def test_no_reasoning_no_change(self):
        history = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello"},
        ]
        stripped, count = strip_reasoning_from_history(history, model="deepseek/deepseek-chat")
        assert count == 0
        assert stripped == history

    def test_mixed_roles_only_assistant_stripped(self):
        """只剥离 assistant 角色的 reasoning。"""
        history = [
            {"role": "system", "content": "Be helpful", "reasoning": "sys think"},
            {"role": "user", "content": "Hi", "reasoning": "user think"},
            {"role": "assistant", "content": "Hello", "reasoning": "思考中..."},
            {"role": "tool", "content": "result", "reasoning": "tool think"},
        ]
        stripped, count = strip_reasoning_from_history(history, model="deepseek/deepseek-chat")
        assert count == 1
        assert "reasoning" in stripped[0]
        assert "reasoning" in stripped[1]
        assert "reasoning" in stripped[3]
        assert "reasoning" not in stripped[2]

    def test_non_dict_messages_preserved(self):
        history = ["string_message", {"role": "user", "content": "hi"}]
        stripped, count = strip_reasoning_from_history(history, model="deepseek/deepseek-chat")
        assert count == 0
        assert len(stripped) == 2

    def test_empty_history(self):
        stripped, count = strip_reasoning_from_history([], model="deepseek/deepseek-chat")
        assert count == 0
        assert stripped == []

    def test_multiple_assistant_messages_all_stripped(self):
        history = [
            {"role": "assistant", "content": "A1", "reasoning": "r1"},
            {"role": "user", "content": "Q2"},
            {"role": "assistant", "content": "A2", "reasoning": "r2"},
        ]
        stripped, count = strip_reasoning_from_history(history, model="deepseek/deepseek-chat")
        assert count == 2
        for msg in stripped:
            if msg.get("content") in ("A1", "A2"):
                assert "reasoning" not in msg

    def test_does_not_mutate_original(self):
        """函数不修改原始消息列表。"""
        history = [
            {"role": "assistant", "content": "A1", "reasoning": "r1"},
        ]
        stripped, count = strip_reasoning_from_history(history, model="deepseek/deepseek-chat")
        assert "reasoning" in history[0]  # 原始未修改
        assert "reasoning" not in stripped[0]


# ========= estimate_tokens_saved =========


class TestEstimateTokensSaved:
    def test_zero_count(self):
        assert estimate_tokens_saved(0) == 0

    def test_positive_count(self):
        assert estimate_tokens_saved(3) == 3 * ESTIMATED_TOKENS_PER_REASONING

    def test_large_count(self):
        assert estimate_tokens_saved(100) == 100 * ESTIMATED_TOKENS_PER_REASONING
