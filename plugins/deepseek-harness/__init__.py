"""数字分身 Plugin — 使用 Hermes Plugin Hook 系统，不改一行核心代码。"""

from .gate import on_pre_llm_call
from .assessor import on_post_tool_call
from .learner import on_session_end
from .subagent_watch import on_subagent_start, on_subagent_stop


def register(ctx):
    """注册所有 Plugin Hook handler。"""
    ctx.register_hook("pre_llm_call", on_pre_llm_call)
    ctx.register_hook("post_tool_call", on_post_tool_call)
    ctx.register_hook("on_session_end", on_session_end)
    ctx.register_hook("subagent_start", on_subagent_start)
    ctx.register_hook("subagent_stop", on_subagent_stop)
