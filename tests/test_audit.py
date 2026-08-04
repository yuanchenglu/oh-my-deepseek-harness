"""AUD-001 JSONL 审计事件源测试。

覆盖 TC-POLICY-006/007/008 + JSONL round-trip + malformed 行隔离。
用临时文件，不触碰真实 ~/.hermes。
"""

from __future__ import annotations

import json
from pathlib import Path

from deepseek_harness import audit_events
from deepseek_harness.audit_events import append_event, events_to_markdown, read_events


def _event() -> dict:
    return {
        "quality": "violation",
        "constraint": "不能删除数据库",
        "tool": "bash",
        "evidence": "bash 执行了: rm production.db",
        "session": "session-a",
    }


# ════════════════════════════════════════════════════════════════
# TC-POLICY-006/008: 写结构化事件 + JSONL 生成报告数量一致
# ════════════════════════════════════════════════════════════════


def test_append_event_writes_structured_jsonl(tmp_path: Path) -> None:
    """TC-POLICY-006: 路径疑似违反写结构化事件（JSONL）。"""
    path = tmp_path / "audit.jsonl"
    append_event(_event(), str(path))

    lines = path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1
    obj = json.loads(lines[0])
    assert obj["constraint"] == "不能删除数据库"
    assert obj["tool"] == "bash"
    assert "timestamp" in obj


def test_events_to_markdown_count_matches(tmp_path: Path) -> None:
    """TC-POLICY-008: JSONL 生成报告，数量字段一致。"""
    path = tmp_path / "audit.jsonl"
    append_event(_event(), str(path))
    append_event(_event(), str(path))

    events = read_events(str(path))
    assert len(events) == 2

    md = events_to_markdown(events)
    assert "**事件总数**: 2" in md
    assert "**有效事件**: 2" in md
    assert "不能删除数据库" in md


# ════════════════════════════════════════════════════════════════
# JSONL round-trip + malformed 行隔离
# ════════════════════════════════════════════════════════════════


def test_jsonl_round_trip(tmp_path: Path) -> None:
    """JSONL 事件写入后读取一致（round-trip）。"""
    path = tmp_path / "audit.jsonl"
    append_event(_event(), str(path))

    events = read_events(str(path))
    assert len(events) == 1
    assert events[0]["constraint"] == "不能删除数据库"
    assert events[0]["tool"] == "bash"


def test_malformed_rows_isolated(tmp_path: Path) -> None:
    """损坏行被隔离为 error 条目，不损坏有效事件。"""
    path = tmp_path / "audit.jsonl"
    path.write_text(
        "{bad json line\n"
        + json.dumps(_event(), ensure_ascii=False)
        + "\n"
        + "not json either\n",
        encoding="utf-8",
    )

    events = read_events(str(path))
    # 2 个损坏行 + 1 个有效事件
    assert len(events) == 3
    valid = [e for e in events if "error" not in e]
    assert len(valid) == 1
    assert valid[0]["constraint"] == "不能删除数据库"  # 有效事件不损坏


# ════════════════════════════════════════════════════════════════
# TC-POLICY-007: 普通 Tool 不误报
# ════════════════════════════════════════════════════════════════


def test_normal_tool_no_false_positive(tmp_path: Path) -> None:
    """TC-POLICY-007: 普通 Tool 调用不产生违反事件。"""
    from deepseek_harness.assessor import _check_constraint_violation
    from deepseek_harness.session_policy import SessionPolicyStore

    SessionPolicyStore.reset_instance()
    store = SessionPolicyStore.get_instance()
    store.add_constraints("s", {"不能删除数据库"})

    # 普通 read 调用（不违反约束）→ 不触发
    result = _check_constraint_violation("read", {"filePath": "/tmp/readme.md"}, "s")
    assert result is None