"""Single-process supervision for the local Harness Server runtime."""

from __future__ import annotations

import importlib.metadata
import os
import signal
import socket
import subprocess
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from typing import Any

import httpx

from .config import RuntimeConfig
from .runtime import (
    ProcessLock,
    RuntimePaths,
    RuntimeState,
    RuntimeStateError,
    pid_is_alive,
    process_is_owned,
    read_state,
    remove_state,
    write_state,
)


class SupervisorError(RuntimeError):
    """Base class for diagnosable runtime supervision failures."""


class PortInUseError(SupervisorError):
    pass


class ProcessOwnershipError(SupervisorError):
    pass


class StartError(SupervisorError):
    def __init__(self, message: str, *, log_path: str, log_tail: str = ""):
        super().__init__(message)
        self.log_path = log_path
        self.log_tail = log_tail


@dataclass(frozen=True)
class RuntimeStatus:
    state: str
    running: bool
    healthy: bool
    ready: bool
    pid: int | None
    host: str | None
    port: int | None
    version: str | None
    started_at: str | None
    log_path: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Supervisor:
    """Own exactly one local Harness Server process for one runtime directory."""

    def __init__(self, paths: RuntimePaths | None = None):
        self.paths = paths or RuntimePaths.from_root()
        self._children: dict[int, subprocess.Popen] = {}

    @staticmethod
    def distribution_version() -> str:
        try:
            return importlib.metadata.version("oh-my-deepseek-harness")
        except importlib.metadata.PackageNotFoundError:
            return "3.0.0b1"

    def _base_url(self, host: str, port: int) -> str:
        rendered_host = f"[{host}]" if ":" in host else host
        return f"http://{rendered_host}:{port}"

    def _probe_json(self, host: str, port: int, path: str) -> tuple[int | None, Any]:
        try:
            with httpx.Client(timeout=0.75, trust_env=False) as client:
                response = client.get(f"{self._base_url(host, port)}{path}")
                try:
                    payload: Any = response.json()
                except ValueError:
                    payload = None
                return response.status_code, payload
        except httpx.HTTPError:
            return None, None

    def _port_is_open(self, host: str, port: int) -> bool:
        try:
            with socket.create_connection((host, port), timeout=0.3):
                return True
        except OSError:
            return False

    def _child_command(self, config: RuntimeConfig, instance_id: str) -> list[str]:
        command = [
            sys.executable,
            "-m",
            "harness_server.runtime",
            "child",
            "--instance-id",
            instance_id,
            "--host",
            config.host,
            "--port",
            str(config.port),
            "--db-path",
            config.db_path,
            "--memories-dir",
            config.memories_dir,
        ]
        if config.import_memories:
            command.append("--import-memories")
        return command

    def _open_log(self):
        self.paths.ensure()
        descriptor = os.open(
            self.paths.log_file,
            os.O_WRONLY | os.O_CREAT | os.O_APPEND,
            0o600,
        )
        if os.name != "nt":
            self.paths.log_file.chmod(0o600)
        return os.fdopen(descriptor, "ab", buffering=0)

    def _log_tail(self, maximum_bytes: int = 4096) -> str:
        try:
            with self.paths.log_file.open("rb") as handle:
                handle.seek(0, os.SEEK_END)
                size = handle.tell()
                handle.seek(max(0, size - maximum_bytes))
                return handle.read().decode("utf-8", errors="replace")
        except OSError:
            return ""

    def _status_unlocked(self, *, clean_stale: bool) -> RuntimeStatus:
        try:
            state = read_state(self.paths)
        except RuntimeStateError as exc:
            return RuntimeStatus(
                state="corrupt",
                running=False,
                healthy=False,
                ready=False,
                pid=None,
                host=None,
                port=None,
                version=None,
                started_at=None,
                log_path=str(self.paths.log_file),
                message=str(exc),
            )

        if state is None:
            return RuntimeStatus(
                state="stopped",
                running=False,
                healthy=False,
                ready=False,
                pid=None,
                host=None,
                port=None,
                version=None,
                started_at=None,
                log_path=str(self.paths.log_file),
                message="runtime is not running",
            )

        if not pid_is_alive(state.pid):
            if clean_stale:
                remove_state(self.paths)
            return RuntimeStatus(
                state="stale",
                running=False,
                healthy=False,
                ready=False,
                pid=state.pid,
                host=state.host,
                port=state.port,
                version=state.version,
                started_at=state.started_at,
                log_path=state.log_path,
                message="stale runtime state: process is not alive",
            )

        if not process_is_owned(state):
            return RuntimeStatus(
                state="foreign",
                running=False,
                healthy=False,
                ready=False,
                pid=state.pid,
                host=state.host,
                port=state.port,
                version=state.version,
                started_at=state.started_at,
                log_path=state.log_path,
                message="PID is alive but is not the recorded Harness Server instance",
            )

        health_code, health_payload = self._probe_json(state.host, state.port, "/health")
        ready_code, ready_payload = self._probe_json(state.host, state.port, "/ready")
        version_code, version_payload = self._probe_json(state.host, state.port, "/version")

        healthy = (
            health_code == 200
            and isinstance(health_payload, dict)
            and health_payload.get("status") == "ok"
            and health_payload.get("service") == "harness-server"
            and version_code == 200
            and isinstance(version_payload, dict)
            and version_payload.get("version") == state.version
        )
        ready = (
            ready_code == 200
            and isinstance(ready_payload, dict)
            and ready_payload.get("status") == "ready"
        )
        return RuntimeStatus(
            state="running" if healthy else "degraded",
            running=True,
            healthy=healthy,
            ready=ready,
            pid=state.pid,
            host=state.host,
            port=state.port,
            version=state.version,
            started_at=state.started_at,
            log_path=state.log_path,
            message="runtime is ready" if healthy and ready else "runtime process is not ready",
        )

    def status(self) -> RuntimeStatus:
        with ProcessLock(self.paths):
            return self._status_unlocked(clean_stale=True)

    def _wait_for_exit(self, pid: int, timeout: float) -> bool:
        deadline = time.monotonic() + timeout
        child = self._children.get(pid)
        while time.monotonic() < deadline:
            if child is not None:
                if child.poll() is not None:
                    child.wait()
                    self._children.pop(pid, None)
                    return True
            elif not pid_is_alive(pid):
                return True
            time.sleep(0.05)
        return False

    def _terminate_child_handle(
        self,
        process: subprocess.Popen,
        *,
        timeout: float = 2,
    ) -> None:
        """Terminate only the exact child represented by this Popen handle."""
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired as exc:
                    raise SupervisorError(
                        "spawned Harness Server child did not exit after force kill"
                    ) from exc
        self._children.pop(process.pid, None)

    def _terminate_owned(self, state: RuntimeState, *, timeout: float) -> None:
        if not process_is_owned(state):
            raise ProcessOwnershipError(
                "refusing to signal a PID that is not the recorded Harness Server instance"
            )
        try:
            os.kill(state.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        if self._wait_for_exit(state.pid, timeout):
            return
        if not process_is_owned(state):
            raise ProcessOwnershipError(
                "process identity changed while waiting for shutdown; refusing force kill"
            )
        try:
            os.kill(state.pid, signal.SIGKILL)
        except ProcessLookupError:
            return
        if not self._wait_for_exit(state.pid, 3):
            raise SupervisorError("Harness Server did not exit after SIGKILL")

    def _cleanup_failed_start(self, state: RuntimeState) -> None:
        child = self._children.get(state.pid)
        if child is not None:
            self._terminate_child_handle(child)
            remove_state(self.paths)
            return
        if not pid_is_alive(state.pid):
            remove_state(self.paths)
            return
        if not process_is_owned(state):
            raise ProcessOwnershipError(
                "failed-start process identity changed; retaining state and refusing signal"
            )
        self._terminate_owned(state, timeout=2)
        if pid_is_alive(state.pid):
            raise SupervisorError(
                "failed-start Harness Server is still alive; retaining runtime state"
            )
        remove_state(self.paths)

    def _start_unlocked(
        self,
        config: RuntimeConfig,
        *,
        timeout: float,
    ) -> RuntimeStatus:
        current = self._status_unlocked(clean_stale=True)
        if current.state == "running" and current.ready:
            return RuntimeStatus(**{**current.to_dict(), "message": "runtime already running"})
        if current.state == "foreign":
            raise ProcessOwnershipError(current.message)
        if current.running:
            raise StartError(
                "an owned Harness Server process exists but is not ready; use restart",
                log_path=current.log_path,
                log_tail=self._log_tail(),
            )
        if current.state == "corrupt":
            raise RuntimeStateError(current.message)

        if self._port_is_open(config.host, config.port):
            raise PortInUseError(
                f"port {config.host}:{config.port} is already in use by an unmanaged process"
            )

        self.paths.ensure()
        instance_id = uuid.uuid4().hex
        command = self._child_command(config, instance_id)
        log_handle = self._open_log()
        try:
            process = subprocess.Popen(
                command,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                close_fds=True,
                start_new_session=True,
            )
        finally:
            log_handle.close()

        self._children[process.pid] = process
        try:
            state = RuntimeState.create(
                instance_id=instance_id,
                pid=process.pid,
                host=config.host,
                port=config.port,
                version=self.distribution_version(),
                log_path=str(self.paths.log_file),
                db_path=config.db_path,
            )
        except Exception:
            self._terminate_child_handle(process)
            raise
        try:
            write_state(self.paths, state)
        except Exception:
            self._cleanup_failed_start(state)
            raise

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if process.poll() is not None:
                process.wait()
                self._children.pop(process.pid, None)
                remove_state(self.paths)
                raise StartError(
                    f"Harness Server exited during startup with code {process.returncode}",
                    log_path=str(self.paths.log_file),
                    log_tail=self._log_tail(),
                )
            status = self._status_unlocked(clean_stale=False)
            if status.state == "running" and status.ready:
                return status
            if status.state == "foreign":
                self._cleanup_failed_start(state)
                raise ProcessOwnershipError(status.message)
            time.sleep(0.1)

        self._cleanup_failed_start(state)
        raise StartError(
            "Harness Server did not become ready before timeout",
            log_path=str(self.paths.log_file),
            log_tail=self._log_tail(),
        )

    def start(
        self,
        config: RuntimeConfig | None = None,
        *,
        timeout: float = 20,
    ) -> RuntimeStatus:
        runtime = config or RuntimeConfig.from_env()
        with ProcessLock(self.paths):
            return self._start_unlocked(runtime, timeout=timeout)

    def _stop_unlocked(self, *, timeout: float) -> RuntimeStatus:
        state = read_state(self.paths)
        if state is None:
            return RuntimeStatus(
                state="stopped",
                running=False,
                healthy=False,
                ready=False,
                pid=None,
                host=None,
                port=None,
                version=None,
                started_at=None,
                log_path=str(self.paths.log_file),
                message="runtime already stopped",
            )
        if not pid_is_alive(state.pid):
            remove_state(self.paths)
            return RuntimeStatus(
                state="stopped",
                running=False,
                healthy=False,
                ready=False,
                pid=state.pid,
                host=state.host,
                port=state.port,
                version=state.version,
                started_at=state.started_at,
                log_path=state.log_path,
                message="stale runtime state removed",
            )
        self._terminate_owned(state, timeout=timeout)
        remove_state(self.paths)
        return RuntimeStatus(
            state="stopped",
            running=False,
            healthy=False,
            ready=False,
            pid=state.pid,
            host=state.host,
            port=state.port,
            version=state.version,
            started_at=state.started_at,
            log_path=state.log_path,
            message="runtime stopped",
        )

    def stop(self, *, timeout: float = 10) -> RuntimeStatus:
        with ProcessLock(self.paths):
            return self._stop_unlocked(timeout=timeout)

    def restart(
        self,
        config: RuntimeConfig | None = None,
        *,
        stop_timeout: float = 10,
        start_timeout: float = 20,
    ) -> RuntimeStatus:
        runtime = config or RuntimeConfig.from_env()
        with ProcessLock(self.paths):
            self._stop_unlocked(timeout=stop_timeout)
            return self._start_unlocked(runtime, timeout=start_timeout)
