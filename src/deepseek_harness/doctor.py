"""Read-only environment diagnostics for the installed Harness distribution."""

from __future__ import annotations

import importlib.util
import os
import re
import shutil
import socket
import sqlite3
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import httpx
import yaml

from harness_server.runtime import (
    RuntimeStateError,
    process_is_owned,
    read_state,
)

from .installer import InstallPlan, build_install_plan

DOCTOR_OK = 0
DOCTOR_FAILED = 1
DOCTOR_MISSING_DEPENDENCY = 3
DOCTOR_PORT_CONFLICT = 4
DOCTOR_UNSUPPORTED = 5

SUPPORTED_PACKAGE_PYTHON = ">=3.10,<3.13"
SUPPORTED_HERMES_PYTHON = "3.11-3.12"
SUPPORTED_HERMES_VERSION = "0.19.0"
REQUIRED_RUNTIME_MODULES = (
    "fastapi",
    "uvicorn",
    "pydantic",
    "yaml",
    "httpx",
)

DependencyFinder = Callable[[str], object | None]
HermesLocator = Callable[[str], str | None]
HermesVersionReader = Callable[[str], str | None]
PortProbe = Callable[[str, int], bool]
EndpointProbe = Callable[[str, str], tuple[int | None, dict[str, Any] | None]]


@dataclass(frozen=True)
class DoctorCheck:
    check_id: str
    status: str
    message: str
    recovery: str | None = None
    failure_class: str | None = None
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.check_id,
            "status": self.status,
            "message": self.message,
        }
        if self.recovery:
            payload["recovery"] = self.recovery
        if self.details:
            payload["details"] = self.details
        return payload


@dataclass(frozen=True)
class DoctorReport:
    checks: tuple[DoctorCheck, ...]
    exit_code: int

    @property
    def status(self) -> str:
        return "ok" if self.exit_code == DOCTOR_OK else "error"

    def to_dict(self) -> dict[str, Any]:
        passed = sum(check.status == "pass" for check in self.checks)
        failed = sum(check.status == "fail" for check in self.checks)
        return {
            "schema_version": 1,
            "status": self.status,
            "exit_code": self.exit_code,
            "summary": {
                "total": len(self.checks),
                "passed": passed,
                "failed": failed,
            },
            "checks": [check.to_dict() for check in self.checks],
        }


def _pass(
    check_id: str, message: str, *, details: dict[str, Any] | None = None
) -> DoctorCheck:
    return DoctorCheck(check_id, "pass", message, details=details)


def _fail(
    check_id: str,
    message: str,
    recovery: str,
    *,
    failure_class: str = "generic",
    details: dict[str, Any] | None = None,
) -> DoctorCheck:
    return DoctorCheck(
        check_id,
        "fail",
        message,
        recovery=recovery,
        failure_class=failure_class,
        details=details,
    )


def _exit_code(checks: Sequence[DoctorCheck]) -> int:
    failures = {check.failure_class for check in checks if check.status == "fail"}
    if "unsupported" in failures:
        return DOCTOR_UNSUPPORTED
    if "missing_dependency" in failures:
        return DOCTOR_MISSING_DEPENDENCY
    if "port_conflict" in failures:
        return DOCTOR_PORT_CONFLICT
    if failures:
        return DOCTOR_FAILED
    return DOCTOR_OK


def _default_dependency_finder(name: str) -> object | None:
    return importlib.util.find_spec(name)


def _default_hermes_version_reader(executable: str) -> str | None:
    try:
        completed = subprocess.run(
            [executable, "--version"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=3,
            env={"PATH": os.environ.get("PATH", "")},
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    match = re.search(r"(?<!\d)(\d+\.\d+\.\d+)(?!\d)", completed.stdout)
    return match.group(1) if match else None


def _default_port_probe(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.25):
            return True
    except OSError:
        return False


def _default_endpoint_probe(
    base_url: str, path: str
) -> tuple[int | None, dict[str, Any] | None]:
    try:
        with httpx.Client(timeout=1.0, trust_env=False) as client:
            response = client.get(f"{base_url}{path}")
            try:
                payload = response.json()
            except ValueError:
                payload = None
            return response.status_code, payload if isinstance(payload, dict) else None
    except Exception:
        return None, None


def _python_check(version: tuple[int, int, int]) -> DoctorCheck:
    rendered = ".".join(str(value) for value in version)
    if (3, 10, 0) <= version < (3, 13, 0):
        return _pass(
            "python",
            "Python is within the package/core support range",
            details={"detected": rendered, "supported": SUPPORTED_PACKAGE_PYTHON},
        )
    return _fail(
        "python",
        "Python is outside the supported package/core range",
        f"Use Python 3.10, 3.11 or 3.12; supported range is {SUPPORTED_PACKAGE_PYTHON}.",
        failure_class="unsupported",
        details={"detected": rendered, "supported": SUPPORTED_PACKAGE_PYTHON},
    )


def _dependency_check(finder: DependencyFinder) -> DoctorCheck:
    missing = [name for name in REQUIRED_RUNTIME_MODULES if finder(name) is None]
    if not missing:
        return _pass(
            "dependencies",
            "Required runtime modules are importable",
            details={"required": list(REQUIRED_RUNTIME_MODULES)},
        )
    return _fail(
        "dependencies",
        "Required runtime modules are missing",
        "Install the distribution with the server or all extra, then rerun Doctor.",
        failure_class="missing_dependency",
        details={"missing": missing, "required": list(REQUIRED_RUNTIME_MODULES)},
    )


def _hermes_check(
    *,
    python_version: tuple[int, int, int],
    locator: HermesLocator,
    version_reader: HermesVersionReader,
) -> DoctorCheck:
    executable = locator("hermes")
    if not executable:
        return _fail(
            "hermes",
            "Hermes executable was not detected",
            "Install Hermes 0.19.0 and ensure the hermes executable is on PATH.",
            failure_class="missing_dependency",
            details={
                "detected": "not_found",
                "supported_version": SUPPORTED_HERMES_VERSION,
                "supported_python": SUPPORTED_HERMES_PYTHON,
            },
        )
    version = version_reader(executable)
    if version != SUPPORTED_HERMES_VERSION:
        return _fail(
            "hermes",
            "Hermes is outside the selected support matrix",
            f"Use Hermes {SUPPORTED_HERMES_VERSION} with Python {SUPPORTED_HERMES_PYTHON}.",
            failure_class="unsupported",
            details={
                "detected": version or "unknown",
                "supported_version": SUPPORTED_HERMES_VERSION,
                "supported_python": SUPPORTED_HERMES_PYTHON,
            },
        )
    if python_version[:2] not in {(3, 11), (3, 12)}:
        return _fail(
            "hermes",
            "The detected Python/Hermes combination is not supported",
            f"Run Hermes {SUPPORTED_HERMES_VERSION} with Python {SUPPORTED_HERMES_PYTHON}; Python 3.10 is package/core only.",
            failure_class="unsupported",
            details={
                "detected": version,
                "python": ".".join(str(value) for value in python_version),
                "supported_version": SUPPORTED_HERMES_VERSION,
                "supported_python": SUPPORTED_HERMES_PYTHON,
            },
        )
    return _pass(
        "hermes",
        "Hermes matches the selected support matrix",
        details={
            "detected": version,
            "supported_version": SUPPORTED_HERMES_VERSION,
            "supported_python": SUPPORTED_HERMES_PYTHON,
        },
    )


def _managed_file_check(
    check_id: str, label: str, expected: dict[Path, str]
) -> DoctorCheck:
    missing: list[str] = []
    mismatched: list[str] = []
    for path, content in expected.items():
        logical = path.name
        if not path.is_file() or path.is_symlink():
            missing.append(logical)
            continue
        try:
            if path.read_text(encoding="utf-8") != content:
                mismatched.append(logical)
        except OSError:
            mismatched.append(logical)
    if not missing and not mismatched:
        return _pass(check_id, f"{label} adapter is installed and matches the package")
    return _fail(
        check_id,
        f"{label} adapter is missing or differs from the installed package",
        "Run deepseek-harness install after preserving any user-managed conflicting files.",
        details={"missing": missing, "mismatched": mismatched},
    )


def _config_check(plan: InstallPlan) -> DoctorCheck:
    path = plan.config_path
    if not path.is_file() or path.is_symlink():
        return _fail(
            "config",
            "Product configuration is not installed",
            "Run deepseek-harness install to create the managed configuration.",
        )
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return _fail(
            "config",
            "Product configuration is unreadable",
            "Restore a valid managed configuration or rerun install after preserving the file.",
        )
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        return _fail(
            "config",
            "Product configuration schema is unsupported",
            "Use the configuration generated by the installed distribution version.",
            failure_class="unsupported",
            details={"supported_schema": 1},
        )
    runtime = payload.get("runtime") if isinstance(payload.get("runtime"), dict) else {}
    privacy = payload.get("privacy") if isinstance(payload.get("privacy"), dict) else {}
    expected = plan.runtime_config
    valid = (
        runtime.get("host") == expected.host
        and runtime.get("port") == expected.port
        and runtime.get("db_path") == expected.db_path
        and runtime.get("memory_import_on_startup") is False
        and privacy.get("summary_enabled") is False
        and privacy.get("summary_allow_tool_arguments") is False
        and privacy.get("log_include_content") is False
    )
    if not valid:
        return _fail(
            "config",
            "Product configuration does not match the safe installed contract",
            "Review the configuration and rerun install only after preserving intentional user changes.",
        )
    return _pass("config", "Product configuration matches the safe installed contract")


def _server_and_port_checks(
    plan: InstallPlan,
    *,
    port_probe: PortProbe,
    endpoint_probe: EndpointProbe,
) -> tuple[DoctorCheck, DoctorCheck]:
    paths = plan.runtime_paths
    port_open = port_probe(plan.runtime_config.host, plan.runtime_config.port)
    if not paths.state_file.exists():
        if port_open:
            return (
                _fail(
                    "server",
                    "No managed Server state exists",
                    "Stop the unmanaged listener or choose another HARNESS_PORT before starting the Server.",
                ),
                _fail(
                    "port",
                    "Configured port is occupied by an unmanaged process",
                    "Stop the process using the configured port or select a free loopback port.",
                    failure_class="port_conflict",
                    details={"host": plan.runtime_config.host, "port": plan.runtime_config.port},
                ),
            )
        return (
            _fail(
                "server",
                "Managed Server is not running",
                "Run deepseek-harness install or deepseek-harness server start.",
            ),
            _pass(
                "port",
                "Configured loopback port is available",
                details={"host": plan.runtime_config.host, "port": plan.runtime_config.port},
            ),
        )

    try:
        state = read_state(paths)
    except RuntimeStateError:
        return (
            _fail(
                "server",
                "Managed Server state is unreadable",
                "Preserve the state file for diagnosis; do not signal any PID until ownership is proven.",
            ),
            _fail(
                "port",
                "Port ownership cannot be proven from the current state",
                "Inspect the configured loopback port without stopping an unverified process.",
            ),
        )
    if state is None or not process_is_owned(state):
        return (
            _fail(
                "server",
                "Managed Server process ownership cannot be proven",
                "Do not signal the PID; preserve state and inspect the process identity.",
            ),
            _fail(
                "port",
                "Configured port is not owned by a verified Harness Server",
                "Inspect the listener and resolve the ownership conflict manually.",
                failure_class="port_conflict" if port_open else "generic",
                details={"host": plan.runtime_config.host, "port": plan.runtime_config.port},
            ),
        )

    base_url = f"http://{state.host}:{state.port}"
    health_code, health = endpoint_probe(base_url, "/health")
    ready_code, ready = endpoint_probe(base_url, "/ready")
    version_code, version = endpoint_probe(base_url, "/version")
    server_ok = (
        port_open
        and health_code == 200
        and health == {"status": "ok", "service": "harness-server"}
        and ready_code == 200
        and ready == {"status": "ready"}
        and version_code == 200
        and isinstance(version, dict)
        and version.get("version") == state.version
        and version.get("api_version") == "1"
    )
    if server_ok:
        return (
            _pass(
                "server",
                "Managed Server ownership and health/ready/version probes are valid",
                details={"version": state.version, "api_version": "1"},
            ),
            _pass(
                "port",
                "Configured port is owned by the verified Harness Server",
                details={"host": state.host, "port": state.port},
            ),
        )
    return (
        _fail(
            "server",
            "Managed Server probes are not ready or version-consistent",
            "Inspect the user-accessible Server log and restart only through the Supervisor CLI.",
        ),
        _fail(
            "port",
            "Configured port does not expose a verified ready Harness Server",
            "Inspect the listener and Server log without signaling an unverified PID.",
            failure_class="port_conflict" if port_open else "generic",
            details={"host": state.host, "port": state.port},
        ),
    )


def _database_check(plan: InstallPlan) -> DoctorCheck:
    path = Path(plan.runtime_config.db_path).expanduser().resolve()
    if not path.is_file() or path.is_symlink():
        return _fail(
            "database",
            "Harness database is not installed",
            "Run deepseek-harness install and verify the data directory is writable during installation.",
        )
    try:
        connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=1)
        try:
            connection.execute("SELECT 1").fetchone()
        finally:
            connection.close()
    except sqlite3.Error:
        return _fail(
            "database",
            "Harness database cannot be opened read-only",
            "Check file ownership, permissions and database integrity before retrying.",
        )
    return _pass("database", "Harness database opens successfully in read-only mode")


def _provider_check(environ: Mapping[str, str]) -> DoctorCheck:
    if environ.get("DEEPSEEK_API_KEY", "").strip():
        return _pass(
            "provider",
            "DeepSeek provider credentials are present",
            details={"api_key": "configured", "base_url": "configured" if environ.get("DEEPSEEK_BASE_URL") else "default"},
        )
    return _fail(
        "provider",
        "DeepSeek provider credentials are missing",
        "Set DEEPSEEK_API_KEY in the process environment; Doctor never prints the secret value.",
    )


def _permissions_check(plan: InstallPlan) -> DoctorCheck:
    if os.name == "nt":
        return _pass(
            "permissions",
            "POSIX mode validation is not applicable on Windows",
            details={"policy": "Windows ACL matrix is later work"},
        )
    directories = [
        plan.data_root,
        plan.data_root / "config",
        plan.data_root / "data",
        plan.runtime_paths.runtime_dir,
        plan.runtime_paths.logs_dir,
        plan.hermes_home / "plugins" / "deepseek-harness",
        plan.hermes_home / "plugins" / "deepseek-context",
    ]
    files = [
        plan.config_path,
        plan.runtime_paths.state_file,
        plan.runtime_paths.lock_file,
        plan.runtime_paths.log_file,
        *plan.desired_files.keys(),
    ]
    bad_directories = [
        path.name
        for path in directories
        if path.exists() and stat.S_IMODE(path.stat().st_mode) != 0o700
    ]
    bad_files = [
        path.name
        for path in files
        if path.exists() and stat.S_IMODE(path.stat().st_mode) != 0o600
    ]
    if not bad_directories and not bad_files:
        return _pass(
            "permissions",
            "Managed POSIX directories and files use private modes",
            details={"directory_mode": "0700", "file_mode": "0600"},
        )
    return _fail(
        "permissions",
        "Managed paths have non-private POSIX modes",
        "Restore managed directory mode 0700 and managed file mode 0600, then rerun Doctor.",
        details={"directories": sorted(set(bad_directories)), "files": sorted(set(bad_files))},
    )


def diagnose(
    *,
    environ: Mapping[str, str] | None = None,
    data_root: str | os.PathLike[str] | None = None,
    python_version: tuple[int, int, int] | None = None,
    dependency_finder: DependencyFinder = _default_dependency_finder,
    hermes_locator: HermesLocator = shutil.which,
    hermes_version_reader: HermesVersionReader = _default_hermes_version_reader,
    port_probe: PortProbe = _default_port_probe,
    endpoint_probe: EndpointProbe = _default_endpoint_probe,
) -> DoctorReport:
    """Return one deterministic diagnostic result without modifying product state."""
    env = os.environ if environ is None else environ
    version = python_version or tuple(sys.version_info[:3])
    plan = build_install_plan(environ=env, data_root=data_root)
    harness_root = plan.hermes_home / "plugins" / "deepseek-harness"
    context_root = plan.hermes_home / "plugins" / "deepseek-context"
    checks: list[DoctorCheck] = [
        _python_check(version),
        _dependency_check(dependency_finder),
        _hermes_check(
            python_version=version,
            locator=hermes_locator,
            version_reader=hermes_version_reader,
        ),
        _managed_file_check(
            "plugin",
            "Harness Plugin",
            {
                path: content
                for path, content in plan.desired_files.items()
                if path.parent == harness_root
            },
        ),
        _managed_file_check(
            "context",
            "Context Plugin",
            {
                path: content
                for path, content in plan.desired_files.items()
                if path.parent == context_root
            },
        ),
        _config_check(plan),
    ]
    checks.extend(
        _server_and_port_checks(
            plan,
            port_probe=port_probe,
            endpoint_probe=endpoint_probe,
        )
    )
    checks.extend(
        [
            _database_check(plan),
            _provider_check(env),
            _permissions_check(plan),
        ]
    )
    return DoctorReport(tuple(checks), _exit_code(checks))


def render_human(report: DoctorReport) -> str:
    """Render the same structured report used by JSON output."""
    payload = report.to_dict()
    lines = [
        f"status: {payload['status']}",
        f"exit_code: {payload['exit_code']}",
        (
            "summary: "
            f"{payload['summary']['passed']} passed, "
            f"{payload['summary']['failed']} failed"
        ),
    ]
    for check in report.checks:
        lines.append(f"[{check.status.upper()}] {check.check_id}: {check.message}")
        if check.recovery:
            lines.append(f"  recovery: {check.recovery}")
        if check.details:
            rendered = ", ".join(
                f"{key}={check.details[key]}" for key in sorted(check.details)
            )
            lines.append(f"  details: {rendered}")
    return "\n".join(lines)


__all__ = [
    "DOCTOR_FAILED",
    "DOCTOR_MISSING_DEPENDENCY",
    "DOCTOR_OK",
    "DOCTOR_PORT_CONFLICT",
    "DOCTOR_UNSUPPORTED",
    "DoctorCheck",
    "DoctorReport",
    "SUPPORTED_HERMES_PYTHON",
    "SUPPORTED_HERMES_VERSION",
    "SUPPORTED_PACKAGE_PYTHON",
    "diagnose",
    "render_human",
]
