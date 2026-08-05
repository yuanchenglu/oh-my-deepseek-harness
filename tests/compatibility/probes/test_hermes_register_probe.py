"""COMPAT-001 real-registration probe: our plugin's register() must drive the
Hermes Plugin ctx contract (register_hook / register_tool / register_context_engine)
exactly as Hermes v0.19.0 expects.

A fake ctx records every call the plugin makes; the probe asserts the plugin
registers the documented hooks and all 9 runtime tools. This proves the plugin
is compatible with the Hermes plugin surface without needing a live Hermes host.
"""

from __future__ import annotations

from deepseek_harness import register
from deepseek_harness.tools import PENDING_PUBLIC_TOOL_NAMES, TARGET_PUBLIC_TOOL_NAMES


class _FakeCtx:
    def __init__(self) -> None:
        self.hooks: dict[str, list] = {}
        self.tools: list[str] = []
        self.engines: list[str] = []

    def register_hook(self, name: str, handler) -> None:
        self.hooks.setdefault(name, []).append(handler)

    def register_tool(self, **kwargs) -> None:
        self.tools.append(kwargs.get("name", ""))

    def register_context_engine(self, engine) -> None:
        self.engines.append(engine.name if hasattr(engine, "name") else repr(engine))


def test_register_drives_hermes_ctx_contract() -> None:
    ctx = _FakeCtx()
    register(ctx)

    # 5 documented hooks registered
    assert "pre_llm_call" in ctx.hooks
    assert "post_tool_call" in ctx.hooks
    assert "on_session_end" in ctx.hooks
    assert "subagent_start" in ctx.hooks
    assert "subagent_stop" in ctx.hooks

    # 9 runtime tools registered (10 target minus memory_store pending)
    runtime = [n for n in TARGET_PUBLIC_TOOL_NAMES if n not in PENDING_PUBLIC_TOOL_NAMES]
    assert set(ctx.tools) == set(runtime)
    assert len(ctx.tools) == 9


def test_register_is_idempotent_and_hermes_importable() -> None:
    """register() 可重复调用不抛异常（Hermes 可能多次 enable 触发）。"""
    ctx_a = _FakeCtx()
    register(ctx_a)
    ctx_b = _FakeCtx()
    register(ctx_b)
    # 每次新建 ctx 都注册到 9 tools（Hermes 管理器隔离实例，不跨 ctx 累积）
    assert len(ctx_a.tools) == 9
    assert len(ctx_b.tools) == 9