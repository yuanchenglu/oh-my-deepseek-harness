"""latest_reminder.py 单元测试 — 验证 I-18 时效信息注入逻辑。"""

from deepseek_harness.latest_reminder import on_pre_llm_call, _build_reminder_text


class TestBuildReminderText:
    def test_reminder_contains_date(self):
        """时效信息应包含当前日期。"""
        text = _build_reminder_text()
        assert "[I-18]" in text
        assert "Current time:" in text


class TestOnPreLlmCall:
    def test_first_turn_returns_context(self):
        """首轮应返回含时效信息的 context。"""
        r = on_pre_llm_call(is_first_turn=True)
        assert r is not None
        assert "context" in r
        assert "[I-18]" in r["context"]

    def test_non_first_turn_returns_none(self):
        """非首轮应返回 None。"""
        r = on_pre_llm_call(is_first_turn=False)
        assert r is None

    def test_empty_kwargs_non_first_defaults_to_none(self):
        """is_first_turn 默认为 False，应返回 None。"""
        r = on_pre_llm_call()
        assert r is None
