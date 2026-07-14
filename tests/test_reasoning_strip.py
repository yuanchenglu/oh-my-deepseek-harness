"""reasoning_strip.py 单元测试 — 验证 I-14 reasoning 剥离逻辑。"""

from deepseek_harness.reasoning_strip import (
    strip_reasoning_from_history,
    on_pre_llm_call,
    _is_anthropic_model,
)


# ── _is_anthropic_model ─────────────────────────────────


class TestIsAnthropicModel:
    def test_claude_is_anthropic(self):
        assert _is_anthropic_model("claude-sonnet-4-20250514") is True

    def test_anthropic_provider(self):
        assert _is_anthropic_model("anthropic/claude-sonnet-4") is True

    def test_deepseek_is_not_anthropic(self):
        assert _is_anthropic_model("deepseek/deepseek-chat") is False

    def test_openai_is_not_anthropic(self):
        assert _is_anthropic_model("openai/gpt-4o") is False

    def test_empty_string_is_not_anthropic(self):
        assert _is_anthropic_model("") is False


# ── strip_reasoning_from_history ────────────────────────


class TestStripReasoningFromHistory:
    def test_deepseek_strips_reasoning(self):
        """DeepSeek 模型应剥离 assistant 消息的 reasoning 字段。"""
        history = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello", "reasoning": "思考中..."},
        ]
        stripped, count = strip_reasoning_from_history(history, model="deepseek/deepseek-chat")
        assert count == 1
        assert "reasoning" not in stripped[1]

    def test_anthropic_keeps_reasoning(self):
        """Anthropic 模型应保留 reasoning 字段。"""
        history = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello", "reasoning": "Claude thinking..."},
        ]
        stripped, count = strip_reasoning_from_history(history, model="claude-sonnet-4")
        assert count == 0
        assert "reasoning" in stripped[1]

    def test_no_reasoning_no_change(self):
        """消息没有 reasoning 字段时不改变任何内容。"""
        history = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello"},
        ]
        stripped, count = strip_reasoning_from_history(history, model="deepseek/deepseek-chat")
        assert count == 0
        assert stripped == history

    def test_mixed_roles_only_assistant_stripped(self):
        """只剥离 assistant 角色的 reasoning，不碰其他角色。"""
        history = [
            {"role": "system", "content": "Be helpful", "reasoning": "sys think"},
            {"role": "user", "content": "Hi", "reasoning": "user think"},
            {"role": "assistant", "content": "Hello", "reasoning": "思考中..."},
            {"role": "tool", "content": "result", "reasoning": "tool think"},
        ]
        stripped, count = strip_reasoning_from_history(history, model="deepseek/deepseek-chat")
        assert count == 1
        # system、user、tool 应保留 reasoning
        assert "reasoning" in stripped[0]
        assert "reasoning" in stripped[1]
        assert "reasoning" in stripped[3]
        # assistant 的 reasoning 应被剥离
        assert "reasoning" not in stripped[2]

    def test_non_dict_messages_preserved(self):
        """非 dict 的消息原样保留。"""
        history = ["string_message", {"role": "user", "content": "hi"}]
        stripped, count = strip_reasoning_from_history(history, model="deepseek/deepseek-chat")
        assert count == 0
        assert len(stripped) == 2

    def test_empty_history(self):
        stripped, count = strip_reasoning_from_history([], model="deepseek/deepseek-chat")
        assert count == 0
        assert stripped == []

    def test_multiple_assistant_messages_all_stripped(self):
        """多条 assistant 消息的 reasoning 全部被剥离。"""
        history = [
            {"role": "assistant", "content": "A1", "reasoning": "r1"},
            {"role": "user", "content": "Q2"},
            {"role": "assistant", "content": "A2", "reasoning": "r2"},
            {"role": "user", "content": "Q3"},
            {"role": "assistant", "content": "A3", "reasoning": "r3"},
        ]
        stripped, count = strip_reasoning_from_history(history, model="deepseek/deepseek-chat")
        assert count == 3
        for msg in stripped:
            if msg["content"] in ("A1", "A2", "A3"):
                assert "reasoning" not in msg


# ── on_pre_llm_call hook ────────────────────────────────


class TestOnPreLlmCall:
    def test_no_conversation_history_returns_none(self):
        r = on_pre_llm_call(is_first_turn=True)
        assert r is None

    def test_with_history_strip_returns_none(self):
        """on_pre_llm_call 应返回 None（不注入 context），
        但原地修改 conversation_history。"""
        history = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello", "reasoning": "think..."},
        ]
        kwargs = {
            "conversation_history": history,
            "model": "deepseek/deepseek-chat",
        }
        r = on_pre_llm_call(**kwargs)
        assert r is None  # 不注入 context
        # 原地修改了 history
        assert "reasoning" not in kwargs["conversation_history"][1]
