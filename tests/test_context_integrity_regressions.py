"""Context Engine 数据完整性回归测试。

尚未修复的缺陷继续使用 strict xfail；进入 canonical Work ID 的缺陷必须先转为普通失败测试。
"""

from __future__ import annotations

import copy

import pytest

from deepseek_context import DeepSeekContextEngine
from deepseek_context._merge_integrity import remove_exact_duplicate_merge_tail


_MERGE_MARKER = (
    "\n\n--- END OF CONTEXT SUMMARY — "
    "respond to the message below, not the summary above ---\n\n"
)


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


def _assert_lossless_failure(
    monkeypatch: pytest.MonkeyPatch,
    engine: DeepSeekContextEngine,
    summary_behavior,
) -> None:
    _fix_boundaries(monkeypatch, engine)
    monkeypatch.setattr(engine._compressor, "generate_summary", summary_behavior)

    messages = _messages()
    snapshot = copy.deepcopy(messages)
    result = engine.compress(messages, current_tokens=8_000)

    assert result is messages
    assert result == snapshot
    assert messages == snapshot
    assert all("[Earlier context summary unavailable]" not in str(item) for item in result)


def _tool_pair_sets(messages: list[dict]) -> tuple[set[str], set[str]]:
    calls: set[str] = set()
    results: set[str] = set()
    for message in messages:
        if message.get("role") == "assistant":
            for call in message.get("tool_calls") or []:
                if isinstance(call, dict) and call.get("id"):
                    calls.add(call["id"])
        if message.get("role") == "tool" and message.get("tool_call_id"):
            results.add(message["tool_call_id"])
    return calls, results


def test_merge_path_does_not_duplicate_tail_messages(monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-CTX-003: every protected tail ID appears exactly once, in source order."""
    engine = _engine()
    _fix_boundaries(monkeypatch, engine)
    monkeypatch.setattr(engine._compressor, "generate_summary", lambda turns: "SUMMARY")

    result = engine.compress(_messages(), current_tokens=8_000)
    tail_ids = [
        message.get("id")
        for message in result
        if message.get("id") in {"tail-a-id", "tail-b-id"}
    ]
    contents = [message.get("content") for message in result]

    assert tail_ids == ["tail-a-id", "tail-b-id"]
    assert len(tail_ids) == len(set(tail_ids))
    assert sum("tail-a" in str(content) for content in contents) == 1
    assert sum("tail-b" in str(content) for content in contents) == 1


def test_exact_duplicate_merge_tail_guard_removes_only_second_sequence() -> None:
    merged_tail_a = {
        "id": "tail-a-id",
        "role": "assistant",
        "content": f"SUMMARY{_MERGE_MARKER}tail-a",
    }
    tail_b = {"id": "tail-b-id", "role": "user", "content": "tail-b"}
    duplicate_tail_a = {"id": "tail-a-id", "role": "assistant", "content": "tail-a"}
    messages = [
        {"role": "system", "content": "system"},
        merged_tail_a,
        tail_b,
        duplicate_tail_a,
        tail_b.copy(),
    ]

    result = remove_exact_duplicate_merge_tail(messages)
    assert result == messages[:3]


def test_exact_duplicate_merge_tail_guard_preserves_ordinary_repetition() -> None:
    repeated = {"id": "intentional-id", "role": "user", "content": "repeat this"}
    messages = [{"role": "system", "content": "system"}, repeated, repeated.copy()]
    result = remove_exact_duplicate_merge_tail(messages)
    assert result == messages
    assert result is messages


def test_exact_duplicate_merge_tail_guard_preserves_incomplete_sequence() -> None:
    messages = [
        {"role": "system", "content": "system"},
        {
            "id": "tail-a-id",
            "role": "assistant",
            "content": f"SUMMARY{_MERGE_MARKER}tail-a",
        },
        {"id": "tail-b-id", "role": "user", "content": "tail-b"},
        {"id": "tail-a-id", "role": "assistant", "content": "tail-a"},
    ]
    result = remove_exact_duplicate_merge_tail(messages)
    assert result == messages
    assert result is messages


def test_summary_timeout_preserves_original_messages(monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-CTX-004: provider timeout is a lossless no-op."""

    def timeout(_turns):
        raise TimeoutError("provider timeout")

    _assert_lossless_failure(monkeypatch, _engine(), timeout)


def test_summary_exception_preserves_original_messages_without_secret_leak(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """TC-CTX-005: provider exceptions do not alter context or expose payloads."""
    secret = "sk-test-summary-secret"
    prompt_fragment = "private prompt fragment"

    def provider_error(_turns):
        raise RuntimeError(f"provider echoed {secret}: {prompt_fragment}")

    _assert_lossless_failure(monkeypatch, _engine(), provider_error)
    assert secret not in caplog.text
    assert prompt_fragment not in caplog.text


@pytest.mark.parametrize("empty_summary", [None, "", "   "])
def test_empty_summary_preserves_original_messages(
    monkeypatch: pytest.MonkeyPatch,
    empty_summary: str | None,
) -> None:
    """TC-CTX-006: None, empty and whitespace-only summaries are failures."""
    _assert_lossless_failure(monkeypatch, _engine(), lambda _turns: empty_summary)


def test_missing_key_summary_failure_preserves_original_messages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-CTX-006: malformed provider responses remain lossless."""

    def missing_key(_turns):
        raise KeyError("choices")

    _assert_lossless_failure(monkeypatch, _engine(), missing_key)


def test_hard_constraint_message_survives_verbatim(monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-CTX-007: hard constraints survive verbatim with one stable ID."""
    engine = _engine()
    _fix_boundaries(monkeypatch, engine)
    monkeypatch.setattr(engine._compressor, "generate_summary", lambda turns: "SUMMARY")

    messages = _messages()
    constraint = "绝对不能删除生产数据库"
    messages[2] = {"id": "constraint-id", "role": "user", "content": constraint}

    result = engine.compress(messages, current_tokens=8_000)
    matches = [message for message in result if message.get("id") == "constraint-id"]

    assert len(matches) == 1
    assert matches[0]["content"] == constraint


def test_latest_user_request_survives_verbatim_once(monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-CTX-008: latest user request is byte-equivalent and appears once."""
    engine = _engine()
    _fix_boundaries(monkeypatch, engine)
    monkeypatch.setattr(engine._compressor, "generate_summary", lambda turns: "SUMMARY")

    messages = _messages()
    messages[-1] = {
        "id": "latest-user-id",
        "role": "user",
        "content": "latest user request",
    }
    result = engine.compress(messages, current_tokens=8_000)
    matches = [message for message in result if message.get("id") == "latest-user-id"]

    assert len(matches) == 1
    assert matches[0]["content"] == "latest user request"


def test_tool_call_result_pair_remains_legal(monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-CTX-009: protected Tool Call/Result pairs survive together exactly once."""
    engine = _engine()
    _fix_boundaries(monkeypatch, engine)
    monkeypatch.setattr(engine._compressor, "generate_summary", lambda turns: "SUMMARY")

    messages = _messages()
    messages[2] = {
        "id": "call-message-id",
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "id": "call-1",
                "type": "function",
                "function": {"name": "read_file", "arguments": '{"path":"a"}'},
            }
        ],
    }
    messages[3] = {
        "id": "result-message-id",
        "role": "tool",
        "tool_call_id": "call-1",
        "content": "result",
    }

    result = engine.compress(messages, current_tokens=8_000)
    calls, results = _tool_pair_sets(result)

    assert calls == {"call-1"}
    assert results == {"call-1"}
    assert sum(message.get("id") == "call-message-id" for message in result) == 1
    assert sum(message.get("id") == "result-message-id" for message in result) == 1


def test_generated_message_ids_are_stable_and_unique(monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-CTX-014: identical inputs produce stable unique message identities."""
    engine = _engine()
    _fix_boundaries(monkeypatch, engine)
    monkeypatch.setattr(engine._compressor, "generate_summary", lambda turns: "SUMMARY")
    messages = [{k: v for k, v in message.items() if k != "id"} for message in _messages()]

    first = engine.compress(copy.deepcopy(messages), current_tokens=8_000)
    second = engine.compress(copy.deepcopy(messages), current_tokens=8_000)
    first_ids = [message.get("id") for message in first]
    second_ids = [message.get("id") for message in second]

    assert all(isinstance(message_id, str) and message_id for message_id in first_ids)
    assert len(first_ids) == len(set(first_ids))
    assert first_ids == second_ids
