"""Context Engine 数据完整性回归测试。

尚未修复的缺陷继续使用 strict xfail：
- 当前缺陷存在时，测试记为 XFAIL，CI 可继续提供完整基线；
- 缺陷被修复后，用例会 XPASS 并使 CI 失败，提醒维护者移除 xfail 标记，
  将其转为永久回归测试。

已进入 canonical Work ID 修复的用例必须移除 xfail，先成为普通失败测试。
"""

from __future__ import annotations

import pytest

from deepseek_context import DeepSeekContextEngine


def _engine() -> DeepSeekContextEngine:
    return DeepSeekContextEngine(
        quiet_mode=True,
        protect_first_n=1,
        protect_last_n=1,
        context_length=10_000,
        threshold_percent=0.5,
    )


def _messages() -> list[dict]:
    return [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "head-user"},
        {"role": "assistant", "content": "middle-assistant"},
        {"role": "user", "content": "middle-user"},
        {"id": "tail-a-id", "role": "assistant", "content": "tail-a"},
        {"id": "tail-b-id", "role": "user", "content": "tail-b"},
    ]


def _fix_boundaries(monkeypatch: pytest.MonkeyPatch, engine: DeepSeekContextEngine) -> None:
    monkeypatch.setattr(
        engine._compressor,
        "prune_old_tool_results",
        lambda messages, **kwargs: (messages, 0),
    )
    # Force compress_start=2 and compress_end=4. With the message roles above,
    # the summary must merge into the first tail message, exercising _merge=True.
    monkeypatch.setattr(
        engine._compressor,
        "align_boundary_forward",
        lambda messages, start: 2,
    )
    monkeypatch.setattr(
        engine._compressor,
        "find_tail_cut_by_tokens",
        lambda messages, start, token_budget: 4,
    )
    monkeypatch.setattr(
        engine._compressor,
        "sanitize_tool_pairs",
        lambda messages: messages,
    )


def test_merge_path_does_not_duplicate_tail_messages(monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-CTX-003: every protected tail ID appears exactly once, in source order."""
    engine = _engine()
    _fix_boundaries(monkeypatch, engine)
    monkeypatch.setattr(engine._compressor, "generate_summary", lambda turns: "SUMMARY")

    result = engine.compress(_messages(), current_tokens=8_000)
    tail_ids = [message.get("id") for message in result if message.get("id")]
    contents = [message.get("content") for message in result]

    assert tail_ids == ["tail-a-id", "tail-b-id"]
    assert len(tail_ids) == len(set(tail_ids))
    assert sum("tail-a" in str(content) for content in contents) == 1
    assert sum("tail-b" in str(content) for content in contents) == 1


@pytest.mark.xfail(
    strict=True,
    reason="已知缺陷：摘要 API 失败时压缩区原始消息被静态占位文本替代",
)
def test_summary_failure_preserves_original_messages(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = _engine()
    _fix_boundaries(monkeypatch, engine)
    monkeypatch.setattr(engine._compressor, "generate_summary", lambda turns: None)

    messages = _messages()
    result = engine.compress(messages, current_tokens=8_000)

    assert result == messages


@pytest.mark.xfail(
    strict=True,
    reason="已知缺陷：受保护硬约束仍位于压缩切片内，不能保证逐字保留",
)
def test_hard_constraint_message_survives_verbatim(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = _engine()
    _fix_boundaries(monkeypatch, engine)
    monkeypatch.setattr(engine._compressor, "generate_summary", lambda turns: "SUMMARY")

    messages = _messages()
    constraint = "绝对不能删除生产数据库"
    messages[2] = {"role": "user", "content": constraint}

    result = engine.compress(messages, current_tokens=8_000)

    assert any(message.get("content") == constraint for message in result)
