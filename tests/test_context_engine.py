"""Context Engine unit and concurrency tests for I-03/04/07/13 and CTX-004."""

from concurrent.futures import ThreadPoolExecutor
from threading import Lock

import pytest

from deepseek_context import DeepSeekContextEngine


# ── Fixtures ─────────────────────────────────────────────


def make_engine(**overrides) -> DeepSeekContextEngine:
    """创建测试用的 ContextEngine 实例（安静模式 + 小窗口）。"""
    defaults = dict(
        model="deepseek-chat",
        context_length=128_000,
        quiet_mode=True,
    )
    defaults.update(overrides)
    return DeepSeekContextEngine(**defaults)


def make_msg(role: str, content: str) -> dict:
    return {"role": role, "content": content}


# ========= I-03 注意力预算 =========


class TestI03IntentAwareness:
    """验证 I-03 意图感知的差异化压缩策略。"""

    def test_default_intent(self):
        e = make_engine()
        assert e.get_intent() == "default"

    def test_set_intent_valid(self):
        e = make_engine()
        e.set_intent("convergent")
        assert e.get_intent() == "convergent"
        e.set_intent("divergent")
        assert e.get_intent() == "divergent"

    def test_set_intent_invalid_falls_to_default(self):
        e = make_engine()
        e.set_intent("unknown")
        assert e.get_intent() == "default"

    def test_compute_effective_ratio_default(self):
        e = make_engine(summary_target_ratio=0.20)
        assert e._compute_effective_ratio() == 0.20

    def test_compute_effective_ratio_convergent(self):
        e = make_engine(convergent_target_ratio=0.40)
        e.set_intent("convergent")
        assert e._compute_effective_ratio() == 0.40

    def test_compute_effective_ratio_divergent(self):
        e = make_engine(divergent_target_ratio=0.25)
        e.set_intent("divergent")
        assert e._compute_effective_ratio() == 0.25


# ========= I-03 hard constraint protection =========


class TestI03HardConstraintProtection:
    """验证 _contains_hard_constraint 和 protect_hard_constraints。"""

    def test_contains_hard_constraint_positive(self):
        assert DeepSeekContextEngine._contains_hard_constraint("不能修改配置文件") is True

    def test_contains_hard_constraint_negative(self):
        assert DeepSeekContextEngine._contains_hard_constraint("请帮我写代码") is False

    def test_contains_hard_constraint_empty(self):
        assert DeepSeekContextEngine._contains_hard_constraint("") is False

    def test_protect_hard_constraints_finds_indices(self):
        e = make_engine()
        messages = [
            make_msg("system", "你是助手"),
            make_msg("user", "不能删除数据库"),
            make_msg("user", "请帮我写一个函数"),
        ]
        protected = e.protect_hard_constraints(messages)
        assert 1 in protected
        assert 0 not in protected

    def test_protect_hard_constraints_with_list_content(self):
        e = make_engine()
        messages = [
            make_msg("system", [{"text": "不能修改配置文件"}, {"text": "其他内容"}]),
            make_msg("user", "安全的内容"),
        ]
        protected = e.protect_hard_constraints(messages)
        assert 0 in protected


# ========= I-04 KV Cache 前缀约束隔离 =========


class TestI04HardConstraintExtraction:
    """验证 extract_hard_constraints 和 inject_constraint_prefix。"""

    def test_extract_simple(self):
        e = make_engine()
        messages = [make_msg("user", "不能修改配置文件。请帮我写代码。")] 
        constraints = e.extract_hard_constraints(messages)
        assert len(constraints) >= 1
        assert "不能修改配置文件" in constraints[0]

    def test_extract_multiple_sentences(self):
        e = make_engine()
        messages = [make_msg("user", "不能删除数据库。不要修改系统配置。")] 
        constraints = e.extract_hard_constraints(messages)
        assert len(constraints) >= 1

    def test_extract_no_constraints(self):
        e = make_engine()
        messages = [make_msg("user", "请帮我写一个 Python 函数")]
        constraints = e.extract_hard_constraints(messages)
        assert constraints == []

    def test_inject_constraint_prefix(self):
        e = make_engine()
        text = e.inject_constraint_prefix(["不能修改配置", "不要删除日志"])
        assert "[硬约束]" in text
        assert "不能修改配置" in text
        assert "不要删除日志" in text

    def test_inject_empty(self):
        e = make_engine()
        assert e.inject_constraint_prefix([]) == ""


# ========= I-07 审查深度切换 =========


class TestI07ReviewDepth:
    """验证 get_review_depth 的 f(K, P) 函数和滞后机制。"""

    def test_shallow_below_8k(self):
        e = make_engine(context_length=128_000)
        d = e.get_review_depth(5000, plan_complexity=3.0)
        assert d == "shallow"

    def test_medium_16k_low_complexity(self):
        e = make_engine(context_length=128_000)
        d = e.get_review_depth(16000, plan_complexity=2.0)
        assert d == "medium"

    def test_deep_16k_high_complexity(self):
        e = make_engine(context_length=128_000)
        d = e.get_review_depth(16000, plan_complexity=5.0)
        assert d == "deep"

    def test_deep_40k_low_complexity(self):
        e = make_engine(context_length=128_000)
        d = e.get_review_depth(40000, plan_complexity=2.0)
        assert d == "deep"

    def test_deepest_40k_high_complexity(self):
        e = make_engine(context_length=128_000)
        d = e.get_review_depth(40000, plan_complexity=5.0)
        assert d == "deepest"

    def test_reject_at_context_limit(self):
        e = make_engine(context_length=128_000)
        d = e.get_review_depth(128_000, plan_complexity=5.0)
        assert d in ("reject", "deepest")

    def test_hysteresis_boundary_stability(self):
        """在阈值 8K 附近±10% 内不应反复切换。"""
        e = make_engine(context_length=128_000)
        d1 = e.get_review_depth(7000, plan_complexity=3.0)
        assert d1 == "shallow"
        d2 = e.get_review_depth(8500, plan_complexity=3.0)
        assert d2 in ("shallow", "medium")

    def test_get_context_state_structure(self):
        e = make_engine(context_length=128_000)
        state = e.get_context_state()
        assert "kv_cache_tokens" in state
        assert "context_window" in state
        assert "plan_complexity" in state
        assert "k_ratio" in state
        assert "review_depth" in state

    def test_get_review_depth_annotation(self):
        e = make_engine(context_length=128_000)
        ann = e.get_review_depth_annotation()
        assert "I-07" in ann


# ========= I-13 Byte-Stable Prefix 前缀冻结 =========


class TestI13PrefixFreeze:
    """验证 I-13 前缀冻结和稳定性检查。"""

    def test_freeze_prefix(self):
        e = make_engine()
        assert e.is_prefix_frozen() is False
        e.freeze_prefix()
        assert e.is_prefix_frozen() is True

    def test_is_prefix_stable_before_freeze(self):
        e = make_engine()
        assert e.is_prefix_stable() is True

    def test_is_prefix_stable_after_freeze_same_fingerprint(self):
        e = make_engine()
        e.freeze_prefix()
        assert e.is_prefix_stable(e._prefix_fingerprint) is True

    def test_is_prefix_stable_after_freeze_different_fingerprint(self):
        e = make_engine()
        e.freeze_prefix()
        assert e.is_prefix_stable("different_fingerprint") is False

    def test_compose_turn_tail_memory(self):
        text = DeepSeekContextEngine.compose_turn_tail("新记忆内容", "memory_update")
        assert "[Memory 更新]" in text
        assert "新记忆内容" in text

    def test_compose_turn_tail_plan_mode(self):
        text = DeepSeekContextEngine.compose_turn_tail("plan 内容", "plan_mode")
        assert "[Plan Mode]" in text

    def test_compose_turn_tail_unknown_type(self):
        text = DeepSeekContextEngine.compose_turn_tail("内容", "unknown")
        assert "[系统消息]" in text


# ========= should_compress =========


class TestShouldCompress:
    def test_below_threshold(self):
        e = make_engine(context_length=128_000)
        assert e.should_compress(50000) is False

    def test_above_threshold(self):
        e = make_engine(context_length=128_000)
        assert e.should_compress(100000) is True

    def test_default_uses_last_prompt_tokens(self):
        e = make_engine(context_length=128_000)
        e.last_prompt_tokens = 100000
        assert e.should_compress() is True


# ========= CTX-004 concurrent Session state =========


def test_concurrent_contextvars_do_not_cross_compressor_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Concurrent ContextVars restore each Session's own committed summary."""
    engine = make_engine(
        context_length=10_000,
        threshold_percent=0.5,
        protect_first_n=1,
        protect_last_n=1,
    )
    monkeypatch.setattr(
        engine._compressor,
        "prune_old_tool_results",
        lambda messages, **kwargs: (messages, 0),
    )
    monkeypatch.setattr(
        engine._compressor,
        "align_boundary_forward",
        lambda messages, start: 2,
    )
    monkeypatch.setattr(
        engine._compressor,
        "find_tail_cut_by_tokens",
        lambda messages, start, token_budget: 6,
    )

    prompt_lock = Lock()
    prompts: dict[str, list[str]] = {"session-a": [], "session-b": []}

    def fake_llm(prompt: str, max_tokens: int, model: str | None = None) -> str:
        session_id = "session-a" if "marker-a" in prompt else "session-b"
        with prompt_lock:
            prompts[session_id].append(prompt)
            sequence = len(prompts[session_id])
        return f"summary-{session_id}-{sequence}"

    monkeypatch.setattr(engine._compressor, "_call_deepseek_llm", fake_llm)

    def run_session(session_id: str, marker: str) -> None:
        engine.on_session_start(session_id)
        messages = [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "head"},
            {"role": "assistant", "content": marker * 400},
            {"role": "user", "content": "B" * 1200},
            {"role": "assistant", "content": "C" * 1200},
            {"role": "user", "content": "D" * 1200},
            {"role": "assistant", "content": "tail"},
            {"role": "user", "content": f"latest-{marker}"},
        ]
        first = engine.compress(messages, current_tokens=8_000)
        second = engine.compress(messages, current_tokens=8_000)
        assert first is not messages
        assert second is not messages

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(run_session, "session-a", "marker-a"),
            executor.submit(run_session, "session-b", "marker-b"),
        ]
        for future in futures:
            future.result()

    assert len(prompts["session-a"]) == 2
    assert len(prompts["session-b"]) == 2
    assert "summary-session-a-1" in prompts["session-a"][1]
    assert "summary-session-b-1" not in prompts["session-a"][1]
    assert "summary-session-b-1" in prompts["session-b"][1]
    assert "summary-session-a-1" not in prompts["session-b"][1]
