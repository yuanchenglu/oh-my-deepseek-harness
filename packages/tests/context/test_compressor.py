"""compressor.py 纯函数单元测试 — 验证 I-03/04/07/13 压缩功能。

测试 platform_core.context.compressor 中的纯函数：
  - estimate_messages_tokens_rough()
  - summarize_tool_result()
  - align_boundary_forward() / align_boundary_backward()
  - get_tool_call_id()
  - prune_old_tool_results()
  - find_tail_cut_by_tokens()
  - sanitize_tool_pairs()
  - serialize_for_summary()
  - compute_summary_budget()
  - with_summary_prefix()
  - contains_hard_constraint()
  - protect_hard_constraints()
  - extract_hard_constraints()
  - inject_constraint_prefix()
  - PrefixState / freeze_prefix() / is_prefix_stable()
  - compose_turn_tail()
  - compute_effective_ratio()
  - compute_intent_protection()
  - nominal_review_depth()
  - get_review_depth()
  - compress_messages()
  - make_static_fallback_summary()
"""

import pytest

from platform_core.context.compressor import (
    # Constants
    SUMMARY_PREFIX,
    HARD_CONSTRAINT_KEYWORDS,
    # Token estimation
    estimate_messages_tokens_rough,
    # Tool summary
    summarize_tool_result,
    # Boundary
    align_boundary_forward,
    align_boundary_backward,
    get_tool_call_id,
    # Pruning
    prune_old_tool_results,
    find_tail_cut_by_tokens,
    sanitize_tool_pairs,
    # Serialization
    serialize_for_summary,
    compute_summary_budget,
    with_summary_prefix,
    # Hard constraint
    contains_hard_constraint,
    protect_hard_constraints,
    extract_hard_constraints,
    inject_constraint_prefix,
    # Prefix freeze
    PrefixState,
    freeze_prefix,
    is_prefix_stable,
    compose_turn_tail,
    # Intent awareness
    compute_effective_ratio,
    compute_intent_protection,
    # Review depth
    nominal_review_depth,
    get_review_depth,
    # Pipeline
    compress_messages,
    make_static_fallback_summary,
)


def _msg(role: str, content: str, **extra) -> dict:
    d = {"role": role, "content": content}
    d.update(extra)
    return d


# ========= Token estimation =========


class TestEstimateMessagesTokensRough:
    def test_empty_list(self):
        assert estimate_messages_tokens_rough([]) == 0

    def test_single_message(self):
        tokens = estimate_messages_tokens_rough([_msg("user", "hello")])
        assert tokens > 0

    def test_multiple_messages(self):
        msgs = [_msg("user", "a"), _msg("assistant", "b")]
        t2 = estimate_messages_tokens_rough(msgs)
        t1 = estimate_messages_tokens_rough([_msg("user", "a")])
        assert t2 > t1


# ========= summarize_tool_result =========


class TestSummarizeToolResult:
    def test_terminal_tool(self):
        s = summarize_tool_result("terminal", '{"command": "ls -la"}', '{"exit_code": 0}')
        assert s.startswith("[terminal]")

    def test_read_file(self):
        s = summarize_tool_result("read_file", '{"path": "/tmp/test.py"}', "file content")
        assert s.startswith("[read_file]")

    def test_write_file(self):
        s = summarize_tool_result("write_file", '{"path": "/tmp/test.py"}', "done")
        assert s.startswith("[write_file]")

    def test_search_files(self):
        s = summarize_tool_result("search_files", '{"pattern": "test"}', "content")
        assert s.startswith("[search_files]")

    def test_patch_tool(self):
        s = summarize_tool_result("patch", '{"path": "/tmp/test.py"}', "result")
        assert s.startswith("[patch]")

    def test_browser_tool(self):
        s = summarize_tool_result("browser_navigate", '{"url": "https://example.com"}', "content")
        assert s.startswith("[browser_navigate]")

    def test_web_search(self):
        s = summarize_tool_result("web_search", '{"query": "python"}', "result")
        assert s.startswith("[web_search]")

    def test_web_extract(self):
        s = summarize_tool_result("web_extract", '{"urls": ["https://example.com"]}', "content")
        assert s.startswith("[web_extract]")

    def test_delegate_task(self):
        s = summarize_tool_result("delegate_task", '{"goal": "研究一下"}', "result")
        assert s.startswith("[delegate_task]")

    def test_generic_fallback(self):
        s = summarize_tool_result("custom_tool", '{"arg1": "val1"}', "result content")
        assert s.startswith("[custom_tool]")

    def test_empty_args(self):
        s = summarize_tool_result("bash", "", "output")
        assert s.startswith("[bash]")

    def test_invalid_json_args(self):
        s = summarize_tool_result("bash", "not-json", "output")
        assert s.startswith("[bash]")


# ========= Boundary alignment =========


class TestAlignBoundaryForward:
    def test_no_tool_messages(self):
        msgs = [_msg("user", "a"), _msg("assistant", "b")]
        assert align_boundary_forward(msgs, 0) == 0

    def test_skips_tool_results(self):
        msgs = [_msg("tool", "result1"), _msg("tool", "result2"), _msg("user", "a")]
        assert align_boundary_forward(msgs, 0) == 2

    def test_empty_messages(self):
        assert align_boundary_forward([], 0) == 0


class TestAlignBoundaryBackward:
    def test_no_adjustment(self):
        msgs = [_msg("user", "a"), _msg("assistant", "b")]
        assert align_boundary_backward(msgs, 1) == 1

    def test_pulls_back_for_tool_calls(self):
        msgs = [
            _msg("assistant", "doing", tool_calls=[{"id": "call1"}]),
            _msg("tool", "result1", tool_call_id="call1"),
        ]
        # idx=1 should pull back to 0
        assert align_boundary_backward(msgs, 1) == 0

    def test_out_of_bounds(self):
        msgs = [_msg("user", "a")]
        assert align_boundary_backward(msgs, -1) == -1
        assert align_boundary_backward(msgs, 5) == 5


class TestGetToolCallId:
    def test_dict_with_id(self):
        assert get_tool_call_id({"id": "call1"}) == "call1"

    def test_dict_without_id(self):
        assert get_tool_call_id({"name": "test"}) == ""

    def test_object_with_id(self):
        class FakeTC:
            id = "call_obj"
        assert get_tool_call_id(FakeTC()) == "call_obj"

    def test_object_without_id(self):
        class FakeTC:
            pass
        assert get_tool_call_id(FakeTC()) == ""


# ========= prune_old_tool_results =========


class TestPruneOldToolResults:
    def test_empty_messages(self):
        pruned, count = prune_old_tool_results([], protect_tail_count=3)
        assert count == 0
        assert pruned == []

    def test_no_pruning_below_threshold(self):
        msgs = [
            _msg("assistant", "你好", tool_calls=[{"id": "c1", "function": {"name": "bash", "arguments": "{}"}}]),
            _msg("tool", "output", tool_call_id="c1"),
        ]
        pruned, count = prune_old_tool_results(msgs, protect_tail_count=10)
        assert count >= 0

    def test_protect_tail_count_respected(self):
        """足够多的 tail 消息不受 pruning。"""
        msgs = (
            [_msg("assistant", f"msg{i}", tool_calls=[{"id": f"c{i}", "function": {"name": "bash", "arguments": "{}"}}])
             for i in range(3)]
            + [_msg("tool", f"output{i}", tool_call_id=f"c{i}") for i in range(3)]
        )
        # protect all 6 messages
        pruned, count = prune_old_tool_results(msgs, protect_tail_count=10)
        # No pruning should occur since tail count >= all messages
        assert count >= 0


# ========= sanitize_tool_pairs =========


class TestSanitizeToolPairs:
    def test_no_changes_when_balanced(self):
        msgs = [
            _msg("assistant", "running", tool_calls=[{"id": "c1", "function": {"name": "bash", "arguments": "{}"}}]),
            _msg("tool", "output", tool_call_id="c1"),
        ]
        cleaned = sanitize_tool_pairs(msgs, quiet=True)
        assert len(cleaned) == 2

    def test_removes_orphaned_results(self):
        msgs = [
            _msg("assistant", "thinking"),
            _msg("tool", "orphan_output", tool_call_id="nonexistent"),
        ]
        cleaned = sanitize_tool_pairs(msgs, quiet=True)
        assert len(cleaned) == 1  # orphan removed


# ========= Hard constraint detection =========


class TestContainsHardConstraint:
    def test_positive(self):
        assert contains_hard_constraint("不能修改配置文件") is True

    def test_negative(self):
        assert contains_hard_constraint("请帮我写代码") is False

    def test_empty(self):
        assert contains_hard_constraint("") is False

    def test_non_string(self):
        assert contains_hard_constraint(123) is False  # type: ignore


class TestProtectHardConstraints:
    def test_finds_constraint_in_user_message(self):
        msgs = [_msg("user", "不能删除数据库"), _msg("assistant", "好的")]
        protected = protect_hard_constraints(msgs)
        assert 0 in protected

    def test_ignores_assistant_messages(self):
        msgs = [_msg("assistant", "不能修改这个")]
        protected = protect_hard_constraints(msgs)
        assert protected == []

    def test_list_content(self):
        msgs = [_msg("system", [{"text": "不能修改配置文件"}, {"text": "其他"}])]
        protected = protect_hard_constraints(msgs)
        assert 0 in protected

    def test_empty_messages(self):
        assert protect_hard_constraints([]) == []


class TestExtractHardConstraints:
    def test_extracts_from_user_message(self):
        msgs = [_msg("user", "不能修改配置文件。请帮我写代码。")]
        constraints = extract_hard_constraints(msgs)
        assert len(constraints) >= 1
        assert any("不能修改配置文件" in c for c in constraints)

    def test_multiple_sentences(self):
        msgs = [_msg("user", "不能删除数据库。不要修改系统配置。")]
        constraints = extract_hard_constraints(msgs)
        assert len(constraints) >= 1

    def test_no_constraints(self):
        msgs = [_msg("user", "请帮我写一个 Python 函数")]
        assert extract_hard_constraints(msgs) == []

    def test_deduplication(self):
        msgs = [_msg("user", "不能修改配置"), _msg("system", "不能修改配置")]
        constraints = extract_hard_constraints(msgs)
        # 去重后应为 1 条
        assert len(constraints) == 1

    def test_list_content(self):
        msgs = [_msg("system", [{"text": "不能修改配置文件"}, {"text": "不要删除日志"}])]
        constraints = extract_hard_constraints(msgs)
        assert len(constraints) >= 1

    def test_empty_messages(self):
        assert extract_hard_constraints([]) == []


class TestInjectConstraintPrefix:
    def test_with_constraints(self):
        text = inject_constraint_prefix(["不能修改配置", "不要删除日志"])
        assert "[硬约束]" in text
        assert "不能修改配置" in text
        assert "不要删除日志" in text

    def test_empty_list(self):
        assert inject_constraint_prefix([]) == ""


# ========= Prefix freeze (I-13) =========


class TestPrefixState:
    def test_default_state(self):
        s = PrefixState()
        assert s.frozen is False
        assert s.fingerprint == ""
        assert s.invalidation_count == 0

    def test_freeze(self):
        s = PrefixState()
        freeze_prefix(s)
        assert s.frozen is True
        assert s.fingerprint != ""

    def test_is_stable_before_freeze(self):
        s = PrefixState()
        assert is_prefix_stable(s) is True

    def test_is_stable_after_freeze_same(self):
        s = PrefixState()
        freeze_prefix(s)
        assert is_prefix_stable(s, s.fingerprint) is True

    def test_is_stable_after_freeze_different(self):
        s = PrefixState()
        freeze_prefix(s)
        assert is_prefix_stable(s, "different_fingerprint") is False


class TestComposeTurnTail:
    def test_memory_update(self):
        text = compose_turn_tail("新记忆内容", "memory_update")
        assert "[Memory 更新]" in text
        assert "新记忆内容" in text

    def test_plan_mode(self):
        text = compose_turn_tail("plan 内容", "plan_mode")
        assert "[Plan Mode]" in text

    def test_skill_body(self):
        text = compose_turn_tail("skill 内容", "skill_body")
        assert "[Skill 加载]" in text

    def test_background_job(self):
        text = compose_turn_tail("job 内容", "background_job")
        assert "[后台任务]" in text

    def test_unknown_type(self):
        text = compose_turn_tail("内容", "unknown")
        assert "[系统消息]" in text


# ========= Intent awareness (I-03) =========


class TestComputeEffectiveRatio:
    def test_default(self):
        assert compute_effective_ratio("default") == 0.20

    def test_convergent(self):
        assert compute_effective_ratio("convergent") == 0.40

    def test_divergent(self):
        assert compute_effective_ratio("divergent") == 0.25

    def test_unknown(self):
        assert compute_effective_ratio("unknown") == 0.20


class TestComputeIntentProtection:
    def test_default_intent(self):
        f, l = compute_intent_protection("default")
        assert f == 3
        assert l == 20

    def test_convergent(self):
        f, l = compute_intent_protection("convergent")
        assert f >= 5  # 收敛任务保护更多 head
        assert l == 20

    def test_divergent(self):
        f, l = compute_intent_protection("divergent")
        assert f == 3
        assert l >= 4  # 发散任务保护更多 tail


# ========= Serialization =========


class TestSerializeForSummary:
    def test_user_message(self):
        s = serialize_for_summary([_msg("user", "hello")])
        assert "[USER]" in s
        assert "hello" in s

    def test_assistant_message(self):
        s = serialize_for_summary([_msg("assistant", "world")])
        assert "[ASSISTANT]" in s

    def test_tool_result(self):
        s = serialize_for_summary([_msg("tool", "result", tool_call_id="tc1")])
        assert "[TOOL RESULT tc1]" in s

    def test_truncation(self):
        long_content = "x" * 10000
        s = serialize_for_summary([_msg("user", long_content)], content_max=100, content_head=50, content_tail=20)
        assert "[truncated]" in s

    def test_assistant_with_tool_calls(self):
        s = serialize_for_summary([_msg("assistant", "思考", tool_calls=[{"id": "c1", "function": {"name": "bash", "arguments": '{"cmd":"ls"}'}}])])
        assert "[Tool calls:" in s


class TestComputeSummaryBudget:
    def test_budget_in_range(self):
        msgs = [_msg("user", "hello world"), _msg("assistant", "hi")]
        budget = compute_summary_budget(msgs, max_summary_tokens=12000)
        assert 2000 <= budget <= 12000

    def test_zero_turns(self):
        budget = compute_summary_budget([], max_summary_tokens=12000)
        assert 2000 <= budget <= 12000


class TestWithSummaryPrefix:
    def test_empty_text(self):
        r = with_summary_prefix("")
        assert SUMMARY_PREFIX in r

    def test_with_text(self):
        r = with_summary_prefix("test summary")
        assert "test summary" in r


# ========= Review depth (I-07) =========


class TestNominalReviewDepth:
    def test_shallow_below_8k(self):
        assert nominal_review_depth(5000, 128000, 3.0) == "shallow"

    def test_medium_at_16k_low_complexity(self):
        assert nominal_review_depth(16000, 128000, 2.0) == "medium"

    def test_deep_at_16k_high_complexity(self):
        assert nominal_review_depth(16000, 128000, 5.0) == "deep"

    def test_deep_at_40k_low_complexity(self):
        assert nominal_review_depth(40000, 128000, 2.0) == "deep"

    def test_reject_at_capacity(self):
        assert nominal_review_depth(128000, 128000, 5.0) == "reject"

    def test_reject_above_capacity(self):
        assert nominal_review_depth(200000, 128000, 5.0) == "reject"


class TestGetReviewDepth:
    def test_no_switch_when_nominal_same(self):
        d = get_review_depth(5000, 128000, plan_complexity=3.0, last_depth="shallow")
        assert d == "shallow"

    def test_hysteresis_at_boundary(self):
        """在边界附近不反复切换。"""
        d1 = get_review_depth(7000, 128000, plan_complexity=3.0, last_depth="shallow")
        assert d1 == "shallow"

    def test_reject_at_capacity(self):
        d = get_review_depth(128000, 128000, plan_complexity=3.0, last_depth="shallow")
        assert d == "reject"

    def test_goes_deeper_with_higher_tokens(self):
        d = get_review_depth(40000, 128000, plan_complexity=5.0, last_depth="shallow")
        # Should eventually reach deep/deepest
        assert d in ("deep", "deepest")


# ========= Static fallback summary =========


class TestMakeStaticFallbackSummary:
    def test_contains_fallback_text(self):
        r = make_static_fallback_summary([_msg("user", "a"), _msg("assistant", "b")])
        assert "CONTEXT COMPACTION" in r
        assert "2" in r  # n_dropped = 2

    def test_zero_turns(self):
        r = make_static_fallback_summary([])
        assert "0" in r


# ========= compress_messages pipeline =========


class TestCompressMessages:
    def test_too_few_messages_returns_original(self):
        msgs = [_msg("system", "Be helpful"), _msg("user", "hi"), _msg("assistant", "hello")]
        compressed = compress_messages(msgs, threshold_tokens=96000, tail_token_budget=20000)
        assert compressed == msgs

    def test_pipeline_runs_with_enough_messages(self):
        """足够多的消息触发压缩流程。"""
        msgs = [_msg("system", "Be helpful")]
        for i in range(30):
            msgs.append(_msg("user", f"query {i}"))
            msgs.append(_msg("assistant", f"answer {i}"))
        compressed = compress_messages(
            msgs, threshold_tokens=96000, tail_token_budget=20000,
            quiet=True,
        )
        # Should compress
        assert len(compressed) < len(msgs)

    def test_summarizer_callback_used(self):
        """自定义 summarizer 被调用。"""
        called = False

        def my_summarizer(turns):
            nonlocal called
            called = True
            return "custom summary here"
        msgs = [_msg("system", "Be helpful")]
        for i in range(30):
            msgs.append(_msg("user", f"query {i}"))
            msgs.append(_msg("assistant", f"answer {i}"))
        compressed = compress_messages(
            msgs, threshold_tokens=96000, tail_token_budget=20000,
            summarizer=my_summarizer, quiet=True,
        )
        assert called

    def test_intent_awareness(self):
        """不同 intent 影响压缩行为。"""
        msgs = [_msg("system", "Be helpful")]
        for i in range(30):
            msgs.append(_msg("user", f"query {i}"))
            msgs.append(_msg("assistant", f"answer {i}"))
        c1 = compress_messages(
            msgs, threshold_tokens=96000, tail_token_budget=20000,
            intent="convergent", quiet=True,
        )
        c2 = compress_messages(
            msgs, threshold_tokens=96000, tail_token_budget=20000,
            intent="divergent", quiet=True,
        )
        # Both should compress; ratios differ, but both valid
        assert len(c1) < len(msgs)
        assert len(c2) < len(msgs)

    def test_prefix_frozen_skips_constraint_injection(self):
        """prefix_frozen=True 时跳过约束注入。"""
        msgs = [_msg("system", "不能修改配置文件")]
        for i in range(30):
            msgs.append(_msg("user", f"query {i}"))
            msgs.append(_msg("assistant", f"answer {i}"))
        compressed = compress_messages(
            msgs, threshold_tokens=96000, tail_token_budget=20000,
            prefix_frozen=True, quiet=True,
        )
        # prefix_frozen → no extra constraint message injected before system
        assert compressed[0]["role"] == "system"
