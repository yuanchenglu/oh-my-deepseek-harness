"""Platform-context compression toolkit.

Provides:

*   :class:`PlatformContext` — abstract interface that platform providers
    (Hermes, OpenCode, Claude Code, …) implement to expose their message
    list and system prompt for context compression.

*   :func:`compress_messages` — pure-function compression pipeline
    (orchestrates pruning, boundary detection, summary insertion, and
    tool-pair repair).  A caller provides an optional LLM summariser
    callback; otherwise a static fallback is used.

*   A full suite of atomic compression algorithms exported from
    :mod:`.compressor`.

Usage::

    from platform_core.context import (
        PlatformContext,
        compress_messages,
        prune_old_tool_results,
        sanitize_tool_pairs,
        estimate_messages_tokens_rough,
    )

    # Pure algos — bring your own messages
    pruned, count = prune_old_tool_results(messages, protect_tail_count=10)

    # Full pipeline — drop in any platform
    compressed = compress_messages(
        messages,
        threshold_tokens=96_000,
        tail_token_budget=20_000,
        summarizer=my_llm_caller,  # optional
    )

    # Implement the ABC
    class MyPlatformContext(PlatformContext):
        def get_messages(self): ...
        def get_system_prompt(self): ...
        def compress(self, messages, **kw): ...
        def get_hard_constraints(self): ...
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from . import config as config
from .compressor import (
    # ── Constants ──────────────────────────────────────────────────────
    SUMMARY_PREFIX,
    # ── Pure-function helpers ──────────────────────────────────────────
    estimate_messages_tokens_rough,
    summarize_tool_result,
    # ── Boundary alignment ─────────────────────────────────────────────
    align_boundary_forward,
    align_boundary_backward,
    get_tool_call_id,
    # ── Pruning / sanitisation ─────────────────────────────────────────
    prune_old_tool_results,
    find_tail_cut_by_tokens,
    sanitize_tool_pairs,
    # ── Serialization ──────────────────────────────────────────────────
    serialize_for_summary,
    compute_summary_budget,
    with_summary_prefix,
    # ── I-03 / I-04 hard constraints ───────────────────────────────────
    contains_hard_constraint,
    protect_hard_constraints,
    extract_hard_constraints,
    inject_constraint_prefix,
    HARD_CONSTRAINT_KEYWORDS,
    # ── I-13 prefix freeze ─────────────────────────────────────────────
    PrefixState,
    freeze_prefix,
    is_prefix_stable,
    compose_turn_tail,
    # ── I-03 intent awareness ──────────────────────────────────────────
    compute_effective_ratio,
    compute_intent_protection,
    # ── I-07 review depth ──────────────────────────────────────────────
    nominal_review_depth,
    get_review_depth,
    # ── Pipeline ───────────────────────────────────────────────────────
    compress_messages,
    SummarizerFn,
    make_static_fallback_summary,
)

__all__ = [
    # ABC
    "PlatformContext",
    # Config
    "config",
    # Constants
    "SUMMARY_PREFIX",
    "HARD_CONSTRAINT_KEYWORDS",
    # Pure helpers
    "estimate_messages_tokens_rough",
    "summarize_tool_result",
    # Boundary alignment
    "align_boundary_forward",
    "align_boundary_backward",
    "get_tool_call_id",
    # Pruning / sanitisation
    "prune_old_tool_results",
    "find_tail_cut_by_tokens",
    "sanitize_tool_pairs",
    # Serialization
    "serialize_for_summary",
    "compute_summary_budget",
    "with_summary_prefix",
    # I-03 / I-04 hard constraints
    "contains_hard_constraint",
    "protect_hard_constraints",
    "extract_hard_constraints",
    "inject_constraint_prefix",
    # I-13 prefix freeze
    "PrefixState",
    "freeze_prefix",
    "is_prefix_stable",
    "compose_turn_tail",
    # I-03 intent awareness
    "compute_effective_ratio",
    "compute_intent_protection",
    # I-07 review depth
    "nominal_review_depth",
    "get_review_depth",
    # Pipeline
    "compress_messages",
    "SummarizerFn",
    "make_static_fallback_summary",
]


class PlatformContext(ABC):
    """Abstract interface for platform context providers.

    Each platform (Hermes, OpenCode, Claude Code, …) implements this ABC
    to expose its conversation state for context compression, independent
    of how the platform stores or manages messages internally.

    Method overview
    ---------------
    *   :meth:`get_messages` — return the current conversation message
        list (as standard OpenAI-format dicts).

    *   :meth:`get_system_prompt` — return the active system prompt
        string (used for prefix-freeze fingerprinting under I-13).

    *   :meth:`compress` — compress the conversation, returning the
        compressed message list.  The default implementation calls the
        pure-function :func:`compress_messages` pipeline with intent and
        constraint awareness.

    *   :meth:`get_hard_constraints` — return any hard constraints
        (I-03/I-04) extracted from the system prompt or earlier messages.
    """

    @abstractmethod
    def get_messages(self) -> List[Dict[str, Any]]:
        """Return the current message list (OpenAI-format dicts)."""
        ...

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the current system prompt string."""
        ...

    @abstractmethod
    def compress(
        self,
        messages: Optional[List[Dict[str, Any]]] = None,
        *,
        intent: str = "default",
        summarizer: Optional[SummarizerFn] = None,
        quiet: bool = False,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Compress *messages* (or ``self.get_messages()`` if omitted).

        Args:
            messages: Messages to compress.  Defaults to ``self.get_messages()``.
            intent: Intent label for I-03 differentiated compression.
            summarizer: Optional LLM summariser callback.  When omitted a
                        static fallback is used.
            quiet: Suppress info-level logging.
            **kwargs: Passed through to :func:`compress_messages`.

        Returns:
            Compressed message list.
        """
        ...

    @abstractmethod
    def get_hard_constraints(self) -> List[str]:
        """Return extracted hard-constraint sentences (I-03/I-04).

        Returns:
            Deduplicated list of constraint descriptions.
        """
        ...


# ── Default no-op implementation sketch ─────────────────────────────────────


class NullPlatformContext(PlatformContext):
    """Trivial PlatformContext — returns empty / unchanged data.

    Useful as a default placeholder when no real platform has been wired.
    """

    def __init__(self) -> None:
        self._messages: List[Dict[str, Any]] = []
        self._system_prompt: str = ""

    def get_messages(self) -> List[Dict[str, Any]]:
        return self._messages

    def get_system_prompt(self) -> str:
        return self._system_prompt

    def compress(
        self,
        messages: Optional[List[Dict[str, Any]]] = None,
        *,
        intent: str = "default",
        summarizer: Optional[SummarizerFn] = None,
        quiet: bool = False,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        msgs = messages if messages is not None else self._messages
        if not msgs:
            return msgs
        return compress_messages(
            msgs,
            threshold_tokens=kwargs.pop("threshold_tokens", 96_000),
            tail_token_budget=kwargs.pop("tail_token_budget", 20_000),
            max_summary_tokens=kwargs.pop("max_summary_tokens", 8_000),
            protect_first_n=kwargs.pop("protect_first_n", 3),
            protect_last_n=kwargs.pop("protect_last_n", 20),
            intent=intent,
            summarizer=summarizer,
            quiet=quiet,
            **kwargs,
        )

    def get_hard_constraints(self) -> List[str]:
        return extract_hard_constraints(self._messages)
