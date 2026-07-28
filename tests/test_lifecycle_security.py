"""INS-003 destructive lifecycle path and backup-manifest security tests."""

from __future__ import annotations

import json
import os
import socket
from pathlib import Path

import pytest
import yaml

import deepseek_harness.lifecycle as lifecycle
from deepseek_harness.installer import build_install_plan, execute_install
from deepseek_harness.lifecycle import (
    LifecycleConflictError,
    LifecyclePaths,
    LifecycleRollbackError,
    TransactionRecord,
    recover,
    uninstall,
    upgrade,
)
from harness_server.supervisor import Supervisor


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _plan(tmp_path: Path, *, db_path: Path | None = None):
    home = tmp_path / "home"
    home.mkdir()
    data_root = home / ".hermes" / "oh-my-deepseek-harness"
    env = {
        **os.environ,
        "HOME": str(home),
        "USERPROFILE": str(home),
        "HARNESS_DATA_ROOT": str(data_root),
        "HARNESS_DB_PATH": str(db_path or data_root / "data" / "harness.db"),
        "HARNESS_MEMORIES_DIR": str(home / ".hermes" / "memories"),
        "HARNESS_IMPORT_MEMORIES": "0",
        "HARNESS_HOST": "127.0.0.1",
        "HARNESS_PORT": str(_free_port()),
        "DEEPSEEK_API_KEY": "fake-security-key",
    }
    return build_install_plan(environ=env)


def _old_version(plan) -> None:
    payload = yaml.safe_load(plan.config_path.read_text(encoding="utf-8"))
    payload["distribution_version"] = "2.9.0"
    plan.config_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    if os.name != "nt":
        plan.config_path.chmod(0o600)


def _stop(plan) -> None:
    try:
        Supervisor(plan.runtime_paths).stop(timeout=10)
    except Exception:
        pass


@pytest.mark.skipif(os.name == "nt", reason="Windows lifecycle process matrix is later work")
def test_upgrade_rejects_external_database_symlink_before_process_change(tmp_path: Path) -> None:
    outside = tmp_path / "outside.db"
    outside.write_bytes(b"not-a-real-database")
    linked_db = tmp_path / "linked.db"
    linked_db.symlink_to(outside)
    plan = _plan(tmp_path, db_path=linked_db)
    # Install cannot safely initialize a symlink DB, so install with a regular DB then
    # replace only the runtime plan's external DB fixture for upgrade preflight.
    regular_plan = _plan(tmp_path / "regular")
    installed = execute_install(regular_plan, dry_run=False, timeout=20)
    assert installed["ready"] is True
    _old_version(regular_plan)
    object.__setattr__(regular_plan.runtime_config, "db_path", str(linked_db))
    try:
        with pytest.raises(LifecycleConflictError, match="symlink"):
            upgrade(regular_plan, timeout=20)
        status = Supervisor(regular_plan.runtime_paths).status()
        assert status.running and status.ready
        assert outside.read_bytes() == b"not-a-real-database"
        assert not LifecyclePaths.from_plan(regular_plan).marker.exists()
    finally:
        _stop(regular_plan)


@pytest.mark.skipif(os.name == "nt", reason="Windows lifecycle process matrix is later work")
def test_recovery_rejects_manifest_traversal_before_restoring_owned_files(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    execute_install(plan, dry_run=False, timeout=20)
    _old_version(plan)
    config_before = plan.config_path.read_bytes()
    transaction_id = "manifest-traversal"
    backup_dir = lifecycle._create_backup(plan, transaction_id)
    manifest_path = backup_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["items"][0]["backup_relative"] = "../../outside"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    marker = TransactionRecord(
        schema_version=1,
        transaction_id=transaction_id,
        operation="upgrade",
        phase="deployment_replaced",
        backup_dir=str(backup_dir),
        previous_running=True,
        previous_version="2.9.0",
        target_version="3.0.0b1",
    )
    lifecycle._write_marker(LifecyclePaths.from_plan(plan), marker)
    try:
        with pytest.raises(LifecycleRollbackError, match="contract mismatch"):
            recover(plan, timeout=20)
        assert plan.config_path.read_bytes() == config_before
        assert LifecyclePaths.from_plan(plan).marker.is_file()
        assert not (plan.data_root / "outside").exists()
    finally:
        _stop(plan)


@pytest.mark.skipif(os.name == "nt", reason="Windows lifecycle process matrix is later work")
def test_purge_rejects_symlink_hermes_parent_and_preserves_target(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    outside_hermes = tmp_path / "outside-hermes"
    product = outside_hermes / "oh-my-deepseek-harness"
    product.mkdir(parents=True)
    sentinel = product / "user-data.txt"
    sentinel.write_text("preserve", encoding="utf-8")
    (home / ".hermes").symlink_to(outside_hermes, target_is_directory=True)
    plan = build_install_plan(
        environ={
            **os.environ,
            "HOME": str(home),
            "USERPROFILE": str(home),
            "HARNESS_DATA_ROOT": str(home / ".hermes" / "oh-my-deepseek-harness"),
            "HARNESS_DB_PATH": str(home / ".hermes" / "oh-my-deepseek-harness" / "data" / "harness.db"),
            "HARNESS_MEMORIES_DIR": str(home / ".hermes" / "memories"),
            "HARNESS_PORT": str(_free_port()),
        }
    )

    with pytest.raises(LifecycleConflictError, match="symlink .hermes"):
        uninstall(plan, purge_data=True, confirm=True)
    assert sentinel.read_text(encoding="utf-8") == "preserve"
    assert (home / ".hermes").is_symlink()
