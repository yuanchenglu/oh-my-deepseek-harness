"""Public Context Engine with integrity and lossless-failure enforcement."""

from __future__ import annotations

import copy
from threading import RLock
from typing import Any, Dict, List

from ._engine import DeepSeekContextEngine as _BaseDeepSeekContextEngine
from ._merge_integrity import remove_exact_duplicate_merge_tail


class DeepSeekContextEngine(_BaseDeepSeekContextEngine):
    """Canonical exported engine with transactional compression safeguards."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._summary_failure_lock = RLock()

    def compress(
        self,
        messages: List[Dict[str, Any]],
        current_tokens: int | None = None,
    ) -> List[Dict[str, Any]]:
        original_generate_summary = self._compressor.generate_summary
        summary_failed = False

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

        # The compressor is instance-scoped. Serialize the temporary method
        # interception so another caller cannot observe the transaction wrapper.
        with self._summary_failure_lock:
            self._compressor.generate_summary = guarded_generate_summary
            try:
                compressed = super().compress(
                    copy.deepcopy(messages),
                    current_tokens=current_tokens,
                )
            finally:
                self._compressor.generate_summary = original_generate_summary

        if summary_failed:
            return messages
        return remove_exact_duplicate_merge_tail(compressed)
