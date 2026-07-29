"""Deterministic property-style tests for CTX-003 message integrity."""

from __future__ import annotations

import copy
import random

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


def _force_compression(
    monkeypatch: pytest.MonkeyPatch,
    engine: DeepSeekContextEngine,
    compress_end: int,
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
    monkeypatch.setattr(engine._compressor, "generate_summary", lambda turns: "SUMMARY")


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
