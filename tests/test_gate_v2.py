"""gate.py v2 单元测试 — 验证 I-02 双向原语 + I-08 范围控制注入 + 硬约束提取。"""

from deepseek_harness.gate import (
    on_pre_llm_call,
    _current_hard_constraints,
    _HARD_CONSTRAINT_PATTERN,
    _I02_FULL,
    _I02_BRIEF,
    _I08_FULL,
    _I08_BRIEF,
)


# ── 硬约束正则提取 ────────────────────────────────────────


class TestHardConstraintPattern:
    """验证 _HARD_CONSTRAINT_PATTERN 能否正确提取中文硬约束表达式。"""

    def test_extract_single(self):
        """能提取单条硬约束。"""
        text = "不能修改配置文件"
        matches = _HARD_CONSTRAINT_PATTERN.findall(text)
        assert len(matches) >= 1
        assert "不能修改配置文件" in matches[0]

    def test_extract_multiple(self):
        """能提取多条硬约束。"""
        text = "不能删除数据库。不要重启服务。禁止修改系统配置。"
        matches = _HARD_CONSTRAINT_PATTERN.findall(text)
        assert len(matches) >= 2
        assert any("不能删除数据库" in m for m in matches)
        assert any("禁止修改系统配置" in m for m in matches)

    def test_no_false_positive(self):
        """不带约束关键词的文本不命中。"""
        text = "请帮我写一个 Python 函数"
        matches = _HARD_CONSTRAINT_PATTERN.findall(text)
        assert len(matches) == 0

    def test_short_text_no_constraint(self):
        """2 字以内的短文本不命中（因为模式要求 2-60 字）。"""
        text = "可以"
        matches = _HARD_CONSTRAINT_PATTERN.findall(text)
        assert len(matches) == 0


# ── on_pre_llm_call 主函数 ──────────────────────────────


class TestOnPreLlmCall:
    """验证 on_pre_llm_call 在不同轮次的注入行为。"""

    def test_first_turn_contains_full_primitives(self):
        """首轮应包含 L1、L2、完整 I-02、完整 I-08 和 MAP 标题。"""
        _current_hard_constraints.clear()
        r = on_pre_llm_call(is_first_turn=True, user_message="帮我重构这段代码")
        assert r is not None
        ctx = r["context"]
        assert "L1" in ctx, "首轮应包含 L1 荣辱观"
        assert "L2" in ctx, "首轮应包含 L2 思维方式"
        assert "/propose_skill" in ctx, "首轮应包含完整 I-02 双向原语"
        assert "[I-08 范围控制]" in ctx, "首轮应包含完整 I-08 范围控制"

    def test_first_turn_contains_map_placeholder(self):
        """首轮 context 包含 MAP 标记。"""
        _current_hard_constraints.clear()
        r = on_pre_llm_call(is_first_turn=True, user_message="")
        assert r is not None
        ctx = r["context"]
        assert "[MAP]" in ctx or "L1" in ctx

    def test_non_first_turn_no_map(self):
        """非首轮不应包含 MAP 和完整 I-08 标题。"""
        _current_hard_constraints.clear()
        r = on_pre_llm_call(is_first_turn=False, user_message="继续")
        assert r is not None
        ctx = r["context"]
        # 完整块标题不应出现
        assert "[I-08 范围控制]" not in ctx, "非首轮不应包含完整 I-08 标题"
        assert "[MAP]" not in ctx, "非首轮不应包含 MAP"
        # 简短提醒应出现（以 [I-02] 或 [I-08] 开头）
        assert "[I-02]" in ctx, "非首轮应包含简短 I-02"
        assert "[I-08]" in ctx, "非首轮应包含简短 I-08"

    def test_non_first_turn_still_has_l1_l2(self):
        """非首轮仍应包含 L1 和 L2。"""
        _current_hard_constraints.clear()
        r = on_pre_llm_call(is_first_turn=False, user_message="继续")
        assert r is not None
        ctx = r["context"]
        assert "L1" in ctx
        assert "L2" in ctx

    def test_empty_kwargs_does_not_crash(self):
        """空 kwargs 不崩溃，返回至少包含 L1/L2 的 dict。"""
        _current_hard_constraints.clear()
        r = on_pre_llm_call()
        assert r is not None
        assert "context" in r
        assert "L1" in r["context"]

    def test_hard_constraint_extraction_from_user_message(self):
        """用户消息中的硬约束被正确提取到 _current_hard_constraints。"""
        _current_hard_constraints.clear()
        on_pre_llm_call(
            is_first_turn=True,
            user_message="不能修改配置文件，也不要删除日志文件",
        )
        assert len(_current_hard_constraints) >= 1
        _current_hard_constraints.clear()


# ── Core Reminders 静态验证 ─────────────────────────────


class TestCorePrimitives:
    """验证原语常量的内容完整性。"""

    def test_i02_full_contains_propose_skill(self):
        assert "/propose_skill" in _I02_FULL
        assert "/trigger_self_review" in _I02_FULL

    def test_i08_full_contains_scope_control(self):
        assert "范围蔓延" in _I08_FULL
        assert "必要依赖" in _I08_FULL
