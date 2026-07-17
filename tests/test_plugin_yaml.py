"""plugin.yaml 格式验证 — 确保 YAML 语法正确、Hook 列表完整。"""

import os
import sys
from pathlib import Path

import yaml


def _load_plugin_yaml(name: str) -> dict:
    """从插件目录加载 plugin.yaml。"""
    path = Path(__file__).resolve().parent.parent / "plugins" / name / "plugin.yaml"
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestHarnessPluginYaml:
    """验证 deepseek-harness/plugin.yaml。"""

    def test_yaml_parses_correctly(self):
        """YAML 语法正确，能正常解析。"""
        data = _load_plugin_yaml("deepseek-harness")
        assert isinstance(data, dict)

    def test_has_required_fields(self):
        data = _load_plugin_yaml("deepseek-harness")
        assert "name" in data
        assert "version" in data
        assert "hooks" in data
        assert data["name"] == "deepseek-harness"

    def test_hooks_contain_all_required(self):
        """hooks 列表包含所有必要 hook 类型。"""
        data = _load_plugin_yaml("deepseek-harness")
        hooks = data["hooks"]
        # 应该有多个 pre_llm_call 和 post_tool_call
        assert "pre_llm_call" in hooks
        assert "post_tool_call" in hooks
        assert "on_session_end" in hooks
        assert "subagent_start" in hooks
        assert "subagent_stop" in hooks

    def test_hooks_pre_llm_call_count(self):
        """pre_llm_call 注册了至少 3 次（gate + intent_router + reasoning_effort + latest_reminder + immune_audit）。"""
        data = _load_plugin_yaml("deepseek-harness")
        count = sum(1 for h in data["hooks"] if h == "pre_llm_call")
        assert count >= 3

    def test_provides_tools_declared(self):
        """provides_tools 声明了 9 个工具。"""
        data = _load_plugin_yaml("deepseek-harness")
        tools = data.get("provides_tools", [])
        assert len(tools) == 9
        assert "plan_create" in tools
        assert "memory_tag" in tools
        assert "checkpoint_review" in tools

    def test_no_mcp_block(self):
        """不应再有 mcp 块（已改为 provides_tools + ctx.register_tool）。"""
        data = _load_plugin_yaml("deepseek-harness")
        assert "mcp" not in data, "plugin.yaml 不应再有 mcp 块"

    def test_version_format(self):
        data = _load_plugin_yaml("deepseek-harness")
        v = data["version"]
        parts = v.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)


class TestContextPluginYaml:
    """验证 deepseek-context/plugin.yaml。"""

    def test_yaml_parses(self):
        data = _load_plugin_yaml("deepseek-context")
        assert isinstance(data, dict)

    def test_has_required_fields(self):
        data = _load_plugin_yaml("deepseek-context")
        assert data["name"] == "deepseek-context"
        assert "type" in data
        assert data["type"] == "context_engine"
