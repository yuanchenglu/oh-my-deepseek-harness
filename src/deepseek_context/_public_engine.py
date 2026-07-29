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
    _COMPRESSOR_TRANSACTION_FIELDS = (
        "_previous_summary",
        "_ineffective_compression_count",
        "_summary_failure_cooldown_until",
    )

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
        self._initial_compressor_state = self._snapshot_compressor_state()
        self._session_compressor_states: dict[str, dict[str, Any]] = {
            self._DEFAULT_SESSION_ID: copy.deepcopy(self._initial_compressor_state)
        }
        self._loaded_compressor_session = self._DEFAULT_SESSION_ID

    @staticmethod
    def _new_summary_state() -> dict[str, int]:
        return {
            "compression_count": 0,
            "rollback_count": 0,
            "last_before_tokens": 0,
            "last_after_tokens": 0,
        }

    def _summary_state(self, session_id: str | None = None) -> dict[str, int]:
        resolved = (
            self._active_summary_session.get()
            if session_id is None
            else str(session_id)
        )
        with self._summary_state_lock:
            return self._session_summary_states.setdefault(
                resolved,
                self._new_summary_state(),
            )

    def _snapshot_compressor_state(self) -> dict[str, Any]:
        """Snapshot every mutable summary-transaction field in the compressor."""
        return {
            field: copy.deepcopy(getattr(self._compressor, field))
            for field in self._COMPRESSOR_TRANSACTION_FIELDS
        }

    def _restore_compressor_state(self, snapshot: dict[str, Any]) -> None:
        """Restore an exact compressor transaction snapshot."""
        for field in self._COMPRESSOR_TRANSACTION_FIELDS:
            setattr(self._compressor, field, copy.deepcopy(snapshot[field]))

    def _activate_compressor_session(self, session_id: str) -> None:
        """Persist the loaded Session and restore the target Session atomically."""
        resolved = str(session_id)
        if resolved == self._loaded_compressor_session:
            return
        self._session_compressor_states[
            self._loaded_compressor_session
        ] = self._snapshot_compressor_state()
        target = self._session_compressor_states.setdefault(
            resolved,
            copy.deepcopy(self._initial_compressor_state),
        )
        self._restore_compressor_state(target)
        self._loaded_compressor_session = resolved

    def _commit_compressor_session(self, session_id: str) -> None:
        resolved = str(session_id)
        self._session_compressor_states[resolved] = self._snapshot_compressor_state()
        self._loaded_compressor_session = resolved

    def _record_rollback(
        self,
        state: dict[str, int],
        before_tokens: int,
        after_tokens: int,
    ) -> None:
        with self._summary_state_lock:
            state["rollback_count"] += 1
            state["last_before_tokens"] = before_tokens
            state["last_after_tokens"] = after_tokens

    def get_session_summary_state(self, session_id: str) -> dict[str, int]:
        """Return a copy of non-content compression metrics for one Session."""
        with self._summary_state_lock:
            state = self._session_summary_states.get(session_id)
            return dict(state or self._new_summary_state())

    def on_session_start(self, session_id: str, **kwargs: Any) -> None:
        """Activate isolated metrics and compressor state for this context."""
        resolved = str(session_id)
        self._active_summary_session.set(resolved)
        with self._summary_failure_lock:
            self._activate_compressor_session(resolved)
            state = self._summary_state(resolved)
            self.compression_count = state["compression_count"]
        try:
            super().on_session_start(session_id, **kwargs)
        except AttributeError:
            pass

    def on_session_end(self, session_id: str, **kwargs: Any) -> None:
        """Detach the ContextVar without overwriting another Session's state."""
        try:
            super().on_session_end(session_id, **kwargs)
        except AttributeError:
            pass
        if self._active_summary_session.get() == str(session_id):
            self._active_summary_session.set(self._DEFAULT_SESSION_ID)

    def compress(
        self,
        messages: List[Dict[str, Any]],
        current_tokens: int | None = None,
    ) -> List[Dict[str, Any]]:
        # Provider/current tokens decide whether compression is attempted only.
        threshold_tokens = (
            current_tokens
            if current_tokens is not None
            else self.last_prompt_tokens
            or estimate_messages_tokens_rough(messages)
        )
        if threshold_tokens < self.threshold_tokens:
            return messages

        identified_messages = assign_stable_message_ids(messages)
        # Acceptance always compares one deterministic estimator on both sides.
        deterministic_before_tokens = estimate_messages_tokens_rough(
            identified_messages
        )
        protected_ids = classify_protected_message_ids(
            identified_messages,
            self._contains_hard_constraint,
        )
        session_id = self._active_summary_session.get()

        with self._summary_failure_lock:
            self._activate_compressor_session(session_id)
            state = self._summary_state(session_id)
            prior_count = state["compression_count"]
            self.compression_count = prior_count
            transaction_state = self._snapshot_compressor_state()

            original_generate_summary = self._compressor.generate_summary
            had_instance_override = "generate_summary" in vars(self._compressor)
            instance_override = vars(self._compressor).get("generate_summary")
            summary_failed = False

            def guarded_generate_summary(
                turns: List[Dict[str, Any]],
            ) -> str | None:
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

            self._compressor.generate_summary = guarded_generate_summary
            try:
                compressed = super().compress(
                    copy.deepcopy(identified_messages),
                    current_tokens=current_tokens,
                )
            except Exception:
                # Unexpected engine defects must stay observable after state rollback.
                self._restore_compressor_state(transaction_state)
                self._commit_compressor_session(session_id)
                self.compression_count = prior_count
                raise
            finally:
                if had_instance_override:
                    self._compressor.generate_summary = instance_override
                else:
                    delattr(self._compressor, "generate_summary")

            if summary_failed:
                self._restore_compressor_state(transaction_state)
                self._commit_compressor_session(session_id)
                self.compression_count = prior_count
                self._record_rollback(
                    state,
                    deterministic_before_tokens,
                    deterministic_before_tokens,
                )
                return messages

            try:
                compressed = remove_exact_duplicate_merge_tail(compressed)
                candidate = reconcile_protected_messages(
                    identified_messages,
                    compressed,
                    protected_ids,
                )
                deterministic_after_tokens = estimate_messages_tokens_rough(
                    candidate
                )
            except Exception:
                # Integrity implementation defects are not valid lossless fallbacks.
                self._restore_compressor_state(transaction_state)
                self._commit_compressor_session(session_id)
                self.compression_count = prior_count
                raise

            if deterministic_after_tokens >= deterministic_before_tokens:
                self._restore_compressor_state(transaction_state)
                self._commit_compressor_session(session_id)
                self.compression_count = prior_count
                self._record_rollback(
                    state,
                    deterministic_before_tokens,
                    deterministic_after_tokens,
                )
                return messages

            self._commit_compressor_session(session_id)
            with self._summary_state_lock:
                state["compression_count"] = prior_count + 1
                state["last_before_tokens"] = deterministic_before_tokens
                state["last_after_tokens"] = deterministic_after_tokens
            self.compression_count = state["compression_count"]
            return candidate
