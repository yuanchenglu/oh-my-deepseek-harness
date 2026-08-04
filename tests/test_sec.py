"""SEC-001: SBOM generation, dependency audit, release checklist.

FR-SEC-005: dependency vuln scan; unwaived High/Critical blocks release.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECURITY = ROOT / "scripts" / "security"


def test_sbom_script_exists_and_generates() -> None:
    """sbom.sh 存在且能生成合法 JSON SBOM。"""
    assert (SECURITY / "sbom.sh").exists()
    out = ROOT / "dist" / "sbom-test.json"
    subprocess.run(
        [sys.executable, "-c", "pass"], check=True, capture_output=True
    )  # sys.executable sanity
    r = subprocess.run(
        ["bash", str(SECURITY / "sbom.sh"), str(out)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "SBOM written" in r.stdout
    sbom = json.loads(out.read_text(encoding="utf-8"))
    assert sbom["bomFormat"] == "CycloneDX"
    assert len(sbom["dependencies"]) >= 2  # base deps PyYAML + httpx
    out.unlink(missing_ok=True)


def test_audit_script_exists() -> None:
    """audit_deps.sh 存在（FR-SEC-005 依赖审计）。"""
    assert (SECURITY / "audit_deps.sh").exists()


def test_release_checklist_exists_and_covers_security_gate() -> None:
    """RELEASE_CHECKLIST.md 存在且覆盖依赖/SBOM/权限最小化。"""
    text = (ROOT / "docs" / "release" / "RELEASE_CHECKLIST.md").read_text(
        encoding="utf-8"
    )
    assert "sbom.sh" in text
    assert "audit_deps.sh" in text
    assert "OIDC" in text or "Trusted Publisher" in text
    assert "High/Critical" in text


def test_security_md_references_release_checklist() -> None:
    """SECURITY.md 引用 RELEASE_CHECKLIST.md。"""
    text = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
    assert "RELEASE_CHECKLIST.md" in text