"""级联修正引擎 — DAG 拓扑排序与 BFS 级联传播

基于 I-06 OKR PlanStep 级联修正理论：
1. 从 modified_step_id 出发 BFS 遍历依赖图
2. 按 association_strength 分级处理影响
3. 更新被影响步骤的状态为 pending_review 或 notify
"""

from __future__ import annotations

import logging
from typing import Dict, List, Protocol

from platform_core.plan_engine.models import AssociationStrength, OKRPlanStep, PlanStatus

logger = logging.getLogger(__name__)


class PlanStorageProtocol(Protocol):
    """级联修正引擎所需的存储接口协议

    实现此协议的对象负责持久化步骤状态变更。
    """

    def update_step_statuses(self, updates: Dict[str, str]) -> None:
        """批量更新步骤状态

        Args:
            updates: {step_id: action}，action 为 "pending_review" 或 "notify"
        """
        ...

    def update_plan_timestamp(self, plan_id: str) -> None:
        """更新 Plan 的时间戳"""
        ...


def cascade_correct(
    plan_id: str,
    modified_step_id: str,
    plan_steps: Dict[str, OKRPlanStep],
    storage: PlanStorageProtocol,
) -> Dict:
    """级联修正引擎核心算法

    从 modified_step_id 出发，沿 dependency_ids 和 parent_id→children BFS 遍历。
    按 association_strength 分级处理：
    - STRONG → pending_review（需人工审查）
    - MODERATE → pending_review（浅审查）
    - WEAK → notify（仅通知）

    Args:
        plan_id: Plan 唯一标识
        modified_step_id: 被修改的步骤 ID
        plan_steps: {step_id: OKRPlanStep} 映射
        storage: 存储层接口（需实现 PlanStorageProtocol）

    Returns:
        {"affected_steps": [...], "action": {step_id: action}}
    """
    affected: Dict[str, str] = {}
    visited: set = set()
    queue: List[str] = [modified_step_id]

    while queue:
        current_id = queue.pop(0)
        if current_id in visited:
            continue
        visited.add(current_id)

        # 搜索所有依赖此步骤的步骤（反向查找：谁依赖我？）
        for sid, s in plan_steps.items():
            if current_id in s.dependency_ids:
                if sid not in visited:
                    queue.append(sid)

                if s.association_strength == AssociationStrength.STRONG:
                    affected[sid] = "pending_review"
                    s.status = PlanStatus.PENDING_REVIEW
                elif s.association_strength == AssociationStrength.MODERATE:
                    affected[sid] = "pending_review"
                    s.status = PlanStatus.PENDING_REVIEW
                else:
                    affected[sid] = "notify"

        # 搜索子步骤（我依赖谁？正向传播）
        for sid, s in plan_steps.items():
            if s.parent_id == current_id:
                if sid not in visited:
                    queue.append(sid)
                affected[sid] = "notify"

    # 持久化受影响步骤的状态变更
    if affected:
        storage.update_step_statuses(
            {sid: action for sid, action in affected.items() if action == "pending_review"}
        )
        storage.update_plan_timestamp(plan_id)

    return {"affected_steps": list(affected.keys()), "action": affected}


def detect_cycle(steps: List[OKRPlanStep]) -> bool:
    """使用拓扑排序（Kahn 算法）检测循环依赖

    如果存在循环依赖，返回 True，否则 False。
    """
    # 构建入度表 + 邻接表
    in_degree: Dict[str, int] = {}
    adj: Dict[str, List[str]] = {}
    step_ids = {s.step_id for s in steps}

    for s in steps:
        in_degree.setdefault(s.step_id, 0)
        adj.setdefault(s.step_id, [])

    for s in steps:
        for dep_id in s.dependency_ids:
            # 只统计在同一 plan 内的依赖
            if dep_id in step_ids:
                adj.setdefault(dep_id, []).append(s.step_id)
                in_degree[s.step_id] = in_degree.get(s.step_id, 0) + 1

    # Kahn 算法
    queue = [sid for sid, deg in in_degree.items() if deg == 0]
    visited_count = 0

    while queue:
        node = queue.pop(0)
        visited_count += 1
        for neighbor in adj.get(node, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return visited_count != len(steps)


def build_adjacency_list(steps: List[OKRPlanStep]) -> Dict[str, List[str]]:
    """构建依赖图邻接表（正向：step → 依赖于 step 的步骤列表）"""
    adj: Dict[str, List[str]] = {}
    for s in steps:
        adj.setdefault(s.step_id, [])
    for s in steps:
        for dep_id in s.dependency_ids:
            adj.setdefault(dep_id, []).append(s.step_id)
    return adj
