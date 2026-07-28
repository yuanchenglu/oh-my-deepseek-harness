"""数字分身 Plugin — 使用 Hermes Plugin Hook 系统，不改一行核心代码。"""

from .gate import on_pre_llm_call as on_cognitive_gate
from .assessor import on_post_tool_call
from .learner import on_session_end
from .subagent_watch import on_subagent_start, on_subagent_stop
from .intent_router import on_pre_llm_call as on_intent_router
from .reasoning_effort import on_pre_llm_call as on_reasoning_effort
from .latest_reminder import on_pre_llm_call as on_latest_reminder
from .tools import register_all_tools


def register(ctx):
    """注册所有 Plugin Hook handler + 工具。"""
    # Hook 注册
    ctx.register_hook("pre_llm_call", on_cognitive_gate)
    ctx.register_hook("pre_llm_call", on_intent_router)
    ctx.register_hook("pre_llm_call", on_reasoning_effort)
    ctx.register_hook("pre_llm_call", on_latest_reminder)
    ctx.register_hook("post_tool_call", on_post_tool_call)
    ctx.register_hook("on_session_end", on_session_end)
    ctx.register_hook("subagent_start", on_subagent_start)
    ctx.register_hook("subagent_stop", on_subagent_stop)

    # 工具注册（I-06 规划引擎 + I-12 记忆标签 + I-11 快照审查）
    register_all_tools(ctx)
