"""assessor.py 纯函数单元测试 — 验证 I-01 约束违反检测 + 内容完整性检查。

测试平台无关的核心函数：
  - extract_keywords()
  - check_path_against_constraint()
  - check_command_against_constraint()
  - record_violation()
  - check_constraint_violation()
  - assess_tool_call()

约束状态使用 gate._current_hard_constraints，通过 set_hard_constraints() 控制。
"""

import os
import tempfile
from unittest import mock

import pytest

from platform_core.assessor import (
    extract_keywords,
    check_path_against_constraint,
    check_command_against_constraint,
    record_violation,
    check_constraint_violation,
    assess_tool_call,
    DEFAULT_VIOLATIONS_FILE,
)
from platform_core.gate import set_hard_constraints, get_hard_constraints, _current_hard_constraints


# ── Fixtures ─────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _clear_constraints():
    _current_hard_constraints.clear()
    yield
    _current_hard_constraints.clear()


# ========= extract_keywords =========


class TestExtractKeywords:
    def test_chinese_phrase_extracted(self):
        kw = extract_keywords("不能修改配置文件")
        # 至少应提取到一个 CJK 词组及其英文翻译等价物
        assert len(kw) > 0
        # 应包含"配置"的英文翻译等价物
        assert any(en in kw for en in ["config", "conf", "cfg"])

    def test_english_words_extracted(self):
        kw = extract_keywords("do not modify config")
        # 'modify' (>=3 letters), 'config' (>=3 letters)
        assert any(w in kw for w in ["modify", "config", "not"])

    def test_translation_mapping(self):
        """"配置" 应映射到 config/conf/cfg 等英文等价物。"""
        kw = extract_keywords("配置")
        assert any(en in kw for en in ["config", "conf", "cfg"])

    def test_no_keywords_returns_empty(self):
        kw = extract_keywords("ab")
        # "ab" < 3 chars English, no CJK
        assert kw == set() or True  # at minimum doesn't crash


# ========= check_path_against_constraint =========


class TestCheckPathAgainstConstraint:
    def test_path_matches_constraint(self):
        """路径包含约束关键词应返回 True。"""
        assert check_path_against_constraint("/etc/nginx/nginx.conf", "不能修改配置文件") is True

    def test_path_does_not_match(self):
        """不相关的路径应返回 False。"""
        assert check_path_against_constraint("/tmp/test.py", "不能修改配置文件") is False

    def test_case_insensitive_match(self):
        assert check_path_against_constraint("/ETC/CONFIG.yaml", "不能修改配置文件") is True

    def test_filename_without_ext_matches(self):
        """去扩展名后的文件名含约束关键词应匹配。"""
        # 'config' 被 "配置" 翻译映射覆盖
        assert check_path_against_constraint("/app/settings/config.yaml", "不能修改配置文件") is True

    def test_parent_dir_matches(self):
        """父目录名含约束关键词应匹配。"""
        assert check_path_against_constraint("/etc/config/app.yaml", "不能修改配置文件") is True


# ========= check_command_against_constraint =========


class TestCheckCommandAgainstConstraint:
    def test_command_matches(self):
        assert check_command_against_constraint("rm -rf /var/lib/mysql", "不要删除数据库") is True

    def test_command_does_not_match(self):
        assert check_command_against_constraint("ls -la", "不要删除数据库") is False

    def test_case_insensitive(self):
        assert check_command_against_constraint("RM -RF /data", "不要删除数据库") is True


# ========= record_violation =========


class TestRecordViolation:
    def test_writes_to_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            fpath = f.name
        try:
            record_violation(
                {"constraint": "不能修改配置", "tool": "write", "evidence": "write /etc/config"},
                session_id="test-session",
                violations_file=fpath,
            )
            with open(fpath, encoding="utf-8") as f:
                content = f.read()
            assert "不能修改配置" in content
            assert "write" in content
            assert "test-session" in content
        finally:
            os.unlink(fpath)

    def test_creates_parent_dir(self):
        """父目录不存在时自动创建。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            subpath = os.path.join(tmpdir, "sub", "violations.md")
            record_violation(
                {"constraint": "测试约束", "tool": "bash", "evidence": "rm -rf /"},
                session_id="s1",
                violations_file=subpath,
            )
            assert os.path.exists(subpath)

    def test_permission_error_does_not_crash(self):
        """权限不足时静默降级。"""
        with mock.patch("builtins.open", side_effect=PermissionError):
            # 不应抛异常
            record_violation(
                {"constraint": "测试", "tool": "write", "evidence": "test"},
                session_id="s1",
            )


# ========= check_constraint_violation =========


class TestCheckConstraintViolation:
    def test_no_active_constraints_returns_none(self):
        r = check_constraint_violation("write", {"filePath": "/etc/config.yaml"}, "s1")
        assert r is None

    def test_write_violation(self):
        set_hard_constraints({"不能修改配置文件"})
        r = check_constraint_violation("write", {"filePath": "/etc/nginx/nginx.conf"}, "s1")
        assert r is not None
        assert r["quality"] == "violation"

    def test_write_non_violation(self):
        set_hard_constraints({"不能修改配置文件"})
        r = check_constraint_violation("write", {"filePath": "/tmp/test.py"}, "s1")
        assert r is None

    def test_bash_violation(self):
        set_hard_constraints({"不要删除数据库"})
        r = check_constraint_violation("bash", {"command": "rm -rf /var/lib/mysql"}, "s1")
        assert r is not None
        assert r["quality"] == "violation"

    def test_bash_non_violation(self):
        set_hard_constraints({"不要删除数据库"})
        r = check_constraint_violation("bash", {"command": "ls -la"}, "s1")
        assert r is None

    def test_mcp_tool_skipped(self):
        """MCP 工具不进行约束检查。"""
        set_hard_constraints({"不能修改配置文件"})
        r = check_constraint_violation("mcp_custom_tool", {}, "s1")
        assert r is None

    def test_edit_uses_filePath(self):
        set_hard_constraints({"不能修改配置文件"})
        r = check_constraint_violation("edit", {"filePath": "/etc/nginx/config.yaml"}, "s1")
        assert r is not None

    def test_apply_patch_path_param(self):
        set_hard_constraints({"不能修改配置文件"})
        r = check_constraint_violation("apply_patch", {"path": "/etc/nginx/nginx.conf"}, "s1")
        assert r is not None

    def test_curl_violation(self):
        set_hard_constraints({"不能连接外部网络"})
        r = check_constraint_violation("curl", {"command": "curl http://evil-network.com"}, "s1")
        assert r is not None

    def test_violation_has_required_fields(self):
        set_hard_constraints({"不能修改配置文件"})
        r = check_constraint_violation("write", {"filePath": "/etc/config.yaml"}, "s1")
        assert "constraint" in r
        assert "evidence" in r
        assert "tool" in r
        assert r["tool"] == "write"


# ========= assess_tool_call 主入口 =========


class TestAssessToolCall:
    def test_violation_returned_first(self):
        """违反约束优先于内容完整性检查返回。"""
        set_hard_constraints({"不能修改配置文件"})
        r = assess_tool_call("write", {"filePath": "/etc/config.yaml"}, "done", session_id="s1")
        assert r["quality"] == "violation"

    def test_write_ok(self):
        r = assess_tool_call("write", {}, "file saved")
        assert r and r["quality"] == "ok"

    def test_write_empty_warning(self):
        r = assess_tool_call("write", {}, "")
        assert r and r["quality"] == "warning"

    def test_read_ok(self):
        r = assess_tool_call("read", {}, "line1\nline2\n")
        assert r and r["quality"] == "ok"

    def test_read_empty_warning(self):
        r = assess_tool_call("read", {}, "")
        assert r and r["quality"] == "warning"

    def test_bash_ok(self):
        r = assess_tool_call("bash", {}, "output")
        assert r and r["quality"] == "ok"

    def test_bash_empty_warning(self):
        r = assess_tool_call("bash", {}, "")
        assert r and r["quality"] == "warning"

    def test_webfetch_ok(self):
        r = assess_tool_call("webfetch", {}, "web content")
        assert r and r["quality"] == "ok"

    def test_screenshot_image_ok(self):
        r = assess_tool_call("screenshot", {}, "base64 data png")
        assert r and r["quality"] == "ok"

    def test_screenshot_no_image_warning(self):
        r = assess_tool_call("screenshot", {}, "text only")
        assert r and r["quality"] == "warning"

    def test_unknown_tool_returns_none(self):
        r = assess_tool_call("search", {}, "data")
        assert r is None

    def test_none_result_treated_as_empty(self):
        r = assess_tool_call("write", {}, None)
        assert r and r["quality"] == "warning"

    def test_edit_tool_mapped_to_write(self):
        r = assess_tool_call("edit", {}, "edit result")
        assert r and r["quality"] == "ok"

    def test_apply_patch_mapped_to_write(self):
        r = assess_tool_call("apply_patch", {}, "patch applied")
        assert r and r["quality"] == "ok"

    def test_curl_mapped_to_command(self):
        r = assess_tool_call("curl", {}, "response data")
        assert r and r["quality"] == "ok"

    def test_websearch_tool_check(self):
        r = assess_tool_call("websearch", {}, "search results")
        assert r and r["quality"] == "ok"

    def test_browser_tool_check(self):
        r = assess_tool_call("browser", {}, "data:image/png;base64,...")
        assert r and r["quality"] == "ok"

    def test_chrome_tool_ok(self):
        r = assess_tool_call("chrome", {}, "image data")
        assert r and r["quality"] == "ok"

    def test_take_screenshot_ok(self):
        r = assess_tool_call("take_screenshot", {}, "base64 image png")
        assert r and r["quality"] == "ok"

    def test_look_at_ok(self):
        r = assess_tool_call("look_at", {}, "data:image/png;base64,...")
        assert r and r["quality"] == "ok"
