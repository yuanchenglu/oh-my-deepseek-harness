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


# ── REL-006 ──────────────────────────────────────────────────


def test_release_script_exists_and_reproducible() -> None:
    """build_rc.sh 存在且做可复现构建 + provenance。"""
    text = (ROOT / "scripts" / "release" / "build_rc.sh").read_text(encoding="utf-8")
    assert "-m build" in text
    assert "shasum -a 256" in text
    assert "provenance" in text
    assert "withdrawal" in text


def test_release_workflow_least_privilege_and_non_publishing() -> None:
    """release.yml 用最小权限，不发布。"""
    text = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert "contents: read" in text
    assert "build_rc.sh" in text
    assert "test_release.sh" in text
    assert "publish" not in text.lower() or "non-publishing" in text.lower()


# ── BETA-002 ──────────────────────────────────────────────────


def test_beta_metrics_schema_and_log_exist() -> None:
    """METRICS_SCHEMA.md + VALIDATION_LOG.csv + VALIDATION_REPORT.md 存在。"""
    beta = ROOT / "docs" / "beta"
    assert (beta / "METRICS_SCHEMA.md").exists()
    assert (beta / "VALIDATION_LOG.csv").exists()
    assert (beta / "VALIDATION_REPORT.md").exists()


def test_wilson_interval_computable() -> None:
    """METRICS_SCHEMA 的 Wilson 公式可复算（x=18, n=20 → ≥90% 阈值的区间）。"""
    import math

    x, n = 18, 20
    p_hat = x / n
    z = 1.96
    denom = 1 + z * z / n
    center = (p_hat + z * z / (2 * n)) / denom
    half = z * math.sqrt(p_hat * (1 - p_hat) / n + z * z / (4 * n * n)) / denom
    lower, upper = center - half, center + half
    # x=18/20 → 90% point estimate; 95% Wilson interval straddles 0.90
    assert lower < 0.90 < upper
    # Same numbers as schema formula
    text = (ROOT / "docs" / "beta" / "METRICS_SCHEMA.md").read_text(encoding="utf-8")
    assert "z = 1.96" in text


def test_validation_report_is_honest_zero_state() -> None:
    """VALIDATION_REPORT 诚实记录当前 0 收集，不虚报。"""
    text = (ROOT / "docs" / "beta" / "VALIDATION_REPORT.md").read_text(encoding="utf-8")
    assert "0/N" in text
    assert "no evidence yet" in text