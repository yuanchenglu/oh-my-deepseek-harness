"""gate.py 纯函数单元测试 — 验证 I-02 双向原语 + I-08 范围控制 + 硬约束提取。

测试 gate.py 中所有平台无关的核心函数：
  - extract_hard_constraints()
  - set_hard_constraints() / get_hard_constraints()
  - core_reminders()
  - build_map_navigation()
  - build_gate_context()

不依赖任何 Hermes API，所有输入通过函数参数传入。
"""

import os
import tempfile
from unittest import mock

from platform_core.gate import (
    extract_hard_constraints,
    set_hard_constraints,
    get_hard_constraints,
    _current_hard_constraints,
    core_reminders,
    build_map_navigation,
    build_gate_context,
)


# ========= 硬约束提取测试 =========


class TestExtractHardConstraints:
    def test_extract_single(self):
        """能提取单条硬约束。"""
        r = extract_hard_constraints("不能修改配置文件")
        assert len(r) >= 1
        assert "不能修改配置文件" in r

    def test_extract_multiple(self):
        """能提取多条硬约束。"""
        r = extract_hard_constraints("不能删除数据库。不要重启服务。")
        assert len(r) >= 2
        assert any("不能删除数据库" in c for c in r)
        assert any("不要重启服务" in c for c in r)

    def test_no_constraints(self):
        """无约束关键词返回空集合。"""
        assert extract_hard_constraints("请帮我写一个函数") == set()

    def test_short_text_no_match(self):
        """极短文本不命中。"""
        assert extract_hard_constraints("可以") == set()

    def test_non_string_returns_empty(self):
        """非字符串输入返回空集合。"""
        assert extract_hard_constraints(123) == set()  # type: ignore
        assert extract_hard_constraints("") == set()


# ========= 硬约束状态通道测试 =========


class TestHardConstraintsState:
    def teardown_method(self):
        _current_hard_constraints.clear()

    def test_set_and_get(self):
        set_hard_constraints({"不能修改配置", "不要删除日志"})
        r = get_hard_constraints()
        assert len(r) == 2
        assert "不能修改配置" in r
        assert "不要删除日志" in r

    def test_set_replaces(self):
        set_hard_constraints({"旧约束"})
        set_hard_constraints({"新约束"})
        r = get_hard_constraints()
        assert "旧约束" not in r
        assert "新约束" in r

    def test_get_returns_copy(self):
        """get_hard_constraints 返回快照，修改不影响模块级变量。"""
        set_hard_constraints({"测试"})
        r = get_hard_constraints()
        r.add("不应影响原始集合")
        assert "不应影响原始集合" not in get_hard_constraints()


# ========= 核心提醒测试 =========


class TestCoreReminders:
    def test_returns_list(self):
        r = core_reminders()
        assert isinstance(r, list)
        assert len(r) == 2

    def test_l1_is_first_item(self):
        r = core_reminders()
        assert "[L1]" in r[0]

    def test_l2_is_second_item(self):
        r = core_reminders()
        assert "[L2]" in r[1]


# ========= MAP 导航测试 =========


class TestBuildMapNavigation:
    def test_file_not_found_returns_empty(self):
        """文件不存在时返回空字符串。"""
        r = build_map_navigation("/tmp/nonexistent-map-xxx.md")
        assert r == ""

    def test_reads_file_content(self):
        """能读取 MAP.md 文件内容。"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("# MAP\n- 记忆1\n- 记忆2")
            fpath = f.name
        try:
            r = build_map_navigation(fpath)
            assert "[MAP]" in r
            assert "记忆1" in r
            assert "记忆2" in r
        finally:
            os.unlink(fpath)

    def test_empty_file_returns_empty(self):
        """空文件返回空字符串。"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            fpath = f.name
        try:
            r = build_map_navigation(fpath)
            assert r == ""
        finally:
            os.unlink(fpath)


# ========= 门控上下文构建测试 =========


class TestBuildGateContext:
    def teardown_method(self):
        _current_hard_constraints.clear()

    def test_first_turn_has_full_content(self):
        """首轮注入完整 L1/L2/MAP/I-02/I-08。"""
        r = build_gate_context(is_first_turn=True, map_path="/tmp/nonexistent-map.md")
        assert r is not None
        ctx = r["context"]
        assert "L1" in ctx
        assert "L2" in ctx
        assert "I-02" in ctx
        assert "I-08" in ctx

    def test_first_turn_no_map_file_skips_map(self):
        """首轮但 MAP 文件不存在时应跳过 MAP 块。"""
        r = build_gate_context(is_first_turn=True, map_path="/tmp/nonexistent-map.md")
        assert "[MAP]" not in r["context"]

    def test_non_first_turn_uses_brief(self):
        """非首轮注入简短 I-02/I-08。"""
        r = build_gate_context(is_first_turn=False)
        ctx = r["context"]
        assert "L1" in ctx
        assert "L2" in ctx
        assert "[I-02]" in ctx or "/propose_skill" not in ctx
        assert "[I-08]" in ctx or "范围控制" in ctx

    def test_extracts_constraints_from_user_message(self):
        """从 user_message 提取硬约束并更新状态。"""
        _current_hard_constraints.clear()
        build_gate_context(is_first_turn=True, user_message="不能修改配置文件")
        assert len(get_hard_constraints()) >= 1
        _current_hard_constraints.clear()

    def test_empty_message_no_constraints(self):
        """空消息不应提取约束。"""
        _current_hard_constraints.clear()
        build_gate_context(is_first_turn=True, user_message="")
        assert len(get_hard_constraints()) == 0

    def test_always_returns_context_key(self):
        """始终返回包含 context 的 dict。"""
        r = build_gate_context(is_first_turn=True)
        assert "context" in r
        assert r["context"]
