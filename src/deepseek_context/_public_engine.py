"""Public Context Engine with merge-integrity enforcement."""

from __future__ import annotations

from typing import Any, Dict, List

from ._engine import DeepSeekContextEngine as _BaseDeepSeekContextEngine
from ._merge_integrity import remove_exact_duplicate_merge_tail


class DeepSeekContextEngine(_BaseDeepSeekContextEngine):
    """Canonical exported engine.

    The base implementation owns compression semantics.  The public boundary
    enforces the CTX-001 invariant that an exact protected-tail sequence may
    appear only once after summary merging.
    """

    def compress(
        self,
        messages: List[Dict[str, Any]],
        current_tokens: int | None = None,
    ) -> List[Dict[str, Any]]:
        compressed = super().compress(messages, current_tokens=current_tokens)
        return remove_exact_duplicate_merge_tail(compressed)
