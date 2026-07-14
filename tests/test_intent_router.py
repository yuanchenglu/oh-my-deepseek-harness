"""intent_router.py 单元测试 — 验证 7+1 意图分类 + 策略绑定 + 排除清单。"""

from deepseek_harness.intent_router import (
    _keyword_match_score,
    classify_intent,
    get_strategy,
    generate_exclusion_list,
    build_context_injection,
)


# ========= _keyword_match_score =========


class TestKeywordMatchScore:
    """验证关键词匹配评分算法。"""

    def test_exact_substring_english(self):
        """精确子串匹配英文返回 1.0。"""
        assert _keyword_match_score("refactor", "I need to refactor this") == 1.0

    def test_exact_substring_chinese(self):
        """精确子串匹配中文返回 1.0。"""
        assert _keyword_match_score("重构", "帮我重构这段代码") == 1.0

    def test_no_match_returns_zero(self):
        """完全不匹配返回 0.0。"""
        assert _keyword_match_score("重构", "帮我写一个新项目") == 0.0

    def test_partial_cjk_match_long_keyword(self):
        """3 字以上中文关键词有字符重叠时返回比例得分。"""
        # "模块拆分" vs "拆分模块" 有 2/4 重叠
        score = _keyword_match_score("模块拆分", "把这个模块拆分成两个")
        assert 0.0 < score <= 1.0

    def test_short_cjk_no_partial(self):
        """≤2 字中文关键词精确匹配失败则返回 0。"""
        assert _keyword_match_score("重建", "创建一个新项目") == 0.0


# ========= classify_intent 意图分类 =========


class TestClassifyIntent:
    """验证 7 种意图 + 1 种兜底的分类准确率。"""

    def test_classify_refactor(self):
        """重构意图应被识别为 refactor。"""
        r = classify_intent("重构用户模块，把登录逻辑拆分成独立服务")
        assert r["intent"] == "refactor"

    def test_classify_new(self):
        """新建意图应被识别为 new。"""
        r = classify_intent("从零开始创建一个新的 React 项目")
        assert r["intent"] == "new"

    def test_classify_medium(self):
        """中等修改意图应被识别为 medium。"""
        r = classify_intent("在现有代码中添加用户评论功能")
        assert r["intent"] == "medium"

    def test_classify_collaboration(self):
        """协作意图应被识别为 collaboration。"""
        r = classify_intent("需要多人协作并行开发这个功能")
        assert r["intent"] == "collaboration"

    def test_classify_architecture(self):
        """架构意图应被识别为 architecture。"""
        r = classify_intent("设计系统架构方案，做技术选型")
        assert r["intent"] == "architecture"

    def test_classify_research(self):
        """调研意图应被识别为 research。"""
        r = classify_intent("对目前的技术趋势做深入调研和探究")
        assert r["intent"] == "research"

    def test_classify_simple(self):
        """简单修复意图应被识别为 simple。"""
        r = classify_intent("修复登录页面的按钮样式问题")
        assert r["intent"] == "simple"

    def test_classify_spec_driven_fallback(self):
        """无关键词匹配时返回 spec_driven 兜底。"""
        r = classify_intent("你好，今天天气怎么样")
        assert r["intent"] == "spec_driven"
        assert r["confidence"] == 0.0

    def test_classify_refactor_english(self):
        """英文重构描述应被识别为 refactor。"""
        r = classify_intent("Restructure the auth module to improve maintainability")
        assert r["intent"] == "refactor"

    def test_classify_medium_english(self):
        """英文中等修改描述应被识别为 medium。"""
        r = classify_intent("Modify the existing search module to add filtering support")
        assert r["intent"] == "medium"


# ========= get_strategy 策略绑定 =========


class TestGetStrategy:
    """验证策略绑定查询。"""

    def test_refactor_strategy_has_fields(self):
        s = get_strategy("refactor")
        assert s.get("interview_depth") == "deep"
        assert s.get("plan_granularity") == "fine"
        assert s.get("review_standard") == "strict"
        assert s.get("execution_mode") == "sequential"

    def test_simple_strategy(self):
        s = get_strategy("simple")
        assert s.get("interview_depth") == "none"
        assert s.get("plan_granularity") == "minimal"

    def test_unknown_intent_returns_empty(self):
        s = get_strategy("nonexistent")
        assert s == {}


# ========= generate_exclusion_list 排除清单 =========


class TestGenerateExclusionList:
    """验证 I-08 Layer 1 排除清单生成。"""

    def test_refactor_has_exclusions(self):
        ex = generate_exclusion_list("重构代码", "refactor")
        assert len(ex) > 0
        assert any("不新增功能" in e for e in ex)
        assert any("不修改 API 契约" in e for e in ex)

    def test_new_has_exclusions(self):
        ex = generate_exclusion_list("新建项目", "new")
        assert len(ex) > 0
        assert any("不加权限系统" in e for e in ex)

    def test_unknown_intent_empty_exclusions(self):
        ex = generate_exclusion_list("test", "nonexistent")
        assert ex == []


# ========= build_context_injection 编排函数 =========


class TestBuildContextInjection:
    """验证核心编排函数。"""

    def test_first_turn_refactor_has_context(self):
        r = build_context_injection(
            "重构用户模块，把登录逻辑拆分出来",
            is_first_turn=True,
        )
        assert r is not None
        assert "I-10 意图路由" in r["context"]
        assert "refactor" in r["context"]

    def test_non_first_turn_returns_none(self):
        r = build_context_injection(
            "继续重构",
            is_first_turn=False,
        )
        assert r is None

    def test_empty_message_returns_none(self):
        r = build_context_injection("", is_first_turn=True)
        assert r is None

    def test_spec_driven_still_injects_context(self):
        """无分类兜底时仍注入 context，不返回 None。"""
        r = build_context_injection(
            "你好",
            is_first_turn=True,
        )
        assert r is not None
        assert "spec_driven" in r["context"]
