"""Plan Engine MCP Server — FastAPI HTTP Server

基于 I-06 OKR PlanStep 级联修正理论，提供 5 个 REST API 端点：
1. POST /plan/create     — 从任务描述创建 OKR PlanStep 列表
2. PUT  /plan/step/{step_id} — 更新步骤状态/内容 + 自动级联修正
3. POST /plan/cascade    — 级联修正引擎
4. GET  /plan/status/{plan_id} — 获取 Plan 状态和依赖图
5. GET  /health          — 健康检查

数据持久化：SQLite (~/.hermes/mcp/plan-engine.db)
"""

from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from engine import build_adjacency_list, cascade_correct, detect_cycle
from models import (
    AssociationStrength,
    CascadeRequest,
    CascadeResponse,
    CreatePlanRequest,
    CreatePlanResponse,
    ErrorResponse,
    OKRPlanStep,
    PlanStatus,
    PlanStatusResponse,
    UpdateStepRequest,
)
from storage import PlanStorage

# ── 日志 ────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("plan-engine")

# ── 存储层初始化 ─────────────────────────────────────────────

db_path = os.environ.get(
    "PLAN_ENGINE_DB_PATH",
    os.path.expanduser("~/.hermes/mcp/plan-engine.db"),
)
storage = PlanStorage(db_path=db_path)

# ── 工具函数 ────────────────────────────────────────────────


def _decompose_task(task_description: str) -> List[Dict]:
    """将任务描述分解为 3-8 个 PlanStep

    这是一个简单的基于规则的分割：
    - 如果包含换行符，按行分割
    - 如果包含序号列表，按序号分割
    - 否则按句子分割
    """
    lines = [l.strip() for l in task_description.strip().split("\n") if l.strip()]
    steps_raw = []

    # 尝试按序号分割
    import re
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
        # 按句号/分号分割
        sentences = re.split(r"[。；;]", task_description)
        steps_raw = [s.strip() for s in sentences if len(s.strip()) > 4]

    # 如果还是太少，按逗号/空格分割
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
    """将步骤字典列表转换为 OKRPlanStep 列表

    自动设置：
    - step_id（UUID）
    - dependency_ids（按顺序链接：step_2 依赖 step_1 等）
    - association_strength（按位置：相邻步骤 strong，隔一步 moderate，更远 weak）
    """
    steps: List[OKRPlanStep] = []
    for i, sd in enumerate(steps_data):
        step_id = str(uuid.uuid4())
        dep_ids = []
        # 按顺序链接：每个步骤依赖前一个步骤
        if i > 0:
            dep_ids.append(steps[i - 1].step_id)

        # 关联强度：相邻 strong，隔一步 moderate，更远 weak
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


# ── FastAPI 应用 ────────────────────────────────────────────

app = FastAPI(
    title="Plan Engine MCP Server",
    description="OKR PlanStep DAG + 级联修正引擎",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== API 端点 ==========


@app.post(
    "/plan/create",
    response_model=CreatePlanResponse,
    responses={422: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
    summary="从任务描述创建 OKR PlanStep 列表",
    description="输入任务描述 → 自动分解为 3-8 个步骤 → 返回 OKRPlanStep 列表",
)
async def create_plan(req: CreatePlanRequest):
    """POST /plan/create — 从任务描述创建 OKR PlanStep 列表"""
    try:
        if not req.task_description or not req.task_description.strip():
            raise HTTPException(status_code=422, detail="任务描述不能为空")

        # 分解任务
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
    """PUT /plan/step/{step_id} — 更新步骤状态/内容"""
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
                    storage=storage,
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
    """POST /plan/cascade — 级联修正引擎"""
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
            storage=storage,
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


@app.get(
    "/health",
    summary="健康检查",
    description="返回服务状态和存储统计",
)
async def health_check():
    """GET /health — 健康检查"""
    conn = storage._connection()
    try:
        plan_count = conn.execute("SELECT COUNT(*) as cnt FROM plans").fetchone()["cnt"]
        step_count = conn.execute("SELECT COUNT(*) as cnt FROM steps").fetchone()["cnt"]
        return {
            "status": "ok",
            "plans": plan_count,
            "steps": step_count,
            "db_path": storage.db_path,
        }
    finally:
        conn.close()


# ── 入口 ────────────────────────────────────────────────────


def main():
    """启动 FastAPI 服务"""
    import uvicorn

    host = os.environ.get("PLAN_ENGINE_HOST", "127.0.0.1")
    port = int(os.environ.get("PLAN_ENGINE_PORT", "8200"))

    logger.info("启动 Plan Engine MCP Server — %s:%d", host, port)
    logger.info("数据库路径: %s", storage.db_path)

    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
