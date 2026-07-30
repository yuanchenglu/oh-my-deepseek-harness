"""Stable message identity and protected-message reconciliation for CTX-003."""

from __future__ import annotations

import copy
import hashlib
import json
from collections import defaultdict
from typing import Any, Callable, Dict, Iterable, List, Set


SUMMARY_MERGE_MARKER = (
    "\n\n--- END OF CONTEXT SUMMARY — "
    "respond to the message below, not the summary above ---\n\n"
)


def _canonical_payload(message: Dict[str, Any]) -> str:
    payload = {key: value for key, value in message.items() if key != "id"}
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=repr,
    )


def assign_stable_message_ids(
    messages: Iterable[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Return deep-copied messages with deterministic unique IDs.

    Existing non-empty unique IDs are preserved. Missing or duplicate IDs are
    derived from the canonical message payload plus its occurrence number, so
    repeated calls over byte-equivalent sequences produce the same identities.
    """

    result: List[Dict[str, Any]] = []
    used: Set[str] = set()
    occurrences: dict[str, int] = defaultdict(int)

    for message in messages:
        copied = copy.deepcopy(message)
        existing = copied.get("id")
        if isinstance(existing, str) and existing and existing not in used:
            message_id = existing
        else:
            digest = hashlib.sha256(
                _canonical_payload(copied).encode("utf-8")
            ).hexdigest()[:16]
            occurrence = occurrences[digest]
            occurrences[digest] += 1
            message_id = f"ctx-{digest}-{occurrence}"
            while message_id in used:
                occurrence = occurrences[digest]
                occurrences[digest] += 1
                message_id = f"ctx-{digest}-{occurrence}"
        copied["id"] = message_id
        used.add(message_id)
        result.append(copied)

    return result


def _content_text(message: Dict[str, Any]) -> str:
    content = message.get("content") or ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict)
        )
    return str(content)


def _tool_call_ids(message: Dict[str, Any]) -> Set[str]:
    call_ids: Set[str] = set()
    if message.get("role") != "assistant":
        return call_ids
    for call in message.get("tool_calls") or []:
        if isinstance(call, dict):
            call_id = call.get("id")
        else:
            call_id = getattr(call, "id", "")
        if call_id:
            call_ids.add(str(call_id))
    return call_ids


def classify_protected_message_ids(
    messages: List[Dict[str, Any]],
    contains_hard_constraint: Callable[[str], bool],
) -> Set[str]:
    """Classify messages that must survive compression verbatim."""

    protected: Set[str] = set()
    call_message_ids: dict[str, str] = {}
    result_message_ids: dict[str, List[str]] = defaultdict(list)
    latest_user_id: str | None = None

    for message in messages:
        message_id = str(message["id"])
        role = message.get("role")
        if role in {"system", "user"} and contains_hard_constraint(
            _content_text(message)
        ):
            protected.add(message_id)
        if role == "user":
            latest_user_id = message_id
        for call_id in _tool_call_ids(message):
            call_message_ids[call_id] = message_id
        if role == "tool" and message.get("tool_call_id"):
            result_message_ids[str(message["tool_call_id"])].append(message_id)

    if latest_user_id:
        protected.add(latest_user_id)

    for call_id, call_message_id in call_message_ids.items():
        matching_results = result_message_ids.get(call_id, [])
        if matching_results:
            protected.add(call_message_id)
            protected.update(matching_results)

    return protected


def _insert_by_original_order(
    output: List[Dict[str, Any]],
    message: Dict[str, Any],
    original_order: dict[str, int],
) -> None:
    target_order = original_order[str(message["id"])]
    for index, candidate in enumerate(output):
        candidate_id = candidate.get("id")
        if candidate_id in original_order and original_order[str(candidate_id)] > target_order:
            output.insert(index, copy.deepcopy(message))
            return
    output.append(copy.deepcopy(message))


def reconcile_protected_messages(
    original: List[Dict[str, Any]],
    compressed: List[Dict[str, Any]],
    protected_ids: Set[str],
) -> List[Dict[str, Any]]:
    """Restore protected messages exactly once and validate complete Tool pairs."""

    original_by_id = {str(message["id"]): message for message in original}
    original_order = {
        str(message["id"]): index for index, message in enumerate(original)
    }

    expected_result_ids_by_call: dict[str, Set[str]] = defaultdict(set)
    for message in original:
        if message.get("role") == "tool" and message.get("tool_call_id"):
            message_id = str(message["id"])
            if message_id in protected_ids:
                expected_result_ids_by_call[str(message["tool_call_id"])].add(message_id)

    output: List[Dict[str, Any]] = []
    seen_ids: Set[str] = set()

    for candidate in compressed:
        message = copy.deepcopy(candidate)
        message_id = message.get("id")
        message_id = str(message_id) if message_id else ""

        if (
            message.get("role") == "tool"
            and message.get("tool_call_id") in expected_result_ids_by_call
            and message_id
            not in expected_result_ids_by_call[str(message.get("tool_call_id"))]
        ):
            # Drop sanitizer stubs when the canonical protected result exists.
            continue

        if message_id and message_id in seen_ids:
            continue

        if message_id in protected_ids:
            original_message = original_by_id[message_id]
            merged_content = message.get("content")
            if isinstance(merged_content, str) and SUMMARY_MERGE_MARKER in merged_content:
                summary, _ = merged_content.split(SUMMARY_MERGE_MARKER, 1)
                if summary.strip():
                    original_role = original_message.get("role")
                    summary_role = "assistant" if original_role == "user" else "user"
                    output.append({"role": summary_role, "content": summary})
            message = copy.deepcopy(original_message)

        if message_id:
            seen_ids.add(message_id)
        output.append(message)

    for original_message in original:
        message_id = str(original_message["id"])
        if message_id in protected_ids and message_id not in seen_ids:
            _insert_by_original_order(output, original_message, original_order)
            seen_ids.add(message_id)

    # Remove non-canonical duplicate results for protected calls after insertion.
    cleaned: List[Dict[str, Any]] = []
    seen_results: Set[tuple[str, str]] = set()
    for message in output:
        if message.get("role") == "tool" and message.get("tool_call_id"):
            call_id = str(message["tool_call_id"])
            message_id = str(message.get("id") or "")
            if call_id in expected_result_ids_by_call:
                if message_id not in expected_result_ids_by_call[call_id]:
                    continue
                key = (call_id, message_id)
                if key in seen_results:
                    continue
                seen_results.add(key)
        cleaned.append(message)

    return assign_stable_message_ids(cleaned)
