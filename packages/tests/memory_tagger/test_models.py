"""Memory Tagger 数据模型测试 — 验证 MemoryLayer 枚举和 MemoryEntry 模型。

测试 platform_core.memory_tagger.models 中的：
  - MemoryLayer 枚举
  - MemoryEntry Pydantic 模型
"""

from datetime import datetime

from platform_core.memory_tagger.models import MemoryLayer, MemoryEntry


class TestMemoryLayer:
    def test_values(self):
        assert MemoryLayer.CONSTRAINT.value == "constraint"
        assert MemoryLayer.PREFERENCE.value == "preference"
        assert MemoryLayer.STYLE.value == "style"
        assert MemoryLayer.DECISION.value == "decision"
        assert MemoryLayer.PATTERN.value == "pattern"

    def test_five_layers(self):
        assert len(MemoryLayer) == 5


class TestMemoryEntry:
    def test_minimal_creation(self):
        entry = MemoryEntry(
            content="不能修改配置文件",
            layer=MemoryLayer.CONSTRAINT,
        )
        assert entry.content == "不能修改配置文件"
        assert entry.layer == MemoryLayer.CONSTRAINT
        assert entry.tags == []
        assert isinstance(entry.created_at, datetime)

    def test_with_tags(self):
        entry = MemoryEntry(
            content="测试内容",
            layer=MemoryLayer.PATTERN,
            tags=["tag1", "tag2"],
        )
        assert len(entry.tags) == 2

    def test_custom_created_at(self):
        from datetime import timezone
        dt = datetime(2025, 1, 1, tzinfo=timezone.utc)
        entry = MemoryEntry(
            content="test",
            layer=MemoryLayer.DECISION,
            created_at=dt,
        )
        assert entry.created_at == dt
