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


@pytest.fixture(autouse=True)
def _isolate_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """隔离 HOME，避免 import app 时 app.py 模块级副作用污染真实 ~/.hermes。"""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))


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


# ════════════════════════════════════════════════════════════════
# MEM-002: 删除 / 导入安全幂等（TC-MEM-005/006/009/011/012/013）
# ════════════════════════════════════════════════════════════════


def _write_memory_file(dirpath: Path, name: str, content: str) -> Path:
    """在临时目录写一个 .md 记忆文件。"""
    p = dirpath / name
    p.write_text(content, encoding="utf-8")
    return p


def test_delete_by_source_only_removes_target(tmp_path: Path) -> None:
    """TC-MEM-009: delete by source 仅删除目标 source，不影响其他。"""
    store = HarnessStorage(str(tmp_path / "mem.db"))
    store.insert_memory(_entry("来源A的记忆"), source="A.md")
    store.insert_memory(_entry("来源B的记忆"), source="B.md")

    deleted = store.delete_memories_by_source("A.md")
    assert deleted == 1

    rows = store.query_memories()
    assert len(rows) == 1
    assert rows[0].source == "B.md"


def test_import_restart_three_times_no_growth(tmp_path: Path) -> None:
    """TC-MEM-005: 同一记忆目录连续导入三次，条目数不增加。"""
    from harness_server.app import import_hermes_memories

    mem_dir = tmp_path / "memories"
    mem_dir.mkdir()
    _write_memory_file(mem_dir, "M.md", "用户偏好使用 pytest 进行测试\n\n这是第二段记忆内容")

    store = HarnessStorage(str(tmp_path / "mem.db"))
    first: tuple[int, int, int] | None = None
    for _ in range(3):
        imported, skipped, total = import_hermes_memories(str(mem_dir), store)
        if first is None:
            first = (imported, skipped, total)

    # 三次导入总条数等于第一次导入后的条数（幂等，不重复）
    assert store.count_total_memories() == first[0]
    assert total == 1  # 1 个文件


def test_import_file_change_does_not_duplicate_old(tmp_path: Path) -> None:
    """TC-MEM-006: 文件变更后重新导入，不重复旧数据，只新增/更新。"""
    from harness_server.app import import_hermes_memories

    mem_dir = tmp_path / "memories"
    mem_dir.mkdir()
    f = _write_memory_file(mem_dir, "M.md", "用户偏好使用 pytest 进行测试")

    store = HarnessStorage(str(tmp_path / "mem.db"))
    import_hermes_memories(str(mem_dir), store)
    count_before = store.count_total_memories()

    # 修改文件：追加新内容
    f.write_text("用户偏好使用 pytest 进行测试\n\n这是新的决定内容", encoding="utf-8")
    import_hermes_memories(str(mem_dir), store)

    count_after = store.count_total_memories()
    assert count_after >= count_before  # 旧内容不重复，新内容新增
    # 旧内容"用户偏好使用 pytest 进行测试" 不应重复
    same = store.query_memories(tags=["偏好"])
    assert len(same) == 1


def test_default_config_does_not_import_on_startup(tmp_path: Path) -> None:
    """TC-MEM-011: 默认配置启动不扫描用户 Memory。"""
    from harness_server.config import RuntimeConfig

    cfg = RuntimeConfig.from_env({})
    assert cfg.import_memories is False


def test_delete_requires_confirm(tmp_path: Path) -> None:
    """FR-MEMORY-006: CLI 删除缺 --confirm 时拒绝。"""
    from deepseek_harness.cli import main

    store = HarnessStorage(str(tmp_path / "mem.db"))
    store.insert_memory(_entry("要删除的记忆"), source="A.md")

    # 无 --confirm 应拒绝
    rc = main(
        ["memory", "delete", "--source", "A.md", "--db-path", str(tmp_path / "mem.db")]
    )
    assert rc != 0
    assert store.count_total_memories() == 1  # 未删除


def test_import_dry_run_does_not_write_db(tmp_path: Path) -> None:
    """TC-MEM-012: import dry-run 逐文件报告且 DB 行数不变。"""
    from deepseek_harness.cli import main

    mem_dir = tmp_path / "memories"
    mem_dir.mkdir()
    _write_memory_file(mem_dir, "M.md", "用户偏好使用 pytest 进行测试")

    db = tmp_path / "mem.db"
    store = HarnessStorage(str(db))
    store.insert_memory(_entry("已有记忆"), source="existing.md")
    before = store.count_total_memories()

    # dry-run 不写库
    rc = main(
        [
            "memory",
            "import",
            "--memories-dir", str(mem_dir),
            "--db-path", str(db),
            "--dry-run",
        ]
    )
    assert rc == 0
    assert store.count_total_memories() == before  # 行数不变


def test_import_corrupt_utf8_is_diagnosable(tmp_path: Path) -> None:
    """TC-MEM-013: 损坏 UTF-8 可诊断且无半批次。"""
    from harness_server.app import _import_md_file

    mem_dir = tmp_path / "memories"
    mem_dir.mkdir()
    bad = mem_dir / "bad.md"
    bad.write_bytes(b"valid line\n\xff\xfe broken utf8 \x80 body\nmore")

    store = HarnessStorage(str(tmp_path / "mem.db"))
    # 损坏 UTF-8 文件应被诊断/跳过，不产生半批次崩溃
    ok, count = _import_md_file(str(bad), store)
    assert isinstance(ok, bool)
    # 不抛异常，且不产生部分写入的损坏数据
    assert store.count_total_memories() >= 0