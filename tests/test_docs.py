"""DOC-001: Capability documentation must be evidence-backed and status-classified.

CR-P2-001 / CR-P2-005: README must not over-claim beyond code evidence.
Every capability claim must carry a Stable/Beta/Experimental/Degraded/Removed
status and link to test or runtime evidence.

TC-DOC-001-001: status enum is exactly the five allowed values.
TC-DOC-001-002: STATUS.md defines all five statuses.
TC-DOC-001-003: CAPABILITY_MATRIX.md rows only use valid statuses.
TC-DOC-001-004: every matrix row links to an existing evidence file.
TC-DOC-001-005: README (zh/en) must not contain absolute over-claims.
TC-DOC-001-006: docs/README.md indexes the capability docs.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
CAPS = REPO / "docs" / "capabilities"
EVIDENCE = REPO / "docs" / "testing" / "evidence"

ALLOWED_STATUSES = {"Stable", "Beta", "Experimental", "Degraded", "Removed"}

# CR-P2-005 forbidden absolute claims (must not appear in README)
FORBIDDEN_README_TERMS = [
    "零配置",
    "安全无副作用",
    "对话多长都不卡",
    "自动学习 Skill",
    "不影响其他插件",
    "currently the only",
    "唯一",
    "zero-config",
    "safe with no side effects",
    "never conflicts",
]


class TestStatusEnum:
    def test_five_allowed_statuses(self):
        assert ALLOWED_STATUSES == {
            "Stable",
            "Beta",
            "Experimental",
            "Degraded",
            "Removed",
        }


class TestStatusDefinitions:
    def test_status_doc_exists(self):
        p = CAPS / "STATUS.md"
        assert p.exists(), f"missing {p}"

    def test_status_doc_defines_all_five(self):
        text = (CAPS / "STATUS.md").read_text(encoding="utf-8")
        for s in ALLOWED_STATUSES:
            assert s in text, f"STATUS.md must define status {s}"


class TestCapabilityMatrix:
    def test_matrix_exists(self):
        p = CAPS / "CAPABILITY_MATRIX.md"
        assert p.exists(), f"missing {p}"

    def test_matrix_rows_use_valid_statuses(self):
        text = (CAPS / "CAPABILITY_MATRIX.md").read_text(encoding="utf-8")
        rows = _matrix_rows(text)
        assert rows, "matrix has no capability rows"
        for row in rows:
            status = row["status"]
            assert status in ALLOWED_STATUSES, f"invalid status {status!r} in row: {row['name']}"

    def test_matrix_rows_link_to_existing_evidence(self):
        text = (CAPS / "CAPABILITY_MATRIX.md").read_text(encoding="utf-8")
        rows = _matrix_rows(text)
        for row in rows:
            ev = row["evidence"]
            assert ev, f"row {row['name']} missing evidence link"
            # evidence cell may contain multiple links separated by 、
            for link in re.split(r"[、,]", ev):
                link = link.strip().strip("`")
                assert link, f"row {row['name']} has empty evidence link"
                target = REPO / link
                assert target.exists(), f"row {row['name']} evidence link broken: {link}"


class TestReadmeNoOverclaim:
    @pytest.mark.parametrize("fn", ["README.md", "README_EN.md"])
    def test_no_absolute_claims(self, fn):
        text = (REPO / fn).read_text(encoding="utf-8")
        for term in FORBIDDEN_README_TERMS:
            assert term not in text, f"{fn} contains forbidden absolute claim: {term!r}"

    def test_readme_links_capability_matrix(self):
        text = (REPO / "README.md").read_text(encoding="utf-8")
        assert "docs/capabilities/CAPABILITY_MATRIX.md" in text
        en = (REPO / "README_EN.md").read_text(encoding="utf-8")
        assert "docs/capabilities/CAPABILITY_MATRIX.md" in en


class TestDocsIndex:
    def test_docs_readme_indexes_capabilities(self):
        text = (REPO / "docs" / "README.md").read_text(encoding="utf-8")
        assert "capabilities" in text


# ── helpers ──────────────────────────────────────────────

_STATUS_RE = re.compile(r"^\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|")


def _matrix_rows(text: str) -> list[dict]:
    """Parse markdown table rows: | name | status | evidence | note |"""
    rows = []
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        m = _STATUS_RE.match(line)
        if not m:
            continue
        name, status, evidence, note = (c.strip() for c in m.groups())
        name = name.strip("`")
        status = status.strip("`")
        evidence = evidence.strip("`")
        note = note.strip("`")
        if name in {"能力", "Capability", "Name", "ID"}:
            continue  # skip header
        if re.fullmatch(r"-{2,}", status) or re.fullmatch(r"-{2,}", name):
            continue  # skip separator rows (|------|------|)
        rows.append(
            {
                "name": name,
                "status": status,
                "evidence": evidence,
                "note": note,
            }
        )
    return rows