"""Safe upgrade, uninstall, purge and interrupted-transaction recovery.

This module manages only the installed Harness deployment and product-owned
paths. It never installs or uninstalls the Python distribution.
"""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import yaml

from harness_server.runtime import RuntimeStateError, process_is_owned, read_state
from harness_server.supervisor import ProcessOwnershipError, Supervisor

from .installer import InstallPlan, build_install_plan, execute_install

PIP_UNINSTALL_COMMAND = "python -m pip uninstall oh-my-deepseek-harness"
TRANSACTION_SCHEMA_VERSION = 1
KNOWN_PRODUCT_CHILDREN = frozenset(
    {"config", "data", "logs", "events", "runtime", "backups"}
)


class LifecycleError(RuntimeError):
    """Base lifecycle failure with a stable CLI exit code."""

    exit_code = 4


class ConfirmationRequired(LifecycleError):
    """A destructive operation requires explicit confirmation."""

    exit_code = 2


class LifecycleFailedError(LifecycleError):
    """The requested lifecycle transaction failed but rollback completed."""

    exit_code = 5


class LifecycleRollbackError(LifecycleError):
    """Rollback or recovery could not restore the previous deployment."""

    exit_code = 6


class LifecycleConflictError(LifecycleError):
    """An unsafe path or unmanaged conflict blocks the transaction."""


@dataclass(frozen=True)
class LifecyclePaths:
    marker: Path
    backups_root: Path

    @classmethod
    def from_plan(cls, plan: InstallPlan) -> "LifecyclePaths":
        return cls(
            marker=plan.data_root / "runtime" / "lifecycle-transaction.json",
            backups_root=plan.data_root / "backups",
        )


@dataclass(frozen=True)
class BackupItem:
    name: str
    source: Path
    backup_relative: str
    kind: str


@dataclass(frozen=True)
class TransactionRecord:
    schema_version: int
    transaction_id: str
    operation: str
    phase: str
    backup_dir: str
    previous_running: bool
    previous_version: str | None
    target_version: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "transaction_id": self.transaction_id,
            "operation": self.operation,
            "phase": self.phase,
            "backup_dir": self.backup_dir,
            "previous_running": self.previous_running,
            "previous_version": self.previous_version,
            "target_version": self.target_version,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TransactionRecord":
        try:
            record = cls(
                schema_version=int(payload["schema_version"]),
                transaction_id=str(payload["transaction_id"]),
                operation=str(payload["operation"]),
                phase=str(payload["phase"]),
                backup_dir=str(payload["backup_dir"]),
                previous_running=bool(payload["previous_running"]),
                previous_version=(
                    None
                    if payload.get("previous_version") is None
                    else str(payload["previous_version"])
                ),
                target_version=str(payload["target_version"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise LifecycleRollbackError("lifecycle transaction marker is invalid") from exc
        if record.schema_version != TRANSACTION_SCHEMA_VERSION:
            raise LifecycleRollbackError(
                f"unsupported lifecycle transaction schema: {record.schema_version}"
            )
        if record.operation != "upgrade" or not record.transaction_id:
            raise LifecycleRollbackError("lifecycle transaction marker values are invalid")
        return record


PhaseHook = Callable[[str, InstallPlan, TransactionRecord | None], None]


def _chmod_private(path: Path, mode: int) -> None:
    if os.name != "nt":
        path.chmod(mode)


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _chmod_private(path.parent, 0o700)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}-", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        if os.name != "nt":
            os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        _chmod_private(path, 0o600)
    except Exception:
        try:
            os.close(descriptor)
        except OSError:
            pass
        temporary.unlink(missing_ok=True)
        raise


def _read_marker(paths: LifecyclePaths) -> TransactionRecord | None:
    if not paths.marker.exists():
        return None
    if paths.marker.is_symlink() or not paths.marker.is_file():
        raise LifecycleRollbackError("lifecycle transaction marker is not a regular file")
    try:
        payload = json.loads(paths.marker.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LifecycleRollbackError("lifecycle transaction marker is unreadable") from exc
    if not isinstance(payload, dict):
        raise LifecycleRollbackError("lifecycle transaction marker must be an object")
    return TransactionRecord.from_dict(payload)


def _write_marker(paths: LifecyclePaths, record: TransactionRecord) -> None:
    _atomic_write_json(paths.marker, record.to_dict())


def _current_version(plan: InstallPlan) -> str | None:
    if not plan.config_path.is_file() or plan.config_path.is_symlink():
        return None
    try:
        payload = yaml.safe_load(plan.config_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    if not isinstance(payload, dict) or payload.get("distribution_version") is None:
        return None
    return str(payload["distribution_version"])


def _target_version(plan: InstallPlan) -> str:
    try:
        payload = yaml.safe_load(plan.desired_files[plan.config_path])
    except yaml.YAMLError as exc:  # pragma: no cover - package resource invariant
        raise LifecycleError("packaged configuration is invalid") from exc
    if not isinstance(payload, dict) or payload.get("distribution_version") is None:
        raise LifecycleError("packaged configuration has no distribution version")
    return str(payload["distribution_version"])


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _assert_no_symlink_tree(path: Path) -> None:
    if not path.exists():
        return
    if path.is_symlink():
        raise LifecycleConflictError(f"refusing symlink lifecycle path: {path}")
    if path.is_file():
        return
    for root, directories, files in os.walk(path, followlinks=False):
        root_path = Path(root)
        for name in [*directories, *files]:
            child = root_path / name
            if child.is_symlink():
                raise LifecycleConflictError(f"refusing symlink lifecycle path: {child}")


def _adapter_roots(plan: InstallPlan) -> tuple[Path, Path]:
    return (
        plan.hermes_home / "plugins" / "deepseek-harness",
        plan.hermes_home / "plugins" / "deepseek-context",
    )


def _backup_items(plan: InstallPlan) -> tuple[BackupItem, ...]:
    db_path = Path(plan.runtime_config.db_path).expanduser().resolve()
    harness_adapter, context_adapter = _adapter_roots(plan)
    return (
        BackupItem("harness_adapter", harness_adapter, "deployment/deepseek-harness", "tree"),
        BackupItem("context_adapter", context_adapter, "deployment/deepseek-context", "tree"),
        BackupItem("config", plan.config_path, "config/config.yaml", "file"),
        BackupItem("database", db_path, "data/harness.db", "database"),
        BackupItem("events", plan.data_root / "events", "events", "tree"),
    )


def _copy_database(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    _chmod_private(destination.parent, 0o700)
    source_connection = sqlite3.connect(f"file:{source}?mode=ro", uri=True, timeout=5)
    try:
        destination_connection = sqlite3.connect(destination)
        try:
            source_connection.backup(destination_connection)
        finally:
            destination_connection.close()
    finally:
        source_connection.close()
    _chmod_private(destination, 0o600)


def _copy_item_to_backup(item: BackupItem, backup_dir: Path) -> dict[str, Any]:
    source = item.source
    destination = backup_dir / item.backup_relative
    existed = source.exists()
    if existed:
        _assert_no_symlink_tree(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        _chmod_private(destination.parent, 0o700)
        if item.kind == "tree":
            shutil.copytree(source, destination)
            for root, directories, files in os.walk(destination):
                _chmod_private(Path(root), 0o700)
                for name in directories:
                    _chmod_private(Path(root) / name, 0o700)
                for name in files:
                    _chmod_private(Path(root) / name, 0o600)
        elif item.kind == "database":
            _copy_database(source, destination)
        else:
            shutil.copy2(source, destination)
            _chmod_private(destination, 0o600)
    return {
        "name": item.name,
        "source": str(source),
        "backup_relative": item.backup_relative,
        "kind": item.kind,
        "existed": existed,
    }


def _create_backup(plan: InstallPlan, transaction_id: str) -> Path:
    paths = LifecyclePaths.from_plan(plan)
    paths.backups_root.mkdir(parents=True, exist_ok=True)
    _chmod_private(paths.backups_root, 0o700)
    backup_dir = paths.backups_root / f"upgrade-{transaction_id}"
    backup_dir.mkdir(mode=0o700)
    manifest = {
        "schema_version": 1,
        "transaction_id": transaction_id,
        "items": [_copy_item_to_backup(item, backup_dir) for item in _backup_items(plan)],
    }
    _atomic_write_json(backup_dir / "manifest.json", manifest)
    return backup_dir


def _read_backup_manifest(backup_dir: Path) -> dict[str, Any]:
    manifest_path = backup_dir / "manifest.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise LifecycleRollbackError("upgrade backup manifest is missing")
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LifecycleRollbackError("upgrade backup manifest is unreadable") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise LifecycleRollbackError("upgrade backup manifest is invalid")
    return payload


def _remove_known_path(path: Path) -> None:
    if not path.exists():
        return
    _assert_no_symlink_tree(path)
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def _restore_backup(plan: InstallPlan, backup_dir: Path) -> None:
    paths = LifecyclePaths.from_plan(plan)
    resolved_backup = backup_dir.resolve()
    if not _is_relative_to(resolved_backup, paths.backups_root.resolve()):
        raise LifecycleRollbackError("upgrade backup is outside the canonical backups root")
    manifest = _read_backup_manifest(resolved_backup)
    expected = {item.name: item for item in _backup_items(plan)}
    failures: list[str] = []
    for payload in manifest["items"]:
        try:
            name = str(payload["name"])
            item = expected[name]
            existed = bool(payload["existed"])
            source = resolved_backup / str(payload["backup_relative"])
            target = item.source
            _remove_known_path(target)
            if not existed:
                continue
            if not source.exists():
                raise LifecycleRollbackError(f"backup item is missing: {name}")
            target.parent.mkdir(parents=True, exist_ok=True)
            _chmod_private(target.parent, 0o700)
            if item.kind == "tree":
                shutil.copytree(source, target)
            elif item.kind == "database":
                _copy_database(source, target)
            else:
                shutil.copy2(source, target)
                _chmod_private(target, 0o600)
        except Exception as exc:  # failure injection/report aggregation
            failures.append(f"{payload.get('name', 'unknown')}: {exc}")
    if failures:
        raise LifecycleRollbackError("; ".join(failures))


def _managed_process_running(plan: InstallPlan) -> bool:
    try:
        state = read_state(plan.runtime_paths)
    except RuntimeStateError as exc:
        raise LifecycleConflictError(
            "runtime state is unreadable; preserve it before lifecycle changes"
        ) from exc
    if state is None:
        return False
    if not process_is_owned(state):
        raise ProcessOwnershipError(
            "runtime PID ownership cannot be proven; refusing lifecycle process changes"
        )
    return True


def _replace_managed_files(plan: InstallPlan) -> None:
    for path, content in plan.desired_files.items():
        if path.exists() and (path.is_symlink() or not path.is_file()):
            raise LifecycleConflictError(f"managed path is unsafe: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        _chmod_private(path.parent, 0o700)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}-", suffix=".upgrade", dir=path.parent
        )
        temporary = Path(temporary_name)
        try:
            if os.name != "nt":
                os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
            _chmod_private(path, 0o600)
        except Exception:
            try:
                os.close(descriptor)
            except OSError:
                pass
            temporary.unlink(missing_ok=True)
            raise


def upgrade_plan(plan: InstallPlan, *, dry_run: bool) -> dict[str, Any]:
    paths = LifecyclePaths.from_plan(plan)
    current = _current_version(plan)
    target = _target_version(plan)
    marker = _read_marker(paths)
    db_path = Path(plan.runtime_config.db_path).expanduser().resolve()
    return {
        "state": "planned" if dry_run else "upgrade_ready",
        "dry_run": dry_run,
        "current_version": current or "not_installed",
        "target_version": target,
        "same_version": current == target,
        "backup_required": current != target,
        "config": "replace_with_packaged_contract" if current != target else "validate",
        "database": "backup_and_validate" if db_path.exists() and current != target else "validate",
        "events_jsonl": "backup" if (plan.data_root / "events").exists() and current != target else "preserve",
        "process": "restart_if_running" if current != target else "start_or_reuse",
        "interrupted_transaction": marker.to_dict() if marker else None,
    }


def upgrade(
    plan: InstallPlan,
    *,
    dry_run: bool = False,
    timeout: float = 20,
    phase_hook: PhaseHook | None = None,
) -> dict[str, Any]:
    """Upgrade managed deployment/config/data with backup and rollback."""
    preview = upgrade_plan(plan, dry_run=dry_run)
    if dry_run:
        return preview
    paths = LifecyclePaths.from_plan(plan)
    if _read_marker(paths) is not None:
        raise LifecycleConflictError(
            "an interrupted lifecycle transaction exists; run deepseek-harness recover first"
        )
    current = _current_version(plan)
    target = _target_version(plan)
    if current == target:
        result = execute_install(plan, dry_run=False, timeout=timeout)
        return {
            **preview,
            "state": "up_to_date",
            "changed": False,
            "server_pid": result.get("server_pid"),
            "ready": result.get("ready"),
            "backup_dir": None,
        }

    previous_running = _managed_process_running(plan)
    transaction_id = uuid.uuid4().hex
    backup_dir = _create_backup(plan, transaction_id)
    record = TransactionRecord(
        schema_version=TRANSACTION_SCHEMA_VERSION,
        transaction_id=transaction_id,
        operation="upgrade",
        phase="backup_complete",
        backup_dir=str(backup_dir),
        previous_running=previous_running,
        previous_version=current,
        target_version=target,
    )
    _write_marker(paths, record)
    if phase_hook:
        phase_hook("backup_complete", plan, record)

    supervisor = Supervisor(plan.runtime_paths)
    try:
        if previous_running:
            supervisor.stop(timeout=10)
        record = TransactionRecord(**{**record.__dict__, "phase": "process_stopped"})
        _write_marker(paths, record)
        if phase_hook:
            phase_hook("process_stopped", plan, record)

        _replace_managed_files(plan)
        record = TransactionRecord(**{**record.__dict__, "phase": "deployment_replaced"})
        _write_marker(paths, record)
        if phase_hook:
            phase_hook("deployment_replaced", plan, record)

        result = execute_install(plan, dry_run=False, timeout=timeout)
        if not result.get("ready"):
            raise LifecycleError("upgraded Server did not reach ready state")
        if phase_hook:
            phase_hook("validated", plan, record)
        paths.marker.unlink(missing_ok=True)
        return {
            **preview,
            "state": "upgraded",
            "changed": True,
            "backup_dir": str(backup_dir),
            "server_pid": result.get("server_pid"),
            "ready": result.get("ready"),
        }
    except Exception as exc:
        try:
            if plan.runtime_paths.state_file.exists():
                supervisor.stop(timeout=10)
            _restore_backup(plan, backup_dir)
            if previous_running:
                supervisor.start(plan.runtime_config, timeout=timeout)
            paths.marker.unlink(missing_ok=True)
        except Exception as rollback_exc:
            raise LifecycleRollbackError(
                "upgrade failed and automatic rollback is incomplete; preserve the "
                f"transaction marker and backup {backup_dir}: {rollback_exc}"
            ) from rollback_exc
        raise LifecycleFailedError(
            f"upgrade failed; previous deployment was restored from {backup_dir}: {exc}"
        ) from exc


def recover(
    plan: InstallPlan, *, timeout: float = 20, phase_hook: PhaseHook | None = None
) -> dict[str, Any]:
    """Restore an interrupted upgrade from its private transaction marker."""
    paths = LifecyclePaths.from_plan(plan)
    record = _read_marker(paths)
    if record is None:
        return {"state": "clean", "changed": False, "message": "no interrupted transaction"}
    backup_dir = Path(record.backup_dir)
    supervisor = Supervisor(plan.runtime_paths)
    try:
        if plan.runtime_paths.state_file.exists():
            supervisor.stop(timeout=10)
        _restore_backup(plan, backup_dir)
        if phase_hook:
            phase_hook("restored", plan, record)
        status = None
        if record.previous_running:
            status = supervisor.start(plan.runtime_config, timeout=timeout)
        paths.marker.unlink(missing_ok=True)
        return {
            "state": "recovered",
            "changed": True,
            "backup_dir": str(backup_dir),
            "previous_version": record.previous_version,
            "server_pid": None if status is None else status.pid,
            "ready": None if status is None else status.ready,
        }
    except Exception as exc:
        raise LifecycleRollbackError(
            "recovery is incomplete; preserve the transaction marker and backup "
            f"{backup_dir}: {exc}"
        ) from exc


def _preflight_managed_adapters(plan: InstallPlan) -> list[Path]:
    managed: list[Path] = []
    adapter_roots = set(_adapter_roots(plan))
    for path, desired in plan.desired_files.items():
        if path.parent not in adapter_roots or not path.exists():
            continue
        if path.is_symlink() or not path.is_file():
            raise LifecycleConflictError(f"managed adapter path is unsafe: {path}")
        if path.read_text(encoding="utf-8") != desired:
            raise LifecycleConflictError(
                f"managed adapter differs from installed package; preserving user file: {path}"
            )
        managed.append(path)
    return managed


def _assert_canonical_purge_root(plan: InstallPlan) -> None:
    root = plan.data_root
    canonical = (plan.hermes_home / "oh-my-deepseek-harness").resolve()
    if root.is_symlink() or root.resolve() != canonical:
        raise LifecycleConflictError(
            "purge data root must be the canonical ~/.hermes/oh-my-deepseek-harness path"
        )
    if root in {Path(root.anchor), plan.hermes_home, plan.hermes_home.parent}:
        raise LifecycleConflictError("refusing unsafe purge root")
    if root.exists():
        _assert_no_symlink_tree(root)
        unknown = {entry.name for entry in root.iterdir()} - KNOWN_PRODUCT_CHILDREN
        if unknown:
            raise LifecycleConflictError(
                f"refusing purge with unknown top-level product paths: {sorted(unknown)}"
            )


def _safe_remove_tree(root: Path) -> None:
    if not root.exists():
        return
    _assert_no_symlink_tree(root)
    for current, directories, files in os.walk(root, topdown=False, followlinks=False):
        current_path = Path(current)
        for name in files:
            path = current_path / name
            if path.is_symlink():
                raise LifecycleConflictError(f"refusing symlink during purge: {path}")
            path.unlink()
        for name in directories:
            path = current_path / name
            if path.is_symlink():
                raise LifecycleConflictError(f"refusing symlink during purge: {path}")
            path.rmdir()
    root.rmdir()


def uninstall(
    plan: InstallPlan,
    *,
    purge_data: bool = False,
    confirm: bool = False,
) -> dict[str, Any]:
    """Remove managed deployment while preserving distribution and user data."""
    if purge_data and not confirm:
        raise ConfirmationRequired(
            "purge requires --confirm; no deployment or data changes were made"
        )
    paths = LifecyclePaths.from_plan(plan)
    if _read_marker(paths) is not None:
        raise LifecycleConflictError(
            "an interrupted lifecycle transaction exists; run deepseek-harness recover first"
        )
    managed_files = _preflight_managed_adapters(plan)
    if purge_data:
        _assert_canonical_purge_root(plan)

    supervisor = Supervisor(plan.runtime_paths)
    if plan.runtime_paths.state_file.exists():
        supervisor.stop(timeout=10)

    removed: list[str] = []
    for path in managed_files:
        path.unlink()
        removed.append(path.name)
    for root in _adapter_roots(plan):
        try:
            root.rmdir()
        except OSError:
            pass
    try:
        (plan.hermes_home / "plugins").rmdir()
    except OSError:
        pass

    plan.runtime_paths.state_file.unlink(missing_ok=True)
    plan.runtime_paths.lock_file.unlink(missing_ok=True)
    try:
        plan.runtime_paths.runtime_dir.rmdir()
    except OSError:
        pass

    if purge_data:
        _safe_remove_tree(plan.data_root)
        state = "purged"
    else:
        state = "uninstalled"
    return {
        "state": state,
        "changed": bool(removed) or purge_data,
        "purge_data": purge_data,
        "removed_managed_files": sorted(removed),
        "data_preserved": not purge_data,
        "distribution_preserved": True,
        "pip_uninstall_command": PIP_UNINSTALL_COMMAND,
    }


def plan_from_environment(
    *, data_root: str | os.PathLike[str] | None = None
) -> InstallPlan:
    return build_install_plan(data_root=data_root)


__all__ = [
    "ConfirmationRequired",
    "LifecycleConflictError",
    "LifecycleError",
    "LifecycleFailedError",
    "LifecyclePaths",
    "LifecycleRollbackError",
    "PIP_UNINSTALL_COMMAND",
    "TransactionRecord",
    "plan_from_environment",
    "recover",
    "uninstall",
    "upgrade",
    "upgrade_plan",
]
