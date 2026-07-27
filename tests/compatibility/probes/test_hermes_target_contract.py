"""COMPAT-000 static probes for the selected Hermes v0.19.0 target.

These probes freeze source/document contracts only. Real installation and lifecycle E2E
remain the responsibility of COMPAT-001.
"""

from __future__ import annotations

import ast
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "tests" / "fixtures" / "hermes" / "v0.19.0-contract.yaml"
PLUGIN_MANIFEST = ROOT / "plugins" / "deepseek-harness" / "plugin.yaml"
TOOLS_SOURCE = ROOT / "plugins" / "deepseek-harness" / "tools.py"
CONTEXT_SOURCE = ROOT / "plugins" / "deepseek-context" / "__init__.py"


def _fixture() -> dict:
    return yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))


def _literal_value(node: ast.AST):
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "frozenset"
        and len(node.args) == 1
        and not node.keywords
    ):
        return frozenset(ast.literal_eval(node.args[0]))
    return ast.literal_eval(node)


def _literal_assignment(module: ast.Module, name: str):
    for node in module.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Name) and target.id == name for target in targets):
                return _literal_value(node.value)
    raise AssertionError(f"missing literal assignment: {name}")


def test_selected_candidate_identity_and_python_layers() -> None:
    data = _fixture()
    assert data["candidate"] == {
        "repository": "NousResearch/hermes-agent",
        "version": "0.19.0",
        "tag": "v2026.7.20",
        "license": "MIT",
        "requires_python": ">=3.11,<3.14",
    }
    assert data["support"]["package_core_python"] == ["3.10", "3.11", "3.12"]
    assert data["support"]["full_hermes_python"] == ["3.11", "3.12"]
    assert data["support"]["python_3_10_full_hermes"] == "unsupported"


def test_project_hooks_are_supported_by_selected_hermes() -> None:
    data = _fixture()
    official_hooks = set(data["official_hooks"])
    manifest = yaml.safe_load(PLUGIN_MANIFEST.read_text(encoding="utf-8"))
    project_hooks = set(manifest["hooks"])

    assert project_hooks
    assert project_hooks <= official_hooks
    assert {"pre_llm_call", "post_tool_call", "on_session_end"} <= project_hooks
    assert {"subagent_start", "subagent_stop"} <= project_hooks


def test_target_and_runtime_tool_name_contract_remains_10_and_9() -> None:
    module = ast.parse(TOOLS_SOURCE.read_text(encoding="utf-8"))
    target = tuple(_literal_assignment(module, "TARGET_PUBLIC_TOOL_NAMES"))
    pending = frozenset(_literal_assignment(module, "PENDING_PUBLIC_TOOL_NAMES"))

    assert len(target) == 10
    assert len(set(target)) == 10
    assert pending == {"memory_store"}
    assert len([name for name in target if name not in pending]) == 9


def test_context_engine_source_matches_methods_and_records_property_gap() -> None:
    fixture = _fixture()
    module = ast.parse(CONTEXT_SOURCE.read_text(encoding="utf-8"))
    engine = next(
        node
        for node in module.body
        if isinstance(node, ast.ClassDef) and node.name == "DeepSeekContextEngine"
    )

    methods = {
        node.name
        for node in engine.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    required_methods = set(fixture["context_engine_required"]["methods"])
    required_properties = set(fixture["context_engine_required"]["properties"])
    recorded_missing = set(
        fixture["known_compatibility_gaps"]["context_engine_missing_properties"]
    )

    assert required_methods <= methods
    assert recorded_missing == {"name"}
    assert required_properties - methods == recorded_missing
    assert fixture["known_compatibility_gaps"]["owner_work_ids"] == [
        "PKG-001",
        "COMPAT-001",
    ]

    init = next(
        node
        for node in engine.body
        if isinstance(node, ast.FunctionDef) and node.name == "__init__"
    )
    assigned_attributes = {
        node.attr
        for node in ast.walk(init)
        if isinstance(node, ast.Attribute)
        and isinstance(node.ctx, ast.Store)
        and isinstance(node.value, ast.Name)
        and node.value.id == "self"
    }
    assert set(fixture["context_engine_required"]["attributes"]) <= assigned_attributes


def test_normative_documents_distinguish_package_and_full_integration_support() -> None:
    documents = [
        ROOT / "docs" / "compatibility" / "HERMES_MATRIX.md",
        ROOT / "docs" / "roadmap" / "OPEN_SOURCE_RELEASE_PLAN.md",
        ROOT / "README.md",
        ROOT / "README_EN.md",
    ]

    for path in documents:
        text = path.read_text(encoding="utf-8")
        assert "3.10" in text, f"package/core Python 3.10 distinction missing: {path}"
        assert "3.11" in text and "3.12" in text, f"full Hermes Python matrix missing: {path}"
        assert "v0.19.0" in text or "v2026.7.20" in text, f"Hermes target missing: {path}"


def test_activation_contract_is_explicit() -> None:
    activation = _fixture()["activation"]
    assert activation["general_plugin_requires_enablement"] is True
    assert activation["context_engine_requires_explicit_selection"] is True
    assert activation["pip_entry_point_group"] == "hermes_agent.plugins"
