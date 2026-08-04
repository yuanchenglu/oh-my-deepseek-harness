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