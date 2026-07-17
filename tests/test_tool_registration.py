"""工具注册测试 — 验证 9 个工具能正确注册到 Hermes。

不依赖真实 Hermes 运行环境，用 mock ctx 验证注册逻辑。
"""

import sys
from pathlib import Path

# 把项目根目录加到 path，让 import 能找到 deepseek_harness
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "plugins"))


class MockCtx:
    """模拟 Hermes PluginContext，记录 register_tool 调用。"""

    def __init__(self):
        self.hooks = []
        self.tools = []

    def register_hook(self, name, handler):
        self.hooks.append((name, handler))

    def register_tool(self, name, toolset, schema, handler, **kwargs):
        self.tools.append({
            "name": name,
            "toolset": toolset,
            "schema": schema,
            "handler": handler,
            "description": kwargs.get("description", ""),
        })


class TestToolRegistration:
    """验证工具注册逻辑。"""

    def test_register_all_tools_registers_9(self):
        """register_all_tools 应注册恰好 9 个工具。"""
        from deepseek_harness.tools import register_all_tools
        ctx = MockCtx()
        register_all_tools(ctx)
        assert len(ctx.tools) == 9

    def test_tool_names_complete(self):
        """9 个工具名应完整。"""
        from deepseek_harness.tools import register_all_tools
        ctx = MockCtx()
        register_all_tools(ctx)
        names = {t["name"] for t in ctx.tools}
        expected = {
            "plan_create", "plan_update_step", "plan_cascade", "plan_status",
            "memory_tag", "memory_query", "memory_filter",
            "checkpoint_create", "checkpoint_review",
        }
        assert names == expected

    def test_all_tools_have_schema(self):
        """每个工具都应有非空 schema。"""
        from deepseek_harness.tools import register_all_tools
        ctx = MockCtx()
        register_all_tools(ctx)
        for t in ctx.tools:
            assert isinstance(t["schema"], dict)
            assert "type" in t["schema"]
            assert "properties" in t["schema"]

    def test_all_tools_have_description(self):
        """每个工具都应有非空描述。"""
        from deepseek_harness.tools import register_all_tools
        ctx = MockCtx()
        register_all_tools(ctx)
        for t in ctx.tools:
            assert t["description"], f"工具 {t['name']} 缺少描述"

    def test_all_tools_have_handler(self):
        """每个工具都应有可调用的 handler。"""
        from deepseek_harness.tools import register_all_tools
        ctx = MockCtx()
        register_all_tools(ctx)
        for t in ctx.tools:
            assert callable(t["handler"]), f"工具 {t['name']} handler 不可调用"

    def test_toolset_is_deepseek_harness(self):
        """所有工具的 toolset 应为 deepseek-harness。"""
        from deepseek_harness.tools import register_all_tools
        ctx = MockCtx()
        register_all_tools(ctx)
        for t in ctx.tools:
            assert t["toolset"] == "deepseek-harness"

    def test_plan_create_handler_returns_string(self):
        """plan_create handler 返回值应为字符串（即使服务未启动也应是字符串错误信息）。"""
        from deepseek_harness.tools import _tool_plan_create
        result = _tool_plan_create(task_description="test task")
        assert isinstance(result, str)
