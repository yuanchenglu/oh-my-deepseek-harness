"""CTX-004 regressions for deterministic compression token accounting."""

from __future__ import annotations

import copy

import pytest

from deepseek_context import DeepSeekContextEngine
from deepseek_context.compressor import estimate_messages_tokens_rough


def test_generated_ids_cannot_create_false_token_reduction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Internal stable IDs cannot make a larger candidate look smaller."""
    engine = DeepSeekContextEngine(
        quiet_mode=True,
        protect_first_n=1,
        protect_last_n=1,
        context_length=10_000,
        threshold_percent=0.5,
    )
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
        lambda messages, start, token_budget: 7,
    )
    monkeypatch.setattr(
        engine._compressor,
        "generate_summary",
        lambda turns: "S",
    )
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
