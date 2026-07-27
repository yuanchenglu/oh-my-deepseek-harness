"""开源发布就绪度回归测试。

本文件把 Code Review 发现的跨模块契约、安装、状态隔离和数据幂等性问题
转化为可执行规格。当前已知缺陷使用 strict xfail 管理。
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.xfail(
    strict=True,
    reason="已知缺陷：硬约束保存在模块级全局集合，未按 session_id 隔离",
)
def test_hard_constraints_are_isolated_between_sessions() -> None:
    from deepseek_harness import gate

    gate._current_hard_constraints.clear()
    gate.on_pre_llm_call(
        session_id="session-a",
        is_first_turn=True,
        user_message="绝对不能删除数据库",
    )
    gate.on_pre_llm_call(
        session_id="session-b",
        is_first_turn=True,
        user_message="请查看项目状态",
    )

    assert not gate._current_hard_constraints


@pytest.mark.xfail(
    strict=True,
    reason="已知缺陷：assessor 写入的 Markdown 格式无法被 immune_audit 解析",
)
def test_immune_audit_parses_assessor_output_format() -> None:
    from deepseek_harness.immune_audit import _parse_violations

    content = """
## 2026-07-27 10:00
- **约束**: 不能删除数据库
- **工具**: bash
- **证据**: bash 执行了: rm production.db
- **会话**: session-a
"""

    rows = _parse_violations(content)
    assert len(rows) == 1
    assert rows[0]["constraint"] == "不能删除数据库"


@pytest.mark.xfail(
    strict=True,
    reason="已知缺陷：memory_filter 工具发送 lambda_value，而 API 只接收 lambda 别名",
)
def test_memory_filter_tool_uses_api_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    from deepseek_harness import tools

    captured: dict = {}

    def fake_call(method: str, path: str, **kwargs):
        captured.update({"method": method, "path": path, **kwargs})
        return {"entries": [], "total": 0, "lambda_value": 0.5, "included_layers": []}

    monkeypatch.setattr(tools, "_call_server", fake_call)
    tools._tool_memory_filter(lambda_value=0.5)

    assert captured["json"] == {"lambda": 0.5}


@pytest.mark.xfail(
    strict=True,
    reason="已知缺陷：checkpoint_create 工具 schema 未声明 API 的两个必填字段",
)
def test_checkpoint_tool_schema_matches_api_required_fields() -> None:
    from deepseek_harness.tools import _TOOL_SCHEMAS

    required = set(_TOOL_SCHEMAS["checkpoint_create"].get("required", []))
    assert {"plan_id", "plan_steps", "completed_step_ids"} <= required


@pytest.mark.xfail(
    strict=True,
    reason="已知缺陷：plan_update_step schema 描述 blocked，但服务枚举不支持该状态",
)
def test_plan_status_schema_matches_service_enum() -> None:
    from deepseek_harness.tools import _TOOL_SCHEMAS
    from harness_server.models import PlanStatus

    status_schema = _TOOL_SCHEMAS["plan_update_step"]["properties"]["status"]
    assert set(status_schema.get("enum", [])) == {s.value for s in PlanStatus}


@pytest.mark.xfail(
    strict=True,
    reason="已知缺陷：安装脚本未安装或复制 mcp/harness_server",
)
def test_install_script_installs_harness_server_runtime() -> None:
    install_text = (ROOT / "scripts" / "install.sh").read_text(encoding="utf-8")
    assert "mcp/harness_server" in install_text or "harness_server" in install_text


@pytest.mark.xfail(
    strict=True,
    reason="已知缺陷：Context Engine 运行依赖 openai，但正式依赖未声明",
)
def test_runtime_dependencies_include_openai() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert re.search(r'["\']openai(?:[<>=!~].*)?["\']', pyproject)


@pytest.mark.xfail(
    strict=True,
    reason="已知缺陷：根包、Harness 插件、Context 插件版本号不一致",
)
def test_project_versions_are_consistent() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    root_version = re.search(r'^version\s*=\s*["\']([^"\']+)', pyproject, re.MULTILINE).group(1)

    harness = yaml.safe_load(
        (ROOT / "plugins" / "deepseek-harness" / "plugin.yaml").read_text(encoding="utf-8")
    )
    context = yaml.safe_load(
        (ROOT / "plugins" / "deepseek-context" / "plugin.yaml").read_text(encoding="utf-8")
    )

    assert root_version == str(harness["version"]) == str(context["version"])


@pytest.mark.xfail(
    strict=True,
    reason="已知缺陷：启动导入没有内容唯一键，同一记忆会重复写入",
)
def test_memory_import_storage_is_idempotent(tmp_path: Path) -> None:
    from harness_server.models import MemoryEntry, MemoryLayer
    from harness_server.storage import HarnessStorage

    store = HarnessStorage(str(tmp_path / "harness.db"))
    entry = MemoryEntry(
        content="用户明确要求所有技术文档使用中文",
        tags=["中文", "文档"],
        layer=MemoryLayer.PREFERENCE,
        created_at=datetime.now(timezone.utc),
    )

    store.insert_memory(entry, source="MEMORY.md")
    store.insert_memory(entry, source="MEMORY.md")

    rows = store.query_memories(tags=["中文"])
    assert len(rows) == 1


def test_harness_server_defaults_to_loopback() -> None:
    """安全基线：默认监听地址必须是本机回环地址。"""
    server_text = (ROOT / "mcp" / "harness_server" / "server.py").read_text(encoding="utf-8")
    assert 'os.environ.get("HARNESS_HOST", "127.0.0.1")' in server_text


def test_sqlite_updates_use_field_allowlist() -> None:
    """安全基线：动态 UPDATE 字段必须经过白名单过滤。"""
    storage_text = (ROOT / "mcp" / "harness_server" / "storage.py").read_text(encoding="utf-8")
    assert 'allowed = {"text", "key", "status", "parent_id", "dependency_ids", "association_strength"}' in storage_text
