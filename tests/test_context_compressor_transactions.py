"""CTX-004 regressions for compressor transaction state."""

from __future__ import annotations

import time

import pytest

from deepseek_context import DeepSeekContextEngine


def _messages() -> list[dict]:
    return [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "head"},
        {"role": "assistant", "content": "A" * 1200},
        {"role": "user", "content": "B" * 1200},
        {"role": "assistant", "content": "C" * 1200},
        {"role": "user", "content": "D" * 1200},
        {"role": "assistant", "content": "tail"},
        {"role": "user", "content": "latest"},
    ]


def test_real_provider_failure_commits_only_session_cooldown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Provider failure rolls back candidate state but retains anti-thrashing."""
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
        lambda messages, start, token_budget: 6,
    )

    calls = 0

    def failing_provider(
        prompt: str,
        max_tokens: int,
        model: str | None = None,
    ) -> None:
        nonlocal calls
        calls += 1
        return None

    monkeypatch.setattr(engine._compressor, "_call_deepseek_llm", failing_provider)
    engine.on_session_start("session-a")
    engine._compressor._previous_summary = "committed-old"
    engine._compressor._ineffective_compression_count = 7
    messages = _messages()

    first = engine.compress(messages, current_tokens=8_000)
    cooldown = engine._compressor._summary_failure_cooldown_until
    second = engine.compress(messages, current_tokens=8_000)

    assert first is messages
    assert second is messages
    assert calls == 1
    assert cooldown > time.monotonic()
    assert engine._compressor._summary_failure_cooldown_until == cooldown
    assert engine._compressor._previous_summary == "committed-old"
    assert engine._compressor._ineffective_compression_count == 7
    assert engine.compression_count == 0
