"""意图路由模块 — 平台无关核心。

7+1 意图分类 + 策略绑定 + I-08 Layer 1 Metis 反向追问。

通过关键词匹配规则识别用户任务意图，绑定对应策略参数，
并生成策略指引和排除清单，供调用者在 pre_llm_call 阶段注入。

意图类型（7+1）：
  - refactor       : 重构/拆分/迁移，不改变外部行为
  - new            : 从零开始构建新项目/功能
  - medium         : 中等规模功能添加或修改
  - collaboration  : 多 Agent 或人机协作
  - architecture   : 系统级架构设计和决策
  - research       : 探索性任务，产出知识和建议
  - simple         : 单文件或极少文件的明确修改
  - spec_driven    : （兜底）基于结构化 Spec 推导策略

本模块不依赖任何 Hermes API，strategies.yaml 路径通过参数传入。
"""

import logging
import os
import re
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)

# CJK 统一字符范围（用于中文关键词模糊匹配）
_CJK_RE = re.compile(r"[\u4e00-\u9fff]+")

# 模块级缓存：策略配置
_strategies: dict = None


def keyword_match_score(keyword: str, text: str) -> float:
    """计算关键词与文本的匹配得分。

    匹配策略（由简到繁）：
    1. 精确子串匹配 → 1.0（最高优先级）
    2. 纯英文关键词不匹配 → 0.0
    3. 短 CJK 关键词（≤2 字）→ 精确子串匹配（不上溯单字）
    4. 长 CJK 关键词（≥3 字）→ 单字符重叠比例 ≥ 0.5

    Args:
        keyword: 关键词
        text: 待匹配文本

    Returns:
        匹配得分 [0.0, 1.0]
    """
    # 优先精确子串匹配
    if keyword.lower() in text.lower():
        return 1.0

    cjk_chars = _CJK_RE.findall(keyword)
    if not cjk_chars:
        return 0.0

    kw_cjk = "".join(cjk_chars)
    cjk_text = "".join(_CJK_RE.findall(text))
    if not cjk_text:
        return 0.0

    # 短 CJK 关键词（≤2 字）：精确匹配已经试过且失败，直接返回 0
    if len(kw_cjk) <= 2:
        return 0.0

    # 长 CJK 关键词（≥3 字）：字符级重叠
    kw_chars = set(kw_cjk)
    matches = sum(1 for c in kw_chars if c in cjk_text)
    return matches / len(kw_cjk)


def load_strategies(strategies_path: Optional[str] = None) -> dict:
    """加载 strategies.yaml。

    使用模块级缓存避免重复 IO。
    默认路径为同目录下的 strategies.yaml。

    Args:
        strategies_path: YAML 配置文件路径。为 None 时使用默认路径。

    Returns:
        完整的 YAML 配置 dict，加载失败则返回空 dict。
    """
    global _strategies
    if _strategies is not None:
        return _strategies

    path = strategies_path
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "strategies.yaml")

    try:
        with open(path, "r", encoding="utf-8") as f:
            _strategies = yaml.safe_load(f)
    except Exception as e:
        logger.warning("加载 strategies.yaml 失败: %s", e)
        _strategies = {}
    return _strategies


def classify_intent(
    task_description: str,
    strategies: Optional[dict] = None,
) -> Dict[str, Any]:
    """从任务描述中识别意图类型。

    使用关键词匹配 + 置信度评分规则。
    - 对每个意图的关键词列表在 task_description 中逐词匹配
    - 计算每个意图的匹配得分
    - 取最高得分意图，置信度 = best / (best + second)
    - 如果最高置信度 < 0.5，返回 spec_driven 兜底

    Args:
        task_description: 用户任务描述文本
        strategies: 预加载的策略配置。为 None 时自动加载。

    Returns:
        dict with keys:
            intent: str — 识别的意图名称（7+1 中的一种）
            confidence: float — 置信度 [0.0, 1.0]
    """
    if strategies is None:
        strategies = load_strategies()
    intents = strategies.get("intents", {})

    scores: Dict[str, float] = {}
    for intent_name, intent_config in intents.items():
        keywords = intent_config.get("keywords", [])
        if not keywords:
            continue
        score = 0.0
        for kw in keywords:
            match = keyword_match_score(kw, task_description)
            if match >= 0.5:
                score += match
        if score > 0:
            scores[intent_name] = score

    if not scores:
        return {"intent": "spec_driven", "confidence": 0.0}

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best_intent = ranked[0][0]
    best_score = ranked[0][1]
    second_score = ranked[1][1] if len(ranked) > 1 else 0.0

    confidence = best_score / (best_score + second_score) if best_score > 0 else 0.0

    if confidence < 0.5:
        return {"intent": "spec_driven", "confidence": confidence}

    return {"intent": best_intent, "confidence": confidence}


def get_strategy(
    intent: str,
    strategies: Optional[dict] = None,
) -> Dict[str, Any]:
    """从 strategies.yaml 查询对应策略参数。

    Args:
        intent: 意图名称（7+1 中的一种）
        strategies: 预加载的策略配置。为 None 时自动加载。

    Returns:
        策略配置 dict，包含 interview_depth / plan_granularity / review_standard / execution_mode。
        意图不存在则返回空 dict。
    """
    if strategies is None:
        strategies = load_strategies()
    intent_config = strategies.get("intents", {}).get(intent, {})
    return intent_config.get("strategy", {})


def generate_exclusion_list(
    intent: str,
    strategies: Optional[dict] = None,
) -> List[str]:
    """I-08 Layer 1 Metis 反向追问：根据 intent 生成排除清单。

    从 strategies.yaml 读取该 intent 的 common_creep 列表作为排除项。

    Args:
        intent: 识别的意图名称
        strategies: 预加载的策略配置。为 None 时自动加载。

    Returns:
        排除项字符串列表
    """
    if strategies is None:
        strategies = load_strategies()
    intent_config = strategies.get("intents", {}).get(intent, {})
    return intent_config.get("common_creep", [])


def build_context_injection(
    user_message: str,
    is_first_turn: bool = False,
    strategies: Optional[dict] = None,
) -> Optional[Dict[str, str]]:
    """构建策略指引 + 排除清单的上下文注入内容。

    这是核心编排函数：
    1. classify_intent() 识别意图
    2. get_strategy() 查询对应策略
    3. generate_exclusion_list() 生成排除清单
    4. 拼装为自然语言字符串

    Args:
        user_message: 用户消息原文
        is_first_turn: 是否为首轮调用
        strategies: 预加载的策略配置。为 None 时自动加载。

    Returns:
        dict with 'context' key 包含注入文本，或 None（非首轮或无法处理时）
    """
    if not is_first_turn or not user_message:
        return None

    if strategies is None:
        strategies = load_strategies()

    # 1. 分类
    result = classify_intent(user_message, strategies)
    intent = result["intent"]
    confidence = result["confidence"]

    # 2. 查策略
    strategy = get_strategy(intent, strategies)

    # 3. 排除清单
    exclusions = generate_exclusion_list(intent, strategies)

    # 4. 拼装
    parts: List[str] = []
    parts.append(
        f"[I-10 意图路由] 识别意图: {intent}（置信度: {confidence:.1f}）"
    )

    if strategy:
        parts.append(
            "策略："
            f"面谈={strategy.get('interview_depth', '?')}, "
            f"Plan粒度={strategy.get('plan_granularity', '?')}, "
            f"审查标准={strategy.get('review_standard', '?')}"
        )

    if exclusions:
        parts.append(
            "[I-08 排除清单] 以下不在本次任务范围内: "
            + " / ".join(exclusions)
        )

    return {"context": "\n".join(parts)}
