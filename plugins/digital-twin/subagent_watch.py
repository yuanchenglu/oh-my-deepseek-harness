"""子任务监控模块 — 记录子任务的启动和结束状态，供数字分身感知外部任务进度。

kwargs 字段来源验证：
    - delegate_tool.py L1384-L1393 (subagent_start call site)
    - delegate_tool.py L2717-L2726 (subagent_stop call site)
    - hooks.py _DEFAULT_PAYLOADS (合成测试负载)
"""

from typing import Optional, Dict, Any


def on_subagent_start(**kwargs) -> Optional[Dict[str, Any]]:
    """子任务启动时记录标识和时间戳。

    通过 child_subagent_id 追踪子任务，不修改任何外部状态，
    单纯返回一个确认 dict 供 plugin 框架消费。

    kwargs 字段（来源于 delegate_tool.py invoke_hook("subagent_start", ...)）:
        parent_session_id (str):       父会话的 session_id
        parent_turn_id (str):          父会话的当前 turn_id
        parent_subagent_id (str):      父会话中的子任务 ID（父方视角）
        child_session_id (str):        子任务的 session_id
        child_subagent_id (str):       子任务的 subagent_id（用作 task_id）
        child_role (str):              子任务的角色描述（如 "explore"）
        child_goal (str):              子任务的目标描述

    Returns:
        dict: {"task_id": child_subagent_id, "status": "recorded"}
        如果找不到有效的 task_id 则返回 None。
    """
    # 以 child_subagent_id 作为唯一标识 —— 与 delegate_tool.py 的调用约定一致
    task_id = kwargs.get("child_subagent_id")
    if not task_id:
        # 无有效的子任务 ID，跳过记录但不阻断调用链
        return None

    # 当前仅做记录确认；后续可在此处添加持久化存储
    return {"task_id": task_id, "status": "recorded"}


def on_subagent_stop(**kwargs) -> Optional[Dict[str, Any]]:
    """子任务结束时检查结果质量。

    根据 child_status 字段判断是否异常，返回质量标记。
    不维护 start/stop 配对状态，仅检查当前调用的参数。

    kwargs 字段（来源于 delegate_tool.py invoke_hook("subagent_stop", ...)）:
        parent_session_id (str):       父会话的 session_id
        parent_turn_id (str):          父会话的当前 turn_id
        child_session_id (str):        子任务的 session_id
        child_role (str | None):       子任务的角色
        child_summary (str | None):    子任务的结果摘要
        child_status (str | None):     子任务的结束状态（如 "completed" / "error"）
        duration_ms (int):             子任务执行耗时（毫秒）

    Returns:
        dict: 包含 task_id、quality 标记和备注的 dict；
        如果找不到有效标识字段则返回 None。

        quality = "ok"      → 子任务正常结束（child_status == "completed"）
        quality = "warning" → 子任务状态异常或为空
    """
    # 优先用 child_session_id，降级到 child_role 作为标识
    task_id = kwargs.get("child_session_id") or kwargs.get("child_role")
    if not task_id:
        return None

    # 判断子任务是否出现异常
    status = kwargs.get("child_status")
    if status and status == "completed":
        return {
            "task_id": task_id,
            "quality": "ok",
            "note": "子任务已完成",
        }

    # 状态为空或非正常完成 → 标记 warning
    return {
        "task_id": task_id,
        "quality": "warning",
        "note": f"子任务结果异常（status={status!r}）",
    }
