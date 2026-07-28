"""Intent classification and strategy binding for the packaged plugin."""

from __future__ import annotations

import logging
import re
from importlib import resources
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)
_CJK_RE = re.compile(r"[\u4e00-\u9fff]+")
_strategies: Optional[dict] = None


def _keyword_match_score(keyword: str, text: str) -> float:
    if keyword.lower() in text.lower():
        return 1.0
    cjk_chars = _CJK_RE.findall(keyword)
    if not cjk_chars:
        return 0.0
    keyword_cjk = "".join(cjk_chars)
    text_cjk = "".join(_CJK_RE.findall(text))
    if not text_cjk or len(keyword_cjk) <= 2:
        return 0.0
    keyword_chars = set(keyword_cjk)
    matches = sum(1 for character in keyword_chars if character in text_cjk)
    return matches / len(keyword_cjk)


def _load_strategies() -> dict:
    global _strategies
    if _strategies is not None:
        return _strategies
    try:
        strategy_file = resources.files("deepseek_harness.resources").joinpath(
            "strategies.yaml"
        )
        with strategy_file.open("r", encoding="utf-8") as handle:
            _strategies = yaml.safe_load(handle) or {}
    except Exception as exc:
        logger.warning("加载 strategies.yaml 失败: %s", exc)
        _strategies = {}
    return _strategies


def classify_intent(task_description: str) -> Dict[str, Any]:
    intents = _load_strategies().get("intents", {})
    scores: Dict[str, float] = {}
    for intent_name, intent_config in intents.items():
        keywords = intent_config.get("keywords", [])
        if not keywords:
            continue
        score = sum(
            match
            for keyword in keywords
            if (match := _keyword_match_score(keyword, task_description)) >= 0.5
        )
        if score > 0:
            scores[intent_name] = score

    if not scores:
        return {"intent": "spec_driven", "confidence": 0.0}

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    best_intent, best_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else 0.0
    confidence = best_score / (best_score + second_score) if best_score else 0.0
    if confidence < 0.5:
        return {"intent": "spec_driven", "confidence": confidence}
    return {"intent": best_intent, "confidence": confidence}


def get_strategy(intent: str) -> Dict[str, Any]:
    return _load_strategies().get("intents", {}).get(intent, {}).get("strategy", {})


def generate_exclusion_list(
    task_description: str,
    intent: str,
    project_context: Optional[dict] = None,
) -> List[str]:
    del task_description, project_context
    return _load_strategies().get("intents", {}).get(intent, {}).get(
        "common_creep", []
    )


def build_context_injection(
    user_message: str,
    is_first_turn: bool = False,
) -> Optional[Dict[str, str]]:
    if not is_first_turn or not user_message:
        return None

    result = classify_intent(user_message)
    intent = result["intent"]
    confidence = result["confidence"]
    strategy = get_strategy(intent)
    exclusions = generate_exclusion_list(user_message, intent)

    parts = [f"[I-10 意图路由] 识别意图: {intent}（置信度: {confidence:.1f}）"]
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


def on_pre_llm_call(**kwargs) -> Optional[Dict[str, Any]]:
    try:
        return build_context_injection(
            user_message=kwargs.get("user_message", ""),
            is_first_turn=kwargs.get("is_first_turn", False),
        )
    except Exception as exc:  # pragma: no cover - hook isolation contract
        logger.error("intent_router.on_pre_llm_call 异常: %s", exc, exc_info=True)
        return None
