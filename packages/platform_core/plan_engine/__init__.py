"""Plan Engine — DAG 级联修正核心逻辑"""

from platform_core.plan_engine.models import OKRPlanStep, PlanStatus, AssociationStrength
from platform_core.plan_engine.dag import cascade_correct, detect_cycle, build_adjacency_list, PlanStorageProtocol

# ── 类名别名（兼容期望模块级类名的调用方） ──
import platform_core.plan_engine.dag as PlanEngine  # noqa: F401

__all__ = [
    "OKRPlanStep",
    "PlanStatus",
    "AssociationStrength",
    "cascade_correct",
    "detect_cycle",
    "build_adjacency_list",
    "PlanStorageProtocol",
    "PlanEngine",
]
