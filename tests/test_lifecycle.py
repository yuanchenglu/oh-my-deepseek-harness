"""INS-003 lifecycle tests for TC-INSTALL-006 through 008 and 010."""

from __future__ import annotations

import importlib.metadata
import json
import os
import socket
import sqlite3
import stat
from pathlib import Path

import pytest
import yaml

from deepseek_harness import cli
from deepseek_harness.installer import InstallPlan, build_install_plan, execute_install
from deepseek_harness.lifecycle import (
    ConfirmationRequired,
    LifecycleConflictError,
    LifecycleFailedError,
    LifecyclePaths,
    PIP_UNINSTALL_COMMAND,
    recover,
    uninstall,
    upgrade,
    upgrade_plan,
)
from harness_server.supervisor import Supervisor


FAKE_SECRET = "fake-ins-003-secret"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _environment(
    tmp_path: Path, *, external_db: bool = False
) -> tuple[InstallPlan, dict[str, str]]:
    home = tmp_path / "home"
    home.mkdir()
    data_root = home / ".hermes" / "oh-my-deepseek-harness"
    db_path = tmp_path / "external" / "harness.db" if external_db else data_root / "data" / "harness.db"
    env = {
        **os.environ,
        "HOME": str(home),
        "USERPROFILE": str(home),
        "HARNESS_DATA_ROOT": str(data_root),
        "HARNESS_DB_PATH": str(db_path),
        "HARNESS_MEMORIES_DIR": str(home / ".hermes" / "memories"),
        "HARNESS_IMPORT_MEMORIES": "0",
        "HARNESS_HOST": "127.0.0.1",
        "HARNESS_PORT": str(_free_port()),
        "DEEPSEEK_API_KEY": FAKE_SECRET,
        "PYTHONNOUSERSITE": "1",
    }
    return build_install_plan(environ=env), env


def _install(plan: InstallPlan) -> dict:
    result = execute_install(plan, dry_run=False, timeout=20)
    assert result["ready"] is True
    events = plan.data_root / "events"
    events.mkdir(exist_ok=True)
    if os.name != "nt":
        events.chmod(0o700)
    event = events / "constraint-events.jsonl"
    event.write_text('{"event":"sentinel"}\n', encoding="utf-8")
    if os.name != "nt":
        event.chmod(0o600)
    return result


def _set_old_version(plan: InstallPlan, version: str = "2.9.0") -> bytes:
    payload = yaml.safe_load(plan.config_path.read_text(encoding="utf-8"))
    payload["distribution_version"] = version
    payload["legacy_sentinel"] = "preserve-on-rollback"
    plan.config_path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    if os.name != "nt":
        plan.config_path.chmod(0o600)
    return plan.config_path.read_bytes()


def _db_sentinel(plan: InstallPlan, value: str = "old-data") -> bytes:
    path = Path(plan.runtime_config.db_path)
    connection = sqlite3.connect(path)
    try:
        connection.execute("CREATE TABLE IF NOT EXISTS lifecycle_probe(value TEXT NOT NULL)")
        connection.execute("DELETE FROM lifecycle_probe")
        connection.execute("INSERT INTO lifecycle_probe(value) VALUES (?)", (value,))
        connection.commit()
    finally:
        connection.close()
    return path.read_bytes()


def _db_value(plan: InstallPlan) -> str:
    connection = sqlite3.connect(plan.runtime_config.db_path)
    try:
        row = connection.execute("SELECT value FROM lifecycle_probe").fetchone()
        assert row is not None
        return str(row[0])
    finally:
        connection.close()


def _tree_snapshot(root: Path) -> tuple[tuple[str, str, int, bytes], ...]:
    if not root.exists():
        return ()
    rows: list[tuple[str, str, int, bytes]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        mode = stat.S_IMODE(path.lstat().st_mode)
        if path.is_symlink():
            rows.append((relative, "symlink", mode, os.readlink(path).encode()))
        elif path.is_dir():
            rows.append((relative, "directory", mode, b""))
        else:
            rows.append((relative, "file", mode, path.read_bytes()))
    return tuple(rows)


def _stop(plan: InstallPlan) -> None:
    try:
        Supervisor(plan.runtime_paths).stop(timeout=10)
    except Exception:
        pass


@pytest.mark.skipif(os.name == "nt", reason="Windows lifecycle process matrix is later work")
def test_same_version_upgrade_is_idempotent_without_backup_growth(tmp_path: Path) -> None:
    plan, _ = _environment(tmp_path)
    installed = _install(plan)
    backup_before = sorted(path.name for path in (plan.data_root / "backups").iterdir())
    config_before = plan.config_path.read_bytes()
    try:
        result = upgrade(plan, timeout=20)
        assert result["state"] == "up_to_date"
        assert result["changed"] is False
        assert result["server_pid"] == installed["server_pid"]
        assert plan.config_path.read_bytes() == config_before
        assert sorted(path.name for path in (plan.data_root / "backups").iterdir()) == backup_before
        assert not LifecyclePaths.from_plan(plan).marker.exists()
    finally:
        _stop(plan)


@pytest.mark.skipif(os.name == "nt", reason="Windows lifecycle process matrix is later work")
def test_upgrade_dry_run_reports_impact_without_changes(tmp_path: Path) -> None:
    plan, _ = _environment(tmp_path)
    _install(plan)
    _set_old_version(plan)
    before = _tree_snapshot(Path(os.environ.get("NON_EXISTENT_INS003", plan.hermes_home)))
    try:
        result = upgrade_plan(plan, dry_run=True)
        assert result["state"] == "planned"
        assert result["current_version"] == "2.9.0"
        assert result["target_version"] == "3.0.0b1"
        assert result["backup_required"] is True
        assert result["config"] == "replace_with_packaged_contract"
        assert result["database"] == "backup_and_validate"
        assert result["events_jsonl"] == "backup"
        assert result["process"] == "restart_if_running"
        assert _tree_snapshot(plan.hermes_home) == before
    finally:
        _stop(plan)


@pytest.mark.skipif(os.name == "nt", reason="Windows lifecycle process matrix is later work")
def test_failed_upgrade_restores_config_database_events_and_running_state(
    tmp_path: Path,
) -> None:
    plan, _ = _environment(tmp_path)
    _install(plan)
    old_config = _set_old_version(plan)
    _db_sentinel(plan)
    event_path = plan.data_root / "events" / "constraint-events.jsonl"
    old_event = event_path.read_bytes()

    def fail_after_replace(phase: str, _plan: InstallPlan, _record) -> None:
        if phase == "deployment_replaced":
            raise RuntimeError("injected upgrade failure")

    try:
        with pytest.raises(LifecycleFailedError, match="previous deployment was restored"):
            upgrade(plan, timeout=20, phase_hook=fail_after_replace)
        assert plan.config_path.read_bytes() == old_config
        assert _db_value(plan) == "old-data"
        assert event_path.read_bytes() == old_event
        assert not LifecyclePaths.from_plan(plan).marker.exists()
        status = Supervisor(plan.runtime_paths).status()
        assert status.running and status.healthy and status.ready
    finally:
        _stop(plan)


@pytest.mark.skipif(os.name == "nt", reason="Windows lifecycle process matrix is later work")
def test_interrupted_upgrade_recovers_from_marker_and_is_retryable(tmp_path: Path) -> None:
    """TC-INSTALL-008: an interruption leaves a recoverable marker, not half-state."""
    plan, _ = _environment(tmp_path)
    _install(plan)
    old_config = _set_old_version(plan)
    _db_sentinel(plan, "recover-me")
    event_path = plan.data_root / "events" / "constraint-events.jsonl"
    old_event = event_path.read_bytes()

    def interrupt(phase: str, _plan: InstallPlan, _record) -> None:
        if phase == "deployment_replaced":
            raise KeyboardInterrupt("simulated process interruption")

    try:
        with pytest.raises(KeyboardInterrupt):
            upgrade(plan, timeout=20, phase_hook=interrupt)
        marker = LifecyclePaths.from_plan(plan).marker
        assert marker.is_file()
        assert plan.config_path.read_bytes() != old_config

        result = recover(plan, timeout=20)
        assert result["state"] == "recovered"
        assert result["changed"] is True
        assert result["ready"] is True
        assert not marker.exists()
        assert plan.config_path.read_bytes() == old_config
        assert _db_value(plan) == "recover-me"
        assert event_path.read_bytes() == old_event

        retry = upgrade(plan, timeout=20)
        assert retry["state"] == "upgraded"
        assert retry["ready"] is True
        assert yaml.safe_load(plan.config_path.read_text())["distribution_version"] == "3.0.0b1"
    finally:
        _stop(plan)


@pytest.mark.skipif(os.name == "nt", reason="Windows lifecycle process matrix is later work")
def test_ordinary_uninstall_removes_deployment_and_preserves_distribution_and_data(
    tmp_path: Path,
) -> None:
    """TC-INSTALL-006/010: remove deployment, preserve data and print pip command."""
    plan, _ = _environment(tmp_path)
    _install(plan)
    backup_sentinel = plan.data_root / "backups" / "user-backup.txt"
    backup_sentinel.write_text("preserve", encoding="utf-8")
    config = plan.config_path.read_bytes()
    db_value = _db_sentinel(plan, "preserved")
    event = (plan.data_root / "events" / "constraint-events.jsonl").read_bytes()

    result = uninstall(plan)
    assert result["state"] == "uninstalled"
    assert result["data_preserved"] is True
    assert result["distribution_preserved"] is True
    assert result["pip_uninstall_command"] == PIP_UNINSTALL_COMMAND
    assert importlib.metadata.version("oh-my-deepseek-harness") == "3.0.0b1"
    assert not (plan.hermes_home / "plugins" / "deepseek-harness" / "__init__.py").exists()
    assert not (plan.hermes_home / "plugins" / "deepseek-context" / "__init__.py").exists()
    assert plan.config_path.read_bytes() == config
    assert Path(plan.runtime_config.db_path).read_bytes() == db_value
    assert (plan.data_root / "events" / "constraint-events.jsonl").read_bytes() == event
    assert backup_sentinel.read_text() == "preserve"
    assert not plan.runtime_paths.state_file.exists()


@pytest.mark.skipif(os.name == "nt", reason="Windows lifecycle process matrix is later work")
def test_purge_requires_confirm_and_makes_no_change(monkeypatch: pytest.MonkeyPatch, capsys, tmp_path: Path) -> None:
    """TC-INSTALL-007: missing --confirm returns 2 with no state change."""
    plan, env = _environment(tmp_path)
    _install(plan)
    before = _tree_snapshot(plan.hermes_home)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    try:
        code = cli.main(["uninstall", "--purge-data", "--json"])
        payload = json.loads(capsys.readouterr().err.strip())
        assert code == 2
        assert payload["state"] == "lifecycle_error"
        assert "--confirm" in payload["message"]
        assert _tree_snapshot(plan.hermes_home) == before
        status = Supervisor(plan.runtime_paths).status()
        assert status.running and status.ready
    finally:
        _stop(plan)


@pytest.mark.skipif(os.name == "nt", reason="Windows lifecycle process matrix is later work")
def test_confirmed_purge_deletes_only_canonical_product_root_and_preserves_external_db(
    tmp_path: Path,
) -> None:
    plan, _ = _environment(tmp_path, external_db=True)
    _install(plan)
    external_db = Path(plan.runtime_config.db_path)
    assert external_db.is_file()

    result = uninstall(plan, purge_data=True, confirm=True)
    assert result["state"] == "purged"
    assert result["data_preserved"] is False
    assert not plan.data_root.exists()
    assert external_db.is_file()
    assert not (plan.hermes_home / "plugins" / "deepseek-harness").exists()
    assert importlib.metadata.version("oh-my-deepseek-harness") == "3.0.0b1"


@pytest.mark.skipif(os.name == "nt", reason="Windows lifecycle process matrix is later work")
def test_purge_rejects_symlink_and_unknown_paths_before_process_or_adapter_changes(
    tmp_path: Path,
) -> None:
    plan, _ = _environment(tmp_path)
    _install(plan)
    adapter = plan.hermes_home / "plugins" / "deepseek-harness" / "__init__.py"
    unknown = plan.data_root / "user-unknown.txt"
    unknown.write_text("do not delete", encoding="utf-8")
    symlink = plan.data_root / "events" / "outside-link"
    outside = tmp_path / "outside"
    outside.write_text("outside", encoding="utf-8")
    symlink.symlink_to(outside)
    try:
        with pytest.raises(LifecycleConflictError):
            uninstall(plan, purge_data=True, confirm=True)
        assert adapter.is_file()
        assert unknown.read_text() == "do not delete"
        assert symlink.is_symlink()
        status = Supervisor(plan.runtime_paths).status()
        assert status.running and status.ready
    finally:
        symlink.unlink(missing_ok=True)
        unknown.unlink(missing_ok=True)
        _stop(plan)


def test_purge_rejects_noncanonical_data_root_without_changes(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    unsafe_root = tmp_path / "other-product-root"
    plan = build_install_plan(
        environ={
            **os.environ,
            "HOME": str(home),
            "USERPROFILE": str(home),
            "HARNESS_DATA_ROOT": str(unsafe_root),
            "HARNESS_DB_PATH": str(unsafe_root / "data" / "harness.db"),
            "HARNESS_MEMORIES_DIR": str(home / ".hermes" / "memories"),
            "HARNESS_PORT": str(_free_port()),
        }
    )
    with pytest.raises(LifecycleConflictError, match="canonical"):
        uninstall(plan, purge_data=True, confirm=True)
    assert not unsafe_root.exists()


def test_lifecycle_never_invokes_pip_or_keeps_shell_destructive_logic() -> None:
    """TC-INSTALL-010: CLI only reports the exact manual distribution command."""
    root = Path(__file__).resolve().parents[1]
    source = (root / "src" / "deepseek_harness" / "lifecycle.py").read_text(encoding="utf-8")
    shell = (root / "scripts" / "install.sh").read_text(encoding="utf-8")
    assert "subprocess" not in source
    assert PIP_UNINSTALL_COMMAND in source
    assert "pip uninstall" not in shell
    assert "rm -rf" not in shell
