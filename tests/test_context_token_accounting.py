"""CTX-004 regressions for deterministic compression token accounting."""

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


def _force_candidate(
    monkeypatch: pytest.MonkeyPatch,
    engine: DeepSeekContextEngine,
    compress_end: int,
    summary: str,
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


def test_generated_ids_cannot_create_false_token_reduction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Internal stable IDs cannot make a larger candidate look smaller."""
    engine = _engine()
    _force_candidate(monkeypatch, engine, compress_end=7, summary="S")
    messages = [
        {"role": "system", "content": "m0"},
        {"role": "user", "content": "m1"},
        {"role": "assistant", "content": "m2"},
        {"role": "user", "content": "m3"},
        {"role": "assistant", "content": "m4"},
        {"role": "user", "content": "m5"},
        {"role": "assistant", "content": "m6"},
        {"role": "user", "content": "m7"},
        {"role": "assistant", "content": "m8"},
    ]
    snapshot = copy.deepcopy(messages)
    deterministic_before = estimate_messages_tokens_rough(messages)

    result = engine.compress(messages, current_tokens=8_000)
    state = engine.get_session_summary_state(engine._DEFAULT_SESSION_ID)

    assert result is messages
    assert messages == snapshot
    assert engine.compression_count == 0
    assert state["last_before_tokens"] == deterministic_before
    assert state["last_after_tokens"] >= deterministic_before


def test_seeded_acceptance_always_reduces_actual_input_tokens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every accepted seeded candidate is smaller than the caller input."""
    rng = random.Random(20260729)

    for case in range(64):
        engine = _engine()
        message_count = rng.randint(8, 14)
        compress_end = rng.randint(4, message_count - 2)
        summary = "S" * rng.randint(1, 120)
        messages = [
            {
                "role": "system" if index == 0 else (
                    "user" if index % 2 else "assistant"
                ),
                "content": f"m{case}-{index}-" * rng.randint(1, 80),
            }
            for index in range(message_count)
        ]
        snapshot = copy.deepcopy(messages)
        deterministic_before = estimate_messages_tokens_rough(messages)
        _force_candidate(
            monkeypatch,
            engine,
            compress_end=compress_end,
            summary=summary,
        )

        result = engine.compress(messages, current_tokens=8_000)
        deterministic_after = estimate_messages_tokens_rough(result)
        state = engine.get_session_summary_state(engine._DEFAULT_SESSION_ID)

        assert messages == snapshot
        if result is messages:
            assert engine.compression_count == 0
            assert state["last_after_tokens"] >= state["last_before_tokens"]
        else:
            assert engine.compression_count == 1
            assert deterministic_after < deterministic_before
            assert state["last_before_tokens"] == deterministic_before
            assert state["last_after_tokens"] == deterministic_after
