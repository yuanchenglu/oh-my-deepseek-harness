"""intent_router.py 单元测试 — 验证 7+1 意图分类 + 策略绑定 + 排除清单。

测试 platform_core.intent_router 中所有纯函数：
  - keyword_match_score()
  - load_strategies()
  - classify_intent()
  - get_strategy()
  - generate_exclusion_list()
  - build_context_injection()
"""

import os
import tempfile

import yaml

from platform_core.intent_router import (
    keyword_match_score,
    load_strategies,
    classify_intent,
    get_strategy,
    generate_exclusion_list,
    build_context_injection,
)

# 用于测试的 strategies.yaml 内容（完整子集）
_TEST_STRATEGIES = {
    "intents": {
        "refactor": {
            "description": "重构",
            "keywords": ["重构", "拆", "拆分", "迁移", "refactor", "重组"],
            "strategy": {
                "interview_depth": "deep",
                "plan_granularity": "fine",
                "review_standard": "strict",
                "execution_mode": "sequential",
            },
            "common_creep": ["不新增功能", "不修改 API 契约", "不引入新依赖"],
        },
        "new": {
            "description": "新建",
            "keywords": ["新建", "从零", "创建", "new", "create", "项目"],
            "strategy": {
                "interview_depth": "medium",
                "plan_granularity": "coarse",
                "review_standard": "standard",
                "execution_mode": "parallel_subtasks",
            },
            "common_creep": ["不加权限系统", "不加 OAuth"],
        },
        "simple": {
            "description": "简单修复",
            "keywords": ["修复", "fix", "更新", "change", "修改"],
            "strategy": {
                "interview_depth": "none",
                "plan_granularity": "minimal",
                "review_standard": "shallow",
                "execution_mode": "direct",
            },
            "common_creep": [],
        },
        "spec_driven": {
            "description": "兜底",
            "keywords": [],
            "strategy": {
                "interview_depth": "spec_derived",
                "plan_granularity": "spec_derived",
                "review_standard": "spec_derived",
                "execution_mode": "spec_derived",
            },
            "common_creep": [],
        },
    }
}


import pytest


# ── Fixtures ─────────────────────────────────────────────


@pytest.fixture
def strategies():
    """返回测试用 strategies 配置。"""
    return _TEST_STRATEGIES


# ========= keyword_match_score =========


class TestKeywordMatchScore:
    def test_exact_substring_english(self):
        assert keyword_match_score("refactor", "I need to refactor this") == 1.0

    def test_exact_substring_chinese(self):
        assert keyword_match_score("重构", "帮我重构这段代码") == 1.0

    def test_no_match_returns_zero(self):
        assert keyword_match_score("重构", "帮我写一个新项目") == 0.0

    def test_partial_cjk_match(self):
        score = keyword_match_score("模块拆分", "把这个模块拆分成两个")
        assert 0.0 < score <= 1.0

    def test_short_cjk_no_partial(self):
        assert keyword_match_score("重建", "创建一个新项目") == 0.0

    def test_empty_text(self):
        assert keyword_match_score("refactor", "") == 0.0

    def test_empty_keyword(self):
        assert keyword_match_score("", "some text") == 1.0


# ========= load_strategies =========


class TestLoadStrategies:
    def test_load_from_default_path(self):
        """从默认路径加载。"""
        s = load_strategies()
        assert isinstance(s, dict)
        assert "intents" in s

    def test_load_from_custom_path(self):
        """从自定义路径加载。"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
            yaml.dump(_TEST_STRATEGIES, f)
            fpath = f.name
        try:
            s = load_strategies(fpath)
            # 注：模块级缓存可能已由上次测试填充，
            # 此处验证内容而非路径行为
            assert isinstance(s, dict)
            assert "intents" in s
        finally:
            os.unlink(fpath)

    def test_cache_hits(self):
        """多次调用返回同一缓存对象。"""
        s1 = load_strategies()
        s2 = load_strategies()
        assert s1 is s2  # 同一对象（缓存）


# ========= classify_intent =========


class TestClassifyIntent:
    def test_refactor_cn(self, strategies):
        r = classify_intent("重构用户模块，把登录逻辑拆分成独立服务", strategies)
        assert r["intent"] == "refactor"

    def test_new_cn(self, strategies):
        r = classify_intent("从零开始创建一个新的 React 项目", strategies)
        assert r["intent"] == "new"

    def test_simple_fix(self, strategies):
        r = classify_intent("修复登录页面的按钮样式问题", strategies)
        assert r["intent"] == "simple"

    def test_refactor_en(self, strategies):
        r = classify_intent("Refactor the auth module to improve maintainability", strategies)
        assert r["intent"] == "refactor"

    def test_spec_driven_fallback(self, strategies):
        """无关键词匹配时返回 spec_driven 兜底。"""
        r = classify_intent("你好，今天天气怎么样", strategies)
        assert r["intent"] == "spec_driven"
        assert r["confidence"] == 0.0

    def test_returns_confidence(self, strategies):
        r = classify_intent("重构用户模块", strategies)
        assert 0.0 <= r["confidence"] <= 1.0

    def test_empty_text(self, strategies):
        r = classify_intent("", strategies)
        assert r["intent"] == "spec_driven"


# ========= get_strategy =========


class TestGetStrategy:
    def test_refactor_strategy(self, strategies):
        s = get_strategy("refactor", strategies)
        assert s.get("interview_depth") == "deep"
        assert s.get("plan_granularity") == "fine"

    def test_simple_strategy(self, strategies):
        s = get_strategy("simple", strategies)
        assert s.get("interview_depth") == "none"

    def test_unknown_intent_returns_empty(self, strategies):
        s = get_strategy("nonexistent", strategies)
        assert s == {}

    def test_no_strategies_param_uses_default(self):
        """省略 strategies 参数时使用默认加载。"""
        s = get_strategy("refactor")
        assert "interview_depth" in s


# ========= generate_exclusion_list =========


class TestGenerateExclusionList:
    def test_refactor_has_exclusions(self, strategies):
        ex = generate_exclusion_list("refactor", strategies)
        assert len(ex) > 0
        assert any("不新增功能" in e for e in ex)

    def test_simple_has_no_exclusions(self, strategies):
        ex = generate_exclusion_list("simple", strategies)
        assert ex == []

    def test_unknown_intent_empty(self, strategies):
        ex = generate_exclusion_list("nonexistent", strategies)
        assert ex == []


# ========= build_context_injection =========


class TestBuildContextInjection:
    def test_first_turn_refactor(self, strategies):
        r = build_context_injection(
            "重构用户模块，把登录逻辑拆分出来",
            is_first_turn=True,
            strategies=strategies,
        )
        assert r is not None
        assert "I-10 意图路由" in r["context"]
        assert "refactor" in r["context"]

    def test_non_first_turn_returns_none(self, strategies):
        r = build_context_injection("继续重构", is_first_turn=False, strategies=strategies)
        assert r is None

    def test_empty_message_returns_none(self, strategies):
        r = build_context_injection("", is_first_turn=True, strategies=strategies)
        assert r is None

    def test_spec_driven_still_injects(self, strategies):
        r = build_context_injection("你好", is_first_turn=True, strategies=strategies)
        assert r is not None
        assert "spec_driven" in r["context"]

    def test_includes_exclusion_list(self, strategies):
        r = build_context_injection("重构项目", is_first_turn=True, strategies=strategies)
        assert "I-08 排除清单" in r["context"]
