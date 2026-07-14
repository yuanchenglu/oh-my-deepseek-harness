"""Memory 标签分类逻辑 — 关键词规则引擎

基于 I-12 §3.1–3.2 的层级定义，通过关键词匹配为记忆内容
自动分配层级标签（constraint / preference / style / decision / pattern）。
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from models import MemoryLayer

logger = logging.getLogger(__name__)


@dataclass
class LayerRule:
    """单条层级匹配规则"""
    layer: MemoryLayer
    keywords: List[str]
    weight: float = 1.0  # 匹配权重，用于置信度计算


# 层级匹配规则（关键词按优先级排列）
# 每条规则中的关键词越多，匹配的置信度越高
LAYER_RULES: Dict[MemoryLayer, LayerRule] = {
    MemoryLayer.CONSTRAINT: LayerRule(
        layer=MemoryLayer.CONSTRAINT,
        keywords=[
            "不能", "不要", "必须", "禁止", "严禁",
            "不得", "不可", "不允许", "一定不要", "绝对不要",
            "should not", "must not", "never",
            "禁止使用", "禁用", "不允许使用",
        ],
        weight=2.0,  # 约束层高权重——安全/合规关键
    ),
    MemoryLayer.PREFERENCE: LayerRule(
        layer=MemoryLayer.PREFERENCE,
        keywords=[
            "喜欢", "偏好", "习惯", "倾向于",
            "prefer", "preferred", "favorite",
            "喜欢用", "习惯用", "偏好使用",
            "更倾向于", "更加喜欢",
        ],
        weight=1.0,
    ),
    MemoryLayer.STYLE: LayerRule(
        layer=MemoryLayer.STYLE,
        keywords=[
            "风格", "格式", "方式", "样式",
            "style", "format", "manner",
            "写作风格", "编码风格", "语言风格",
            "格式要求", "排版风格",
        ],
        weight=1.0,
    ),
    MemoryLayer.DECISION: LayerRule(
        layer=MemoryLayer.DECISION,
        keywords=[
            "决定", "结论", "确认", "选定",
            "decide", "decision", "conclusion", "confirmed",
            "最终决定", "最终结论", "达成一致",
            "我们决定", "决定采用", "确定使用",
        ],
        weight=1.0,
    ),
    MemoryLayer.PATTERN: LayerRule(
        layer=MemoryLayer.PATTERN,
        keywords=[
            "每次", "经常", "总是", "往往",
            "usually", "always", "often", "typically",
            "每次都要", "通常需要", "一般都是",
            "常规做法", "习惯做法",
        ],
        weight=1.0,
    ),
}


def _find_matches(content: str) -> List[Tuple[MemoryLayer, int]]:
    """在内容中查找所有匹配的关键词，返回 (层级, 匹配数) 列表"""
    matches: List[Tuple[MemoryLayer, int]] = []
    for layer, rule in LAYER_RULES.items():
        count = 0
        for kw in rule.keywords:
            # 不区分大小写的全文匹配
            if re.search(re.escape(kw), content, re.IGNORECASE):
                count += 1
        if count > 0:
            matches.append((layer, count))
    return matches


def classify(content: str) -> Tuple[MemoryLayer, List[str], float]:
    """对记忆内容进行分类

    返回 (layer, matched_keywords, confidence)
    其中 confidence ∈ [0, 1]
    """
    matches = _find_matches(content)

    if not matches:
        # 无匹配时默认归入 pattern（可降级到其他默认层）
        return MemoryLayer.PATTERN, [], 0.0

    # 按加权匹配数排序：score = count * weight
    scored = [
        (layer, count, LAYER_RULES[layer].weight * count)
        for layer, count in matches
    ]
    scored.sort(key=lambda x: x[2], reverse=True)

    best_layer, best_count, best_score = scored[0]
    total_score = sum(s for _, _, s in scored)

    # 提取命中的关键词
    matched_kws: List[str] = []
    for kw in LAYER_RULES[best_layer].keywords:
        if re.search(re.escape(kw), content, re.IGNORECASE):
            matched_kws.append(kw)

    # 置信度 = 最高分 / 总分（单一规则匹配时接近 1.0）
    confidence = best_score / total_score if total_score > 0 else 0.0

    # 至少匹配到 1 个关键词时置信度不低于 0.3
    if best_count > 0 and confidence < 0.3:
        confidence = max(confidence, 0.3)

    return best_layer, matched_kws, round(confidence, 4)


def extract_tags(content: str) -> List[str]:
    """从内容中提取标签（关键词级别的标记）

    返回去重后的关键词列表
    """
    tags: List[str] = []
    for rule in LAYER_RULES.values():
        for kw in rule.keywords:
            if re.search(re.escape(kw), content, re.IGNORECASE):
                tags.append(kw)
    return tags


def detect_task_type(task_prompt: str) -> str:
    """检测任务类型：convergent / divergent / mixed

    返回任务类型标识
    """
    config_lookup = {
        "convergent": ["修复", "部署", "排查", "调试", "构建", "发布", "合并", "删除"],
        "divergent": ["构思", "设计", "写作", "批判", "探索", "头脑风暴", "创意", "灵感"],
        "mixed": ["方案", "策略", "分析", "评估", "对比", "评审", "规划"],
    }

    scores = {"convergent": 0, "divergent": 0, "mixed": 0}
    for task_type, keywords in config_lookup.items():
        for kw in keywords:
            if re.search(re.escape(kw), task_prompt, re.IGNORECASE):
                scores[task_type] += 1

    if all(v == 0 for v in scores.values()):
        return "mixed"  # 无法识别时默认 mixed

    return max(scores, key=scores.get)
