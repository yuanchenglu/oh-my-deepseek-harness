"""Register packaged Harness Server capabilities as Hermes tools.

The Beta target contains ten public Tool names. The current Runtime registers nine
working Tools; ``memory_store`` remains pending until CON-001 + MEM-001.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

import httpx

from harness_server.config import RuntimeConfig
from harness_server.supervisor import Supervisor

logger = logging.getLogger(__name__)

TARGET_PUBLIC_TOOL_NAMES: tuple[str, ...] = (
    "plan_create",
    "plan_update_step",
    "plan_cascade",
    "plan_status",
    "memory_tag",
    "memory_store",
    "memory_query",
    "memory_filter",
    "checkpoint_create",
    "checkpoint_review",
)
PENDING_PUBLIC_TOOL_NAMES: frozenset[str] = frozenset({"memory_store"})
RUNTIME_PUBLIC_TOOL_NAMES: tuple[str, ...] = tuple(
    name for name in TARGET_PUBLIC_TOOL_NAMES if name not in PENDING_PUBLIC_TOOL_NAMES
)


def _runtime_config() -> RuntimeConfig:
    return RuntimeConfig.from_env()


def _ensure_server_running() -> RuntimeConfig:
    """Start or reuse the single Supervisor-managed local Server."""
    runtime = _runtime_config()
    status = Supervisor().start(runtime)
    logger.info(
        "[harness_server] supervisor state=%s pid=%s endpoint=%s",
        status.state,
        status.pid,
        runtime.server_url,
    )
    return runtime


def _call_server(method: str, path: str, **kwargs) -> Dict[str, Any]:
    try:
        runtime = _ensure_server_running()
        with httpx.Client(timeout=30, trust_env=False) as client:
            response = client.request(
                method,
                f"{runtime.server_url}{path}",
                **kwargs,
            )
            response.raise_for_status()
            return response.json()
    except Exception as exc:
        logger.error("[harness_server] %s %s failed: %s", method, path, exc)
        return {"error": str(exc)}


def _format_result(result: Dict[str, Any]) -> str:
    return json.dumps(result, ensure_ascii=False, indent=2)


def _tool_plan_create(**kwargs) -> str:
    return _format_result(
        _call_server(
            "POST",
            "/plan/create",
            json={"task_description": kwargs.get("task_description", "")},
        )
    )


def _tool_plan_update_step(**kwargs) -> str:
    step_id = kwargs.get("step_id", "")
    body = {key: value for key, value in kwargs.items() if key != "step_id" and value is not None}
    return _format_result(_call_server("PUT", f"/plan/step/{step_id}", json=body))


def _tool_plan_cascade(**kwargs) -> str:
    return _format_result(
        _call_server(
            "POST",
            "/plan/cascade",
            json={
                "plan_id": kwargs.get("plan_id", ""),
                "modified_step_id": kwargs.get("modified_step_id", ""),
            },
        )
    )


def _tool_plan_status(**kwargs) -> str:
    return _format_result(_call_server("GET", f"/plan/status/{kwargs.get('plan_id', '')}"))


def _tool_memory_tag(**kwargs) -> str:
    return _format_result(
        _call_server("POST", "/memory/tag", json={"content": kwargs.get("content", "")})
    )


def _tool_memory_query(**kwargs) -> str:
    return _format_result(
        _call_server("POST", "/memory/query", json={key: value for key, value in kwargs.items() if value is not None})
    )


def _tool_memory_filter(**kwargs) -> str:
    return _format_result(
        _call_server(
            "POST",
            "/memory/filter",
            json={"lambda_value": kwargs.get("lambda_value", 0.5)},
        )
    )


def _tool_checkpoint_create(**kwargs) -> str:
    return _format_result(
        _call_server(
            "POST",
            "/checkpoint/create",
            json={key: value for key, value in kwargs.items() if value is not None},
        )
    )


def _tool_checkpoint_review(**kwargs) -> str:
    checkpoint_id = kwargs.get("checkpoint_id", "")
    return _format_result(
        _call_server("POST", f"/checkpoint/review/{checkpoint_id}", json={})
    )


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
        "properties": {"plan_id": {"type": "string", "description": "Plan ID"}},
        "required": ["plan_id"],
    },
    "memory_tag": {
        "type": "object",
        "properties": {"content": {"type": "string", "description": "要分类的记忆内容"}},
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
        "properties": {"checkpoint_id": {"type": "string", "description": "Checkpoint ID"}},
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


def _validate_runtime_registry() -> None:
    expected = set(RUNTIME_PUBLIC_TOOL_NAMES)
    registries = {
        "handlers": set(_TOOL_HANDLERS),
        "schemas": set(_TOOL_SCHEMAS),
        "descriptions": set(_TOOL_DESCRIPTIONS),
    }
    mismatches = {
        registry: sorted(values ^ expected)
        for registry, values in registries.items()
        if values != expected
    }
    if mismatches:
        raise RuntimeError(f"Tool registry contract mismatch: {mismatches}")


def register_all_tools(ctx) -> None:
    _validate_runtime_registry()
    for name in RUNTIME_PUBLIC_TOOL_NAMES:
        try:
            ctx.register_tool(
                name=name,
                toolset="deepseek-harness",
                schema=_TOOL_SCHEMAS[name],
                handler=_TOOL_HANDLERS[name],
                description=_TOOL_DESCRIPTIONS[name],
            )
            logger.debug("[tools] registered: %s", name)
        except Exception as exc:
            logger.warning("[tools] registration failed for %s: %s", name, exc)
