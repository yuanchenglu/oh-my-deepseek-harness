"""工具注册模块 — 把 harness_server 的功能注册为 Hermes 工具。

通过 ctx.register_tool() 把合并服务的 9 个端点暴露为 LLM 可调用的工具，
让模型能主动使用规划引擎（I-06）、记忆标签（I-12）和快照审查（I-11）。

工具列表：
  plan_create        — 从任务描述创建 OKR PlanStep 列表（I-06）
  plan_update_step   — 更新步骤状态/内容 + 自动级联修正（I-06）
  plan_cascade       — 级联修正引擎（I-06）
  plan_status        — 获取 Plan 状态和依赖图（I-06）
  memory_tag         — 输入内容 → 返回层级标签（I-12）
  memory_query       — 按标签/层级查询记忆（I-12）
  memory_filter      — 按 λ 值过滤记忆（I-12）
  checkpoint_create  — 从 Plan 状态提取 Checkpoint 快照（I-11）
  checkpoint_review  — 对 Checkpoint 执行审查（I-11）

关联: docs/innovations/06-okr-planstep-cascade.md
      docs/innovations/11-checkpoint-review.md
      docs/innovations/12-memory-granularity.md
"""

import logging
import os
import subprocess
import time
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)

# 合并服务的地址（单端口 8200）
_SERVER_URL = os.environ.get("HARNESS_SERVER_URL", "http://127.0.0.1:8200")
# 服务脚本路径
_SERVER_SCRIPT = os.path.join(os.path.dirname(__file__), "..", "..", "mcp", "harness_server", "server.py")
_server_process = None  # 服务子进程引用，防止被 GC 回收


def _ensure_server_running() -> None:
    """确保合并服务正在运行。

    如果服务未启动，用 subprocess 拉起一个后台 uvicorn 进程。
    失败时只记录日志，不阻断插件加载（工具调用时会自然失败报错）。
    """
    global _server_process
    if _server_process is not None and _server_process.poll() is None:
        return  # 已经在运行

    try:
        _server_process = subprocess.Popen(
            [
                os.environ.get("PYTHON", "python3"),
                _server_script,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env={**os.environ, "HARNESS_SERVER_PORT": "8200"},
        )
        logger.info("[harness_server] 后台服务已启动, PID=%s", _server_process.pid)
        # 给服务一点启动时间
        time.sleep(1)
    except Exception as e:
        logger.warning("[harness_server] 启动失败: %s", e)


def _call_server(method: str, path: str, **kwargs) -> Dict[str, Any]:
    """调用合并服务的 HTTP 端点。

    Args:
        method: HTTP 方法（GET/POST/PUT）
        path: 路径（如 /plan/create）
        **kwargs: 传给 httpx 的额外参数（json、params 等）

    Returns:
        服务返回的 JSON dict。调用失败时返回 {"error": "..."}。
    """
    _ensure_server_running()
    url = f"{_SERVER_URL}{path}"
    try:
        with httpx.Client(timeout=30) as client:
            resp = client.request(method, url, **kwargs)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.error("[harness_server] 调用 %s %s 失败: %s", method, path, e)
        return {"error": str(e)}


# ============================================================
# 工具 handler 函数（每个对应一个端点）
# ============================================================

def _tool_plan_create(**kwargs) -> str:
    """I-06: 从任务描述创建 OKR PlanStep 列表。"""
    result = _call_server("POST", "/plan/create", json={"task_description": kwargs.get("task_description", "")})
    return _format_result(result)


def _tool_plan_update_step(**kwargs) -> str:
    """I-06: 更新步骤状态/内容，自动触发级联修正。"""
    step_id = kwargs.get("step_id", "")
    body = {k: v for k, v in kwargs.items() if k != "step_id" and v is not None}
    result = _call_server("PUT", f"/plan/step/{step_id}", json=body)
    return _format_result(result)


def _tool_plan_cascade(**kwargs) -> str:
    """I-06: 级联修正引擎，从指定步骤出发分析影响。"""
    result = _call_server("POST", "/plan/cascade", json={
        "plan_id": kwargs.get("plan_id", ""),
        "modified_step_id": kwargs.get("modified_step_id", ""),
    })
    return _format_result(result)


def _tool_plan_status(**kwargs) -> str:
    """I-06: 获取 Plan 状态和依赖图。"""
    plan_id = kwargs.get("plan_id", "")
    result = _call_server("GET", f"/plan/status/{plan_id}")
    return _format_result(result)


def _tool_memory_tag(**kwargs) -> str:
    """I-12: 对内容进行层级分类，输出标签和置信度。"""
    result = _call_server("POST", "/memory/tag", json={"content": kwargs.get("content", "")})
    return _format_result(result)


def _tool_memory_query(**kwargs) -> str:
    """I-12: 按标签/层级查询记忆。"""
    body = {k: v for k, v in kwargs.items() if v is not None}
    result = _call_server("POST", "/memory/query", json=body)
    return _format_result(result)


def _tool_memory_filter(**kwargs) -> str:
    """I-12: 按 λ 值过滤记忆（0.0=仅约束层, 0.5=约束+偏好+决策, 1.0=全部）。"""
    result = _call_server("POST", "/memory/filter", json={
        "lambda_value": kwargs.get("lambda_value", 0.5),
    })
    return _format_result(result)


def _tool_checkpoint_create(**kwargs) -> str:
    """I-11: 从 Plan 状态提取 Checkpoint 快照。"""
    body = {k: v for k, v in kwargs.items() if v is not None}
    result = _call_server("POST", "/checkpoint/create", json=body)
    return _format_result(result)


def _tool_checkpoint_review(**kwargs) -> str:
    """I-11: 对 Checkpoint 执行四维审查。"""
    checkpoint_id = kwargs.get("checkpoint_id", "")
    result = _call_server("POST", f"/checkpoint/review/{checkpoint_id}", json={})
    return _format_result(result)


def _format_result(result: Dict[str, Any]) -> str:
    """把服务返回的 JSON 格式化为字符串（工具返回值必须是字符串）。"""
    import json
    return json.dumps(result, ensure_ascii=False, indent=2)


# ============================================================
# 工具 schema 定义（JSON Schema）
# ============================================================

_TOOL_SCHEMAS = {
    "plan_create": {
        "type": "object",
        "properties": {
            "task_description": {"type": "string", "description": "任务描述文本"},
        },
        "required": ["task_description"],
    },
    "plan_update_step": {
        "type": "object",
        "properties": {
            "step_id": {"type": "string", "description": "步骤 ID"},
            "status": {"type": "string", "description": "新状态（pending/in_progress/completed/blocked）"},
            "text": {"type": "string", "description": "更新后的步骤内容"},
        },
        "required": ["step_id"],
    },
    "plan_cascade": {
        "type": "object",
        "properties": {
            "plan_id": {"type": "string", "description": "Plan ID"},
            "modified_step_id": {"type": "string", "description": "被修改的步骤 ID"},
        },
        "required": ["plan_id", "modified_step_id"],
    },
    "plan_status": {
        "type": "object",
        "properties": {
            "plan_id": {"type": "string", "description": "Plan ID"},
        },
        "required": ["plan_id"],
    },
    "memory_tag": {
        "type": "object",
        "properties": {
            "content": {"type": "string", "description": "要分类的记忆内容"},
        },
        "required": ["content"],
    },
    "memory_query": {
        "type": "object",
        "properties": {
            "tags": {"type": "array", "items": {"type": "string"}, "description": "标签列表"},
            "layer": {"type": "string", "description": "记忆层级"},
            "limit": {"type": "integer", "description": "返回条数上限"},
        },
    },
    "memory_filter": {
        "type": "object",
        "properties": {
            "lambda_value": {"type": "number", "description": "λ 值 [0,1]：0.0=仅约束层, 0.5=约束+偏好+决策, 1.0=全部"},
        },
        "required": ["lambda_value"],
    },
    "checkpoint_create": {
        "type": "object",
        "properties": {
            "plan_id": {"type": "string", "description": "Plan ID"},
            "plan_steps": {"type": "array", "description": "Plan 步骤列表"},
            "completed_step_ids": {"type": "array", "items": {"type": "string"}, "description": "已完成的步骤 ID"},
            "unexpected_findings": {"type": "array", "items": {"type": "string"}, "description": "意外发现"},
        },
        "required": ["plan_id"],
    },
    "checkpoint_review": {
        "type": "object",
        "properties": {
            "checkpoint_id": {"type": "string", "description": "Checkpoint ID"},
        },
        "required": ["checkpoint_id"],
    },
}

_TOOL_HANDLERS = {
    "plan_create": _tool_plan_create,
    "plan_update_step": _tool_plan_update_step,
    "plan_cascade": _tool_plan_cascade,
    "plan_status": _tool_plan_status,
    "memory_tag": _tool_memory_tag,
    "memory_query": _tool_memory_query,
    "memory_filter": _tool_memory_filter,
    "checkpoint_create": _tool_checkpoint_create,
    "checkpoint_review": _tool_checkpoint_review,
}

_TOOL_DESCRIPTIONS = {
    "plan_create": "从任务描述创建 OKR PlanStep 列表（I-06 级联规划）",
    "plan_update_step": "更新步骤状态/内容，自动触发级联修正（I-06）",
    "plan_cascade": "级联修正引擎：从指定步骤出发分析影响传播（I-06）",
    "plan_status": "获取 Plan 状态和依赖图（I-06）",
    "memory_tag": "对内容进行层级分类，输出标签和置信度（I-12）",
    "memory_query": "按标签/层级查询记忆（I-12）",
    "memory_filter": "按 λ 值过滤记忆（I-12: 0.0=约束层, 0.5=+偏好+决策, 1.0=全部）",
    "checkpoint_create": "从 Plan 状态提取 Checkpoint 快照（I-11）",
    "checkpoint_review": "对 Checkpoint 执行四维审查：对齐/进度/影响/调整（I-11）",
}


def register_all_tools(ctx) -> None:
    """注册全部 9 个工具到 Hermes。

    在插件的 register(ctx) 函数中调用此函数即可。

    Args:
        ctx: Hermes PluginContext 对象。
    """
    for name, handler in _TOOL_HANDLERS.items():
        try:
            ctx.register_tool(
                name=name,
                toolset="deepseek-harness",
                schema=_TOOL_SCHEMAS[name],
                handler=handler,
                description=_TOOL_DESCRIPTIONS[name],
            )
            logger.debug("[tools] 注册工具: %s", name)
        except Exception as e:
            logger.warning("[tools] 注册 %s 失败: %s", name, e)
