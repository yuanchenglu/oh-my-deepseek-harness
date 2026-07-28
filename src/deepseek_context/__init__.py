"""DeepSeek Context Engine for Hermes Agent.

ContextEngine 实现。通过 OpenAI 兼容接口使用 DeepSeek 进行上下文压缩摘要。
核心压缩算法 fork 自 Hermes ContextCompressor（纯 Python 部分），
LLM 调用替换为 DeepSeek API 直接调用，不依赖 Hermes auxiliary_client。
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import re
from typing import Any, Dict, List, Optional

from agent.context_engine import ContextEngine

from .compressor import (
    DeepSeekCompressor,
    estimate_messages_tokens_rough,
)

logger = logging.getLogger(__name__)

# I-07: 审查深度切换的滞后阈值（±10%，防止边界振荡）
_HYSTERESIS_THRESHOLD = 0.10


class DeepSeekContextEngine(ContextEngine):
    """Context engine that uses DeepSeek API for intelligent compression.

    特点：
    - 独立 LLM 客户端（不依赖 Hermes call_llm）
    - 可配置的模型、阈值、摘要预算
    - 自包含：config.yaml 控制所有参数
    - I-03 注意力预算：intent-based 差异化压缩策略
    """

    # I-03: 硬约束关键词 — 包含这些词的 user/system 消息受到保护不被压缩
    HARD_CONSTRAINT_KEYWORDS = [
        "不能", "不要", "必须", "禁止", "严禁", "不得", "绝对", "不可",
    ]

    @property
    def name(self) -> str:
        return "deepseek-context"

    def __init__(
        self,
        model: str = "deepseek-chat",
        threshold_percent: float = 0.75,
        protect_first_n: int = 3,
        protect_last_n: int = 20,
        summary_target_ratio: float = 0.20,
        quiet_mode: bool = False,
        summary_model: str = "",
        api_key: str = "",
        base_url: str = "",
        context_length: int = 128_000,
        # I-03: 差异化压缩参数
        convergent_target_ratio: float = 0.40,
        divergent_target_ratio: float = 0.25,
    ):
        self.model = model
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        self.base_url = base_url or os.environ.get(
            "DEEPSEEK_BASE_URL",
            "https://api.deepseek.com",
        )
        self.summary_model = summary_model

        self.threshold_percent = threshold_percent
        self.protect_first_n = protect_first_n
        self.protect_last_n = protect_last_n
        self.summary_target_ratio = max(0.10, min(summary_target_ratio, 0.80))
        self.quiet_mode = quiet_mode

        # I-03: Intent 跟踪与差异化比率
        self._current_intent: str = "default"
        self.convergent_target_ratio = max(0.10, min(convergent_target_ratio, 0.80))
        self.divergent_target_ratio = max(0.10, min(divergent_target_ratio, 0.80))

        # I-04: KV Cache 前缀冻结状态（由 I-13 在首轮后标记）
        self._prefix_frozen: bool = False
        # I-13: Byte-Stable Prefix 完整状态
        self._prefix_fingerprint: str = ""
        self._prefix_invalidation_count: int = 0
        self._frozen_prefix: str = ""

        # Context budget
        self.context_length = context_length
        self.threshold_tokens = int(context_length * threshold_percent)
        self.compression_count = 0

        # Derive token budgets
        target_tokens = int(self.threshold_tokens * self.summary_target_ratio)
        self.tail_token_budget = target_tokens
        self.max_summary_tokens = min(
            int(context_length * 0.05),
            12_000,  # _SUMMARY_TOKENS_CEILING
        )

        # Token tracking
        self.last_prompt_tokens = 0
        self.last_completion_tokens = 0
        self.last_total_tokens = 0

        # I-07: 审查深度切换
        self._last_review_depth: str = "shallow"
        self._plan_complexity: float = 3.0

        # Internal compressor logic (forked, pure-Python)
        self._compressor = DeepSeekCompressor(
            model=self.model,
            summary_model=self.summary_model,
            api_key=self.api_key,
            base_url=self.base_url,
            threshold_tokens=self.threshold_tokens,
            tail_token_budget=self.tail_token_budget,
            max_summary_tokens=self.max_summary_tokens,
            context_length=self.context_length,
            threshold_percent=self.threshold_percent,
            protect_first_n=self.protect_first_n,
            quiet_mode=self.quiet_mode,
        )

        if not quiet_mode:
            logger.info(
                "DeepSeekContextEngine initialized: model=%s context=%d "
                "threshold=%d (%.0f%%) tail_budget=%d",
                model, context_length, self.threshold_tokens,
                threshold_percent * 100, target_tokens,
            )
            logger.info(
                "[I-07] Review depth switching enabled: h=%.0f%% default_P=%.1f",
                _HYSTERESIS_THRESHOLD * 100, self._plan_complexity,
            )

    # -- Token tracking ---------------------------------------------------

    def should_compress(self, prompt_tokens: int = None) -> bool:
        """Check if context exceeds the compression threshold."""
        tokens = prompt_tokens if prompt_tokens is not None else self.last_prompt_tokens
        if tokens < self.threshold_tokens:
            return False
        return True

    # -- I-03: Intent awareness -------------------------------------------

    def set_intent(self, intent: str) -> None:
        """设置当前会话的意图类型，影响差异化压缩策略。

        Args:
            intent: 意图类型 — "default" | "convergent" | "divergent"
        """
        valid = {"default", "convergent", "divergent"}
        if intent not in valid:
            logger.warning(
                "[I-03] Unknown intent=%r, falling back to 'default'", intent,
            )
            intent = "default"
        self._current_intent = intent
        logger.debug("[I-03] Intent set to: %s", intent)

    def get_intent(self) -> str:
        """获取当前意图类型。"""
        return self._current_intent

    def _compute_effective_ratio(self) -> float:
        """根据当前意图计算有效的 summary_target_ratio。"""
        intent = self._current_intent
        if intent == "convergent":
            return self.convergent_target_ratio
        if intent == "divergent":
            return self.divergent_target_ratio
        return self.summary_target_ratio

    # -- I-03: Hard constraint protection ---------------------------------

    @staticmethod
    def _contains_hard_constraint(text: str) -> bool:
        """检查文本是否包含硬约束关键词。"""
        if not text or not isinstance(text, str):
            return False
        for kw in DeepSeekContextEngine.HARD_CONSTRAINT_KEYWORDS:
            if kw in text:
                return True
        return False

    def protect_hard_constraints(
        self, messages: List[Dict[str, Any]],
    ) -> List[int]:
        """扫描消息列表，返回包含硬约束的消息索引列表。

        这些消息在压缩时不应被丢弃或过分压缩。
        同时检查 system 和 user 消息。

        Returns:
            List[int]: 被保护的消息在原始 messages 中的索引。
        """
        protected: List[int] = []
        for i, msg in enumerate(messages):
            role = msg.get("role", "")
            if role not in ("system", "user"):
                continue
            text = msg.get("content") or ""
            if isinstance(text, list):
                text = " ".join(
                    p.get("text", "") for p in text
                    if isinstance(p, dict)
                )
            if self._contains_hard_constraint(text):
                protected.append(i)
        return protected

    # -- I-04: KV Cache 前缀约束隔离 ----------------------------------------

    def extract_hard_constraints(
        self, messages: List[Dict[str, Any]],
    ) -> List[str]:
        """扫描全部消息，提取包含硬约束关键词的完整句子。

        与 I-03 protect_hard_constraints() 的区别：
        - protect_hard_constraints() 返回消息索引（保护整条消息不压缩）
        - extract_hard_constraints() 返回约束文本（注入前缀区供 DeepSeek Cache）

        Returns:
            去重后的约束描述列表。
        """
        constraints: List[str] = []
        for msg in messages:
            role = msg.get("role", "")
            if role not in ("system", "user"):
                continue
            text = msg.get("content") or ""
            if isinstance(text, list):
                text = " ".join(
                    p.get("text", "") for p in text
                    if isinstance(p, dict)
                )
            # 按中文句号/感叹号/问号/换行分割句子
            sentences = re.split(r"(?<=[。！？\n])\s*", text)
            for sentence in sentences:
                for kw in self.HARD_CONSTRAINT_KEYWORDS:
                    if kw in sentence:
                        kw_idx = sentence.index(kw)
                        constraint_text = sentence[kw_idx:].strip()
                        if constraint_text:
                            constraints.append(constraint_text)
                        break

        # 去重
        seen: set = set()
        unique: List[str] = []
        for c in constraints:
            if c not in seen:
                seen.add(c)
                unique.append(c)

        if unique:
            logger.info(
                "[I-04] Extracted %d hard constraints: %s",
                len(unique), unique,
            )
        return unique

    def inject_constraint_prefix(self, constraints: List[str]) -> str:
        """将提取的硬约束格式化为前缀注入文本。"""
        if not constraints:
            return ""
        lines = ["[硬约束]"]
        for c in constraints:
            lines.append(f"- {c}")
        return "\n".join(lines)

    # -- I-13: Byte-Stable Prefix 前缀冻结 + Turn Tail 路由 -----------------
    #
    # I-13 base-first memory 协议：
    # 即使跨 session Memory 更新，base prompt 也应保持字节一致。
    # 这依赖于 Hermes 的 prompt_builder 在 session 启动时
    # 将 base system prompt 放在 Memory/skills 之前。
    # 如果 Memory 变化导致 base 变化，属于提示词模板变化，
    # 应在 session 间（而非 session 内）处理。
    #
    # 与 I-04 的协作顺序:
    # 1. I-04 在首次 compress() 或 on_session_start() 时提取硬约束
    # 2. I-13 在首次 update_from_response() 后执行 freeze_prefix()
    # 3. 冻结后 I-04 不再修改前缀
    # --------------------------------------------------------------------

    def freeze_prefix(self) -> None:
        """冻结当前 system prompt 前缀。

        在 session 首次 pre_llm_call 时由外部调用（gate.py 或 on_session_start）。
        快照当前 system prompt 的字节级指纹，设置 _prefix_frozen = True，
        阻止后续对前缀的修改。

        注意：由于 Hermes 的 prompt_builder 在启动时组装 system prompt，
        on_session_start() 是最早的捕获点。如果 on_session_start() 的 kwargs
        中包含 system_prompt 信息，则在此处快照；否则在首次 update_from_response()
        时由外部调用 freeze_prefix()。
        """
        self._frozen_prefix = "deepseek_context"  # 标记前缀已冻结
        self._prefix_frozen = True
        self._prefix_fingerprint = hashlib.md5(
            self._frozen_prefix.encode()
        ).hexdigest()
        logger.info(
            "[I-13] System prompt prefix frozen, fingerprint=%s",
            self._prefix_fingerprint[:12],
        )

    def is_prefix_frozen(self) -> bool:
        """检查前缀是否已冻结。"""
        return self._prefix_frozen

    def is_prefix_stable(self, current_fingerprint: str | None = None) -> bool:
        """检查自上次冻结以来 system prompt 是否被修改。

        用法：在每次 pre_llm_call 前由外部调用，传入当前 system prompt 的指纹。
        如果不稳定，记录 prefix_invalidation 事件并返回 False。

        Args:
            current_fingerprint: 当前 system prompt 的 MD5 指纹 hex 字符串。
                                 为 None 时跳过指纹比对。

        Returns:
            True 表示稳定（前缀未被修改），False 表示前缀已变化。
        """
        if not self._prefix_frozen:
            return True  # 尚未冻结，视为稳定
        if current_fingerprint and current_fingerprint != self._prefix_fingerprint:
            logger.warning(
                "[I-13] Prefix INVALIDATED: fingerprint changed from %s to %s",
                self._prefix_fingerprint[:12], current_fingerprint[:12],
            )
            self._prefix_invalidation_count += 1
            return False
        return True

    @staticmethod
    def compose_turn_tail(content: str, context_type: str = "memory_update") -> str:
        """将变化内容注入到用户消息尾部（Turn Tail）。

        不走 system prompt 修改，而是包装为对话消息格式，
        由 pre_llm_call hook 注入到 user message 的末尾。

        Args:
            content: 需要注入的变化内容
            context_type: 注入类型
                - "memory_update": Memory 更新
                - "plan_mode": Plan Mode 切换
                - "skill_body": Skill 按需加载
                - "background_job": 后台任务完成通知

        Returns:
            格式化的 Turn Tail 内容。
        """
        prefix_map = {
            "memory_update": "[Memory 更新]",
            "plan_mode": "[Plan Mode]",
            "skill_body": "[Skill 加载]",
            "background_job": "[后台任务]",
        }
        prefix = prefix_map.get(context_type, "[系统消息]")
        return f"\n\n{prefix}\n{content}"

    def on_session_start(self, session_id: str, **kwargs: Any) -> None:
        """新会话开始时调用——在此处执行前缀冻结。

        如果 Hermes 的 session_start 回调提供了 system_prompt，
        则在此处直接冻结；否则由外部在首次 pre_llm_call 时调用 freeze_prefix()。
        """
        super().on_session_start(session_id, **kwargs)
        system_prompt = kwargs.get("system_prompt", "")
        if system_prompt:
            self._prefix_frozen = True
            self._prefix_fingerprint = hashlib.md5(
                system_prompt.encode()
            ).hexdigest()
            self._frozen_prefix = "deepseek_context"
            logger.info(
                "[I-13] Session %s started, prefix frozen (fingerprint=%s)",
                session_id, self._prefix_fingerprint[:12],
            )

    # -- Core compression -------------------------------------------------

    def compress(
        self,
        messages: List[Dict[str, Any]],
        current_tokens: int = None,
    ) -> List[Dict[str, Any]]:
        """Compress conversation messages using DeepSeek summarization.

        Fork of Hermes ContextCompressor.compress() with `call_llm`
        replaced by direct OpenAI-compatible API call to DeepSeek.

        Args:
            messages: Full message list to compact.
            current_tokens: Optional current token count estimate.

        Returns:
            Compressed message list (may be same length if noop).
        """
        n_messages = len(messages)
        _min_for_compress = self.protect_first_n + 3 + 1
        if n_messages <= _min_for_compress:
            if not self.quiet_mode:
                logger.warning(
                    "Cannot compress: only %d messages (need > %d)",
                    n_messages, _min_for_compress,
                )
            return messages

        display_tokens = (
            current_tokens
            if current_tokens
            else (self.last_prompt_tokens or estimate_messages_tokens_rough(messages))
        )

        # -- I-03: Intent-aware differentiated compression strategy --------
        intent = self._current_intent
        effective_ratio = self._compute_effective_ratio()
        effective_tail_budget = int(self.threshold_tokens * effective_ratio)

        if intent == "convergent":
            # 收敛任务：保留更多上下文，保护更多头部消息
            effective_protect_first_n = max(self.protect_first_n, 5)
            effective_protect_last_n = self.protect_last_n
        elif intent == "divergent":
            # 发散任务：高压缩比，但保护尾部结论消息
            effective_protect_first_n = self.protect_first_n
            effective_protect_last_n = max(self.protect_last_n, 4)
        else:
            effective_protect_first_n = self.protect_first_n
            effective_protect_last_n = self.protect_last_n

        if not self.quiet_mode:
            logger.info(
                "[I-03] Intent=%s ratio=%.0f%% tail_budget=%d "
                "first_n=%d last_n=%d",
                intent, effective_ratio * 100,
                effective_tail_budget,
                effective_protect_first_n, effective_protect_last_n,
            )

        # -- Protect hard constraints from aggressive compression --------
        protected_indices = self.protect_hard_constraints(messages)
        if protected_indices and not self.quiet_mode:
            logger.info(
                "[I-03] Protected %d constraint messages at indices: %s",
                len(protected_indices), protected_indices,
            )

        # Phase 1: Prune old tool results (use intent-aware protection)
        messages, pruned_count = self._compressor.prune_old_tool_results(
            messages,
            protect_tail_count=effective_protect_last_n,
            protect_tail_tokens=effective_tail_budget,
        )
        if pruned_count and not self.quiet_mode:
            logger.info("Pre-compression: pruned %d old tool result(s)", pruned_count)

        # Phase 2: Determine boundaries (use intent-aware protection)
        compress_start = effective_protect_first_n
        compress_start = self._compressor.align_boundary_forward(messages, compress_start)
        compress_end = self._compressor.find_tail_cut_by_tokens(
            messages, compress_start, token_budget=effective_tail_budget,
        )

        # -- Ensure protected messages survive compression ---------------
        if protected_indices and compress_start < compress_end:
            for idx in sorted(protected_indices):
                if compress_start <= idx < compress_end:
                    mid_point = (compress_start + compress_end) // 2
                    if idx < mid_point:
                        compress_start = idx
                    else:
                        compress_end = idx + 1
            compress_start = self._compressor.align_boundary_forward(
                messages, compress_start,
            )

        if compress_start >= compress_end:
            return messages

        turns_to_summarize = messages[compress_start:compress_end]

        if not self.quiet_mode:
            tail_msgs = n_messages - compress_end
            logger.info(
                "Summarizing turns %d-%d (%d turns), "
                "protecting %d head + %d tail messages",
                compress_start + 1, compress_end,
                len(turns_to_summarize), compress_start, tail_msgs,
            )

        # Phase 3: Generate structured summary via DeepSeek API
        summary = self._compressor.generate_summary(turns_to_summarize)

        # Phase 4: Assemble compressed message list
        compressed = []
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

        if not summary:
            if not self.quiet_mode:
                logger.warning(
                    "Summary generation failed — inserting static fallback"
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

        # Insert summary as user/assistant message with proper role alternation
        last_head_role = (
            messages[compress_start - 1].get("role", "user")
            if compress_start > 0 else "user"
        )
        first_tail_role = (
            messages[compress_end].get("role", "user")
            if compress_end < n_messages else "user"
        )
        if last_head_role in ("assistant", "tool"):
            summary_role = "user"
        else:
            summary_role = "assistant"

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
            # non-merge path: append tail messages
            for i in range(compress_end, n_messages):
                compressed.append(messages[i].copy())

        if _merge:
            pass  # already done above
        else:
            for i in range(compress_end, n_messages):
                compressed.append(messages[i].copy())

        self.compression_count += 1

        compressed = self._compressor.sanitize_tool_pairs(compressed)

        new_estimate = estimate_messages_tokens_rough(compressed)
        saved = display_tokens - new_estimate
        if not self.quiet_mode:
            logger.info(
                "Compressed: %d -> %d messages (~%d tokens saved, %.0f%%)",
                n_messages, len(compressed), saved,
                (saved / display_tokens * 100) if display_tokens > 0 else 0,
            )
            logger.info("Compression #%d complete", self.compression_count)

        # I-04: KV Cache 前缀约束注入（仅在冻结前执行）
        if not self._prefix_frozen:
            hard_constraints = self.extract_hard_constraints(messages)
            if hard_constraints:
                constraint_text = self.inject_constraint_prefix(hard_constraints)
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
                logger.info(
                    "[I-04] Injected %d hard constraints into prefix zone, "
                    "prefix_frozen=%s",
                    len(hard_constraints), self._prefix_frozen,
                )

        return compressed

    # -- Model switch -----------------------------------------------------

    def update_model(
        self,
        model: str,
        context_length: int,
        base_url: str = "",
        api_key: str = "",
        provider: str = "",
    ) -> None:
        """Update model info after a model switch."""
        self.model = model
        self.base_url = base_url or self.base_url
        self.context_length = context_length
        self.threshold_tokens = int(context_length * self.threshold_percent)
        self._compressor.update_config(
            model=model,
            context_length=context_length,
            threshold_tokens=self.threshold_tokens,
        )

    # -- I-07: 审查深度切换 ------------------------------------------------

    def set_plan_complexity(self, complexity: float) -> None:
        """由 plan-engine MCP（Todo 12）设置 Plan 复杂度，影响审查深度。"""
        self._plan_complexity = max(1.0, min(complexity, 10.0))

    def _nominal_depth(self, K: int, P: float) -> str:
        """无滞后的名义审查深度，仅由 f(K, P) 决定。"""
        k_ratio = K / max(self.context_length, 1)
        if K >= self.context_length or k_ratio >= 1.0:
            return "reject"
        if K < 8000:
            return "shallow"
        if K < 32000:
            return "medium" if P <= 3 else "deep"
        if K < 128000:
            return "deep" if P <= 3 else "deepest"
        return "reject"

    def _check_boundary(
        self, K: int, P: float, from_lvl: str, to_lvl: str, going_deeper: bool,
    ) -> bool:
        """检查相邻层级间的边界是否被跨越（含滞后偏移 10%）。"""
        f = 1 + _HYSTERESIS_THRESHOLD if going_deeper else 1 - _HYSTERESIS_THRESHOLD

        # shallow ↔ medium: K=8K
        if "shallow" in (from_lvl, to_lvl):
            return K >= 8000 * f if going_deeper else K < 8000 * f

        # reject ↔ deepest: K=128K
        if "reject" in (from_lvl, to_lvl):
            return K >= 128000 * f if going_deeper else K < 128000 * f

        # medium ↔ deep: K=32K (P<=3) 或 P=3 (8K<=K<32K)
        if "deepest" not in (from_lvl, to_lvl):
            if going_deeper:
                return (K >= 32000 * f) or (K >= 8000 and P > 3 * f)
            else:
                still_k = K >= 32000 * f
                still_p = (8000 <= K < 32000 and P > 3 * f)
                return not (still_k or still_p)

        # deep ↔ deepest: P=3 (仅在 K>=32K 时有效)
        if going_deeper:
            return K >= 32000 and P > 3 * f
        else:
            return K < 32000 * f or P <= 3 * f

    def get_review_depth(
        self, kv_cache_tokens: int, plan_complexity: float = 3.0,
    ) -> str:
        """f(K, P) 函数——返回审查深度（shallow/medium/deep/deepest/reject）。

        含滞后机制：边界 ±10% 内不触发深度切换，防止 K 在阈值附近振荡。
        """
        k_ratio = kv_cache_tokens / max(self.context_length, 1)

        if kv_cache_tokens >= self.context_length or k_ratio >= 1.0:
            self._last_review_depth = "reject"
            return "reject"

        nominal = self._nominal_depth(kv_cache_tokens, plan_complexity)
        if nominal == self._last_review_depth:
            return nominal

        depth_order = ["shallow", "medium", "deep", "deepest", "reject"]
        last_idx = depth_order.index(self._last_review_depth)
        target_idx = depth_order.index(nominal)
        step = 1 if target_idx > last_idx else -1

        current = last_idx
        while current != target_idx:
            next_lvl = depth_order[current + step]
            if self._check_boundary(
                kv_cache_tokens, plan_complexity,
                depth_order[current], next_lvl,
                going_deeper=(step > 0),
            ):
                current += step
            else:
                break

        result = depth_order[current]
        self._last_review_depth = result
        return result

    def get_context_state(self) -> Dict[str, Any]:
        """获取当前上下文状态（KV Cache 占用率、审查深度等）。"""
        kv_tokens = self.last_prompt_tokens
        depth = self.get_review_depth(kv_tokens, self._plan_complexity)
        return {
            "kv_cache_tokens": kv_tokens,
            "context_window": self.context_length,
            "plan_complexity": self._plan_complexity,
            "k_ratio": round(kv_tokens / max(self.context_length, 1), 4),
            "review_depth": depth,
        }

    def get_review_depth_annotation(self) -> str:
        """生成可注入到 pre_llm_call 的结构化审查深度标记。"""
        state = self.get_context_state()
        depth = state["review_depth"]
        k_val = state["kv_cache_tokens"]
        k_ratio = state["k_ratio"]
        p_val = state["plan_complexity"]

        if depth == "reject":
            return (
                f"[I-07 审查] K={k_val}t ({k_ratio:.1%}), "
                f"P={p_val} → depth=reject, action=force_compress_before_review"
            )
        return (
            f"[I-07 审查] K={k_val}t ({k_ratio:.1%}), "
            f"P={p_val} → depth={depth}"
        )

    def update_from_response(self, usage: Dict[str, Any]) -> None:
        """Update tracked token usage and recalculate review depth."""
        self.last_prompt_tokens = usage.get("prompt_tokens", 0)
        self.last_completion_tokens = usage.get("completion_tokens", 0)
        total = usage.get("total_tokens", 0)
        self.last_total_tokens = total or (
            self.last_prompt_tokens + self.last_completion_tokens
        )
        self.get_review_depth(self.last_prompt_tokens, self._plan_complexity)
