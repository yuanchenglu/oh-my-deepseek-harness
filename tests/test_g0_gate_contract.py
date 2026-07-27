"""Executable offline contract for the G0 repository/execution baseline."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


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


def _assignment(module: ast.Module, name: str):
    for node in module.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Name) and target.id == name for target in targets):
                return _literal_value(node.value)
    raise AssertionError(f"missing literal assignment: {name}")


def test_g0_required_repository_artifacts_exist() -> None:
    required = [
        "SECURITY.md",
        ".github/ISSUE_TEMPLATE/config.yml",
        ".github/ISSUE_TEMPLATE/bug_report.yml",
        ".github/ISSUE_TEMPLATE/work_item.yml",
        ".github/pull_request_template.md",
        "docs/release/RELEASE_CHECKLIST.md",
        "docs/release/PUBLISHING.md",
        "docs/compatibility/HERMES_MATRIX.md",
        "docs/roadmap/OPEN_SOURCE_RELEASE_PLAN.md",
        "docs/roadmap/EXECUTION_STATUS.md",
        "docs/traceability/RELEASE_TRACEABILITY.md",
        "docs/testing/evidence/GATE-G0.md",
        "tests/fixtures/hermes/v0.19.0-contract.yaml",
        "tests/compatibility/probes/test_hermes_target_contract.py",
    ]
    missing = [path for path in required if not (ROOT / path).is_file()]
    assert missing == []


def test_g0_version_identity_is_fixed() -> None:
    pyproject = _read("pyproject.toml")
    version = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.MULTILINE)
    requires_python = re.search(
        r'^requires-python\s*=\s*"([^"]+)"', pyproject, re.MULTILINE
    )
    assert version and version.group(1) == "3.0.0b1"
    assert requires_python and requires_python.group(1) == ">=3.10,<3.13"

    for path in [
        "plugins/deepseek-harness/plugin.yaml",
        "plugins/deepseek-context/plugin.yaml",
    ]:
        manifest = yaml.safe_load(_read(path))
        assert str(manifest["version"]) == "3.0.0-beta.1"


def test_g0_tool_denominator_is_target_10_runtime_9() -> None:
    module = ast.parse(_read("plugins/deepseek-harness/tools.py"))
    target = tuple(_assignment(module, "TARGET_PUBLIC_TOOL_NAMES"))
    pending = frozenset(_assignment(module, "PENDING_PUBLIC_TOOL_NAMES"))

    assert len(target) == 10
    assert len(set(target)) == 10
    assert pending == {"memory_store"}
    assert len([name for name in target if name not in pending]) == 9


def test_g0_traceability_has_48_unique_work_ids_and_issue_urls() -> None:
    trace = _read("docs/traceability/RELEASE_TRACEABILITY.md")
    section = trace.split("## 1. Work ID → Issue → Delivery", 1)[1].split(
        "## 2. Requirement-domain ownership", 1
    )[0]

    work_ids = re.findall(r"\| (?:M0|M1|M2|M3|M4|M5|M6) \| `([A-Z0-9-]+)` \|", section)
    issue_numbers = re.findall(
        r"https://github\.com/yuanchenglu/oh-my-deepseek-harness/issues/(\d+)",
        section,
    )

    assert len(work_ids) == 48
    assert len(set(work_ids)) == 48
    assert len(issue_numbers) == 48
    assert len(set(issue_numbers)) == 48

    assert "**48 Work IDs · 48 unique GitHub Issues · 88 FR IDs · 17 CR IDs · 100 Test IDs**" in trace
    assert "**Total** | **88**" in trace
    assert "Total CR IDs" not in trace or "17" in trace
    assert "**Total** | **100**" in trace
    assert "0 orphan" in trace.lower()


def test_g0_publishing_decision_is_safe_and_explicit() -> None:
    publishing = _read("docs/release/PUBLISHING.md")
    evidence = _read("docs/testing/evidence/REL-005.md")

    assert "GitHub Release is mandatory" in publishing
    assert "PyPI is disabled" in publishing
    assert "not treated as proof" in publishing
    assert "Trusted Publisher" in publishing
    assert "GitHub Release" in evidence
    assert "PyPI" in evidence


def test_g0_hermes_candidate_and_known_gap_are_owned() -> None:
    contract = yaml.safe_load(_read("tests/fixtures/hermes/v0.19.0-contract.yaml"))
    assert contract["candidate"]["version"] == "0.19.0"
    assert contract["candidate"]["tag"] == "v2026.7.20"
    assert contract["candidate"]["requires_python"] == ">=3.11,<3.14"
    assert contract["support"]["package_core_python"] == ["3.10", "3.11", "3.12"]
    assert contract["support"]["full_hermes_python"] == ["3.11", "3.12"]
    assert contract["support"]["python_3_10_full_hermes"] == "unsupported"
    assert contract["known_compatibility_gaps"]["context_engine_missing_properties"] == [
        "name"
    ]
    assert contract["known_compatibility_gaps"]["owner_work_ids"] == [
        "PKG-001",
        "COMPAT-001",
    ]


def test_g0_security_and_issue_forms_are_private_data_safe() -> None:
    security = _read("SECURITY.md")
    config = yaml.safe_load(_read(".github/ISSUE_TEMPLATE/config.yml"))
    bug = yaml.safe_load(_read(".github/ISSUE_TEMPLATE/bug_report.yml"))
    work = yaml.safe_load(_read(".github/ISSUE_TEMPLATE/work_item.yml"))

    assert "security/advisories/new" in security
    assert config["blank_issues_enabled"] is False
    assert any("security/advisories/new" in link["url"] for link in config["contact_links"])
    for form in [bug, work]:
        assert all(key in form for key in ("name", "description", "title", "labels", "body"))
        assert form["body"]
        text = str(form).lower()
        assert "work id" in text
        assert "test" in text
        assert "rollback" in text
        assert "security" in text


def test_g0_status_does_not_claim_product_release_readiness() -> None:
    status = _read("docs/roadmap/EXECUTION_STATUS.md")
    gate = _read("docs/testing/evidence/GATE-G0.md")

    assert "Experimental Preview" in status
    assert "PKG-001" in status
    assert "does not" in status.lower()
    assert "Public Beta" in gate
    assert "does not mean" in gate
    assert "PKG-001" in gate
    assert "COMPAT-001" in gate
