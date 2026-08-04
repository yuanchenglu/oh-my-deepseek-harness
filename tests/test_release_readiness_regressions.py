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

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]


def test_hard_constraints_are_isolated_between_sessions() -> None:
    """XF-POLICY-001 -> SES-001: 硬约束必须按 session_id 隔离，不再使用模块级全局集合。"""
    from deepseek_harness import gate
    from deepseek_harness.session_policy import SessionPolicyStore

    SessionPolicyStore.reset_instance()
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

    # session-b 从未设置约束 -> 应为空
    assert SessionPolicyStore.get_instance().get_active_constraints("session-b") == set()
    # session-a 的约束应存在
    assert "不能删除数据库" in SessionPolicyStore.get_instance().get_active_constraints("session-a") or \
        any("删除数据库" in c for c in SessionPolicyStore.get_instance().get_active_constraints("session-a"))
    SessionPolicyStore.reset_instance()


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


def test_memory_filter_tool_uses_api_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    """XF-CONTRACT-001 -> CON-001: memory_filter must send 'lambda' alias, not 'lambda_value'."""
    from deepseek_harness import tools

    captured: dict = {}

    def fake_call(method: str, path: str, **kwargs):
        captured.update({"method": method, "path": path, **kwargs})
        return {"entries": [], "total": 0, "lambda_value": 0.5, "included_layers": []}

    monkeypatch.setattr(tools, "_call_server", fake_call)
    tools._tool_memory_filter(lambda_value=0.5)

    assert captured["json"] == {"lambda": 0.5}


def test_checkpoint_tool_schema_matches_api_required_fields() -> None:
    """XF-CONTRACT-002 -> CON-001: checkpoint_create schema must declare plan_id, plan_steps, completed_step_ids."""
    from deepseek_harness.tools import _TOOL_SCHEMAS

    required = set(_TOOL_SCHEMAS["checkpoint_create"].get("required", []))
    assert {"plan_id", "plan_steps", "completed_step_ids"} <= required


def test_plan_status_schema_matches_service_enum() -> None:
    """XF-CONTRACT-003 -> CON-001: plan_update_step status enum must match PlanStatus values."""
    from deepseek_harness.tools import _TOOL_SCHEMAS
    from harness_server.models import PlanStatus

    status_schema = _TOOL_SCHEMAS["plan_update_step"]["properties"]["status"]
    assert set(status_schema.get("enum", [])) == {s.value for s in PlanStatus}


def test_install_path_deploys_packaged_harness_server_runtime() -> None:
    """XF-INSTALL-001 closed: one installed CLI path starts the packaged Supervisor."""
    install_text = (ROOT / "scripts" / "install.sh").read_text(encoding="utf-8")
    installer_text = (
        ROOT / "src" / "deepseek_harness" / "installer.py"
    ).read_text(encoding="utf-8")

    assert "deepseek_harness.cli install" in install_text
    assert "from harness_server.supervisor import Supervisor" in installer_text
    assert "supervisor.start(" in installer_text
    assert "pip install" not in installer_text


def test_runtime_dependencies_include_openai() -> None:
    """XF-DEPS-001 closed: Context-capable variants declare OpenAI explicitly."""
    with (ROOT / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle)["project"]

    base = "\n".join(project["dependencies"]).lower()
    extras = project["optional-dependencies"]
    assert "openai" not in base
    for extra in ("context", "all", "dev"):
        assert any(requirement.lower().startswith("openai") for requirement in extras[extra])


def _manifest_version_from_python(python_version: str) -> str:
    """Map PEP 440 prerelease syntax to the plugin manifest SemVer syntax."""
    beta_match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)b(\d+)", python_version)
    if beta_match:
        major, minor, patch, beta = beta_match.groups()
        return f"{major}.{minor}.{patch}-beta.{beta}"

    if re.fullmatch(r"\d+\.\d+\.\d+", python_version):
        return python_version

    raise AssertionError(f"unsupported release version syntax: {python_version}")


def test_project_versions_are_consistent() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    root_version_match = re.search(r'^version\s*=\s*["\']([^"\']+)', pyproject, re.MULTILINE)
    requires_python_match = re.search(
        r'^requires-python\s*=\s*["\']([^"\']+)', pyproject, re.MULTILINE
    )
    assert root_version_match is not None
    assert requires_python_match is not None

    root_version = root_version_match.group(1)
    expected_manifest_version = _manifest_version_from_python(root_version)

    harness = yaml.safe_load(
        (ROOT / "src" / "deepseek_harness" / "resources" / "plugin.yaml").read_text(encoding="utf-8")
    )
    context = yaml.safe_load(
        (ROOT / "src" / "deepseek_context" / "resources" / "plugin.yaml").read_text(encoding="utf-8")
    )

    assert root_version == "3.0.0b1"
    assert expected_manifest_version == "3.0.0-beta.1"
    assert str(harness["version"]) == expected_manifest_version
    assert str(context["version"]) == expected_manifest_version
    assert requires_python_match.group(1) == ">=3.10,<3.13"


def test_memory_import_storage_is_idempotent(tmp_path: Path) -> None:
    """XF-MEM-001 -> MEM-001: storage 层 content_hash+source 唯一索引使导入幂等。"""
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
    """安全基线：默认回环，非回环监听必须被拒绝。"""
    from harness_server.config import RuntimeConfig

    assert RuntimeConfig.from_env({}).host == "127.0.0.1"
    assert RuntimeConfig.from_env({"HARNESS_HOST": "localhost"}).host == "localhost"
    assert RuntimeConfig.from_env({"HARNESS_HOST": "127.0.0.1"}).host == "127.0.0.1"
    assert RuntimeConfig.from_env({"HARNESS_HOST": "::1"}).host == "::1"
    with pytest.raises(ValueError, match="loopback"):
        RuntimeConfig.from_env({"HARNESS_HOST": "0.0.0.0"})
    with pytest.raises(ValueError, match="loopback"):
        RuntimeConfig.from_env({"HARNESS_HOST": "192.168.1.10"})


def test_sqlite_updates_use_field_allowlist() -> None:
    """安全基线：动态 UPDATE 字段必须经过白名单过滤。"""
    storage_text = (ROOT / "src" / "harness_server" / "storage.py").read_text(encoding="utf-8")
    assert 'allowed = {"text", "key", "status", "parent_id", "dependency_ids", "association_strength"}' in storage_text
