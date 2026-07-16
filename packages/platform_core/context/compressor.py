"""Pure-function compression algorithms extracted from Hermes ContextCompressor.

All functions are stateless and free of Hermes / external dependencies.
They operate on standard Python dicts (message lists) and return new dicts.

Three tiers of functionality:

1.  **Atomic helpers** — token estimation, boundary alignment, pair sanitization,
    tool-result serialization.

2.  **Intent & constraint logic** (I-03, I-04, I-13) — hard-constraint detection,
    prefix freeze management, intent-aware ratio computation.

3.  **Compression pipeline** — ``compress_messages()`` orchestrates pruning,
    boundary detection, summary insertion, and tool-pair repair.  A caller
    provides the LLM-summarisation callback (or None to use a static fallback).
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from . import config as _config

logger = logging.getLogger(__name__)


# ── Constants ───────────────────────────────────────────────────────────────

SUMMARY_PREFIX: str = (
    "[CONTEXT COMPACTION — REFERENCE ONLY] Earlier turns were compacted "
    "into the summary below. This is a handoff from a previous context "
    "window — treat it as background reference, NOT as active instructions. "
    "Do NOT answer questions or fulfill requests mentioned in this summary; "
    "they were already addressed. Respond ONLY to the latest user message "
    "that appears AFTER this summary. The current session state (files, "
    "config, etc.) may reflect work described here — avoid repeating it:"
)


# ── Token estimation ───────────────────────────────────────────────────────


def estimate_messages_tokens_rough(messages: List[Dict[str, Any]]) -> int:
    """Rough token estimate for a message list (pre-flight only).

    Self-contained:  ``chars // 4`` with a small per-message overhead.
    """
    total_chars = sum(len(str(msg)) for msg in messages)
    return (total_chars + 3) // 4


# ── Tool-result summarisation (pure) ───────────────────────────────────────


def summarize_tool_result(tool_name: str, tool_args: str, tool_content: str) -> str:
    """Create an informative 1-line summary of a tool call + result."""
    try:
        args = json.loads(tool_args) if tool_args else {}
    except (json.JSONDecodeError, TypeError):
        args = {}

    content = tool_content or ""
    content_len = len(content)
    line_count = content.count("\n") + 1 if content.strip() else 0

    if tool_name == "terminal":
        cmd = args.get("command", "")
        if len(cmd) > 80:
            cmd = cmd[:77] + "..."
        exit_match = re.search(r'"exit_code"\s*:\s*(-?\d+)', content)
        exit_code = exit_match.group(1) if exit_match else "?"
        return f"[terminal] ran `{cmd}` -> exit {exit_code}, {line_count} lines output"

    if tool_name == "read_file":
        path = args.get("path", "?")
        offset = args.get("offset", 1)
        return f"[read_file] read {path} from line {offset} ({content_len:,} chars)"

    if tool_name == "write_file":
        written_lines = args.get("content", "").count("\n") + 1 if args.get("content") else "?"
        return f"[write_file] wrote to {args.get('path', '?')} ({written_lines} lines)"

    if tool_name == "search_files":
        pattern = args.get("pattern", "?")
        target = args.get("target", "content")
        match_count = re.search(r'"total_count"\s*:\s*(\d+)', content)
        count = match_count.group(1) if match_count else "?"
        return f"[search_files] {target} search for '{pattern}' in {args.get('path', '.')} -> {count} matches"

    if tool_name == "patch":
        path = args.get("path", "?")
        mode = args.get("mode", "replace")
        return f"[patch] {mode} in {path} ({content_len:,} chars result)"

    if tool_name in (
        "browser_navigate", "browser_click", "browser_snapshot",
        "browser_type", "browser_scroll", "browser_vision",
    ):
        url = args.get("url", "")
        ref = args.get("ref", "")
        detail = f" {url}" if url else (f" ref={ref}" if ref else "")
        return f"[{tool_name}]{detail} ({content_len:,} chars)"

    if tool_name == "web_search":
        query = args.get("query", "?")
        return f"[web_search] query='{query}' ({content_len:,} chars result)"

    if tool_name == "web_extract":
        urls = args.get("urls", [])
        url_desc = urls[0] if isinstance(urls, list) and urls else "?"
        return f"[web_extract] {url_desc} ({content_len:,} chars)"

    if tool_name == "delegate_task":
        goal = args.get("goal", "")
        if len(goal) > 60:
            goal = goal[:57] + "..."
        return f"[delegate_task] '{goal}' ({content_len:,} chars result)"

    # Generic fallback
    first_arg = ""
    for k, v in list(args.items())[:2]:
        sv = str(v)[:40]
        first_arg += f" {k}={sv}"
    return f"[{tool_name}]{first_arg} ({content_len:,} chars result)"


# ── Boundary alignment ──────────────────────────────────────────────────────


def align_boundary_forward(messages: List[Dict[str, Any]], idx: int) -> int:
    """Push boundary forward past orphan tool results."""
    while idx < len(messages) and messages[idx].get("role") == "tool":
        idx += 1
    return idx


def align_boundary_backward(messages: List[Dict[str, Any]], idx: int) -> int:
    """Pull boundary backward to avoid splitting tool_call/result groups."""
    if idx <= 0 or idx >= len(messages):
        return idx
    check = idx - 1
    while check >= 0 and messages[check].get("role") == "tool":
        check -= 1
    if check >= 0 and messages[check].get("role") == "assistant" and messages[check].get("tool_calls"):
        idx = check
    return idx


def get_tool_call_id(tc: Any) -> str:
    """Extract call ID from a tool_call entry (dict or object)."""
    if isinstance(tc, dict):
        return tc.get("id", "")
    return getattr(tc, "id", "") or ""


# ── Tool result pruning ─────────────────────────────────────────────────────


def prune_old_tool_results(
    messages: List[Dict[str, Any]],
    protect_tail_count: int,
    protect_tail_tokens: Optional[int] = None,
    quiet: bool = False,
) -> Tuple[List[Dict[str, Any]], int]:
    """Replace old tool result contents with informative 1-line summaries.

    Args:
        messages: Full message list (will be shallow-copied).
        protect_tail_count: Minimum number of tail messages to protect.
        protect_tail_tokens: Token budget protecting the tail (mutually
                             reinforcing with ``protect_tail_count``).
        quiet: Suppress info-level logging when true.

    Returns:
        (pruned_messages, count_of_pruned_entries).
    """
    if not messages:
        return messages, 0

    result = [m.copy() for m in messages]
    pruned = 0

    # Build index: tool_call_id -> (tool_name, arguments_json)
    call_id_to_tool: Dict[str, Tuple[str, str]] = {}
    for msg in result:
        if msg.get("role") == "assistant":
            for tc in msg.get("tool_calls") or []:
                if isinstance(tc, dict):
                    cid = tc.get("id", "")
                    fn = tc.get("function", {})
                    call_id_to_tool[cid] = (fn.get("name", "unknown"), fn.get("arguments", ""))
                else:
                    cid = getattr(tc, "id", "") or ""
                    fn = getattr(tc, "function", None)
                    name = getattr(fn, "name", "unknown") if fn else "unknown"
                    args_str = getattr(fn, "arguments", "") if fn else ""
                    call_id_to_tool[cid] = (name, args_str)

    # Determine prune boundary
    if protect_tail_tokens is not None and protect_tail_tokens > 0:
        accumulated = 0
        boundary = len(result)
        min_protect = min(protect_tail_count, len(result) - 1)
        for i in range(len(result) - 1, -1, -1):
            msg = result[i]
            raw_content = msg.get("content") or ""
            content_len = (
                sum(p.get("text", "") for p in raw_content)
                if isinstance(raw_content, list)
                else len(raw_content)
            )
            msg_tokens = content_len // _config.CHARS_PER_TOKEN + 10
            for tc in msg.get("tool_calls") or []:
                if isinstance(tc, dict):
                    args = tc.get("function", {}).get("arguments", "")
                    msg_tokens += len(args) // _config.CHARS_PER_TOKEN
            soft_ceiling = int(protect_tail_tokens * _config.TAIL_BUDGET_SOFT_CEILING_MULTIPLIER)
            if accumulated + msg_tokens > soft_ceiling and (len(result) - i) >= min_protect:
                boundary = i
                break
            accumulated += msg_tokens
            boundary = i
        prune_boundary = max(boundary, len(result) - min_protect)
    else:
        prune_boundary = len(result) - protect_tail_count

    # Pass 1: Deduplicate identical tool results
    content_hashes: Dict[str, Tuple[int, str]] = {}
    for i in range(len(result) - 1, -1, -1):
        msg = result[i]
        if msg.get("role") != "tool":
            continue
        content = msg.get("content") or ""
        if isinstance(content, list):
            continue
        if len(content) < 200:
            continue
        h = hashlib.md5(content.encode("utf-8", errors="replace")).hexdigest()[:12]
        if h in content_hashes:
            result[i] = {**msg, "content": "[Duplicate tool output — same content as a more recent call]"}
            pruned += 1
        else:
            content_hashes[h] = (i, msg.get("tool_call_id", "?"))

    # Pass 2: Replace old tool results with summaries
    for i in range(prune_boundary):
        msg = result[i]
        if msg.get("role") != "tool":
            continue
        content = msg.get("content", "")
        if isinstance(content, list):
            continue
        if not content or content.startswith("[Old tool output"):
            continue
        if content.startswith("[Duplicate tool output"):
            continue
        if len(content) > 200:
            call_id = msg.get("tool_call_id", "")
            tool_name, tool_args = call_id_to_tool.get(call_id, ("unknown", ""))
            summary = summarize_tool_result(tool_name, tool_args, content)
            result[i] = {**msg, "content": summary}
            pruned += 1

    # Pass 3: Truncate large tool_call arguments
    for i in range(prune_boundary):
        msg = result[i]
        if msg.get("role") != "assistant" or not msg.get("tool_calls"):
            continue
        new_tcs = []
        modified = False
        for tc in msg["tool_calls"]:
            if isinstance(tc, dict):
                args = tc.get("function", {}).get("arguments", "")
                if len(args) > 500:
                    tc = {**tc, "function": {**tc["function"], "arguments": args[:200] + "...[truncated]"}}
                    modified = True
            new_tcs.append(tc)
        if modified:
            result[i] = {**msg, "tool_calls": new_tcs}

    return result, pruned


# ── Tail protection by token budget ─────────────────────────────────────────


def find_tail_cut_by_tokens(
    messages: List[Dict[str, Any]],
    head_end: int,
    token_budget: int,
) -> int:
    """Walk backward to find the tail cut point by token budget.

    Returns:
        Index where the tail starts (inclusive).  Everything before this
        index is eligible for compression.
    """
    n = len(messages)
    min_tail = min(3, n - head_end - 1) if n - head_end > 1 else 0
    soft_ceiling = int(token_budget * _config.TAIL_BUDGET_SOFT_CEILING_MULTIPLIER)
    accumulated = 0
    cut_idx = n

    for i in range(n - 1, head_end - 1, -1):
        msg = messages[i]
        content = msg.get("content") or ""
        msg_tokens = len(content) // _config.CHARS_PER_TOKEN + 10
        for tc in msg.get("tool_calls") or []:
            if isinstance(tc, dict):
                args = tc.get("function", {}).get("arguments", "")
                msg_tokens += len(args) // _config.CHARS_PER_TOKEN
        if accumulated + msg_tokens > soft_ceiling and (n - i) >= min_tail:
            break
        accumulated += msg_tokens
        cut_idx = i

    fallback_cut = n - min_tail
    if cut_idx > fallback_cut:
        cut_idx = fallback_cut
    if cut_idx <= head_end:
        cut_idx = max(fallback_cut, head_end + 1)

    cut_idx = align_boundary_backward(messages, cut_idx)
    return max(cut_idx, head_end + 1)


# ── Tool pair sanitization ──────────────────────────────────────────────────


def sanitize_tool_pairs(
    messages: List[Dict[str, Any]],
    quiet: bool = False,
) -> List[Dict[str, Any]]:
    """Fix orphaned tool_call / tool_result pairs after compression.

    Removes tool results whose corresponding tool_call was dropped, and
    inserts stub results for tool_calls whose result was dropped.
    """
    surviving_call_ids: set = set()
    for msg in messages:
        if msg.get("role") == "assistant":
            for tc in msg.get("tool_calls") or []:
                cid = get_tool_call_id(tc)
                if cid:
                    surviving_call_ids.add(cid)

    result_call_ids: set = set()
    for msg in messages:
        if msg.get("role") == "tool":
            cid = msg.get("tool_call_id")
            if cid:
                result_call_ids.add(cid)

    orphaned_results = result_call_ids - surviving_call_ids
    if orphaned_results:
        messages = [
            m for m in messages
            if not (m.get("role") == "tool" and m.get("tool_call_id") in orphaned_results)
        ]
        if not quiet:
            logger.info("Sanitizer: removed %d orphaned tool result(s)", len(orphaned_results))

    missing_results = surviving_call_ids - result_call_ids
    if missing_results:
        patched: List[Dict[str, Any]] = []
        for msg in messages:
            patched.append(msg)
            if msg.get("role") == "assistant":
                for tc in msg.get("tool_calls") or []:
                    cid = get_tool_call_id(tc)
                    if cid in missing_results:
                        patched.append({
                            "role": "tool",
                            "content": "[Result from earlier conversation — see context summary above]",
                            "tool_call_id": cid,
                        })
        messages = patched
        if not quiet:
            logger.info("Sanitizer: added %d stub tool result(s)", len(missing_results))

    return messages


# ── Serialisation for summariser input ──────────────────────────────────────


_DEFAULT_CONTENT_MAX = 6000
_DEFAULT_CONTENT_HEAD = 4000
_DEFAULT_CONTENT_TAIL = 1500
_DEFAULT_TOOL_ARGS_MAX = 1500
_DEFAULT_TOOL_ARGS_HEAD = 1200


def serialize_for_summary(
    turns: List[Dict[str, Any]],
    content_max: int = _DEFAULT_CONTENT_MAX,
    content_head: int = _DEFAULT_CONTENT_HEAD,
    content_tail: int = _DEFAULT_CONTENT_TAIL,
    tool_args_max: int = _DEFAULT_TOOL_ARGS_MAX,
    tool_args_head: int = _DEFAULT_TOOL_ARGS_HEAD,
) -> str:
    """Serialize conversation turns into labeled text for the summariser."""
    parts = []
    for msg in turns:
        role = msg.get("role", "unknown")
        content = msg.get("content") or ""

        if role == "tool":
            tool_id = msg.get("tool_call_id", "")
            if len(content) > content_max:
                content = content[:content_head] + "\n...[truncated]...\n" + content[-content_tail:]
            parts.append(f"[TOOL RESULT {tool_id}]: {content}")
            continue

        if role == "assistant":
            if len(content) > content_max:
                content = content[:content_head] + "\n...[truncated]...\n" + content[-content_tail:]
            tool_calls = msg.get("tool_calls", [])
            if tool_calls:
                tc_parts = []
                for tc in tool_calls:
                    if isinstance(tc, dict):
                        fn = tc.get("function", {})
                        name = fn.get("name", "?")
                        args = fn.get("arguments", "")
                        if len(args) > tool_args_max:
                            args = args[:tool_args_head] + "..."
                        tc_parts.append(f"  {name}({args})")
                    else:
                        fn = getattr(tc, "function", None)
                        name = getattr(fn, "name", "?") if fn else "?"
                        tc_parts.append(f"  {name}(...)")
                content += "\n[Tool calls:\n" + "\n".join(tc_parts) + "\n]"
            parts.append(f"[ASSISTANT]: {content}")
            continue

        if len(content) > content_max:
            content = content[:content_head] + "\n...[truncated]...\n" + content[-content_tail:]
        parts.append(f"[{role.upper()}]: {content}")

    return "\n\n".join(parts)


# ── Summary budget ──────────────────────────────────────────────────────────


def compute_summary_budget(
    turns: List[Dict[str, Any]],
    max_summary_tokens: int,
    summary_ratio: float = _config.SUMMARY_RATIO,
) -> int:
    """Scale summary token budget with content being compressed."""
    content_tokens = estimate_messages_tokens_rough(turns)
    budget = int(content_tokens * summary_ratio)
    return max(_config.MIN_SUMMARY_TOKENS, min(budget, max_summary_tokens))


def with_summary_prefix(summary: str) -> str:
    """Normalize summary text with the compaction handoff prefix."""
    text = (summary or "").strip()
    return f"{SUMMARY_PREFIX}\n{text}" if text else SUMMARY_PREFIX


# ── I-03: Hard constraint detection ─────────────────────────────────────────

# Chinese constraint keywords
HARD_CONSTRAINT_KEYWORDS: List[str] = [
    "不能", "不要", "必须", "禁止", "严禁", "不得", "绝对", "不可",
]


def contains_hard_constraint(text: str) -> bool:
    """Check whether *text* contains a hard constraint keyword."""
    if not text or not isinstance(text, str):
        return False
    for kw in HARD_CONSTRAINT_KEYWORDS:
        if kw in text:
            return True
    return False


def protect_hard_constraints(messages: List[Dict[str, Any]]) -> List[int]:
    """Return indices of system/user messages that contain hard constraints.

    These messages should be protected from aggressive compression.
    """
    protected: List[int] = []
    for i, msg in enumerate(messages):
        role = msg.get("role", "")
        if role not in ("system", "user"):
            continue
        text = msg.get("content") or ""
        if isinstance(text, list):
            text = " ".join(p.get("text", "") for p in text if isinstance(p, dict))
        if contains_hard_constraint(text):
            protected.append(i)
    return protected


def extract_hard_constraints(messages: List[Dict[str, Any]]) -> List[str]:
    """Extract individual constraint sentences from all messages (I-04).

    Returns:
        Deduplicated constraint descriptions.
    """
    constraints: List[str] = []
    for msg in messages:
        role = msg.get("role", "")
        if role not in ("system", "user"):
            continue
        text = msg.get("content") or ""
        if isinstance(text, list):
            text = " ".join(p.get("text", "") for p in text if isinstance(p, dict))
        sentences = re.split(r"(?<=[。！？\n])\s*", text)
        for sentence in sentences:
            for kw in HARD_CONSTRAINT_KEYWORDS:
                if kw in sentence:
                    kw_idx = sentence.index(kw)
                    constraint_text = sentence[kw_idx:].strip()
                    if constraint_text:
                        constraints.append(constraint_text)
                    break

    seen: set = set()
    unique: List[str] = []
    for c in constraints:
        if c not in seen:
            seen.add(c)
            unique.append(c)
    return unique


def inject_constraint_prefix(constraints: List[str]) -> str:
    """Format extracted hard constraints as a prefix block (I-04)."""
    if not constraints:
        return ""
    lines = ["[硬约束]"]
    for c in constraints:
        lines.append(f"- {c}")
    return "\n".join(lines)


# ── I-13: Prefix freeze ────────────────────────────────────────────────────


@dataclass
class PrefixState:
    """Mutable state for byte-stable prefix freeze (I-13)."""
    frozen: bool = False
    fingerprint: str = ""
    invalidation_count: int = 0


def freeze_prefix(state: PrefixState) -> None:
    """Mark the prefix as frozen (I-13)."""
    state.frozen = True
    state.fingerprint = hashlib.md5(_config.PREFIX_FROZEN_MARKER.encode()).hexdigest()


def is_prefix_stable(state: PrefixState, current_fingerprint: Optional[str] = None) -> bool:
    """Check whether the frozen prefix matches *current_fingerprint*.

    Returns True when the prefix is stable or not yet frozen.
    """
    if not state.frozen:
        return True
    if current_fingerprint and current_fingerprint != state.fingerprint:
        state.invalidation_count += 1
        return False
    return True


def compose_turn_tail(content: str, context_type: str = "memory_update") -> str:
    """Wrap dynamic content as a Turn Tail annotation (I-13).

    Args:
        content: The content to inject.
        context_type: One of ``memory_update``, ``plan_mode``, ``skill_body``,
                      ``background_job``.

    Returns:
        Formatted Turn Tail text.
    """
    prefix_map = {
        "memory_update": "[Memory 更新]",
        "plan_mode": "[Plan Mode]",
        "skill_body": "[Skill 加载]",
        "background_job": "[后台任务]",
    }
    prefix = prefix_map.get(context_type, "[系统消息]")
    return f"\n\n{prefix}\n{content}"


# ── I-03: Intent awareness ──────────────────────────────────────────────────


def compute_effective_ratio(
    intent: str,
    default_ratio: float = _config.DEFAULT_SUMMARY_TARGET_RATIO,
    convergent_ratio: float = _config.CONVERGENT_TARGET_RATIO,
    divergent_ratio: float = _config.DIVERGENT_TARGET_RATIO,
) -> float:
    """Map intent string to compression ratio.

    ``convergent`` → relaxed ratio (preserve more context).
    ``divergent`` → aggressive ratio (compress more).
    Anything else → default ratio.
    """
    if intent == _config.INTENT_CONVERGENT:
        return convergent_ratio
    if intent == _config.INTENT_DIVERGENT:
        return divergent_ratio
    return default_ratio


def compute_intent_protection(
    intent: str,
    protect_first_n: int = _config.DEFAULT_PROTECT_FIRST_N,
    protect_last_n: int = _config.DEFAULT_PROTECT_LAST_N,
) -> Tuple[int, int]:
    """Adjust head/tail protection counts based on intent.

    convergent → protect more head messages.
    divergent → protect more tail messages.
    default → unchanged.
    """
    if intent == _config.INTENT_CONVERGENT:
        return max(protect_first_n, 5), protect_last_n
    if intent == _config.INTENT_DIVERGENT:
        return protect_first_n, max(protect_last_n, 4)
    return protect_first_n, protect_last_n


# ── I-07: Review depth switching ────────────────────────────────────────────

_DEPTH_ORDER = ["shallow", "medium", "deep", "deepest", "reject"]


def nominal_review_depth(
    kv_cache_tokens: int,
    context_length: int,
    plan_complexity: float = _config.PLAN_COMPLEXITY_DEFAULT,
) -> str:
    """Un-hysteresis nominal review depth purely from f(K, P)."""
    k_ratio = kv_cache_tokens / max(context_length, 1)
    if kv_cache_tokens >= context_length or k_ratio >= 1.0:
        return "reject"
    if kv_cache_tokens < 8000:
        return "shallow"
    if kv_cache_tokens < 32000:
        return "medium" if plan_complexity <= 3 else "deep"
    if kv_cache_tokens < 128000:
        return "deep" if plan_complexity <= 3 else "deepest"
    return "reject"


def _check_boundary(
    K: int, P: float, from_lvl: str, to_lvl: str, going_deeper: bool,
    hysteresis: float = _config.HYSTERESIS_THRESHOLD,
) -> bool:
    """Check whether an adjacent depth boundary is crossed (with hysteresis)."""
    f = 1 + hysteresis if going_deeper else 1 - hysteresis

    if "shallow" in (from_lvl, to_lvl):
        return K >= 8000 * f if going_deeper else K < 8000 * f

    if "reject" in (from_lvl, to_lvl):
        return K >= 128000 * f if going_deeper else K < 128000 * f

    if "deepest" not in (from_lvl, to_lvl):
        if going_deeper:
            return (K >= 32000 * f) or (K >= 8000 and P > 3 * f)
        else:
            still_k = K >= 32000 * f
            still_p = (8000 <= K < 32000 and P > 3 * f)
            return not (still_k or still_p)

    if going_deeper:
        return K >= 32000 and P > 3 * f
    else:
        return K < 32000 * f or P <= 3 * f


def get_review_depth(
    kv_cache_tokens: int,
    context_length: int,
    plan_complexity: float = _config.PLAN_COMPLEXITY_DEFAULT,
    last_depth: str = "shallow",
    hysteresis: float = _config.HYSTERESIS_THRESHOLD,
) -> str:
    """f(K, P) function — return review depth with hysteresis.

    Prevents oscillation at boundaries (± hysteresis %).
    """
    k_ratio = kv_cache_tokens / max(context_length, 1)
    if kv_cache_tokens >= context_length or k_ratio >= 1.0:
        return "reject"

    nominal = nominal_review_depth(kv_cache_tokens, context_length, plan_complexity)
    if nominal == last_depth:
        return nominal

    last_idx = _DEPTH_ORDER.index(last_depth)
    target_idx = _DEPTH_ORDER.index(nominal)
    step = 1 if target_idx > last_idx else -1

    current = last_idx
    while current != target_idx:
        next_lvl = _DEPTH_ORDER[current + step]
        if _check_boundary(kv_cache_tokens, plan_complexity,
                           _DEPTH_ORDER[current], next_lvl,
                           going_deeper=(step > 0), hysteresis=hysteresis):
            current += step
        else:
            break

    return _DEPTH_ORDER[current]


# ── Compression pipeline ────────────────────────────────────────────────────

# Type alias for an optional LLM summariser callback.
#   messages → summary string (or None on failure)
SummarizerFn = Callable[[List[Dict[str, Any]]], Optional[str]]


def compress_messages(
    messages: List[Dict[str, Any]],
    *,
    # ── Threshold / budget ─────────────────────────────────────────────
    threshold_tokens: int,
    tail_token_budget: int,
    max_summary_tokens: int = _config.SUMMARY_TOKENS_CEILING,
    # ── Protection ─────────────────────────────────────────────────────
    protect_first_n: int = _config.DEFAULT_PROTECT_FIRST_N,
    protect_last_n: int = _config.DEFAULT_PROTECT_LAST_N,
    # ── Intent (I-03) ──────────────────────────────────────────────────
    intent: str = _config.INTENT_DEFAULT,
    convergent_ratio: float = _config.CONVERGENT_TARGET_RATIO,
    divergent_ratio: float = _config.DIVERGENT_TARGET_RATIO,
    # ── Hard constraint protection (I-04) ──────────────────────────────
    prefix_frozen: bool = False,
    # ── LLM ────────────────────────────────────────────────────────────
    summarizer: Optional[SummarizerFn] = None,
    # ── Behaviour ──────────────────────────────────────────────────────
    quiet: bool = False,
) -> List[Dict[str, Any]]:
    """Orchestrate full message compression.

    This is the main entry point for the compression pipeline:

    1. Short-circuit when message count is too low to compress.
    2. Compute intent-aware protection counts and budget (I-03).
    3. Prune old tool results (deduplicate + summarise).
    4. Determine head / summary / tail boundaries.
    5. Respect hard-constraint-protected messages (I-03/I-04).
    6. Generate (or fall back) a summary of the middle turns.
    7. Assemble compressed message list with role-safe summary insertion.
    8. Sanitize orphaned tool pairs.
    9. Inject hard-constraint prefix when prefix is not yet frozen (I-04).
    """
    n_messages = len(messages)
    _min_for_compress = protect_first_n + 3 + 1
    if n_messages <= _min_for_compress:
        if not quiet:
            logger.warning(
                "Cannot compress: only %d messages (need > %d)",
                n_messages, _min_for_compress,
            )
        return messages

    display_tokens = estimate_messages_tokens_rough(messages)

    # ── I-03: Intent-aware parameters ──────────────────────────────────
    effective_ratio = compute_effective_ratio(intent, convergent_ratio=convergent_ratio,
                                              divergent_ratio=divergent_ratio)
    effective_tail_budget = int(threshold_tokens * effective_ratio)
    effective_first_n, effective_last_n = compute_intent_protection(
        intent, protect_first_n, protect_last_n,
    )

    if not quiet:
        logger.info(
            "[I-03] Intent=%s ratio=%.0f%% tail_budget=%d "
            "first_n=%d last_n=%d",
            intent, effective_ratio * 100,
            effective_tail_budget,
            effective_first_n, effective_last_n,
        )

    # ── Protect hard constraints ───────────────────────────────────────
    protected_indices = protect_hard_constraints(messages)
    if protected_indices and not quiet:
        logger.info(
            "[I-03] Protected %d constraint messages at indices: %s",
            len(protected_indices), protected_indices,
        )

    # Phase 1: Prune old tool results
    messages, pruned_count = prune_old_tool_results(
        messages,
        protect_tail_count=effective_last_n,
        protect_tail_tokens=effective_tail_budget,
        quiet=quiet,
    )
    if pruned_count and not quiet:
        logger.info("Pre-compression: pruned %d old tool result(s)", pruned_count)

    # Phase 2: Determine boundaries
    compress_start = effective_first_n
    compress_start = align_boundary_forward(messages, compress_start)
    compress_end = find_tail_cut_by_tokens(
        messages, compress_start, token_budget=effective_tail_budget,
    )

    # Ensure protected messages survive compression
    if protected_indices and compress_start < compress_end:
        for idx in sorted(protected_indices):
            if compress_start <= idx < compress_end:
                mid_point = (compress_start + compress_end) // 2
                if idx < mid_point:
                    compress_start = idx
                else:
                    compress_end = idx + 1
        compress_start = align_boundary_forward(messages, compress_start)

    if compress_start >= compress_end:
        return messages

    turns_to_summarize = messages[compress_start:compress_end]

    if not quiet:
        tail_msgs = n_messages - compress_end
        logger.info(
            "Summarizing turns %d-%d (%d turns), "
            "protecting %d head + %d tail messages",
            compress_start + 1, compress_end,
            len(turns_to_summarize), compress_start, tail_msgs,
        )

    # Phase 3: Generate summary
    summary: Optional[str] = None
    if summarizer is not None:
        summary = summarizer(turns_to_summarize)

    if not summary:
        if not quiet:
            logger.warning(
                "Summary generation unavailable — inserting static fallback"
            )
        n_dropped = compress_end - compress_start
        summary = (
            "[CONTEXT COMPACTION — REFERENCE ONLY] "
            f"Summary generation was unavailable. {n_dropped} conversation "
            f"turns were removed to free context space but could not be "
            f"summarized. The removed turns contained earlier work in this "
            f"session. Continue based on the recent messages below and the "
            f"current state of any files or resources."
        )

    # Phase 4: Assemble compressed message list
    compressed: List[Dict[str, Any]] = []
    for i in range(compress_start):
        msg = messages[i].copy()
        if i == 0 and msg.get("role") == "system":
            existing = msg.get("content") or ""
            _note = (
                "[Note: Some earlier conversation turns have been compacted "
                "into a handoff summary to preserve context space. The current "
                "session state may still reflect earlier work, so build on that "
                "summary and state rather than re-doing work.]"
            )
            if _note not in existing:
                msg["content"] = existing + "\n\n" + _note
        compressed.append(msg)

    # Determine summary role for proper alternation
    last_head_role = messages[compress_start - 1].get("role", "user") if compress_start > 0 else "user"
    first_tail_role = messages[compress_end].get("role", "user") if compress_end < n_messages else "user"

    summary_role = "assistant" if last_head_role in ("assistant", "tool") else "user"

    _merge = False
    if summary_role == first_tail_role:
        flipped = "assistant" if summary_role == "user" else "user"
        if flipped != last_head_role:
            summary_role = flipped
        else:
            _merge = True

    if not _merge:
        compressed.append({"role": summary_role, "content": summary})
    else:
        for i in range(compress_end, n_messages):
            msg = messages[i].copy()
            if i == compress_end:
                original = msg.get("content") or ""
                msg["content"] = (
                    summary
                    + "\n\n--- END OF CONTEXT SUMMARY — "
                    "respond to the message below, not the summary above ---\n\n"
                    + original
                )
            compressed.append(msg)

    # Append remaining tail messages (non-merge path)
    if not _merge:
        for i in range(compress_end, n_messages):
            compressed.append(messages[i].copy())

    # Sanitize orphaned tool pairs
    compressed = sanitize_tool_pairs(compressed, quiet=quiet)

    new_estimate = estimate_messages_tokens_rough(compressed)
    saved = display_tokens - new_estimate
    if not quiet:
        logger.info(
            "Compressed: %d -> %d messages (~%d tokens saved, %.0f%%)",
            n_messages, len(compressed), saved,
            (saved / display_tokens * 100) if display_tokens > 0 else 0,
        )

    # I-04: Inject hard constraints into prefix zone (only before freeze)
    if not prefix_frozen:
        hard_constraints = extract_hard_constraints(messages)
        if hard_constraints:
            constraint_text = inject_constraint_prefix(hard_constraints)
            result_with_constraints: List[Dict[str, Any]] = [messages[0]]
            result_with_constraints.append({
                "role": "user",
                "content": constraint_text,
            })
            if compressed and compressed[0].get("role") == "system":
                result_with_constraints.extend(compressed[1:])
            else:
                result_with_constraints.extend(compressed)
            compressed = result_with_constraints
            if not quiet:
                logger.info(
                    "[I-04] Injected %d hard constraints into prefix zone, "
                    "prefix_frozen=%s",
                    len(hard_constraints), prefix_frozen,
                )

    return compressed


# ── Static fallback summariser ──────────────────────────────────────────────


def make_static_fallback_summary(turns: List[Dict[str, Any]]) -> str:
    """Return a static fallback summary when no LLM summariser is available."""
    n_dropped = len(turns)
    return (
        "[CONTEXT COMPACTION — REFERENCE ONLY] "
        f"Summary generation was unavailable. {n_dropped} conversation "
        f"turns were removed to free context space but could not be "
        f"summarized. The removed turns contained earlier work in this "
        f"session. Continue based on the recent messages below and the "
        f"current state of any files or resources."
    )
