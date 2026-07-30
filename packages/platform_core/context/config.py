"""Compression strategy configuration — extracted from plugins/deepseek-context/config.yaml.

All values are plain Python constants / dataclasses.  No YAML parser needed at
runtime — this module IS the source of truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ── Intent types ────────────────────────────────────────────────────────────

INTENT_DEFAULT: str = "default"
INTENT_CONVERGENT: str = "convergent"
INTENT_DIVERGENT: str = "divergent"
VALID_INTENTS: tuple[str, ...] = (INTENT_DEFAULT, INTENT_CONVERGENT, INTENT_DIVERGENT)


# ── Compression thresholds (I-03 budget) ───────────────────────────────────

# Default compression trigger: prompt tokens > context_length * threshold_percent
DEFAULT_THRESHOLD_PERCENT: float = 0.75

# Protected head/tail message counts (intent-aware may override)
DEFAULT_PROTECT_FIRST_N: int = 3
DEFAULT_PROTECT_LAST_N: int = 20

# Summary token budget ratio (relative to threshold_tokens, used for "default" intent)
DEFAULT_SUMMARY_TARGET_RATIO: float = 0.20

# I-03: 收敛任务 — 保留更多上下文
CONVERGENT_TARGET_RATIO: float = 0.40

# I-03: 发散任务 — 压缩更多
DIVERGENT_TARGET_RATIO: float = 0.25

# Tail protection soft ceiling multiplier (applied to token budget)
TAIL_BUDGET_SOFT_CEILING_MULTIPLIER: float = 1.5


# ── Summary limits ──────────────────────────────────────────────────────────

SUMMARY_TOKENS_CEILING: int = 12_000
MIN_SUMMARY_TOKENS: int = 2_000
SUMMARY_RATIO: float = 0.20
SUMMARY_FAILURE_COOLDOWN_SECONDS: int = 600

# Chars-per-token estimate (conservative, for CJK-heavy content)
CHARS_PER_TOKEN: int = 4


# ── Context length defaults ────────────────────────────────────────────────

DEFAULT_CONTEXT_LENGTH: int = 128_000


# ── I-07 review depth switching ────────────────────────────────────────────

HYSTERESIS_THRESHOLD: float = 0.10
PLAN_COMPLEXITY_DEFAULT: float = 3.0


# ── Prefix freeze (I-13) ───────────────────────────────────────────────────

PREFIX_FROZEN_MARKER: str = "platform_context"


# ── Intent-aware compression config ────────────────────────────────────────


@dataclass
class IntentConfig:
    """Intent-aware differentiated compression ratios."""

    default_ratio: float = DEFAULT_SUMMARY_TARGET_RATIO
    convergent_ratio: float = CONVERGENT_TARGET_RATIO
    divergent_ratio: float = DIVERGENT_TARGET_RATIO
    protect_first_n: int = DEFAULT_PROTECT_FIRST_N  # base value
    protect_last_n: int = DEFAULT_PROTECT_LAST_N  # base value


@dataclass
class CompressionConfig:
    """Top-level compression configuration."""

    threshold_percent: float = DEFAULT_THRESHOLD_PERCENT
    protect_first_n: int = DEFAULT_PROTECT_FIRST_N
    protect_last_n: int = DEFAULT_PROTECT_LAST_N
    summary_ratio: float = DEFAULT_SUMMARY_TARGET_RATIO
    max_summary_tokens: int = SUMMARY_TOKENS_CEILING
    context_length: int = DEFAULT_CONTEXT_LENGTH
    quiet: bool = False

    intent: IntentConfig = field(default_factory=IntentConfig)
