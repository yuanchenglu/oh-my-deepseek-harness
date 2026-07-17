"""Harness Server — 合并后的 FastAPI MCP 服务

本文件将 3 个原服务的 FastAPI 应用合并为一个，提供 10 个核心端点 + 1 个健康检查：

Plan Engine（I-06 OKR PlanStep DAG + 级联修正）：
  1. POST /plan/create           — 从任务描述创建 OKR PlanStep 列表
  2. PUT  /plan/step/{step_id}   — 更新步骤状态/内容 + 自动级联修正
  3. POST /plan/cascade          — 级联修正引擎
  4. GET  /plan/status/{plan_id} — 获取 Plan 状态和依赖图

Memory Tagger（I-12 Memory 标签 + λ 过滤）：
  5. POST /memory/tag            — 输入内容 → 返回层级标签
  6. POST /memory/query          — 按标签/层级查询记忆
  7. POST /memory/filter         — 按 λ 值过滤记忆

Checkpoint Review（I-11 Checkpoint 快照审查）：
  8. POST /checkpoint/create             — 从 Plan 状态提取结构化 Checkpoint 快照
  9. POST /checkpoint/review/{id}        — 对 Checkpoint 执行审查
 10. GET  /checkpoint/chain/{plan_id}    — 获取 Plan 的完整 Checkpoint 链

健康检查：
 11. GET  /health               — 返回服务状态和存储统计

数据持久化：单 SQLite (~/.hermes/mcp/harness.db)
启动端口：8200
"""

from __future__ import annotations

import glob
import logging
import os
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from fastapi import FastAPI, HTTPException, Query

# 使用相对导入（harness_server 包内部）
from .models import (
    AssociationStrength,
    CascadeRequest,
    CascadeResponse,
    ChainResponse,
    Checkpoint,
    CompletedStep,
    CreateCheckpointRequest,
    CreateCheckpointResponse,
    CreatePlanRequest,
    CreatePlanResponse,
    DictStep,
    ErrorResponse,
    FilterRequest,
    FilterResponse,
    MemoryEntry,
    MemoryLayer,
    OKRPlanStep,
    PlanStatus,
    PlanStatusResponse,
    QueryRequest,
    QueryResponse,
    ReviewRequest,
    ReviewResponse,
    ReviewResult,
    TagRequest,
    TagResponse,
    UpdateStepRequest,
    generate_checkpoint_id,
    now_iso,
)
from .storage import HarnessStorage

# ════════════════════════════════════════════════════════════════
# 日志配置
# ════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("harness-server")

# ════════════════════════════════════════════════════════════════
# 配置加载（从 config.yaml 读取 Memory Tagger 相关配置）
# ════════════════════════════════════════════════════════════════

# config.yaml 与 server.py 在同一目录下
CONFIG_PATH = Path(__file__).parent / "config.yaml"


def load_config() -> dict:
    """加载 config.yaml 配置文件

    如果文件不存在或解析失败，返回空字典（使用代码中的默认值）。

    Returns:
        配置字典
    """
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        logger.warning("config.yaml 未找到，使用默认配置")
        return {}
    except yaml.YAMLError as e:
        logger.warning("config.yaml 解析失败: %s，使用默认配置", e)
        return {}


config = load_config()

# 从配置中提取 Memory Tagger 相关设置
storage_config = config.get("storage", {})
TASK_LAMBDA_MAP: Dict[str, dict] = {}
task_mappings = config.get("task_type_mappings", {})
for task_type, mapping in task_mappings.items():
    if isinstance(mapping, dict):
        TASK_LAMBDA_MAP[task_type] = mapping

DEFAULT_LAMBDA = config.get("default_lambda", 0.5)
DEFAULT_LAMBDA_LABEL = config.get("default_lambda_label", "mixed")

# ════════════════════════════════════════════════════════════════
# 存储层初始化（单 SQLite，3 组表）
# ════════════════════════════════════════════════════════════════

# 数据库路径：优先用 config.yaml 中的配置，其次用环境变量，最后用默认路径
db_path = os.path.expanduser(
    storage_config.get("db_path", "~/.hermes/mcp/harness.db")
)
storage = HarnessStorage(db_path=db_path)


# ════════════════════════════════════════════════════════════════
# 第一部分：Memory Tagger 标签分类逻辑
# （迁移自 memory-tagger/tagger.py）
# ════════════════════════════════════════════════════════════════


@dataclass
class LayerRule:
    """单条层级匹配规则

    通过关键词匹配判断记忆内容属于哪个层级。

    Attributes:
        layer: 该规则对应的记忆层级
        keywords: 触发该层级的关键词列表
        weight: 匹配权重，用于置信度计算（权重越高，该层级优先级越高）
    """

    layer: MemoryLayer
    keywords: List[str]
    weight: float = 1.0


# 层级匹配规则表（关键词按优先级排列）
# 每条规则中的关键词越多，匹配的置信度越高
# 这个表是 Memory Tagger 的核心——它定义了如何从文本内容推断记忆层级
LAYER_RULES: Dict[MemoryLayer, LayerRule] = {
    # 约束层：安全/合规相关，权重最高（2.0），因为约束不可遗忘
    MemoryLayer.CONSTRAINT: LayerRule(
        layer=MemoryLayer.CONSTRAINT,
        keywords=[
            "不能", "不要", "必须", "禁止", "严禁",
            "不得", "不可", "不允许", "一定不要", "绝对不要",
            "should not", "must not", "never",
            "禁止使用", "禁用", "不允许使用",
        ],
        weight=2.0,
    ),
    # 偏好层：技术选择和习惯
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
    # 风格层：写作/编码风格
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
    # 决策层：历史决策和结论
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
    # 模式层：成功经验和规律
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
    """在内容中查找所有匹配的关键词

    遍历所有层级的规则，统计每个层级匹配到的关键词数量。

    Args:
        content: 要分析的记忆内容文本

    Returns:
        匹配结果列表，每项是 (层级, 匹配关键词数)，只返回匹配数 > 0 的层级
    """
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
    """对记忆内容进行层级分类

    这是 Memory Tagger 的核心函数。通过关键词匹配判断内容属于哪个层级。

    算法流程：
    1. 查找所有匹配的关键词
    2. 按加权匹配数排序（score = count × weight）
    3. 取分数最高的层级作为分类结果
    4. 置信度 = 最高分 / 总分

    Args:
        content: 记忆内容文本

    Returns:
        元组 (layer, matched_keywords, confidence):
        - layer: 最匹配的记忆层级（无匹配时默认 PATTERN）
        - matched_keywords: 命中的关键词列表
        - confidence: 分类置信度 [0, 1]
    """
    matches = _find_matches(content)

    if not matches:
        # 无匹配时默认归入 pattern 层（可降级到其他默认层）
        return MemoryLayer.PATTERN, [], 0.0

    # 按加权匹配数排序：score = count * weight
    scored = [
        (layer, count, LAYER_RULES[layer].weight * count)
        for layer, count in matches
    ]
    scored.sort(key=lambda x: x[2], reverse=True)

    best_layer, best_count, best_score = scored[0]
    total_score = sum(s for _, _, s in scored)

    # 提取命中层级的关键词
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

    与 classify 不同，这个函数返回所有层级命中的关键词（不区分层级），
    用于给记忆打多个标签方便后续检索。

    Args:
        content: 记忆内容文本

    Returns:
        去重后的关键词列表
    """
    tags: List[str] = []
    for rule in LAYER_RULES.values():
        for kw in rule.keywords:
            if re.search(re.escape(kw), content, re.IGNORECASE):
                tags.append(kw)
    return tags


def detect_task_type(task_prompt: str) -> str:
    """检测任务类型：convergent / divergent / mixed

    通过关键词匹配判断任务属于哪种类型，用于推荐合适的 λ 值。

    - convergent（收敛）：修复/部署/排查等工程任务，需要全部历史约束
    - divergent（发散）：构思/设计/写作等创意任务，不注入偏好避免限制
    - mixed（混合）：方案/策略/分析等，平衡约束与自由度

    Args:
        task_prompt: 任务描述文本

    Returns:
        任务类型字符串："convergent" / "divergent" / "mixed"
    """
    # 任务类型关键词映射表
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

    # 无法识别时默认 mixed
    if all(v == 0 for v in scores.values()):
        return "mixed"

    return max(scores, key=scores.get)


# ════════════════════════════════════════════════════════════════
# 第二部分：Plan Engine 级联修正引擎
# （迁移自 plan-engine/engine.py）
# ════════════════════════════════════════════════════════════════


def cascade_correct(
    plan_id: str,
    modified_step_id: str,
    plan_steps: Dict[str, OKRPlanStep],
    store: HarnessStorage,
) -> Dict:
    """级联修正引擎核心算法

    当某个步骤被修改后，沿依赖图 BFS 遍历，按关联强度分级处理影响。

    算法流程：
    1. 从 modified_step_id 出发
    2. 反向查找：谁依赖我？（搜索 dependency_ids 包含当前步骤的步骤）
    3. 正向查找：我有哪些子步骤？（搜索 parent_id 等于当前步骤的步骤）
    4. 按关联强度分级处理：
       - STRONG → pending_review（需人工审查）
       - MODERATE → pending_review（浅审查）
       - WEAK → notify（仅通知，不改变状态）
    5. 持久化状态变更

    Args:
        plan_id: Plan 唯一标识
        modified_step_id: 被修改的步骤 ID（级联修正的起点）
        plan_steps: Plan 的所有步骤字典 {step_id: OKRPlanStep}
        store: 存储层实例（用于持久化状态变更）

    Returns:
        字典 {"affected_steps": [...], "action": {step_id: "pending_review"|"notify"}}
    """
    affected: Dict[str, str] = {}
    visited: set = set()
    queue: List[str] = [modified_step_id]

    while queue:
        current_id = queue.pop(0)
        if current_id in visited:
            continue
        visited.add(current_id)

        # 反向查找：搜索所有依赖此步骤的步骤（谁依赖我？）
        for sid, s in plan_steps.items():
            if current_id in s.dependency_ids:
                if sid not in visited:
                    queue.append(sid)

                # 按关联强度分级处理
                if s.association_strength == AssociationStrength.STRONG:
                    affected[sid] = "pending_review"
                    s.status = PlanStatus.PENDING_REVIEW
                elif s.association_strength == AssociationStrength.MODERATE:
                    affected[sid] = "pending_review"
                    s.status = PlanStatus.PENDING_REVIEW
                else:
                    # WEAK 关联仅通知，不改变状态
                    affected[sid] = "notify"

        # 正向查找：搜索子步骤（我依赖谁？向下游传播）
        for sid, s in plan_steps.items():
            if s.parent_id == current_id:
                if sid not in visited:
                    queue.append(sid)
                affected[sid] = "notify"

    # 持久化受影响步骤的状态变更（只有 pending_review 需要写库，notify 不改状态）
    if affected:
        conn = store._connection()
        try:
            for sid, action in affected.items():
                if action == "pending_review":
                    conn.execute(
                        "UPDATE steps SET status = ? WHERE step_id = ?",
                        (PlanStatus.PENDING_REVIEW.value, sid),
                    )
            conn.commit()
        finally:
            conn.close()

        # 更新 Plan 时间戳
        store.update_plan_timestamp(plan_id)

    return {"affected_steps": list(affected.keys()), "action": affected}


def detect_cycle(steps: List[OKRPlanStep]) -> bool:
    """使用拓扑排序（Kahn 算法）检测循环依赖

    如果依赖图中存在环，返回 True。

    算法：
    1. 构建入度表和邻接表
    2. 将入度为 0 的节点入队
    3. 每次出队一个节点，将其邻居入度减 1
    4. 如果最终访问的节点数 ≠ 总节点数，说明有环

    Args:
        steps: 步骤列表

    Returns:
        True 表示存在循环依赖，False 表示无环
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

    # Kahn 算法：BFS 拓扑排序
    queue = [sid for sid, deg in in_degree.items() if deg == 0]
    visited_count = 0

    while queue:
        node = queue.pop(0)
        visited_count += 1
        for neighbor in adj.get(node, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # 如果访问的节点数 ≠ 总节点数，说明有环
    return visited_count != len(steps)


def build_adjacency_list(steps: List[OKRPlanStep]) -> Dict[str, List[str]]:
    """构建依赖图邻接表（正向）

    邻接表格式: {step_id: [依赖于它的 step_id 列表]}
    例如: {"s1": ["s2", "s3"]} 表示 s2 和 s3 都依赖 s1

    Args:
        steps: 步骤列表

    Returns:
        邻接表字典
    """
    adj: Dict[str, List[str]] = {}
    for s in steps:
        adj.setdefault(s.step_id, [])
    for s in steps:
        for dep_id in s.dependency_ids:
            adj.setdefault(dep_id, []).append(s.step_id)
    return adj


# ════════════════════════════════════════════════════════════════
# 第三部分：Plan 辅助函数
# （迁移自 plan-engine/server.py）
# ════════════════════════════════════════════════════════════════


def _decompose_task(task_description: str) -> List[Dict]:
    """将任务描述分解为 3-8 个步骤

    这是一个基于规则的任务分解器（不调用 LLM）：
    1. 优先按序号列表分割（"1. xxx\n2. yyy"）
    2. 如果结果太少或太多，按句号/分号分割
    3. 如果还是太少，按逗号分割
    4. 最终保证在 3-8 个步骤之间

    Args:
        task_description: 任务描述文本

    Returns:
        步骤字典列表，每项 {"text": "...", "key": "S1"}
    """
    lines = [l.strip() for l in task_description.strip().split("\n") if l.strip()]
    steps_raw = []

    # 尝试按序号分割（"1. xxx" 或 "1、xxx"）
    numbered = False
    for line in lines:
        m = re.match(r"^(\d+)[.、．\s]+(.+)$", line)
        if m:
            numbered = True
            steps_raw.append(m.group(2))
        elif not numbered and line:
            steps_raw.append(line)

    # 如果结果太少或太多，按句子重新分割
    if len(steps_raw) < 3 or len(steps_raw) > 8:
        sentences = re.split(r"[。；;]", task_description)
        steps_raw = [s.strip() for s in sentences if len(s.strip()) > 4]

    # 如果还是太少，按逗号分割
    if len(steps_raw) < 3:
        chunks = re.split(r"[，,]", task_description)
        steps_raw = [c.strip() for c in chunks if len(c.strip()) > 4]

    # 保证在 3-8 个步骤之间
    if len(steps_raw) < 3:
        steps_raw = [f"步骤 {i+1}: {task_description}" for i in range(3)]
    if len(steps_raw) > 8:
        steps_raw = steps_raw[:8]

    # 生成步骤字典
    result = []
    for i, text in enumerate(steps_raw):
        result.append({
            "text": text.strip(),
            "key": f"S{i+1}",
        })
    return result


def _steps_to_model(steps_data: List[Dict]) -> List[OKRPlanStep]:
    """将步骤字典列表转换为 OKRPlanStep 对象列表

    自动设置：
    - step_id（UUID）
    - dependency_ids（按顺序链式链接：step_2 依赖 step_1）
    - association_strength（按位置：第 1 步 STRONG，第 2 步 MODERATE，之后 WEAK）

    Args:
        steps_data: 步骤字典列表

    Returns:
        OKRPlanStep 对象列表
    """
    steps: List[OKRPlanStep] = []
    for i, sd in enumerate(steps_data):
        step_id = str(uuid.uuid4())
        dep_ids = []
        # 按顺序链接：每个步骤依赖前一个步骤
        if i > 0:
            dep_ids.append(steps[i - 1].step_id)

        # 关联强度：第 1 步 STRONG，第 2 步 MODERATE，之后 WEAK
        strength = AssociationStrength.STRONG
        if i >= 2:
            strength = AssociationStrength.WEAK
        elif i >= 1:
            strength = AssociationStrength.MODERATE

        step = OKRPlanStep(
            step_id=step_id,
            text=sd["text"],
            key=sd.get("key", ""),
            status=PlanStatus.PENDING,
            dependency_ids=dep_ids,
            association_strength=strength,
        )
        steps.append(step)

    return steps


# ════════════════════════════════════════════════════════════════
# 第四部分：Checkpoint 辅助函数
# （迁移自 checkpoint-review/server.py）
# ════════════════════════════════════════════════════════════════


def _build_completed_summary(request: CreateCheckpointRequest) -> List[CompletedStep]:
    """从请求中提取已完成的步骤摘要

    Args:
        request: 创建 Checkpoint 的请求

    Returns:
        已完成步骤的摘要列表
    """
    step_map = {s.step_id: s for s in request.plan_steps}
    summary: List[CompletedStep] = []
    for sid in request.completed_step_ids:
        step = step_map.get(sid)
        if step:
            summary.append(CompletedStep(
                step_id=sid,
                text=step.text,
                result="",
            ))
    return summary


def _build_remaining_plan(request: CreateCheckpointRequest) -> List[str]:
    """提取剩余（未完成）的 Plan 步骤描述

    Args:
        request: 创建 Checkpoint 的请求

    Returns:
        剩余步骤描述列表，格式如 "[step_id] 步骤文本"
    """
    completed_set = set(request.completed_step_ids)
    return [
        f"[{s.step_id}] {s.text}" for s in request.plan_steps
        if s.step_id not in completed_set
    ]


def _build_current_goal(request: CreateCheckpointRequest) -> str:
    """推断当前正在执行的目标

    取第一个未完成的步骤作为当前目标；如果全部完成则返回最后一步。

    Args:
        request: 创建 Checkpoint 的请求

    Returns:
        当前目标描述文本
    """
    completed_set = set(request.completed_step_ids)
    for s in request.plan_steps:
        if s.step_id not in completed_set:
            return s.text
    # 全部完成 → 取最后一步的文本
    if request.plan_steps:
        return request.plan_steps[-1].text
    return ""


def _check_alignment_from_snapshot(checkpoint: Checkpoint) -> str:
    """基于快照检查目标对齐程度

    审查时没有原始 plan_steps，用 completed_steps 和 unexpected_findings 判断：
    - 有 completed_steps 但无 remaining_plan → 全部完成 → aligned
    - 有 completed_steps 且有 remaining_plan → 正在执行 → aligned
    - 有 unexpected_findings → 可能走偏了 → partial

    Args:
        checkpoint: Checkpoint 快照

    Returns:
        对齐程度: "aligned" | "partial" | "deviated"
    """
    if not checkpoint.completed_steps_summary:
        return "aligned"  # 还没开始，无所谓偏离

    if checkpoint.unexpected_findings:
        # 有意外发现 → 可能走偏了
        return "partial"

    return "aligned"


def _check_progress_from_snapshot(checkpoint: Checkpoint) -> str:
    """基于快照检查进度状态

    用已完成步骤数 / (已完成 + 剩余) 的比率估算：
    - ratio >= 0.5 → on_track
    - 0.25 <= ratio < 0.5 → at_risk
    - ratio < 0.25 → behind

    Args:
        checkpoint: Checkpoint 快照

    Returns:
        进度状态: "on_track" | "at_risk" | "behind"
    """
    done = len(checkpoint.completed_steps_summary)
    remaining = len(checkpoint.remaining_plan)
    total = done + remaining

    if total == 0:
        return "on_track"

    ratio = done / total
    if ratio >= 0.5:
        return "on_track"
    elif ratio >= 0.25:
        return "at_risk"
    else:
        return "behind"


def _compute_unexpected_impact(checkpoint: Checkpoint) -> str:
    """评估意外发现的影响程度

    判断规则：
    - 无意外发现 → none
    - 包含严重关键词（安全/漏洞/崩溃等）→ high
    - 发现条数 >= 3 → medium
    - 其他 → low

    Args:
        checkpoint: Checkpoint 快照

    Returns:
        影响程度: "none" | "low" | "medium" | "high"
    """
    findings = checkpoint.unexpected_findings or []
    if not findings:
        return "none"

    # 严重关键词列表（中英文）
    severe_keywords = {"security", "vulnerability", "crash", "data loss",
                       "安全", "漏洞", "崩溃", "数据丢失"}
    combined = " ".join(f.lower() for f in findings)
    for kw in severe_keywords:
        if kw.lower() in combined:
            return "high"

    if len(findings) >= 3:
        return "medium"

    return "low"


def _adjustments_from_snapshot(
    checkpoint: Checkpoint,
    alignment: str,
    progress: str,
    impact: str,
) -> List[str]:
    """从快照生成剩余计划调整建议

    根据审查结果生成可操作的调整建议列表。

    Args:
        checkpoint: Checkpoint 快照
        alignment: 目标对齐程度
        progress: 进度状态
        impact: 意外发现影响

    Returns:
        调整建议字符串列表
    """
    adjustments: List[str] = []

    if alignment == "partial":
        adjustments.append("部分步骤可能偏离原始目标，建议复审已完成的步骤内容")

    if progress == "behind":
        adjustments.append("进度落后，建议考虑缩减范围或增加资源")

    if impact == "high":
        adjustments.append("安全/合规风险较高，建议暂停并优先处理意外发现")
    elif impact == "medium":
        adjustments.append("存在多项意外发现，建议评估后再继续")

    if checkpoint.remaining_plan:
        adjustments.append(
            f"剩余 {len(checkpoint.remaining_plan)} 步: "
            f"{'; '.join(checkpoint.remaining_plan[:3])}"
            f"{'...' if len(checkpoint.remaining_plan) > 3 else ''}"
        )

    return adjustments


def _compute_confidence(alignment: str, progress: str, impact: str) -> float:
    """基于快照信息完整度计算审查置信度

    置信度反映审查结果的可信程度：
    - aligned + none impact → 0.90（一切顺利，信息明确）
    - partial + high impact → 0.70（情况复杂，信息不足）
    - deviated → 0.60（偏离严重，需人工介入）
    - 其他 → 0.85（默认置信度）

    Args:
        alignment: 目标对齐程度
        progress: 进度状态（当前未使用，预留扩展）
        impact: 意外发现影响

    Returns:
        置信度 [0, 1]
    """
    if alignment == "aligned" and impact == "none":
        return 0.90
    if alignment == "partial" and impact == "high":
        return 0.70
    if alignment == "deviated":
        return 0.60
    return 0.85


# ════════════════════════════════════════════════════════════════
# 第五部分：Hermes Memory 导入逻辑
# （从 memory-tagger/storage.py 迁移到此处，因为需要 classify/extract_tags）
# ════════════════════════════════════════════════════════════════


def import_hermes_memories(
    memories_dir: str,
    store: HarnessStorage,
) -> Tuple[int, int, int]:
    """从 Hermes Memory 目录导入 .md 文件

    读取指定目录下的所有 .md 文件，将内容分类后批量插入数据库。
    这个函数放在 server.py 而不是 storage.py，因为它需要 classify() 和
    extract_tags() 函数（避免 storage.py ↔ server.py 循环导入）。

    解析策略：
    - 按空行分割段落
    - 跳过标题行（# 开头）、空行、过短片段
    - 每段落用 classify() 分类，用 extract_tags() 提取标签
    - 批量插入数据库

    Args:
        memories_dir: Hermes Memory 目录路径
        store: 存储层实例

    Returns:
        元组 (imported, skipped, total_files):
        - imported: 成功插入的条数
        - skipped: 跳过的文件数
        - total_files: 扫描的文件总数
    """
    if not os.path.isdir(memories_dir):
        logger.warning("Hermes Memory 目录不存在: %s", memories_dir)
        return 0, 0, 0

    md_files = glob.glob(os.path.join(memories_dir, "*.md"))
    total_files = len(md_files)

    imported = 0
    skipped = 0

    for filepath in md_files:
        try:
            ok, count = _import_md_file(filepath, store)
            if ok:
                imported += count
            else:
                skipped += 1
        except Exception as e:
            logger.warning("导入文件失败 %s: %s", filepath, e)
            skipped += 1

    logger.info(
        "Hermes 导入完成: %d 条插入, %d 文件跳过, 共 %d 文件",
        imported, skipped, total_files,
    )
    return imported, skipped, total_files


def _import_md_file(filepath: str, store: HarnessStorage) -> Tuple[bool, int]:
    """导入单个 .md 文件中的记忆

    Args:
        filepath: .md 文件路径
        store: 存储层实例

    Returns:
        元组 (ok, count): ok=是否成功处理, count=插入条数
    """
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()

    # 按空行分割成段落
    blocks = re.split(r"\n\s*\n", text)
    entries: List[MemoryEntry] = []
    source_name = os.path.basename(filepath)

    for block in blocks:
        block = block.strip()
        # 跳过空行、标题行、过短片段
        if not block or len(block) < 10:
            continue
        if block.startswith("#"):
            continue

        # 用 tagger 函数分类和提取标签
        tags = extract_tags(block)
        layer, _, _ = classify(block)

        entry = MemoryEntry(
            content=block[:500],  # 截断超长内容
            tags=tags,
            layer=layer,
            created_at=datetime.now(timezone.utc),
        )
        entries.append(entry)

    if entries:
        count = store.bulk_insert_memories(entries, source=source_name)
        return True, count

    return True, 0


# ════════════════════════════════════════════════════════════════
# 启动时导入 Hermes Memory（如果配置开启）
# ════════════════════════════════════════════════════════════════

if storage_config.get("import_on_startup", True):
    memories_dir = os.path.expanduser(
        storage_config.get("hermes_memories_dir", "~/.hermes/memories/")
    )
    imported, skipped, total = import_hermes_memories(memories_dir, storage)
    logger.info("启动导入: %d 插入, %d 跳过, 共 %d 文件", imported, skipped, total)


# ════════════════════════════════════════════════════════════════
# FastAPI 应用
# ════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Harness MCP Server",
    description=(
        "合并服务：Plan Engine（I-06）+ Memory Tagger（I-12）+ Checkpoint Review（I-11）。"
        "提供 OKR PlanStep DAG 管理级联修正、Memory 标签分类与 λ 过滤、"
        "Checkpoint 快照审查三大功能。"
    ),
    version="1.0.0",
)
# 注意：不加 CORS middleware（本地服务不需要）


# ════════════════════════════════════════════════════════════════
# Plan Engine 端点（/plan 前缀）
# ════════════════════════════════════════════════════════════════


@app.post(
    "/plan/create",
    response_model=CreatePlanResponse,
    responses={422: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
    summary="从任务描述创建 OKR PlanStep 列表",
    description="输入任务描述 → 自动分解为 3-8 个步骤 → 返回 OKRPlanStep 列表",
)
async def create_plan(req: CreatePlanRequest):
    """POST /plan/create — 从任务描述创建 OKR PlanStep 列表

    流程：
    1. 验证任务描述非空
    2. 用 _decompose_task() 分解为 3-8 个步骤
    3. 用 _steps_to_model() 转换为 OKRPlanStep 对象（自动设置依赖和关联强度）
    4. 用 detect_cycle() 检测循环依赖
    5. 生成 plan_id 并持久化到数据库
    """
    try:
        if not req.task_description or not req.task_description.strip():
            raise HTTPException(status_code=422, detail="任务描述不能为空")

        # 分解任务为步骤
        steps_data = _decompose_task(req.task_description)
        steps = _steps_to_model(steps_data)

        # 检测循环依赖
        if detect_cycle(steps):
            raise HTTPException(
                status_code=409,
                detail="检测到循环依赖，请重新描述任务",
            )

        # 生成 plan_id 并持久化
        plan_id = str(uuid.uuid4())
        storage.create_plan(plan_id)
        storage.insert_steps(plan_id, steps)

        logger.info("创建 Plan: %s, 步骤数: %d", plan_id, len(steps))

        return CreatePlanResponse(plan_id=plan_id, steps=steps)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("create_plan 错误: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.put(
    "/plan/step/{step_id}",
    response_model=dict,
    responses={404: {"model": ErrorResponse}},
    summary="更新步骤状态/内容",
    description="更新步骤后自动触发级联修正",
)
async def update_step(step_id: str, req: UpdateStepRequest):
    """PUT /plan/step/{step_id} — 更新步骤状态/内容

    如果更新了 status 或 text，会自动触发级联修正：
    沿依赖图传播影响，将相关步骤标记为 pending_review 或 notify。
    """
    try:
        # 验证步骤存在
        existing = storage.get_step(step_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"步骤不存在: {step_id}")

        # 获取 plan_id
        plan_id = storage.get_step_plan_id(step_id)
        if not plan_id:
            raise HTTPException(status_code=404, detail=f"步骤所属 Plan 不存在: {step_id}")

        # 更新字段
        updated = storage.update_step(
            step_id,
            text=req.text,
            key=req.key,
            status=req.status,
            parent_id=req.parent_id,
            dependency_ids=req.dependency_ids,
            association_strength=req.association_strength,
        )

        if updated:
            storage.update_plan_timestamp(plan_id)
            logger.info("步骤更新成功: %s", step_id)

            # 自动触发级联修正（如果状态变更或内容变更）
            if req.status or req.text:
                steps = storage.get_steps(plan_id)
                steps_dict = {s.step_id: s for s in steps}

                cascade_result = cascade_correct(
                    plan_id=plan_id,
                    modified_step_id=step_id,
                    plan_steps=steps_dict,
                    store=storage,
                )

                return {
                    "status": "updated",
                    "step_id": step_id,
                    "cascade": cascade_result,
                }

        return {"status": "updated", "step_id": step_id, "cascade": None}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_step 错误: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/plan/cascade",
    response_model=CascadeResponse,
    responses={404: {"model": ErrorResponse}},
    summary="级联修正引擎",
    description="从 modified_step_id 出发 BFS 遍历，按关联强度分级处理影响",
)
async def cascade(req: CascadeRequest):
    """POST /plan/cascade — 级联修正引擎

    手动触发级联修正：从指定步骤出发，沿依赖图传播影响。
    """
    try:
        # 获取 Plan 所有步骤
        steps = storage.get_steps(req.plan_id)
        if not steps:
            raise HTTPException(
                status_code=404,
                detail=f"Plan 不存在或无步骤: {req.plan_id}",
            )

        # 验证 modified_step_id 存在
        step_ids = {s.step_id for s in steps}
        if req.modified_step_id not in step_ids:
            raise HTTPException(
                status_code=404,
                detail=f"步骤不存在于该 Plan: {req.modified_step_id}",
            )

        steps_dict = {s.step_id: s for s in steps}
        result = cascade_correct(
            plan_id=req.plan_id,
            modified_step_id=req.modified_step_id,
            plan_steps=steps_dict,
            store=storage,
        )

        logger.info(
            "级联修正: plan=%s, modified=%s, affected=%d",
            req.plan_id, req.modified_step_id, len(result["affected_steps"]),
        )

        return CascadeResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("cascade 错误: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/plan/status/{plan_id}",
    response_model=PlanStatusResponse,
    responses={404: {"model": ErrorResponse}},
    summary="获取 Plan 状态和依赖图",
    description="返回完整 Plan + 依赖图邻接表",
)
async def get_plan_status(plan_id: str):
    """GET /plan/status/{plan_id} — 获取 Plan 状态和依赖图"""
    try:
        meta = storage.get_plan_meta(plan_id)
        if not meta:
            raise HTTPException(status_code=404, detail=f"Plan 不存在: {plan_id}")

        steps = storage.get_steps(plan_id)
        adjacency_list = build_adjacency_list(steps)

        return PlanStatusResponse(
            plan_id=plan_id,
            steps=steps,
            adjacency_list=adjacency_list,
            created_at=meta["created_at"],
            updated_at=meta["updated_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_plan_status 错误: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════════════
# Memory Tagger 端点（/memory 前缀）
# ════════════════════════════════════════════════════════════════


@app.post(
    "/memory/tag",
    response_model=TagResponse,
    responses={422: {"model": ErrorResponse}},
    summary="输入内容 → 返回层级标签",
    description="对单条记忆内容进行层级分类，输出标签、层级和置信度",
)
async def tag_memory(req: TagRequest):
    """POST /memory/tag — 输入内容 → 返回层级标签

    使用关键词规则引擎（LAYER_RULES）对内容分类，
    返回最匹配的层级、命中的关键词列表和置信度。
    """
    try:
        layer, matched_kws, confidence = classify(req.content)
        tags = extract_tags(req.content)

        return TagResponse(
            content=req.content,
            tags=tags,
            layer=layer,
            confidence=confidence,
        )
    except Exception as e:
        logger.error("tag_memory 错误: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/memory/query",
    response_model=QueryResponse,
    responses={422: {"model": ErrorResponse}},
    summary="按标签/层级查询记忆",
    description="从持久化存储中按标签和/或层级检索记忆条目",
)
async def query_memory(req: QueryRequest):
    """POST /memory/query — 按标签/层级查询记忆

    tags 和 layer 都是可选的筛选条件，同时使用时取交集。
    """
    try:
        entries = storage.query_memories(
            tags=req.tags,
            layer=req.layer,
            limit=req.limit,
        )
        return QueryResponse(entries=entries, total=len(entries))
    except Exception as e:
        logger.error("query_memory 错误: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/memory/filter",
    response_model=FilterResponse,
    responses={422: {"model": ErrorResponse}},
    summary="按 λ 值过滤记忆",
    description=(
        "λ ∈ [0, 1]：0.0=仅约束层, 0.5=约束+偏好+决策, 1.0=全部。"
        "从持久化存储按 λ 值过滤记忆。"
    ),
)
async def filter_memory(req: FilterRequest):
    """POST /memory/filter — 按 λ 值过滤记忆

    λ 值决定注入哪些层级的记忆（见 _lambda_to_layers）。
    """
    try:
        entries = storage.filter_by_lambda(req.lambda_value, limit=req.limit)
        layers = storage.get_layers_for_lambda(req.lambda_value)

        return FilterResponse(
            entries=entries,
            total=len(entries),
            lambda_value=req.lambda_value,
            included_layers=layers,
        )
    except Exception as e:
        logger.error("filter_memory 错误: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════════════
# Checkpoint Review 端点（/checkpoint 前缀）
# ════════════════════════════════════════════════════════════════


@app.post(
    "/checkpoint/create",
    response_model=CreateCheckpointResponse,
    responses={422: {"model": ErrorResponse}},
    summary="从 Plan 状态提取结构化 Checkpoint 快照",
    description=(
        "输入 Plan 步骤列表和已完成步骤 ID，生成结构化 Checkpoint 快照。"
        "自动递增 checkpoint_number。"
    ),
)
async def create_checkpoint(req: CreateCheckpointRequest):
    """POST /checkpoint/create — 创建 Checkpoint 快照

    流程：
    1. 验证 plan_id 非空
    2. 自动计算下一个 checkpoint_number
    3. 构建已完成步骤摘要、剩余步骤列表、当前目标
    4. 创建 Checkpoint 对象并持久化
    """
    try:
        if not req.plan_id:
            raise HTTPException(status_code=422, detail="plan_id 不能为空")

        # 自动计算编号
        next_num = storage._get_next_checkpoint_number(req.plan_id)

        # 构建摘要信息
        completed_summary = _build_completed_summary(req)
        remaining = _build_remaining_plan(req)
        current_goal = _build_current_goal(req)

        # 构建 Checkpoint 对象
        checkpoint = Checkpoint(
            checkpoint_id=generate_checkpoint_id(),
            plan_id=req.plan_id,
            created_at=now_iso(),
            checkpoint_number=next_num,
            current_goal=current_goal,
            completed_steps_summary=completed_summary,
            unexpected_findings=req.unexpected_findings or [],
            remaining_plan=remaining,
            purpose="step_threshold",
        )

        # 持久化
        storage.insert_checkpoint(checkpoint)

        logger.info(
            "Checkpoint 创建成功: %s (plan=%s, #%d)",
            checkpoint.checkpoint_id,
            checkpoint.plan_id,
            checkpoint.checkpoint_number,
        )

        return CreateCheckpointResponse(checkpoint=checkpoint)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("create_checkpoint 错误: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/checkpoint/review/{checkpoint_id}",
    response_model=ReviewResponse,
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
    summary="对 Checkpoint 执行轻量上下文审查",
    description=(
        "从存储读取 Checkpoint 快照，对其执行四维审查："
        "目标对齐、进度偏差、意外发现影响、剩余计划调整建议。"
        "仅读快照，不读完整执行日志（上下文递减原则）。"
    ),
)
async def review_checkpoint(checkpoint_id: str, req: ReviewRequest):  # noqa: ARG001
    """POST /checkpoint/review/{checkpoint_id} — 审查 Checkpoint

    审查基于快照做确定性判断（不调用 LLM），从四个维度评估：
    1. 目标对齐（alignment）
    2. 进度状态（progress_status）
    3. 意外发现影响（unexpected_impact）
    4. 调整建议（adjustments）
    """
    try:
        checkpoint = storage.get_checkpoint(checkpoint_id)
        if checkpoint is None:
            raise HTTPException(
                status_code=404,
                detail=f"Checkpoint 不存在: {checkpoint_id}",
            )

        # 基于快照做四维审查
        alignment = _check_alignment_from_snapshot(checkpoint)
        progress = _check_progress_from_snapshot(checkpoint)
        impact = _compute_unexpected_impact(checkpoint)
        adjustments = _adjustments_from_snapshot(checkpoint, alignment, progress, impact)

        review_result = ReviewResult(
            alignment=alignment,
            progress_status=progress,
            unexpected_impact=impact,
            adjustments=adjustments,
            confidence=_compute_confidence(alignment, progress, impact),
        )

        logger.info(
            "审查完成: %s → alignment=%s, progress=%s, impact=%s",
            checkpoint_id,
            alignment,
            progress,
            impact,
        )

        return ReviewResponse(
            checkpoint_id=checkpoint_id,
            review_result=review_result,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("review_checkpoint 错误: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/checkpoint/chain/{plan_id}",
    response_model=ChainResponse,
    responses={422: {"model": ErrorResponse}},
    summary="获取 Plan 的完整 Checkpoint 链",
    description="返回按 checkpoint_number 升序排列的 Checkpoint 列表",
)
async def get_checkpoint_chain(plan_id: str):
    """GET /checkpoint/chain/{plan_id} — 获取 Checkpoint 链

    返回指定 Plan 的所有 Checkpoint，按编号升序排列。
    """
    try:
        checkpoints = storage.get_checkpoint_chain(plan_id)
        return ChainResponse(
            plan_id=plan_id,
            checkpoints=checkpoints,
            total=len(checkpoints),
        )
    except Exception as e:
        logger.error("get_checkpoint_chain 错误: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════════════
# 健康检查端点
# ════════════════════════════════════════════════════════════════


@app.get(
    "/health",
    summary="健康检查",
    description="返回服务状态和三组表的存储统计",
)
async def health_check():
    """GET /health — 健康检查

    返回三组表的统计信息：plans/steps/memories/checkpoints 的数量。
    """
    conn = storage._connection()
    try:
        plan_count = conn.execute("SELECT COUNT(*) as cnt FROM plans").fetchone()["cnt"]
        step_count = conn.execute("SELECT COUNT(*) as cnt FROM steps").fetchone()["cnt"]
        memory_count = conn.execute("SELECT COUNT(*) as cnt FROM memories").fetchone()["cnt"]
        checkpoint_count = conn.execute("SELECT COUNT(*) as cnt FROM checkpoints").fetchone()["cnt"]
        return {
            "status": "ok",
            "plans": plan_count,
            "steps": step_count,
            "memories": memory_count,
            "checkpoints": checkpoint_count,
            "db_path": storage.db_path,
        }
    finally:
        conn.close()


# ════════════════════════════════════════════════════════════════
# 入口
# ════════════════════════════════════════════════════════════════


def main():
    """启动 FastAPI 服务

    端口：8200（通过环境变量 HARNESS_PORT 可覆盖）
    主机：127.0.0.1（通过环境变量 HARNESS_HOST 可覆盖）
    """
    import uvicorn

    host = os.environ.get("HARNESS_HOST", "127.0.0.1")
    port = int(os.environ.get("HARNESS_PORT", "8200"))

    logger.info("启动 Harness MCP Server — %s:%d", host, port)
    logger.info("数据库路径: %s", storage.db_path)

    uvicorn.run(
        "harness_server.server:app",
        host=host,
        port=port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
