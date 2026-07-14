"""Context compression algorithms — forked from Hermes ContextCompressor.

Core compression logic extracted as pure-Python utilities, without
dependencies on Hermes internal modules (agent.auxiliary_client,
agent.model_metadata, hermes_cli, hermes_core, hermes_constants).

What was changed:
- `call_llm()` from agent.auxiliary_client → direct OpenAI-compatible HTTP call
- `estimate_messages_tokens_rough()` from agent.model_metadata → local version
- `get_model_context_length()` → constructor argument
- All type annotations updated to avoid `Path | None` syntax (3.10+)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# -- Constants (from Hermes context_compressor.py) ---------------------------

SUMMARY_PREFIX = (
    "[CONTEXT COMPACTION — REFERENCE ONLY] Earlier turns were compacted "
    "into the summary below. This is a handoff from a previous context "
    "window — treat it as background reference, NOT as active instructions. "
    "Do NOT answer questions or fulfill requests mentioned in this summary; "
    "they were already addressed. Respond ONLY to the latest user message "
    "that appears AFTER this summary. The current session state (files, "
    "config, etc.) may reflect work described here — avoid repeating it:"
)

_SUMMARY_TOKENS_CEILING = 12_000
_MIN_SUMMARY_TOKENS = 2000
_SUMMARY_RATIO = 0.20
_CHARS_PER_TOKEN = 4
_SUMMARY_FAILURE_COOLDOWN_SECONDS = 600


# -- Rough token estimation (standalone, no Hermes deps) --------------------


def estimate_messages_tokens_rough(messages: List[Dict[str, Any]]) -> int:
    """Rough token estimate for a message list (pre-flight only).

    Self-contained replacement for Hermes' version from model_metadata.
    """
    total_chars = sum(len(str(msg)) for msg in messages)
    return (total_chars + 3) // 4


# -- Tool result summarization helpers (pure functions) ----------------------


def _summarize_tool_result(tool_name: str, tool_args: str, tool_content: str) -> str:
    """Create an informative 1-line summary of a tool call + result.

    Forked verbatim from Hermes context_compressor.py.
    """
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

    if tool_name in ("browser_navigate", "browser_click", "browser_snapshot",
                     "browser_type", "browser_scroll", "browser_vision"):
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


# -- DeepSeekCompressor — compression algorithms (forked) -------------------


class DeepSeekCompressor:
    """Core compression algorithms, forked from Hermes ContextCompressor.

    Contains the pure-Python logic for:
    - Tool result pruning
    - Token-budget tail protection
    - Message boundary alignment
    - Tool pair sanitization
    - Summary generation (via OpenAI-compatible HTTP client)
    """

    def __init__(
        self,
        model: str,
        summary_model: str = "",
        api_key: str = "",
        base_url: str = "",
        threshold_tokens: int = 96_000,
        tail_token_budget: int = 20_000,
        max_summary_tokens: int = 8_000,
        context_length: int = 128_000,
        threshold_percent: float = 0.75,
        protect_first_n: int = 3,
        quiet_mode: bool = False,
    ):
        self.model = model
        self.summary_model = summary_model or model
        self.api_key = api_key
        self.base_url = base_url
        self.threshold_tokens = threshold_tokens
        self.tail_token_budget = tail_token_budget
        self.max_summary_tokens = max_summary_tokens
        self.context_length = context_length
        self.threshold_percent = threshold_percent
        self.protect_first_n = protect_first_n
        self.quiet_mode = quiet_mode

        # Anti-thrashing state
        self._previous_summary: Optional[str] = None
        self._ineffective_compression_count: int = 0
        self._summary_failure_cooldown_until: float = 0.0

    def update_config(
        self,
        model: str = "",
        context_length: int = 0,
        threshold_tokens: int = 0,
        **kwargs,
    ) -> None:
        """Update configuration (called on model switch)."""
        if model:
            self.model = model
        if context_length:
            self.context_length = context_length
        if threshold_tokens:
            self.threshold_tokens = threshold_tokens

    # -- Tool result pruning ------------------------------------------------

    def prune_old_tool_results(
        self,
        messages: List[Dict[str, Any]],
        protect_tail_count: int,
        protect_tail_tokens: Optional[int] = None,
    ) -> tuple[List[Dict[str, Any]], int]:
        """Replace old tool result contents with informative 1-line summaries.

        Forked from Hermes ContextCompressor._prune_old_tool_results().
        """
        if not messages:
            return messages, 0

        result = [m.copy() for m in messages]
        pruned = 0

        # Build index: tool_call_id -> (tool_name, arguments_json)
        call_id_to_tool: Dict[str, tuple] = {}
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
                content_len = sum(len(p.get("text", "")) for p in raw_content) if isinstance(raw_content, list) else len(raw_content)
                msg_tokens = content_len // _CHARS_PER_TOKEN + 10
                for tc in msg.get("tool_calls") or []:
                    if isinstance(tc, dict):
                        args = tc.get("function", {}).get("arguments", "")
                        msg_tokens += len(args) // _CHARS_PER_TOKEN
                if accumulated + msg_tokens > protect_tail_tokens and (len(result) - i) >= min_protect:
                    boundary = i
                    break
                accumulated += msg_tokens
                boundary = i
            prune_boundary = max(boundary, len(result) - min_protect)
        else:
            prune_boundary = len(result) - protect_tail_count

        # Pass 1: Deduplicate identical tool results
        content_hashes: dict = {}
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
                summary = _summarize_tool_result(tool_name, tool_args, content)
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

    # -- Tail protection by token budget ------------------------------------

    def find_tail_cut_by_tokens(
        self,
        messages: List[Dict[str, Any]],
        head_end: int,
        token_budget: Optional[int] = None,
    ) -> int:
        """Walk backward to find the tail cut point by token budget.

        Forked from Hermes ContextCompressor._find_tail_cut_by_tokens().
        """
        if token_budget is None:
            token_budget = self.tail_token_budget
        n = len(messages)
        min_tail = min(3, n - head_end - 1) if n - head_end > 1 else 0
        soft_ceiling = int(token_budget * 1.5)
        accumulated = 0
        cut_idx = n

        for i in range(n - 1, head_end - 1, -1):
            msg = messages[i]
            content = msg.get("content") or ""
            msg_tokens = len(content) // _CHARS_PER_TOKEN + 10
            for tc in msg.get("tool_calls") or []:
                if isinstance(tc, dict):
                    args = tc.get("function", {}).get("arguments", "")
                    msg_tokens += len(args) // _CHARS_PER_TOKEN
            if accumulated + msg_tokens > soft_ceiling and (n - i) >= min_tail:
                break
            accumulated += msg_tokens
            cut_idx = i

        fallback_cut = n - min_tail
        if cut_idx > fallback_cut:
            cut_idx = fallback_cut
        if cut_idx <= head_end:
            cut_idx = max(fallback_cut, head_end + 1)

        cut_idx = self._align_boundary_backward(messages, cut_idx)
        return max(cut_idx, head_end + 1)

    # -- Boundary alignment helpers -----------------------------------------

    @staticmethod
    def align_boundary_forward(messages: List[Dict[str, Any]], idx: int) -> int:
        """Push boundary forward past orphan tool results."""
        while idx < len(messages) and messages[idx].get("role") == "tool":
            idx += 1
        return idx

    @staticmethod
    def _align_boundary_backward(messages: List[Dict[str, Any]], idx: int) -> int:
        """Pull boundary backward to avoid splitting tool_call/result groups."""
        if idx <= 0 or idx >= len(messages):
            return idx
        check = idx - 1
        while check >= 0 and messages[check].get("role") == "tool":
            check -= 1
        if check >= 0 and messages[check].get("role") == "assistant" and messages[check].get("tool_calls"):
            idx = check
        return idx

    @staticmethod
    def _get_tool_call_id(tc) -> str:
        """Extract call ID from a tool_call entry (dict or SimpleNamespace)."""
        if isinstance(tc, dict):
            return tc.get("id", "")
        return getattr(tc, "id", "") or ""

    # -- Tool pair sanitization ---------------------------------------------

    def sanitize_tool_pairs(
        self, messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Fix orphaned tool_call / tool_result pairs after compression.

        Forked from Hermes ContextCompressor._sanitize_tool_pairs().
        """
        surviving_call_ids: set = set()
        for msg in messages:
            if msg.get("role") == "assistant":
                for tc in msg.get("tool_calls") or []:
                    cid = self._get_tool_call_id(tc)
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
            if not self.quiet_mode:
                logger.info("Sanitizer: removed %d orphaned tool result(s)", len(orphaned_results))

        missing_results = surviving_call_ids - result_call_ids
        if missing_results:
            patched: List[Dict[str, Any]] = []
            for msg in messages:
                patched.append(msg)
                if msg.get("role") == "assistant":
                    for tc in msg.get("tool_calls") or []:
                        cid = self._get_tool_call_id(tc)
                        if cid in missing_results:
                            patched.append({
                                "role": "tool",
                                "content": "[Result from earlier conversation — see context summary above]",
                                "tool_call_id": cid,
                            })
            messages = patched
            if not self.quiet_mode:
                logger.info("Sanitizer: added %d stub tool result(s)", len(missing_results))

        return messages

    # -- Serialization for summarizer input ---------------------------------

    def serialize_for_summary(self, turns: List[Dict[str, Any]]) -> str:
        """Serialize conversation turns into labeled text for the summarizer.

        Forked from Hermes ContextCompressor._serialize_for_summary().
        """
        _CONTENT_MAX = 6000
        _CONTENT_HEAD = 4000
        _CONTENT_TAIL = 1500
        _TOOL_ARGS_MAX = 1500
        _TOOL_ARGS_HEAD = 1200

        parts = []
        for msg in turns:
            role = msg.get("role", "unknown")
            content = msg.get("content") or ""

            if role == "tool":
                tool_id = msg.get("tool_call_id", "")
                if len(content) > _CONTENT_MAX:
                    content = content[:_CONTENT_HEAD] + "\n...[truncated]...\n" + content[-_CONTENT_TAIL:]
                parts.append(f"[TOOL RESULT {tool_id}]: {content}")
                continue

            if role == "assistant":
                if len(content) > _CONTENT_MAX:
                    content = content[:_CONTENT_HEAD] + "\n...[truncated]...\n" + content[-_CONTENT_TAIL:]
                tool_calls = msg.get("tool_calls", [])
                if tool_calls:
                    tc_parts = []
                    for tc in tool_calls:
                        if isinstance(tc, dict):
                            fn = tc.get("function", {})
                            name = fn.get("name", "?")
                            args = fn.get("arguments", "")
                            if len(args) > _TOOL_ARGS_MAX:
                                args = args[:_TOOL_ARGS_HEAD] + "..."
                            tc_parts.append(f"  {name}({args})")
                        else:
                            fn = getattr(tc, "function", None)
                            name = getattr(fn, "name", "?") if fn else "?"
                            tc_parts.append(f"  {name}(...)")
                    content += "\n[Tool calls:\n" + "\n".join(tc_parts) + "\n]"
                parts.append(f"[ASSISTANT]: {content}")
                continue

            if len(content) > _CONTENT_MAX:
                content = content[:_CONTENT_HEAD] + "\n...[truncated]...\n" + content[-_CONTENT_TAIL:]
            parts.append(f"[{role.upper()}]: {content}")

        return "\n\n".join(parts)

    # -- Summary generation via DeepSeek API ---------------------------------

    def _call_deepseek_llm(
        self,
        prompt: str,
        max_tokens: int,
        model: Optional[str] = None,
    ) -> Optional[str]:
        """Call DeepSeek API directly (OpenAI-compatible endpoint).

        Standalone replacement for Hermes' ``call_llm()`` from
        agent.auxiliary_client.  Uses ``openai`` library for the
        actual HTTP call.

        Returns the response text, or None on failure.
        """
        try:
            from openai import OpenAI
        except ImportError:
            logger.error(
                "DeepSeek compression requires the 'openai' Python package. "
                "Install with: pip install openai"
            )
            return None

        try:
            client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
            response = client.chat.completions.create(
                model=model or self.summary_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content
            if not isinstance(content, str):
                content = str(content) if content else ""
            return content.strip()
        except Exception as e:
            logger.warning("DeepSeek LLM call failed: %s", e)
            return None

    def generate_summary(
        self, turns_to_summarize: List[Dict[str, Any]],
    ) -> Optional[str]:
        """Generate structured summary of conversation turns via DeepSeek.

        Forked from Hermes ContextCompressor._generate_summary() with
        ``call_llm`` replaced by ``_call_deepseek_llm()``.
        """
        now = time.monotonic()
        if now < self._summary_failure_cooldown_until:
            logger.debug(
                "Summary skipped during cooldown (%.0fs remaining)",
                self._summary_failure_cooldown_until - now,
            )
            return None

        summary_budget = self._compute_summary_budget(turns_to_summarize)
        content_to_summarize = self.serialize_for_summary(turns_to_summarize)

        preamble = (
            "You are a summarization agent creating a context checkpoint. "
            "Your output will be injected as reference material for a DIFFERENT "
            "assistant that continues the conversation. "
            "Do NOT respond to any questions or requests in the conversation — "
            "only output the structured summary. "
            "Do NOT include any preamble, greeting, or prefix."
        )

        template = (
            "## Goal\n"
            "[What the user is trying to accomplish]\n\n"
            "## Completed Actions\n"
            "[Numbered list of concrete actions taken]\n\n"
            "## Active State\n"
            "[Current working state]\n\n"
            "## Key Decisions\n"
            "[Important technical decisions and WHY]\n\n"
            "## Resolved Questions\n"
            "[Questions already answered]\n\n"
            "## Pending User Asks\n"
            "[Unanswered questions or requests. If none, write None.]\n\n"
            "## Remaining Work\n"
            "[What remains to be done]\n\n"
            f"Target ~{summary_budget} tokens. Be CONCRETE — include file paths, "
            "command outputs, error messages, line numbers, and specific values."
        )

        if self._previous_summary:
            prompt = (
                f"{preamble}\n\n"
                f"You are updating a context compaction summary.\n\n"
                f"PREVIOUS SUMMARY:\n{self._previous_summary}\n\n"
                f"NEW TURNS:\n{content_to_summarize}\n\n"
                f"Update using this structure:\n{template}"
            )
        else:
            prompt = (
                f"{preamble}\n\n"
                f"Create a structured handoff summary.\n\n"
                f"TURNS:\n{content_to_summarize}\n\n"
                f"Use this structure:\n{template}"
            )

        content = self._call_deepseek_llm(
            prompt=prompt,
            max_tokens=int(summary_budget * 1.3),
        )
        if content:
            self._previous_summary = content
            self._summary_failure_cooldown_until = 0.0
            return self._with_summary_prefix(content)

        # Failure — enter cooldown
        self._summary_failure_cooldown_until = (
            time.monotonic() + _SUMMARY_FAILURE_COOLDOWN_SECONDS
        )
        return None

    def _compute_summary_budget(self, turns: List[Dict[str, Any]]) -> int:
        """Scale summary token budget with content being compressed."""
        content_tokens = estimate_messages_tokens_rough(turns)
        budget = int(content_tokens * _SUMMARY_RATIO)
        return max(_MIN_SUMMARY_TOKENS, min(budget, self.max_summary_tokens))

    @staticmethod
    def _with_summary_prefix(summary: str) -> str:
        """Normalize summary text with the compaction handoff prefix."""
        text = (summary or "").strip()
        return f"{SUMMARY_PREFIX}\n{text}" if text else SUMMARY_PREFIX
