"""latest_reminder.py 单元测试 — 验证 I-18 时效信息注入逻辑。"""

from datetime import datetime

from deepseek_harness.latest_reminder import on_pre_llm_call, _build_reminder_text


class TestBuildReminderText:
    def test_reminder_contains_date(self):
        """时效信息应包含中文时间标记。"""
        text = _build_reminder_text()
        assert "[I-18 时效信息]" in text
        assert "当前时间:" in text

    def test_context_contains_current_year(self):
        """context 应包含当前年份（2026）。"""
        text = _build_reminder_text()
        assert "2026年" in text

    def test_time_format_is_valid(self):
        """验证 strftime 格式正确。"""
        text = _build_reminder_text()
        now = datetime.now()
        expected_year = str(now.year)
        assert expected_year in text


class TestOnPreLlmCall:
    def test_first_turn_returns_context(self):
        """首轮应返回含时效信息的 context。"""
        r = on_pre_llm_call(is_first_turn=True)
        assert r is not None
        assert "context" in r
        assert "[I-18 时效信息]" in r["context"]

    def test_non_first_turn_returns_none(self):
        """非首轮应返回 None。"""
        r = on_pre_llm_call(is_first_turn=False)
        assert r is None

    def test_empty_kwargs_non_first_defaults_to_none(self):
        """is_first_turn 默认为 False，应返回 None。"""
        r = on_pre_llm_call()
        assert r is None

    def test_context_not_injected_on_subsequent_turns(self):
        """确认非首轮不注入。"""
        r1 = on_pre_llm_call(is_first_turn=True)
        r2 = on_pre_llm_call(is_first_turn=False)
        r3 = on_pre_llm_call(is_first_turn=False)
        assert r1 is not None
        assert r2 is None
        assert r3 is None
