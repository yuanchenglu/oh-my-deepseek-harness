"""JSONL 审计事件源（AUD-001）。

以 JSONL 作为约束违反事件的唯一事实源，并从事件派生 Markdown 报告。
- `append_event`：追加结构化事件（一行 JSON）。
- `read_events`：读取全部事件；malformed 行隔离为 `{"error": ...}` 不崩溃
  （TC-POLICY-006/008 + 损坏行诊断）。
- `events_to_markdown`：从事件派生 Markdown 报告（数量字段一致）。
"""

from __future__ import annotations

import datetime
import json
import logging
import os
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# 默认审计事件文件（JSONL 唯一事实源）
AUDIT_EVENTS_FILE = os.path.expanduser(
    "~/.hermes/memories/audit-events.jsonl"
)


def append_event(
    event: Dict[str, Any],
    path: str = AUDIT_EVENTS_FILE,
) -> None:
    """追加一条结构化审计事件到 JSONL 文件。

    事件含默认字段：timestamp / quality / constraint / evidence / tool / session。
    Args:
        event: 事件字典（至少含 quality/constraint/evidence/tool）
        path: JSONL 文件路径
    """
    if "timestamp" not in event:
        event["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    parent_dir = os.path.dirname(path)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    logger.info("审计事件已写入: %s", path)


def read_events(path: str = AUDIT_EVENTS_FILE) -> List[Dict[str, Any]]:
    """读取全部审计事件。

    malformed 行（非法 JSON / 非对象）隔离为 `{"error": ...}` 条目不崩溃，
    保证有效事件不损坏（TC-POLICY-008 defensiveness）。

    Args:
        path: JSONL 文件路径

    Returns:
        事件列表（含错误隔离条目）
    """
    events: List[Dict[str, Any]] = []
    if not os.path.exists(path):
        return events
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if not isinstance(obj, dict):
                    raise ValueError("event 不是对象")
                events.append(obj)
            except (json.JSONDecodeError, ValueError) as e:
                events.append({"error": f"line {line_no}: {e}"})
    return events


def events_to_markdown(events: List[Dict[str, Any]]) -> str:
    """从事件列表派生 Markdown 报告（TC-POLICY-008：数量字段一致）。

    Args:
        events: 事件列表

    Returns:
        Markdown 报告文本
    """
    valid = [e for e in events if "error" not in e]
    lines = [
        "# 免疫系统审计报告",
        f"**事件总数**: {len(events)}",
        f"**有效事件**: {len(valid)}",
        "",
        "## 约束违反事件",
    ]
    for e in valid:
        lines.append(
            f"- [**{e.get('timestamp', '')}**] 约束: {e.get('constraint', '')} "
            f"| 工具: {e.get('tool', '')} | 证据: {e.get('evidence', '')}"
        )
    if not valid:
        lines.append("（无约束违反事件）")
    return "\n".join(lines)