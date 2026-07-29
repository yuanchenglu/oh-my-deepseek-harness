"""Public Context Engine with transactional message-integrity enforcement."""

from __future__ import annotations

import copy
from contextvars import ContextVar
from threading import RLock
from typing import Any, Dict, List

from ._engine import DeepSeekContextEngine as _BaseDeepSeekContextEngine
from ._merge_integrity import remove_exact_duplicate_merge_tail
from ._message_integrity import (
    assign_stable_message_ids,
    classify_protected_message_ids,
    reconcile_protected_messages,
)
from .compressor import estimate_messages_tokens_rough


class DeepSeekContextEngine(_BaseDeepSeekContextEngine):
    """Canonical exported engine with lossless transactional safeguards."""

    _DEFAULT_SESSION_ID = "__default__"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._summary_failure_lock = RLock()
        self._summary_state_lock = RLock()
        self._active_summary_session: ContextVar[str] = ContextVar(
            f"deepseek_context_session_{id(self)}",
            default=self._DEFAULT_SESSION_ID,
        )
        self._session_summary_states: dict[str, dict[str, int]] = {
            self._DEFAULT_SESSION_ID: self._new_summary_state()
        }

    @staticmethod
    def _new_summary_state() -> dict[str, int]:
        return {
            "compression_count": 0,
            "rollback_count": 0,
            "last_before_tokens": 0,
            "last_after_tokens": 0,
        }

    def _summary_state(self, session_id: str | None = None) -> dict[str, int]:
        resolved = session_id or self._active_summary_session.get()
        with self._summary_state_lock:
            return self._session_summary_states.setdefault(
                resolved,
                self._new_summary_state(),
            )

    def get_session_summary_state(self, session_id: str) -> dict[str, int]:
        """Return a copy of non-content compression metrics for one Session."""
        with self._summary_state_lock:
            state = self._session_summary_states.get(session_id)
            return dict(state or self._new_summary_state())

    def on_session_start(self, session_id: str, **kwargs: Any) -> None:
        """Activate an isolated summary-metrics scope for the current context."""
        self._active_summary_session.set(str(session_id))
        state = self._summary_state(str(session_id))
        self.compression_count = state["compression_count"]
        try:
            super().on_session_start(session_id, **kwargs)
        except AttributeError:
            # The import-only Hermes test fallback does not define lifecycle hooks.
            pass

    def on_session_end(self, session_id: str, **kwargs: Any) -> None:
        """Detach the current context without exposing another Session's state."""
        try:
            super().on_session_end(session_id, **kwargs)
        except AttributeError:
            pass
        if self._active_summary_session.get() == str(session_id):
            self._active_summary_session.set(self._DEFAULT_SESSION_ID)
            default_state = self._summary_state(self._DEFAULT_SESSION_ID)
            self.compression_count = default_state["compression_count"]

    def compress(
        self,
        messages: List[Dict[str, Any]],
        current_tokens: int | None = None,
    ) -> List[Dict[str, Any]]:
        threshold_tokens = (
            current_tokens
            if current_tokens is not None
            else self.last_prompt_tokens
            or estimate_messages_tokens_rough(messages)
        )
        if threshold_tokens < self.threshold_tokens:
            return messages

        identified_messages = assign_stable_message_ids(messages)
        before_tokens = estimate_messages_tokens_rough(identified_messages)
        protected_ids = classify_protected_message_ids(
            identified_messages,
            self._contains_hard_constraint,
        )

        original_generate_summary = self._compressor.generate_summary
        summary_failed = False
        session_id = self._active_summary_session.get()
        state = self._summary_state(session_id)

        def guarded_generate_summary(turns: List[Dict[str, Any]]) -> str | None:
            nonlocal summary_failed
            try:
                summary = original_generate_summary(turns)
            except Exception:
                summary_failed = True
                return None
            if not isinstance(summary, str) or not summary.strip():
                summary_failed = True
                return None
            return summary

        # Base compression mutates only engine metrics and its candidate copy.
        # Serialize the transaction so the temporary summary wrapper and the
        # session-local counter cannot leak across concurrent callers.
        with self._summary_failure_lock:
            prior_count = state["compression_count"]
            self.compression_count = prior_count
            self._compressor.generate_summary = guarded_generate_summary
            try:
                compressed = super().compress(
                    copy.deepcopy(identified_messages),
                    current_tokens=current_tokens,
                )
            finally:
                self._compressor.generate_summary = original_generate_summary

            if summary_failed:
                self.compression_count = prior_count
                return messages

            compressed = remove_exact_duplicate_merge_tail(compressed)
            candidate = reconcile_protected_messages(
                identified_messages,
                compressed,
                protected_ids,
            )
            after_tokens = estimate_messages_tokens_rough(candidate)

            if after_tokens >= before_tokens:
                with self._summary_state_lock:
                    state["rollback_count"] += 1
                    state["last_before_tokens"] = before_tokens
                    state["last_after_tokens"] = after_tokens
                self.compression_count = prior_count
                return messages

            with self._summary_state_lock:
                state["compression_count"] = prior_count + 1
                state["last_before_tokens"] = before_tokens
                state["last_after_tokens"] = after_tokens
            self.compression_count = state["compression_count"]
            return candidate
