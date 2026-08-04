"""MEM-001 Memory 存储/查询/去重不变量测试。

覆盖 TC-MEM-001~004、TC-MEM-007、TC-MEM-008、TC-MEM-010。
只测存储层（HarnessStorage）与分类逻辑，不依赖真实 Hermes 环境，
使用临时 SQLite 与合成内容，不触碰真实 HOME/Memory/Secret。
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

from harness_server.models import MemoryEntry, MemoryLayer
from harness_server.storage import HarnessStorage


def _entry(
    content: str,
    layer: MemoryLayer = MemoryLayer.PREFERENCE,
    tags: list[str] | None = None,
) -> MemoryEntry:
    """构造一条合成记忆条目。"""
    return MemoryEntry(
        content=content,
        tags=tags or ["中文"],
        layer=layer,
        created_at=datetime.now(timezone.utc),
    )


# ════════════════════════════════════════════════════════════════
# TC-MEM-003: Store 同内容同来源两次 → 一条记录（幂等）
# ════════════════════════════════════════════════════════════════


def test_store_same_content_same_source_is_idempotent(tmp_path: Path) -> None:
    """XF-MEM-001 -> MEM-001: 同 content + 同 source identity 只存一条。"""
    store = HarnessStorage(str(tmp_path / "mem.db"))
    entry = _entry("用户明确要求所有技术文档使用中文")

    store.insert_memory(entry, source="MEMORY.md")
    store.insert_memory(entry, source="MEMORY.md")

    rows = store.query_memories(tags=["中文"])
    assert len(rows) == 1


# ════════════════════════════════════════════════════════════════
# TC-MEM-004: 同内容不同来源 → 按 source identity 区分（两条）
# ════════════════════════════════════════════════════════════════


def test_store_same_content_different_source_keeps_both(tmp_path: Path) -> None:
    """TC-MEM-004: 同 content、不同 source，应作为两条独立记录。"""
    store = HarnessStorage(str(tmp_path / "mem.db"))
    entry = _entry("用户偏好使用 pytest 跑测试")

    store.insert_memory(entry, source="MEMORY.md")
    store.insert_memory(entry, source="USER.md")

    rows = store.query_memories(tags=["中文"])
    assert len(rows) == 2


# ════════════════════════════════════════════════════════════════
# TC-MEM-007: λ 边界 0.3/0.4/0.7/0.8 → 无空区间
# ════════════════════════════════════════════════════════════════


def test_lambda_boundaries_have_no_empty_interval(tmp_path: Path) -> None:
    """TC-MEM-007: λ 边界 0.3/0.4/0.7/0.8 映射必须连续无空区间。"""
    store = HarnessStorage(str(tmp_path / "lambda.db"))

    # 边界两侧的层集合必须相邻且非空
    assert store.get_layers_for_lambda(0.3) == ["constraint"]
    assert store.get_layers_for_lambda(0.4) == [
        "constraint",
        "preference",
        "decision",
    ]
    assert store.get_layers_for_lambda(0.7) == [
        "constraint",
        "preference",
        "decision",
    ]
    assert store.get_layers_for_lambda(0.8) == [
        "constraint",
        "preference",
        "style",
        "decision",
        "pattern",
    ]

    # 边界本身（0.3/0.4/0.7/0.8）必须落在一个非空区间内
    for boundary in (0.3, 0.4, 0.7, 0.8):
        layers = store.get_layers_for_lambda(boundary)
        assert layers, f"λ={boundary} 落在空区间"


# ════════════════════════════════════════════════════════════════
# TC-MEM-008: Query 按 tags + layer 交集正确
# ════════════════════════════════════════════════════════════════


def test_query_tags_and_layer_intersection(tmp_path: Path) -> None:
    """TC-MEM-008: tags + layer 同时筛选时取交集。"""
    store = HarnessStorage(str(tmp_path / "mem.db"))

    store.insert_memory(
        _entry("可执行约束", layer=MemoryLayer.CONSTRAINT, tags=["约束"]),
        source="A.md",
    )
    store.insert_memory(
        _entry("偏好一", layer=MemoryLayer.PREFERENCE, tags=["偏好"]),
        source="B.md",
    )
    store.insert_memory(
        _entry("偏好二", layer=MemoryLayer.PREFERENCE, tags=["偏好"]),
        source="C.md",
    )

    # 只查 layer=PREFERENCE
    pref = store.query_memories(layer=MemoryLayer.PREFERENCE)
    assert len(pref) == 2

    # 只查 tags=约束
    told = store.query_memories(tags=["约束"])
    assert len(told) == 1

    # tags + layer 交集：偏好层且标签=约束 → 0 条
    both = store.query_memories(
        tags=["约束"],
        layer=MemoryLayer.PREFERENCE,
    )
    assert len(both) == 0


def test_query_preserves_source_identity(tmp_path: Path) -> None:
    """FR-MEMORY-007: 查询结果保留 source 数据来源。"""
    store = HarnessStorage(str(tmp_path / "mem.db"))
    store.insert_memory(_entry("带来源的记忆"), source="MEMORY.md")

    rows = store.query_memories()
    assert len(rows) == 1
    assert rows[0].source == "MEMORY.md"


# ════════════════════════════════════════════════════════════════
# TC-MEM-010: 10k 数据 → 常规查询 P95 < 200ms
# ════════════════════════════════════════════════════════════════


def test_query_10k_memories_p95_under_200ms(tmp_path: Path) -> None:
    """TC-MEM-010: 10,000 条记忆下常规查询 P95 < 200ms（NFR-001）。"""
    store = HarnessStorage(str(tmp_path / "perf.db"))

    # 插入 10k 条合成记忆
    for i in range(10_000):
        layer = MemoryLayer.PREFERENCE if i % 2 == 0 else MemoryLayer.CONSTRAINT
        store.insert_memory(
            _entry(f"合成记忆内容 {i}", layer=layer, tags=["perf"]),
            source=f"perf-{i % 100}.md",
        )

    assert store.count_total_memories() == 10_000

    # 预热后测 50 次常规查询的 P95
    latencies: list[float] = []
    for _ in range(50):
        start = time.perf_counter()
        store.query_memories(tags=["perf"], layer=MemoryLayer.PREFERENCE, limit=10)
        latencies.append((time.perf_counter() - start) * 1000)

    latencies.sort()
    p95 = latencies[int(len(latencies) * 0.95)]
    assert p95 < 200.0, f"P95={p95:.1f}ms 超过 200ms 目标"


# ════════════════════════════════════════════════════════════════
# TC-MEM-001/002: classify 分类正确 + 无匹配兜底
# ════════════════════════════════════════════════════════════════


def test_classify_constraint_layer(tmp_path: Path) -> None:
    """TC-MEM-001: constraint 内容分类为 constraint 层且 evidence 正确。"""
    from harness_server.app import classify

    layer, matched_kws, confidence = classify("用户明确要求所有技术文档必须使用中文")
    assert layer == MemoryLayer.CONSTRAINT
    assert matched_kws
    assert 0.0 <= confidence <= 1.0


def test_classify_unknown_has_default_behavior(tmp_path: Path) -> None:
    """TC-MEM-002: 无关键词匹配时返回默认兜底，不抛异常。"""
    from harness_server.app import classify

    layer, matched_kws, confidence = classify("完全随机的无意义字符串 abcxyz")
    assert layer is not None
    assert isinstance(matched_kws, list)
    assert confidence == 0.0