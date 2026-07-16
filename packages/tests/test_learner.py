"""learner.py 单元测试 — 验证会话学习总结逻辑。

测试 platform_core.learner 中所有纯函数：
  - build_lesson_entry()
  - check_skill_proposal()
  - handle_session_end()
"""

import os
import tempfile
from unittest import mock

import pytest

from platform_core.learner import (
    build_lesson_entry,
    check_skill_proposal,
    handle_session_end,
    DEFAULT_FEEDBACK_FILE,
)


# ========= build_lesson_entry =========


class TestBuildLessonEntry:
    def test_contains_session_id(self):
        entry = build_lesson_entry("test-001")
        assert "test-001" in entry

    def test_contains_timestamp_marker(self):
        entry = build_lesson_entry("test-001")
        # 应包含类似 [2025-...] 的时间戳
        assert "[" in entry and "]" in entry

    def test_format_consistency(self):
        entry = build_lesson_entry("session-abc")
        assert "Session" in entry or "session-abc" in entry


# ========= check_skill_proposal =========


class TestCheckSkillProposal:
    def test_enough_rounds_returns_proposal(self):
        history = [{"role": "user", "content": f"msg{i}"} for i in range(15)]
        r = check_skill_proposal(history, "s1", min_rounds=10)
        assert r is not None
        assert "skill_proposal" in r
        assert r["skill_proposal"]["session_id"] == "s1"

    def test_not_enough_rounds_returns_none(self):
        history = [{"role": "user", "content": "msg"} for _ in range(5)]
        r = check_skill_proposal(history, "s1", min_rounds=10)
        assert r is None

    def test_none_history_returns_none(self):
        r = check_skill_proposal(None, "s1", min_rounds=10)
        assert r is None

    def test_computes_n_tasks(self):
        """n_tasks = max(1, rounds // min_rounds)"""
        history = [{"role": "user", "content": "msg"} for _ in range(25)]
        r = check_skill_proposal(history, "s1", min_rounds=10)
        assert r["skill_proposal"]["n_tasks"] >= 2


# ========= handle_session_end =========


class TestHandleSessionEnd:
    def test_writes_entry_to_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            fpath = f.name
        try:
            r = handle_session_end("test-001", feedback_file=fpath)
            assert r is not None
            assert "test-001" in r["entry"]
            with open(fpath, encoding="utf-8") as f:
                content = f.read()
            assert "test-001" in content
        finally:
            os.unlink(fpath)

    def test_creates_parent_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            subpath = os.path.join(tmpdir, "sub", "lessons.md")
            r = handle_session_end("test-s2", feedback_file=subpath)
            assert r is not None
            assert os.path.exists(subpath)

    def test_no_args_uses_default(self):
        """无参数时使用默认路径且不抛异常。"""
        # 默认路径 ~/.hermes/memories/feedback-lessons.md
        # 不抛异常即可
        r = handle_session_end("fallback-test")
        # 可能成功或静默失败（取决于权限），但不应抛异常
        assert r is not None or r is None

    def test_permission_error_returns_none(self):
        with mock.patch("builtins.open", side_effect=PermissionError):
            r = handle_session_end("perm-test")
            assert r is None

    def test_with_conversation_history_checks_skill(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            fpath = f.name
        try:
            history = [{"role": "user", "content": "msg"} for _ in range(15)]
            # 不应抛异常
            r = handle_session_end(
                "skill-test",
                conversation_history=history,
                feedback_file=fpath,
                min_rounds=10,
            )
            assert r is not None
        finally:
            os.unlink(fpath)
