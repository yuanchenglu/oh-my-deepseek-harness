"""Transactional Hermes deployment for the installed distribution.

The Python distribution is managed only by pip.  This module deploys the two
thin Hermes adapters, initializes the product data root and starts the single
Supervisor-managed local Server.
"""

from __future__ import annotations

import importlib.metadata
import importlib.util
import os
import shutil
import stat
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

from harness_server.config import (
    ENV_DB_PATH,
    ENV_HOST,
    ENV_IMPORT_MEMORIES,
    ENV_MEMORIES_DIR,
    ENV_PORT,
    RuntimeConfig,
)
from harness_server.runtime import RuntimePaths
from harness_server.supervisor import RuntimeStatus, Supervisor

ENV_DATA_ROOT = "HARNESS_DATA_ROOT"
DISTRIBUTION_NAME = "oh-my-deepseek-harness"
DEFAULT_DATA_ROOT = "~/.hermes/oh-my-deepseek-harness"
_REQUIRED_SERVER_MODULES = ("fastapi", "uvicorn", "pydantic")

_HARNESS_ADAPTER = '''"""Hermes directory-plugin adapter for the installed deepseek_harness package."""\n\nfrom deepseek_harness import register\n\n__all__ = ["register"]\n'''
_CONTEXT_ADAPTER = '''"""Hermes directory-plugin adapter for the installed deepseek_context package."""\n\nfrom deepseek_context.plugin import register\n\n__all__ = ["register"]\n'''


class InstallError(RuntimeError):
    """Base class for installation failures with a stable CLI exit code."""

    exit_code = 4


class InstallConflictError(InstallError):
    """An existing unmanaged file would be overwritten."""


class InstallFailedError(InstallError):
    """Installation failed after rollback completed successfully."""

    exit_code = 5


class InstallRollbackError(InstallError):
    """Installation failed and rollback could not restore a clean boundary."""

    exit_code = 6


@dataclass(frozen=True)
class InstallPlan:
    hermes_home: Path
    data_root: Path
    config_path: Path
    runtime_paths: RuntimePaths
    runtime_config: RuntimeConfig
    desired_files: dict[Path, str]
    desired_directories: tuple[Path, ...]
    hermes_executable: str | None
    missing_dependencies: tuple[str, ...]

    def public_dict(self, *, dry_run: bool) -> dict[str, Any]:
        return {
            "state": "planned" if dry_run else "installing",
            "message": (
                "dry-run complete; no persistent changes were made"
                if dry_run
                else "install plan prepared"
            ),
            "dry_run": dry_run,
            "changed": False,
            "python_version": ".".join(str(value) for value in sys.version_info[:3]),
            "python_support": {
                "package_core": "3.10-3.12",
                "full_hermes_v0.19.0": "3.11-3.12",
            },
            "hermes_executable": self.hermes_executable or "not_found",
            "deployment_paths": [
                str(self.hermes_home / "plugins" / "deepseek-harness"),
                str(self.hermes_home / "plugins" / "deepseek-context"),
            ],
            "data_root": str(self.data_root),
            "config_path": str(self.config_path),
            "host": self.runtime_config.host,
            "port": self.runtime_config.port,
            "db_path": self.runtime_config.db_path,
            "summary_enabled": False,
            "summary_outbound_policy": "redact",
            "summary_allow_tool_arguments": False,
            "memory_import_on_startup": False,
            "log_include_content": False,
            "backup_policy": (
                "same-version managed files are reused; conflicting existing files "
                "are preserved and installation is rejected"
            ),
            "missing_dependencies": list(self.missing_dependencies),
        }


def _distribution_version() -> str:
    try:
        return importlib.metadata.version(DISTRIBUTION_NAME)
    except importlib.metadata.PackageNotFoundError:
        return "3.0.0b1"


def _resource_text(package: str, name: str) -> str:
    from importlib import resources

    return resources.files(package).joinpath(name).read_text(encoding="utf-8")


def _home_path(environ: Mapping[str, str]) -> Path:
    home = environ.get("HOME") or environ.get("USERPROFILE")
    if home:
        return Path(home).expanduser().resolve()
    return Path.home().resolve()


def _runtime_config(
    environ: Mapping[str, str], *, data_root: Path, hermes_home: Path
) -> RuntimeConfig:
    runtime_env = dict(environ)
    runtime_env.setdefault(ENV_HOST, "127.0.0.1")
    runtime_env.setdefault(ENV_PORT, "8200")
    runtime_env.setdefault(ENV_DB_PATH, str(data_root / "data" / "harness.db"))
    runtime_env.setdefault(ENV_MEMORIES_DIR, str(hermes_home / "memories"))
    runtime_env.setdefault(ENV_IMPORT_MEMORIES, "0")
    return RuntimeConfig.from_env(runtime_env)


def _render_config(runtime: RuntimeConfig) -> str:
    payload = {
        "schema_version": 1,
        "distribution_version": _distribution_version(),
        "runtime": {
            "host": runtime.host,
            "port": runtime.port,
            "db_path": runtime.db_path,
            "memories_dir": runtime.memories_dir,
            "memory_import_on_startup": False,
        },
        "privacy": {
            "summary_enabled": False,
            "summary_outbound_policy": "redact",
            "summary_allow_tool_arguments": False,
            "log_include_content": False,
        },
        "deployment": {
            "plugins": ["deepseek-harness", "deepseek-context"],
            "managed_by": "deepseek-harness install",
        },
    }
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)


def build_install_plan(
    *, environ: Mapping[str, str] | None = None, data_root: str | os.PathLike[str] | None = None
) -> InstallPlan:
    env = os.environ if environ is None else environ
    home = _home_path(env)
    hermes_home = home / ".hermes"
    root = Path(
        data_root or env.get(ENV_DATA_ROOT, DEFAULT_DATA_ROOT)
    ).expanduser().resolve()
    runtime = _runtime_config(env, data_root=root, hermes_home=hermes_home)
    paths = RuntimePaths.from_root(root)
    config_path = root / "config" / "config.yaml"
    harness_plugin = hermes_home / "plugins" / "deepseek-harness"
    context_plugin = hermes_home / "plugins" / "deepseek-context"

    desired_files = {
        harness_plugin / "__init__.py": _HARNESS_ADAPTER,
        harness_plugin / "plugin.yaml": _resource_text(
            "deepseek_harness.resources", "plugin.yaml"
        ),
        context_plugin / "__init__.py": _CONTEXT_ADAPTER,
        context_plugin / "plugin.yaml": _resource_text(
            "deepseek_context.resources", "plugin.yaml"
        ),
        config_path: _render_config(runtime),
    }
    desired_directories = (
        hermes_home,
        hermes_home / "plugins",
        harness_plugin,
        context_plugin,
        root,
        root / "config",
        root / "data",
        root / "backups",
    )
    missing = tuple(
        module
        for module in _REQUIRED_SERVER_MODULES
        if importlib.util.find_spec(module) is None
    )
    return InstallPlan(
        hermes_home=hermes_home,
        data_root=root,
        config_path=config_path,
        runtime_paths=paths,
        runtime_config=runtime,
        desired_files=desired_files,
        desired_directories=desired_directories,
        hermes_executable=shutil.which("hermes"),
        missing_dependencies=missing,
    )


def _mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def _preflight(plan: InstallPlan) -> None:
    for directory in plan.desired_directories:
        if directory.is_symlink():
            raise InstallConflictError(f"refusing symlink deployment directory: {directory}")
        if directory.exists() and not directory.is_dir():
            raise InstallConflictError(f"deployment directory is not a directory: {directory}")

    for path, content in plan.desired_files.items():
        if path.is_symlink():
            raise InstallConflictError(f"refusing symlink managed file: {path}")
        if not path.exists():
            continue
        if not path.is_file():
            raise InstallConflictError(f"managed path is not a regular file: {path}")
        try:
            existing = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise InstallConflictError(f"cannot read existing managed file: {path}") from exc
        if existing != content:
            raise InstallConflictError(
                f"existing file differs from the managed same-version content: {path}"
            )


def _ensure_directory(path: Path, created_directories: list[Path]) -> bool:
    if path.exists():
        return False
    missing: list[Path] = []
    current = path
    while not current.exists():
        missing.append(current)
        parent = current.parent
        if parent == current:
            break
        current = parent
    for directory in reversed(missing):
        directory.mkdir()
        if os.name != "nt":
            directory.chmod(0o700)
        created_directories.append(directory)
    return bool(missing)


def _atomic_create(path: Path, content: str, created_files: list[Path]) -> bool:
    if path.exists():
        return False
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}-", suffix=".tmp", dir=path.parent
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
        if os.name != "nt":
            path.chmod(0o600)
        created_files.append(path)
        return True
    except Exception:
        try:
            os.close(descriptor)
        except OSError:
            pass
        temporary.unlink(missing_ok=True)
        raise


def _remove_if_created(path: Path, existed_before: bool) -> None:
    if existed_before or not path.exists() or path.is_symlink():
        return
    if path.is_file():
        path.unlink()
    elif path.is_dir():
        try:
            path.rmdir()
        except OSError:
            pass


def _rollback(
    plan: InstallPlan,
    *,
    supervisor: Supervisor,
    runtime_state_existed: bool,
    created_files: list[Path],
    created_directories: list[Path],
    runtime_artifacts_before: dict[Path, bool],
) -> None:
    failures: list[str] = []
    if not runtime_state_existed and plan.runtime_paths.state_file.exists():
        try:
            supervisor.stop(timeout=5)
        except Exception as exc:  # pragma: no cover - failure injection owns this path
            failures.append(f"server stop failed: {exc}")

    for path in reversed(created_files):
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            failures.append(f"could not remove {path}: {exc}")

    for path, existed_before in runtime_artifacts_before.items():
        try:
            _remove_if_created(path, existed_before)
        except OSError as exc:
            failures.append(f"could not restore {path}: {exc}")

    for directory in reversed(created_directories):
        try:
            directory.rmdir()
        except OSError:
            pass

    if failures:
        raise InstallRollbackError("; ".join(failures))


def execute_install(plan: InstallPlan, *, dry_run: bool, timeout: float = 20) -> dict[str, Any]:
    payload = plan.public_dict(dry_run=dry_run)
    if dry_run:
        return payload

    _preflight(plan)
    created_files: list[Path] = []
    created_directories: list[Path] = []
    supervisor = Supervisor(plan.runtime_paths)
    runtime_state_existed = plan.runtime_paths.state_file.exists()
    db_path = Path(plan.runtime_config.db_path).expanduser().resolve()
    runtime_artifacts_before = {
        plan.runtime_paths.state_file: plan.runtime_paths.state_file.exists(),
        plan.runtime_paths.lock_file: plan.runtime_paths.lock_file.exists(),
        plan.runtime_paths.log_file: plan.runtime_paths.log_file.exists(),
        plan.runtime_paths.runtime_dir: plan.runtime_paths.runtime_dir.exists(),
        plan.runtime_paths.logs_dir: plan.runtime_paths.logs_dir.exists(),
        db_path: db_path.exists(),
        db_path.parent: db_path.parent.exists(),
    }

    changed = False
    try:
        for directory in plan.desired_directories:
            changed = _ensure_directory(directory, created_directories) or changed
        for path, content in plan.desired_files.items():
            changed = _atomic_create(path, content, created_files) or changed

        status = supervisor.start(plan.runtime_config, timeout=timeout)
        if not status.running or not status.healthy or not status.ready:
            raise InstallError("Harness Server did not reach the ready state")
    except Exception as exc:
        try:
            _rollback(
                plan,
                supervisor=supervisor,
                runtime_state_existed=runtime_state_existed,
                created_files=created_files,
                created_directories=created_directories,
                runtime_artifacts_before=runtime_artifacts_before,
            )
        except InstallRollbackError:
            raise
        if isinstance(exc, InstallConflictError):
            raise
        raise InstallFailedError(
            f"install failed and transaction changes were rolled back: {exc}"
        ) from exc

    result = plan.public_dict(dry_run=False)
    result.update(
        {
            "state": "installed",
            "message": (
                "installation completed"
                if changed
                else "same version is already installed; deployment reused"
            ),
            "changed": changed,
            "server": status.to_dict(),
            "server_pid": status.pid,
            "healthy": status.healthy,
            "ready": status.ready,
        }
    )
    return result


def install(
    *,
    dry_run: bool = False,
    timeout: float = 20,
    environ: Mapping[str, str] | None = None,
    data_root: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    plan = build_install_plan(environ=environ, data_root=data_root)
    return execute_install(plan, dry_run=dry_run, timeout=timeout)


__all__ = [
    "ENV_DATA_ROOT",
    "InstallConflictError",
    "InstallError",
    "InstallFailedError",
    "InstallPlan",
    "InstallRollbackError",
    "build_install_plan",
    "execute_install",
    "install",
]
