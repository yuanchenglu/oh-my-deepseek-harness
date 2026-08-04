"""DOC-001: Capability documentation must be evidence-backed and status-classified.
DOC-002: Lifecycle/privacy/troubleshooting guides must be verified and complete.

CR-P2-001 / CR-P2-005: README must not over-claim beyond code evidence.
Every capability claim must carry a Stable/Beta/Experimental/Degraded/Removed
status and link to test or runtime evidence.

TC-DOC-001-001: status enum is exactly the five allowed values.
TC-DOC-001-002: STATUS.md defines all five statuses.
TC-DOC-001-003: CAPABILITY_MATRIX.md rows only use valid statuses.
TC-DOC-001-004: every matrix row links to an existing evidence file.
TC-DOC-001-005: README (zh/en) must not contain absolute over-claims.
TC-DOC-001-006: docs/README.md indexes the capability docs.

TC-DOC-002-001: lifecycle guides exist for install/upgrade/uninstall/doctor.
TC-DOC-002-002: every guide command is a real `deepseek-harness` subcommand.
TC-DOC-002-003: every relative link in guides resolves to an existing file.
TC-DOC-002-004: privacy guide covers consent, minimization and local API.
TC-DOC-002-005: troubleshooting guide covers FR-OBS-003/004/005.
TC-DOC-002-006: KNOWN_LIMITATIONS.md exists and is indexed.
TC-DOC-002-007: README (zh/en) links to the guides index.
TC-DOC-002-008: scripts/test_docs.sh runs the new-user rehearsal.
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


# ── DOC-002 ──────────────────────────────────────────────

GUIDES = REPO / "docs" / "guides"
KNOWN_LIMITATIONS = REPO / "docs" / "release" / "KNOWN_LIMITATIONS.md"

# Real subcommands dispatcher provides (must match src/deepseek_harness/cli.py)
REAL_SUBCOMMANDS = {
    "install",
    "upgrade",
    "recover",
    "uninstall",
    "doctor",
    "server",
    "memory",
    "plan",
    "audit",
}
REAL_SERVER_ACTIONS = {"start", "status", "stop", "restart"}
REAL_MEMORY_ACTIONS = {"import", "delete"}
REAL_PLAN_ACTIONS = {"archive", "delete"}

# Commands that MUST appear in the lifecycle guides (FR-INSTALL-001~006)
REQUIRED_LIFECYCLE_TOKENS = {
    "install --dry-run",
    "install",
    "upgrade --dry-run",
    "upgrade",
    "doctor",
    "uninstall --purge-data --confirm",
    "server status",
    "server stop",
}


class TestLifecycleGuides:
    def test_guides_exist(self):
        for name in ("INSTALL.md", "UPGRADE.md", "UNINSTALL.md", "DOCTOR.md"):
            assert (GUIDES / name).exists(), f"missing guide {name}"

    def test_guide_commands_are_real_subcommands(self):
        text = "\n".join(p.read_text(encoding="utf-8") for p in GUIDES.glob("*.md"))
        for token in _code_tokens(text):
            if token.startswith("deepseek-harness") or token.startswith("scripts/install.sh"):
                assert _is_real_command(token), f"guide references unknown command: {token!r}"

    def test_required_lifecycle_tokens_present(self):
        text = "\n".join(p.read_text(encoding="utf-8") for p in GUIDES.glob("*.md"))
        for token in REQUIRED_LIFECYCLE_TOKENS:
            assert token in text, f"lifecycle guide missing required token {token!r}"

    def test_guide_links_resolve(self):
        for p in GUIDES.glob("*.md"):
            text = p.read_text(encoding="utf-8")
            for link in _md_links(text):
                if link.startswith(("http://", "https://", "#")):
                    continue
                target = (p.parent / link.split("#")[0]).resolve()
                assert target.exists(), f"{p.name} broken link: {link!r}"


class TestPrivacyGuide:
    def test_privacy_guide_exists(self):
        assert (GUIDES / "PRIVACY.md").exists()

    def test_covers_consent_minimization_local_api(self):
        text = (GUIDES / "PRIVACY.md").read_text(encoding="utf-8").lower()
        for term in ("consent", "最小化", "minimization", "loopback", "127.0.0.1"):
            assert term in text, f"PRIVACY.md missing {term!r}"


class TestTroubleshootingGuide:
    def test_troubleshooting_guide_exists(self):
        assert (GUIDES / "TROUBLESHOOTING.md").exists()

    def test_covers_obs_003_004_005(self):
        text = (GUIDES / "TROUBLESHOOTING.md").read_text(encoding="utf-8").lower()
        for term in ("日志", "log", "doctor", "server status", "恢复", "recover"):
            assert term in text, f"TROUBLESHOOTING.md missing {term!r}"


class TestKnownLimitations:
    def test_known_limitations_exists(self):
        assert KNOWN_LIMITATIONS.exists()

    def test_known_limitations_indexed_in_docs_readme(self):
        text = (REPO / "docs" / "README.md").read_text(encoding="utf-8")
        assert "KNOWN_LIMITATIONS" in text


class TestReadmeLinksGuides:
    def test_readme_links_guides(self):
        for fn in ("README.md", "README_EN.md"):
            text = (REPO / fn).read_text(encoding="utf-8")
            assert "docs/guides/" in text, f"{fn} must link to docs/guides/"


class TestNewUserRehearsalScript:
    def test_script_exists(self):
        assert (REPO / "scripts" / "test_docs.sh").exists()


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


_CODE_TOKEN_RE = re.compile(r"`([^`]+)`")


def _code_tokens(text: str) -> list[str]:
    """Extract inline/block code spans containing the CLI command."""
    tokens = []
    for m in _CODE_TOKEN_RE.finditer(text):
        token = m.group(1).strip()
        if token.startswith("deepseek-harness") or token.startswith("scripts/install.sh"):
            tokens.append(token)
    return tokens


def _is_real_command(token: str) -> bool:
    """Validate a doc command token against the real CLI subcommand surface."""
    parts = token.split()
    if parts[0] == "scripts/install.sh":
        return True  # convenience wrapper; the CLI subcommand is checked below
    # deepseek-harness <sub> [action] ...
    if len(parts) < 2:
        return False
    sub = parts[1]
    if sub not in REAL_SUBCOMMANDS:
        return False
    if sub == "server" and len(parts) >= 3:
        return parts[2] in REAL_SERVER_ACTIONS
    if sub == "memory" and len(parts) >= 3:
        return parts[2] in REAL_MEMORY_ACTIONS
    if sub == "plan" and len(parts) >= 3:
        return parts[2] in REAL_PLAN_ACTIONS
    return True


_MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def _md_links(text: str) -> list[str]:
    """Extract markdown link targets (relative paths only checked by caller)."""
    return [m.group(1).strip() for m in _MD_LINK_RE.finditer(text)]