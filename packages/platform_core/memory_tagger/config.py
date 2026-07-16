"""Memory Tagger — λ 阈值与任务类型映射配置

参考：I-12 Memory 粒度控制 §3.1–3.2
"""

from typing import Dict, List

# λ 区间 → 注入的记忆层级
# 低 λ = 仅保留约束层（发散任务/创意场景）
# 高 λ = 全量记忆（收敛任务/工程场景）
LAMBDA_LEVELS: List[Dict] = [
    {
        "min": 0.0,
        "max": 0.3,
        "label": "weak",
        "layers": ["constraint"],
        "description": "弱 Memory：仅约束层，适合发散性任务",
    },
    {
        "min": 0.4,
        "max": 0.7,
        "label": "mixed",
        "layers": ["constraint", "preference", "decision"],
        "description": "中等 Memory：约束+偏好+决策，适合混合任务",
    },
    {
        "min": 0.8,
        "max": 1.0,
        "label": "strong",
        "layers": ["constraint", "preference", "style", "decision", "pattern"],
        "description": "强 Memory：全量注入，适合收敛性任务",
    },
]

# 任务类型 → 建议 λ 值
TASK_TYPE_MAPPINGS: Dict[str, Dict] = {
    "convergent": {
        "label": "convergent",
        "suggested_lambda": 1.0,
        "description": "收敛任务（工程/部署/排查）— 需要全部历史约束",
        "keywords": ["修复", "部署", "排查", "调试", "构建", "发布", "合并", "删除"],
    },
    "divergent": {
        "label": "divergent",
        "suggested_lambda": 0.0,
        "description": "发散任务（创意/写作/构思）— 不注入偏好和风格",
        "keywords": ["构思", "设计", "写作", "批判", "探索", "头脑风暴", "创意", "灵感"],
    },
    "mixed": {
        "label": "mixed",
        "suggested_lambda": 0.5,
        "description": "混合任务（方案/策略/分析）— 平衡约束与自由度",
        "keywords": ["方案", "策略", "分析", "评估", "对比", "评审", "规划"],
    },
}

DEFAULT_LAMBDA: float = 0.5
DEFAULT_LAMBDA_LABEL: str = "mixed"


def resolve_layers(lambda_value: float) -> List[str]:
    """根据 λ 值返回应注入的层级列表

    Args:
        lambda_value: Memory 强度参数 λ ∈ [0, 1]

    Returns:
        应注入的层级名称列表
    """
    for level in LAMBDA_LEVELS:
        if level["min"] <= lambda_value <= level["max"]:
            return level["layers"]
    # fallback: λ=0 时返回最低层级
    return LAMBDA_LEVELS[0]["layers"]


def resolve_task_config(task_type: str) -> Dict:
    """根据任务类型返回建议的 λ 配置

    Args:
        task_type: "convergent" | "divergent" | "mixed"

    Returns:
        任务类型配置字典，含 suggested_lambda、label、description
    """
    return TASK_TYPE_MAPPINGS.get(task_type, TASK_TYPE_MAPPINGS["mixed"])
