"""QA-001: test-fast / test-integration / test-release channels exist and are non-overlapping.

FR-QA-001/004-006/008-009: three non-overlapping commands; fast requires no
network/real HOME/API; integration uses controlled processes/artifacts; release
enforces final matrix and evidence.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
QUALITY = SCRIPTS / "quality"


def _files_in(script: str) -> set[str]:
    text = (SCRIPTS / script).read_text(encoding="utf-8")
    return set(re.findall(r"tests/\S+?\.py", text))


def test_all_three_scripts_exist() -> None:
    for name in ("test_fast.sh", "test_integration.sh", "test_release.sh"):
        assert (SCRIPTS / name).exists(), f"missing {name}"


def test_makefile_targets_exist() -> None:
    text = (ROOT / "Makefile").read_text(encoding="utf-8")
    for target in ("test-fast", "test-integration", "test-release"):
        assert f"{target}:" in text, f"missing Makefile target {target}"


def test_channels_are_non_overlapping() -> None:
    """FAST / INTEGRATION / RELEASE 文件集合两两不相交。"""
    fast = _files_in("test_fast.sh")
    integration = _files_in("test_integration.sh")
    release = _files_in("test_release.sh")
    assert fast & integration == set(), f"overlap fast/integration: {fast & integration}"
    assert fast & release == set(), f"overlap fast/release: {fast & release}"
    assert integration & release == set(), f"overlap integration/release: {integration & release}"


def test_fast_has_no_process_or_network_files() -> None:
    """fast 通道不含需要真实进程/安装的测试文件。"""
    fast = _files_in("test_fast.sh")
    assert not {"tests/test_server_process.py", "tests/test_installer_e2e.py"} & fast
    assert not {"tests/test_package_artifact.py", "tests/test_package_dependencies.py"} & fast


# ── QA-002 ──────────────────────────────────────────────────


def test_quality_script_exists() -> None:
    assert (QUALITY / "qa.sh").exists(), "missing scripts/quality/qa.sh"


def test_quality_script_runs_gates() -> None:
    """qa.sh 引用 ruff/coverage/shellcheck 三个稳定上下文。"""
    text = (QUALITY / "qa.sh").read_text(encoding="utf-8")
    assert "ruff check" in text and "ruff format" in text
    assert "--cov" in text
    assert "shellcheck" in text


def test_ci_has_quality_job() -> None:
    """ci.yml 注册 qa-quality 上下文。"""
    text = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "qa-quality" in text and "scripts/quality/qa.sh" in text


def test_pyproject_has_ruff_config() -> None:
    """pyproject.toml 有 [tool.ruff] 配置。"""
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "[tool.ruff]" in text and "line-length" in text