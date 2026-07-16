"""Memory Tagger 单元测试 — 验证关键词分类和标签提取。

测试 platform_core.memory_tagger.tagger 中的：
  - classify()
  - extract_tags()
  - detect_task_type()
"""

from platform_core.memory_tagger.tagger import (
    classify,
    extract_tags,
    detect_task_type,
)
from platform_core.memory_tagger.models import MemoryLayer


# ========= classify =========


class TestClassify:
    def test_constraint_detected(self):
        """含"不能"的内容应分类为 CONSTRAINT。"""
        layer, kws, conf = classify("不能修改配置文件")
        assert layer == MemoryLayer.CONSTRAINT
        assert len(kws) > 0
        assert conf > 0.0

    def test_preference_detected(self):
        layer, kws, conf = classify("我喜欢用 Python 写后端")
        assert layer == MemoryLayer.PREFERENCE
        assert conf > 0.0

    def test_decision_detected(self):
        layer, kws, conf = classify("最终决定采用 PostgreSQL")
        assert layer == MemoryLayer.DECISION
        assert conf > 0.0

    def test_pattern_detected(self):
        layer, kws, conf = classify("每次发布都要更新 changelog")
        assert layer == MemoryLayer.PATTERN
        assert conf > 0.0

    def test_style_detected(self):
        layer, kws, conf = classify("编码风格使用 black 格式化")
        assert layer == MemoryLayer.STYLE
        assert conf > 0.0

    def test_no_match_falls_to_pattern(self):
        layer, kws, conf = classify("这是一条普通的记忆")
        assert layer == MemoryLayer.PATTERN
        assert conf == 0.0

    def test_english_keywords(self):
        layer, kws, conf = classify("should not use this approach")
        assert layer == MemoryLayer.CONSTRAINT
        assert conf > 0.0

    def test_confidence_between_0_and_1(self):
        _, _, conf = classify("不能修改配置，最终决定使用新架构")
        assert 0.0 <= conf <= 1.0

    def test_empty_content(self):
        layer, kws, conf = classify("")
        assert layer == MemoryLayer.PATTERN
        assert conf == 0.0


# ========= extract_tags =========


class TestExtractTags:
    def test_extracts_matching_keywords(self):
        tags = extract_tags("不能修改配置文件")
        assert len(tags) > 0
        assert any("不能" in t for t in tags)

    def test_deduplicated(self):
        tags = extract_tags("不能修改配置，不能删除文件")
        # "不能" should appear at least once
        assert any("不能" in t for t in tags)

    def test_empty_content(self):
        assert extract_tags("") == []

    def test_case_insensitive(self):
        tags = extract_tags("NEVER use this")
        assert len(tags) > 0


# ========= detect_task_type =========


class TestDetectTaskType:
    def test_convergent_detected(self):
        t = detect_task_type("修复生产环境的部署问题")
        assert t == "convergent"

    def test_divergent_detected(self):
        t = detect_task_type("构思一个新的产品创意")
        assert t == "divergent"

    def test_mixed_detected(self):
        t = detect_task_type("对比两种方案，评估优缺点")
        assert t == "mixed"

    def test_no_match_defaults_to_mixed(self):
        t = detect_task_type("")
        assert t == "mixed"

    def test_convergent_chinese(self):
        t = detect_task_type("修复生产环境问题")
        assert t == "convergent"
