"""INS-002 Doctor tests for TC-INSTALL-004, 005 and 009."""

from __future__ import annotations

import json
import os
import socket
from pathlib import Path

import pytest

from deepseek_harness import cli
from deepseek_harness.doctor import (
    DOCTOR_MISSING_DEPENDENCY,
    DOCTOR_OK,
    DOCTOR_PORT_CONFLICT,
    DOCTOR_UNSUPPORTED,
    DoctorCheck,
    DoctorReport,
    diagnose,
    render_human,
)
from deepseek_harness.installer import build_install_plan, execute_install
from harness_server.supervisor import Supervisor


FAKE_SECRET = "fake-doctor-secret-that-must-not-appear"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _environment(tmp_path: Path, *, port: int | None = None) -> tuple[Path, dict[str, str]]:
    home = tmp_path / "home"
    home.mkdir()
    data_root = home / ".hermes" / "oh-my-deepseek-harness"
    env = {
        **os.environ,
        "HOME": str(home),
        "USERPROFILE": str(home),
        "HARNESS_DATA_ROOT": str(data_root),
        "HARNESS_DB_PATH": str(data_root / "data" / "harness.db"),
        "HARNESS_MEMORIES_DIR": str(home / ".hermes" / "memories"),
        "HARNESS_IMPORT_MEMORIES": "0",
        "HARNESS_HOST": "127.0.0.1",
        "HARNESS_PORT": str(port or _free_port()),
        "DEEPSEEK_API_KEY": FAKE_SECRET,
        "PYTHONNOUSERSITE": "1",
    }
    return data_root, env


def _all_dependencies(_: str) -> object:
    return object()


def _supported_hermes(_: str) -> str:
    return "0.19.0"


def _check(report: DoctorReport, check_id: str) -> dict:
    return next(check for check in report.to_dict()["checks"] if check["id"] == check_id)


def _tree_snapshot(root: Path) -> tuple[tuple[str, str, int, bytes], ...]:
    if not root.exists():
        return ()
    rows: list[tuple[str, str, int, bytes]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            rows.append((relative, "symlink", path.lstat().st_mode, os.readlink(path).encode()))
        elif path.is_dir():
            rows.append((relative, "directory", path.stat().st_mode, b""))
        else:
            rows.append((relative, "file", path.stat().st_mode, path.read_bytes()))
    return tuple(rows)


def test_doctor_missing_runtime_dependency_returns_exit_3_without_writes(
    tmp_path: Path,
) -> None:
    """TC-INSTALL-004: missing runtime dependencies are explicit and actionable."""
    data_root, env = _environment(tmp_path)
    home = Path(env["HOME"])
    before = _tree_snapshot(home)

    report = diagnose(
        environ=env,
        python_version=(3, 11, 9),
        dependency_finder=lambda name: None if name == "uvicorn" else object(),
        hermes_locator=lambda _: "/fake/bin/hermes",
        hermes_version_reader=_supported_hermes,
        port_probe=lambda _host, _port: False,
        endpoint_probe=lambda _base, _path: (None, None),
    )

    dependency = _check(report, "dependencies")
    assert report.exit_code == DOCTOR_MISSING_DEPENDENCY
    assert dependency["status"] == "fail"
    assert dependency["details"]["missing"] == ["uvicorn"]
    assert "server or all extra" in dependency["recovery"]
    assert _tree_snapshot(home) == before
    assert not data_root.exists()


def test_doctor_unmanaged_port_conflict_returns_exit_4_and_does_not_signal(
    tmp_path: Path,
) -> None:
    """TC-INSTALL-005: an unmanaged listener is diagnosed without process action."""
    data_root, env = _environment(tmp_path)
    home = Path(env["HOME"])
    before = _tree_snapshot(home)
    calls: list[tuple[str, int]] = []

    def occupied(host: str, port: int) -> bool:
        calls.append((host, port))
        return True

    report = diagnose(
        environ=env,
        python_version=(3, 11, 9),
        dependency_finder=_all_dependencies,
        hermes_locator=lambda _: "/fake/bin/hermes",
        hermes_version_reader=_supported_hermes,
        port_probe=occupied,
        endpoint_probe=lambda _base, _path: pytest.fail(
            "Doctor must not probe Harness endpoints without managed state"
        ),
    )

    port = _check(report, "port")
    assert report.exit_code == DOCTOR_PORT_CONFLICT
    assert port["status"] == "fail"
    assert "unmanaged process" in port["message"]
    assert "Stop the process" in port["recovery"]
    assert calls == [("127.0.0.1", int(env["HARNESS_PORT"]))]
    assert _tree_snapshot(home) == before
    assert not data_root.exists()


@pytest.mark.parametrize(
    ("python_version", "hermes_version", "expected_fragment"),
    [
        ((3, 13, 0), "0.19.0", ">=3.10,<3.13"),
        ((3, 11, 9), "0.18.0", "0.19.0"),
        ((3, 10, 14), "0.19.0", "package/core only"),
    ],
)
def test_doctor_unsupported_python_hermes_matrix_returns_exit_5(
    tmp_path: Path,
    python_version: tuple[int, int, int],
    hermes_version: str,
    expected_fragment: str,
) -> None:
    """TC-INSTALL-009: detected and supported values are reported explicitly."""
    _, env = _environment(tmp_path)
    report = diagnose(
        environ=env,
        python_version=python_version,
        dependency_finder=_all_dependencies,
        hermes_locator=lambda _: "/fake/bin/hermes",
        hermes_version_reader=lambda _: hermes_version,
        port_probe=lambda _host, _port: False,
        endpoint_probe=lambda _base, _path: (None, None),
    )

    assert report.exit_code == DOCTOR_UNSUPPORTED
    rendered = json.dumps(report.to_dict(), ensure_ascii=False, sort_keys=True)
    assert expected_fragment in rendered
    assert "3.11-3.12" in rendered
    assert str(Path(env["HOME"])) not in rendered
    assert FAKE_SECRET not in rendered


def test_doctor_human_and_json_render_the_same_structured_report(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    report = DoctorReport(
        (
            DoctorCheck("python", "pass", "Python supported", details={"detected": "3.11.9"}),
            DoctorCheck(
                "hermes",
                "fail",
                "Hermes unsupported",
                recovery="Use Hermes 0.19.0.",
                failure_class="unsupported",
                details={"detected": "0.18.0", "supported": "0.19.0"},
            ),
        ),
        DOCTOR_UNSUPPORTED,
    )
    monkeypatch.setattr(cli, "diagnose", lambda **_kwargs: report)

    json_code = cli.main(["doctor", "--json", "--data-root", str(tmp_path / "data")])
    json_output = capsys.readouterr().out.strip()
    assert json_code == DOCTOR_UNSUPPORTED
    assert json.loads(json_output) == report.to_dict()
    assert len(json_output.splitlines()) == 1

    human_code = cli.main(["doctor", "--data-root", str(tmp_path / "data")])
    human_output = capsys.readouterr().out.strip()
    assert human_code == DOCTOR_UNSUPPORTED
    assert human_output == render_human(report)
    for check in report.checks:
        assert check.check_id in human_output
        assert check.status.upper() in human_output
    assert str(tmp_path) not in human_output
    assert FAKE_SECRET not in human_output


@pytest.mark.skipif(os.name == "nt", reason="Windows Doctor process matrix is later work")
def test_doctor_passes_against_installed_ready_runtime_without_state_mutation(
    tmp_path: Path,
) -> None:
    """A ready installed lifecycle produces an all-pass read-only Doctor report."""
    data_root, env = _environment(tmp_path)
    plan = build_install_plan(environ=env)
    result = execute_install(plan, dry_run=False, timeout=20)
    assert result["ready"] is True
    managed_state = plan.runtime_paths.state_file.read_bytes()
    config = plan.config_path.read_bytes()
    database_size = Path(plan.runtime_config.db_path).stat().st_size
    try:
        report = diagnose(
            environ=env,
            python_version=(3, 11, 9),
            dependency_finder=_all_dependencies,
            hermes_locator=lambda _: "/fake/bin/hermes",
            hermes_version_reader=_supported_hermes,
        )
        assert report.exit_code == DOCTOR_OK, report.to_dict()
        assert all(check.status == "pass" for check in report.checks)
        assert plan.runtime_paths.state_file.read_bytes() == managed_state
        assert plan.config_path.read_bytes() == config
        assert Path(plan.runtime_config.db_path).stat().st_size == database_size
        rendered = json.dumps(report.to_dict(), ensure_ascii=False, sort_keys=True)
        assert str(data_root) not in rendered
        assert FAKE_SECRET not in rendered
    finally:
        Supervisor(plan.runtime_paths).stop(timeout=10)


def test_doctor_implementation_is_read_only_and_never_manages_processes() -> None:
    source = (Path(__file__).resolve().parents[1] / "src" / "deepseek_harness" / "doctor.py").read_text(
        encoding="utf-8"
    )
    assert "Supervisor(" not in source
    assert ".start(" not in source
    assert ".stop(" not in source
    assert "pip install" not in source
    assert "pip uninstall" not in source
