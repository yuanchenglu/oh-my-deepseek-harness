"""工具注册测试 — 冻结 10 Tool 目标契约并验证当前 9 Tool Runtime。

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


class TestToolContract:
    """验证 Beta 目标分母和当前 Runtime 迁移状态。"""

    def test_target_public_tool_names_are_exactly_10(self):
        """REL-004：排序后的目标名称必须精确等于固定 10 Tool 契约。"""
        from deepseek_harness.tools import TARGET_PUBLIC_TOOL_NAMES

        expected = sorted([
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
        ])
        assert len(TARGET_PUBLIC_TOOL_NAMES) == 10
        assert sorted(TARGET_PUBLIC_TOOL_NAMES) == expected
        assert len(set(TARGET_PUBLIC_TOOL_NAMES)) == 10

    def test_runtime_names_are_derived_target_minus_pending(self):
        from deepseek_harness.tools import (
            PENDING_PUBLIC_TOOL_NAMES,
            RUNTIME_PUBLIC_TOOL_NAMES,
            TARGET_PUBLIC_TOOL_NAMES,
        )

        assert PENDING_PUBLIC_TOOL_NAMES == {"memory_store"}
        assert tuple(
            name for name in TARGET_PUBLIC_TOOL_NAMES if name not in PENDING_PUBLIC_TOOL_NAMES
        ) == RUNTIME_PUBLIC_TOOL_NAMES
        assert len(RUNTIME_PUBLIC_TOOL_NAMES) == 9
        assert "memory_store" not in RUNTIME_PUBLIC_TOOL_NAMES

    def test_runtime_registries_match_derived_names(self):
        from deepseek_harness.tools import (
            RUNTIME_PUBLIC_TOOL_NAMES,
            _TOOL_DESCRIPTIONS,
            _TOOL_HANDLERS,
            _TOOL_SCHEMAS,
        )

        expected = set(RUNTIME_PUBLIC_TOOL_NAMES)
        assert set(_TOOL_HANDLERS) == expected
        assert set(_TOOL_SCHEMAS) == expected
        assert set(_TOOL_DESCRIPTIONS) == expected
        assert "memory_store" not in _TOOL_HANDLERS
        assert "memory_store" not in _TOOL_SCHEMAS
        assert "memory_store" not in _TOOL_DESCRIPTIONS


class TestToolRegistration:
    """验证当前 9 Tool 注册逻辑。"""

    def test_register_all_tools_registers_9(self):
        """register_all_tools 应注册恰好 9 个可工作 Tool。"""
        from deepseek_harness.tools import register_all_tools
        ctx = MockCtx()
        register_all_tools(ctx)
        assert len(ctx.tools) == 9

    def test_registered_names_equal_derived_runtime_contract(self):
        from deepseek_harness.tools import RUNTIME_PUBLIC_TOOL_NAMES, register_all_tools

        ctx = MockCtx()
        register_all_tools(ctx)
        assert tuple(t["name"] for t in ctx.tools) == RUNTIME_PUBLIC_TOOL_NAMES
        assert "memory_store" not in {t["name"] for t in ctx.tools}

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

    def test_plan_create_handler_returns_string_without_real_runtime(self, monkeypatch):
        """Handler 单测不得启动 Server、写真实 HOME 或访问真实 DB。"""
        from deepseek_harness import tools

        monkeypatch.setattr(
            tools,
            "_call_server",
            lambda *args, **kwargs: {"error": "isolated test runtime"},
        )
        result = tools._tool_plan_create(task_description="test task")
        assert isinstance(result, str)
        assert "isolated test runtime" in result

    def test_supervisor_start_failure_is_returned_as_tool_error(
        self, monkeypatch, tmp_path
    ):
        """Supervisor 状态错误不得逃逸 Tool handler 或访问真实用户数据。"""
        from deepseek_harness import tools
        from harness_server.config import RuntimeConfig
        from harness_server.runtime import RuntimeStateError

        class FailingSupervisor:
            def start(self, runtime):
                raise RuntimeStateError("isolated corrupt runtime state")

        runtime = RuntimeConfig(
            port=18202,
            db_path=str(tmp_path / "runtime.db"),
            memories_dir=str(tmp_path / "memories"),
        )
        monkeypatch.setattr(tools, "Supervisor", FailingSupervisor)
        monkeypatch.setattr(tools, "_runtime_config", lambda: runtime)

        result = tools._tool_plan_create(task_description="test task")
        assert isinstance(result, str)
        assert "isolated corrupt runtime state" in result
        assert not (tmp_path / "runtime.db").exists()
