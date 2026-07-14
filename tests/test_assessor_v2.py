"""assessor.py v2 单元测试 — 验证 I-01 约束违反检测 + 原始内容完整性检查。"""

from deepseek_harness.assessor import on_post_tool_call, _check_constraint_violation
from deepseek_harness.gate import _current_hard_constraints


# ── 辅助：在测试中设置活跃约束 ────────────────────────────


def _set_constraints(*constraints: str) -> None:
    _current_hard_constraints.clear()
    for c in constraints:
        _current_hard_constraints.add(c)


# ========= I-01 约束违反检测 =========


class TestConstraintViolationDetection:
    """验证 I-01 约束违反检测的核心匹配逻辑。"""

    def setup_method(self):
        _current_hard_constraints.clear()

    def teardown_method(self):
        _current_hard_constraints.clear()

    # -- write 工具违反约束 --

    def test_write_violation_config_path(self):
        """write 调用了包含 'config' 关键词的路径应返回 violation。"""
        _set_constraints("不能修改配置文件")
        r = on_post_tool_call(
            tool_name="write",
            args={"filePath": "/etc/nginx/nginx.conf"},
            session_id="test-session",
            result="done",
        )
        assert r is not None
        assert r["quality"] == "violation"
        assert r["constraint"] == "不能修改配置文件"

    def test_write_non_violation_other_path(self):
        """write 调用不相关路径不应返回 violation。"""
        _set_constraints("不能修改配置文件")
        r = on_post_tool_call(
            tool_name="write",
            args={"filePath": "/tmp/test.py"},
            session_id="test-session",
            result="done",
        )
        # 无违反，应该执行正常的内容完整性检查 → result 非空 → quality=ok
        assert r is not None
        assert r["quality"] == "ok"

    # -- bash 工具违反约束 --

    def test_bash_violation_delete_command(self):
        """bash 执行包含 'delete' 关键词的命令应返回 violation。"""
        _set_constraints("不要删除数据库")
        r = on_post_tool_call(
            tool_name="bash",
            args={"command": "rm -rf /var/lib/mysql"},
            session_id="test-session",
            result="done",
        )
        assert r is not None
        assert r["quality"] == "violation"

    def test_bash_non_violation_other_command(self):
        """bash 执行安全命令不应返回 violation。"""
        _set_constraints("不要删除数据库")
        r = on_post_tool_call(
            tool_name="bash",
            args={"command": "ls -la"},
            session_id="test-session",
            result="total 42\n",
        )
        assert r is not None
        assert r["quality"] == "ok"

    # -- 无活跃约束 --

    def test_no_active_constraints(self):
        """_current_hard_constraints 为空时不应触发违反检测。"""
        _current_hard_constraints.clear()
        r = on_post_tool_call(
            tool_name="write",
            args={"filePath": "/etc/config.yaml"},
            session_id="test-session",
            result="done",
        )
        assert r is not None
        assert r["quality"] == "ok"  # 正常内容完整性检查

    # -- curl 工具违反约束 --

    def test_curl_violation_with_constraint(self):
        """curl 执行命中约束关键词的命令应返回 violation。"""
        # "网络" 翻译映射到 {"network", "net", ...}
        _set_constraints("不能连接外部网络")
        r = on_post_tool_call(
            tool_name="curl",
            args={"command": "curl http://evil-network.com"},
            session_id="test-session",
            result="",
        )
        assert r is not None
        assert r["quality"] == "violation"


# ========= 原始内容完整性检查 =========


class TestContentIntegrity:
    """验证不涉及约束违反时的原始内容完整性检查逻辑。"""

    def test_write_ok_nonempty(self):
        r = on_post_tool_call(tool_name="write", result="file saved", args={})
        assert r and r["quality"] == "ok"

    def test_write_warning_empty(self):
        r = on_post_tool_call(tool_name="write", result="", args={})
        assert r and r["quality"] == "warning"

    def test_bash_ok_nonempty(self):
        r = on_post_tool_call(tool_name="bash", result="output", args={})
        assert r and r["quality"] == "ok"

    def test_bash_warning_empty(self):
        r = on_post_tool_call(tool_name="bash", result="", args={})
        assert r and r["quality"] == "warning"

    def test_read_ok_with_lines(self):
        r = on_post_tool_call(tool_name="read", result="line1\nline2\n", args={})
        assert r and r["quality"] == "ok"

    def test_read_warning_empty(self):
        r = on_post_tool_call(tool_name="read", result="", args={})
        assert r and r["quality"] == "warning"

    def test_unknown_tool_returns_none(self):
        r = on_post_tool_call(tool_name="search", result="data", args={})
        assert r is None

    def test_apply_patch_ok(self):
        r = on_post_tool_call(tool_name="apply_patch", result="patch applied", args={})
        assert r and r["quality"] == "ok"

    def test_webfetch_ok(self):
        r = on_post_tool_call(tool_name="webfetch", result="web content", args={})
        assert r and r["quality"] == "ok"


# ========= _check_constraint_violation 直接测试 =========


class TestCheckConstraintViolationDirect:
    """直接测试 _check_constraint_violation 函数。"""

    def setup_method(self):
        _current_hard_constraints.clear()

    def teardown_method(self):
        _current_hard_constraints.clear()

    def test_edit_violation(self):
        _set_constraints("不能修改配置")
        r = _check_constraint_violation(
            "edit", {"filePath": "/etc/config.yaml"}, "session"
        )
        assert r is not None
        assert r["quality"] == "violation"

    def test_mcp_tool_skipped(self):
        _set_constraints("不能删除数据库")
        r = _check_constraint_violation(
            "mcp_custom_tool", {}, "session"
        )
        assert r is None
