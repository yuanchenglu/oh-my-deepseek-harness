"""Integrity guard for Context Engine merge-path assembly.

The legacy merge branch can append the protected tail twice: the first copy has
its first message prefixed with the generated summary, followed by an unchanged
second copy of the whole tail.  This module removes only that exact duplicated
sequence.  It does not deduplicate ordinary repeated messages.
"""

from __future__ import annotations

from typing import Any, Dict, List


_MERGE_MARKER = (
    "\n\n--- END OF CONTEXT SUMMARY — "
    "respond to the message below, not the summary above ---\n\n"
)


def remove_exact_duplicate_merge_tail(
    messages: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Remove an exact second copy of a summary-merged protected tail.

    Expected buggy shape::

        head + [summary + tail[0]] + tail[1:] + tail

    The function reconstructs the logical first tail message by removing the
    summary marker prefix, then requires the two complete tail sequences to be
    structurally identical before dropping the second copy.  If the shape is
    incomplete or ambiguous, the input is returned unchanged.
    """

    marker_index = -1
    logical_first: Dict[str, Any] | None = None

    for index, message in enumerate(messages):
        content = message.get("content")
        if not isinstance(content, str) or _MERGE_MARKER not in content:
            continue

        _, original = content.split(_MERGE_MARKER, 1)
        logical_first = message.copy()
        logical_first["content"] = original
        marker_index = index
        break

    if marker_index < 0 or logical_first is None:
        return messages

    for duplicate_start in range(marker_index + 1, len(messages)):
        if messages[duplicate_start] != logical_first:
            continue

        first_tail = [logical_first, *messages[marker_index + 1 : duplicate_start]]
        second_tail = messages[duplicate_start:]
        if first_tail == second_tail:
            return messages[:duplicate_start]

    return messages
