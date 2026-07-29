"""Deterministic property and transaction tests for Context integrity."""

from __future__ import annotations

import copy
import random

import pytest

from deepseek_context import DeepSeekContextEngine
from deepseek_context.compressor import estimate_messages_tokens_rough


def _engine() -> DeepSeekContextEngine:
    return DeepSeekContextEngine(
        quiet_mode=True,
        protect_first_n=1,
        protect_last_n=1,
        context_length=10_000,
        threshold_percent=0.5,
    )


def _force_compression(
    monkeypatch: pytest.MonkeyPatch,
    engine: DeepSeekContextEngine,
    compress_end: int,
    summary: str = "SUMMARY",
) -> None:
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
        lambda messages, start, token_budget: compress_end,
    )
    monkeypatch.setattr(
        engine._compressor,
        "generate_summary",
        lambda turns: summary,
    )


def _transaction_messages() -> list[dict]:
    return [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "head"},
        {"role": "assistant", "content": "A" * 1200},
        {"role": "user", "content": "B" * 1200},
        {"role": "assistant", "content": "C" * 1200},
        {"role": "user", "content": "D" * 1200},
        {"role": "assistant", "content": "tail"},
        {"role": "user", "content": "latest request"},
    ]


def _pair_sets(messages: list[dict]) -> tuple[set[str], set[str]]:
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


def test_random_message_sequences_preserve_integrity(monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-CTX-014: 64 seeded sequences satisfy all protected-message invariants."""
    rng = random.Random(20260729)
    counterexamples: list[dict] = []

    for case in range(64):
        engine = _engine()
        messages: list[dict] = [
            {"role": "system", "content": f"system-{case}"},
            {"role": "user", "content": f"head-{case}"},
            {"role": "assistant", "content": f"middle-a-{case}"},
            {"role": "user", "content": f"middle-u-{case}"},
            {"role": "assistant", "content": f"middle-b-{case}"},
            {"role": "user", "content": f"middle-v-{case}"},
            {"role": "assistant", "content": f"tail-a-{case}"},
            {"role": "user", "content": f"latest-{case}"},
        ]

        include_tool_pair = rng.choice([True, False])
        if include_tool_pair:
            messages[4] = {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": f"call-{case}",
                        "type": "function",
                        "function": {"name": "read_file", "arguments": "{}"},
                    }
                ],
            }
            messages[5] = {
                "role": "tool",
                "tool_call_id": f"call-{case}",
                "content": f"result-{case}",
            }

        constraint_candidates = [2, 3] if include_tool_pair else [2, 3, 4, 5]
        constraint_index = rng.choice(constraint_candidates)
        constraint_content = f"必须保留约束-{case}"
        messages[constraint_index] = {"role": "user", "content": constraint_content}
        messages[-1] = {"role": "user", "content": f"latest-{case}"}

        _force_compression(monkeypatch, engine, compress_end=6)
        original = copy.deepcopy(messages)
        result = engine.compress(messages, current_tokens=8_000)

        ids = [message.get("id") for message in result]
        constraints = [
            message for message in result if message.get("content") == constraint_content
        ]
        latest = [
            message for message in result if message.get("content") == f"latest-{case}"
        ]
        calls, results = _pair_sets(result)

        valid = (
            all(isinstance(message_id, str) and message_id for message_id in ids)
            and len(ids) == len(set(ids))
            and len(constraints) == 1
            and len(latest) == 1
            and calls == results
            and messages == original
        )
        if not valid:
            counterexamples.append(
                {
                    "case": case,
                    "input": original,
                    "output": result,
                    "ids": ids,
                    "calls": sorted(calls),
                    "results": sorted(results),
                }
            )

    assert counterexamples == []


def test_below_threshold_is_exact_noop() -> None:
    """TC-CTX-001: below-threshold compression returns the original list."""
    engine = _engine()
    messages = _transaction_messages()
    snapshot = copy.deepcopy(messages)

    result = engine.compress(messages, current_tokens=engine.threshold_tokens - 1)

    assert result is messages
    assert messages == snapshot
    assert engine.compression_count == 0


def test_successful_compression_reduces_deterministic_tokens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-CTX-002: accepted compression strictly reduces estimated tokens."""
    engine = _engine()
    _force_compression(monkeypatch, engine, compress_end=6, summary="short summary")
    messages = _transaction_messages()
    snapshot = copy.deepcopy(messages)
    before = estimate_messages_tokens_rough(messages)

    result = engine.compress(messages, current_tokens=8_000)
    after = estimate_messages_tokens_rough(result)

    assert result is not messages
    assert after < before
    assert messages == snapshot
    assert engine.compression_count == 1


def test_non_reducing_candidate_rolls_back_exactly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-CTX-011: a candidate that does not reduce tokens is rejected."""
    engine = _engine()
    _force_compression(monkeypatch, engine, compress_end=6, summary="Z" * 20_000)
    messages = _transaction_messages()
    snapshot = copy.deepcopy(messages)

    result = engine.compress(messages, current_tokens=8_000)

    assert result is messages
    assert messages == snapshot
    assert engine.compression_count == 0


def test_successful_compression_never_mutates_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-CTX-012: successful candidate construction is input-immutable."""
    engine = _engine()
    _force_compression(monkeypatch, engine, compress_end=6, summary="summary")
    messages = _transaction_messages()
    snapshot = copy.deepcopy(messages)

    engine.compress(messages, current_tokens=8_000)

    assert messages == snapshot


def test_summary_state_is_isolated_by_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-CTX-013: synthetic sessions have independent compression state."""
    engine = _engine()
    _force_compression(monkeypatch, engine, compress_end=6, summary="summary")

    engine.on_session_start("session-a")
    engine.compress(_transaction_messages(), current_tokens=8_000)
    state_a = engine.get_session_summary_state("session-a")

    engine.on_session_start("session-b")
    state_b_before = engine.get_session_summary_state("session-b")
    engine.compress(_transaction_messages(), current_tokens=8_000)
    state_b_after = engine.get_session_summary_state("session-b")
    state_a_after = engine.get_session_summary_state("session-a")

    assert state_a["compression_count"] == 1
    assert state_b_before["compression_count"] == 0
    assert state_b_after["compression_count"] == 1
    assert state_a_after == state_a
    assert state_a["last_after_tokens"] < state_a["last_before_tokens"]
    assert state_b_after["last_after_tokens"] < state_b_after["last_before_tokens"]
