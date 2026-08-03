"""RUN-001/002 process, environment and supervision tests."""

from __future__ import annotations

import importlib.metadata
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from harness_server.config import RUNTIME_ENV_VARS, RuntimeConfig
from harness_server.runtime import (
    RuntimePaths,
    RuntimeState,
    file_mode,
    read_state,
    remove_state,
    write_state,
)
from harness_server.server import create_app
from harness_server.supervisor import (
    PortInUseError,
    ProcessOwnershipError,
    StartError,
    Supervisor,
)


class BrokenStorage:
    db_path = "/secret/path/that/must/not/leak.db"

    def _connection(self):
        raise RuntimeError("sensitive storage failure detail")


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _cli_command(
    action: str,
    *,
    data_root: Path,
    port: int | None = None,
    db_path: Path | None = None,
    memories_dir: Path | None = None,
) -> list[str]:
    command = [
        sys.executable,
        "-m",
        "deepseek_harness.cli",
        "server",
        action,
        "--data-root",
        str(data_root),
        "--json",
    ]
    if action in {"start", "restart"}:
        assert port is not None and db_path is not None and memories_dir is not None
        command.extend(
            [
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--db-path",
                str(db_path),
                "--memories-dir",
                str(memories_dir),
                "--no-import-memories",
            ]
        )
    return command


def _run_cli(command: list[str], *, cwd: Path, env: dict[str, str]) -> tuple[int, dict]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=45,
    )
    rendered = completed.stdout.strip() or completed.stderr.strip()
    assert rendered, (completed.returncode, completed.stdout, completed.stderr)
    payload = json.loads(rendered.splitlines()[-1])
    return completed.returncode, payload


def test_server_import_is_side_effect_free(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    db_path = tmp_path / "must-not-exist.db"
    memories = tmp_path / "memories"
    memories.mkdir()
    (memories / "SENTINEL.md").write_text("不得在 import 阶段读取此文件", encoding="utf-8")

    env = {
        **os.environ,
        "HOME": str(home),
        "USERPROFILE": str(home),
        "HARNESS_DB_PATH": str(db_path),
        "HARNESS_MEMORIES_DIR": str(memories),
        "HARNESS_IMPORT_MEMORIES": "1",
        "PYTHONNOUSERSITE": "1",
    }
    completed = subprocess.run(
        [sys.executable, "-I", "-c", "import harness_server.server; print('import-ok')"],
        cwd=tmp_path,
        env=env,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert completed.returncode == 0, completed.stdout
    assert completed.stdout.strip() == "import-ok"
    assert not db_path.exists()
    assert not (home / ".hermes").exists()


def test_runtime_environment_contract_and_loopback_policy(tmp_path: Path) -> None:
    env = {
        "HARNESS_HOST": "127.0.0.1",
        "HARNESS_PORT": "9123",
        "HARNESS_DB_PATH": str(tmp_path / "runtime.db"),
        "HARNESS_IMPORT_MEMORIES": "true",
        "HARNESS_MEMORIES_DIR": str(tmp_path / "memories"),
        "HARNESS_SUMMARY_ENABLED": "false",
        "HARNESS_SUMMARY_OUTBOUND_POLICY": "off",
        "HARNESS_SUMMARY_ALLOW_TOOL_ARGUMENTS": "false",
        "HARNESS_LOG_INCLUDE_CONTENT": "false",
    }
    runtime = RuntimeConfig.from_env(env)
    assert RUNTIME_ENV_VARS == frozenset(env)
    assert runtime.host == "127.0.0.1"
    assert runtime.port == 9123
    assert runtime.server_url == "http://127.0.0.1:9123"
    assert runtime.import_memories is True
    assert runtime.db_path == str(tmp_path / "runtime.db")
    assert runtime.summary_enabled is False
    assert runtime.summary_allow_tool_args is False
    assert runtime.log_include_content is False

    with pytest.raises(ValueError, match="loopback"):
        RuntimeConfig.from_env({"HARNESS_HOST": "0.0.0.0"})
    with pytest.raises(ValueError, match="integer"):
        RuntimeConfig.from_env({"HARNESS_PORT": "invalid"})
    with pytest.raises(ValueError, match="boolean"):
        RuntimeConfig.from_env({"HARNESS_IMPORT_MEMORIES": "maybe"})


def test_legacy_runtime_environment_names_are_absent_and_ignored() -> None:
    legacy_port = "HARNESS_" + "SERVER_PORT"
    legacy_url = "HARNESS_" + "SERVER_URL"
    runtime = RuntimeConfig.from_env(
        {legacy_port: "9999", legacy_url: "http://127.0.0.1:9999"}
    )
    assert runtime.port == 8200
    assert runtime.server_url == "http://127.0.0.1:8200"

    for root_name in ("src", "tests"):
        for path in (Path(__file__).resolve().parents[1] / root_name).rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            assert legacy_port not in text, path
            assert legacy_url not in text, path


def test_probe_failure_isolation_and_redaction(tmp_path: Path) -> None:
    runtime = RuntimeConfig(db_path=str(tmp_path / "unused.db"))
    with TestClient(create_app(runtime, storage=BrokenStorage())) as client:
        health = client.get("/health")
        ready = client.get("/ready")
        version = client.get("/version")

    assert health.status_code == 200
    assert health.json() == {"status": "ok", "service": "harness-server"}
    assert ready.status_code == 503
    assert ready.json() == {"status": "not_ready", "reason": "storage_unavailable"}
    assert version.status_code == 200

    rendered = json.dumps([health.json(), ready.json(), version.json()], ensure_ascii=False)
    assert "secret" not in rendered.lower()
    assert str(tmp_path) not in rendered
    assert "sensitive storage failure detail" not in rendered


def test_real_process_reaches_health_ready_and_version(tmp_path: Path) -> None:
    port = _free_port()
    home = tmp_path / "home"
    home.mkdir()
    db_path = tmp_path / "runtime.db"
    env = {
        **os.environ,
        "HOME": str(home),
        "USERPROFILE": str(home),
        "HARNESS_HOST": "127.0.0.1",
        "HARNESS_PORT": str(port),
        "HARNESS_DB_PATH": str(db_path),
        "HARNESS_IMPORT_MEMORIES": "0",
        "HARNESS_MEMORIES_DIR": str(tmp_path / "memories"),
        "PYTHONUNBUFFERED": "1",
    }
    process = subprocess.Popen(
        [sys.executable, "-m", "harness_server.server"],
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    base_url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 25
    last_error = "server did not respond"
    try:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                output = process.stdout.read() if process.stdout else ""
                raise AssertionError(f"server exited early ({process.returncode}):\n{output}")
            try:
                response = httpx.get(f"{base_url}/health", timeout=0.5)
                if response.status_code == 200:
                    break
            except Exception as exc:  # pragma: no cover - diagnostic only
                last_error = str(exc)
            time.sleep(0.1)
        else:
            raise AssertionError(last_error)

        health = httpx.get(f"{base_url}/health", timeout=2)
        ready = httpx.get(f"{base_url}/ready", timeout=2)
        version = httpx.get(f"{base_url}/version", timeout=2)
        assert health.status_code == 200
        assert health.json() == {"status": "ok", "service": "harness-server"}
        assert ready.status_code == 200
        assert ready.json() == {"status": "ready"}
        assert version.status_code == 200
        assert version.json()["version"] == "3.0.0b1"
        assert version.json()["api_version"] == "1"
        assert db_path.is_file()
        rendered = health.text + ready.text + version.text
        assert str(tmp_path) not in rendered
        assert "db_path" not in rendered
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def test_console_script_metadata_is_installed() -> None:
    entry_points = importlib.metadata.entry_points().select(
        group="console_scripts",
        name="deepseek-harness",
    )
    assert len(entry_points) == 1
    assert next(iter(entry_points)).value == "deepseek_harness.cli:main"


@pytest.mark.skipif(os.name == "nt", reason="Windows process matrix is later work")
def test_concurrent_cli_start_restart_status_and_idempotent_stop(tmp_path: Path) -> None:
    data_root = tmp_path / "product"
    home = tmp_path / "home"
    memories = tmp_path / "memories"
    home.mkdir()
    memories.mkdir()
    db_path = tmp_path / "runtime.db"
    port = _free_port()
    env = {
        **os.environ,
        "HOME": str(home),
        "USERPROFILE": str(home),
        "PYTHONNOUSERSITE": "1",
        "PYTHONUNBUFFERED": "1",
    }
    start_command = _cli_command(
        "start",
        data_root=data_root,
        port=port,
        db_path=db_path,
        memories_dir=memories,
    )
    first = subprocess.Popen(
        start_command,
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    second = subprocess.Popen(
        start_command,
        cwd=tmp_path,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    first_stdout, first_stderr = first.communicate(timeout=45)
    second_stdout, second_stderr = second.communicate(timeout=45)
    assert first.returncode == 0, first_stderr
    assert second.returncode == 0, second_stderr
    first_payload = json.loads(first_stdout.strip().splitlines()[-1])
    second_payload = json.loads(second_stdout.strip().splitlines()[-1])
    assert first_payload["pid"] == second_payload["pid"]
    assert first_payload["ready"] is True
    assert second_payload["ready"] is True

    paths = RuntimePaths.from_root(data_root)
    initial_state = read_state(paths)
    assert initial_state is not None
    assert initial_state.pid == first_payload["pid"]
    assert file_mode(paths.data_root) == 0o700
    assert file_mode(paths.runtime_dir) == 0o700
    assert file_mode(paths.logs_dir) == 0o700
    assert file_mode(paths.state_file) == 0o600
    assert file_mode(paths.lock_file) == 0o600
    assert file_mode(paths.log_file) == 0o600
    assert paths.log_file.read_text(encoding="utf-8", errors="replace").strip()

    status_code, status_payload = _run_cli(
        _cli_command("status", data_root=data_root), cwd=tmp_path, env=env
    )
    assert status_code == 0
    assert status_payload["pid"] == initial_state.pid
    assert status_payload["healthy"] is True
    assert status_payload["ready"] is True

    restart_code, restart_payload = _run_cli(
        _cli_command(
            "restart",
            data_root=data_root,
            port=port,
            db_path=db_path,
            memories_dir=memories,
        ),
        cwd=tmp_path,
        env=env,
    )
    assert restart_code == 0
    restarted_state = read_state(paths)
    assert restarted_state is not None
    assert restarted_state.instance_id != initial_state.instance_id
    assert restart_payload["healthy"] is True
    assert restart_payload["ready"] is True

    stop_code, stopped = _run_cli(
        _cli_command("stop", data_root=data_root), cwd=tmp_path, env=env
    )
    assert stop_code == 0
    assert stopped["state"] == "stopped"
    assert not paths.state_file.exists()

    second_stop_code, stopped_again = _run_cli(
        _cli_command("stop", data_root=data_root), cwd=tmp_path, env=env
    )
    assert second_stop_code == 0
    assert stopped_again["state"] == "stopped"
    assert "already stopped" in stopped_again["message"]


def test_supervisor_rejects_foreign_pid_without_signaling(tmp_path: Path) -> None:
    paths = RuntimePaths.from_root(tmp_path / "foreign")
    state = RuntimeState.create(
        instance_id="definitely-not-in-this-pytest-command",
        pid=os.getpid(),
        host="127.0.0.1",
        port=_free_port(),
        version="3.0.0b1",
        log_path=str(paths.log_file),
        db_path=str(tmp_path / "foreign.db"),
    )
    write_state(paths, state)
    try:
        with pytest.raises(ProcessOwnershipError, match="refusing to signal"):
            Supervisor(paths).stop(timeout=0.1)
        assert read_state(paths) == state
        assert os.getpid() == state.pid
    finally:
        remove_state(paths)


def test_supervisor_rejects_unmanaged_port(tmp_path: Path) -> None:
    port = _free_port()
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", port))
    listener.listen(1)
    try:
        config = RuntimeConfig(
            port=port,
            db_path=str(tmp_path / "port.db"),
            memories_dir=str(tmp_path / "memories"),
        )
        paths = RuntimePaths.from_root(tmp_path / "port-root")
        with pytest.raises(PortInUseError, match="already in use"):
            Supervisor(paths).start(config, timeout=1)
        assert not paths.state_file.exists()
    finally:
        listener.close()


@pytest.mark.skipif(os.name == "nt", reason="Windows process matrix is later work")
def test_failed_start_keeps_diagnosable_stderr_log(tmp_path: Path) -> None:
    invalid_parent = tmp_path / "not-a-directory"
    invalid_parent.write_text("file blocks SQLite parent directory", encoding="utf-8")
    config = RuntimeConfig(
        port=_free_port(),
        db_path=str(invalid_parent / "runtime.db"),
        memories_dir=str(tmp_path / "memories"),
    )
    paths = RuntimePaths.from_root(tmp_path / "failed-root")
    with pytest.raises(StartError) as captured:
        Supervisor(paths).start(config, timeout=5)

    error = captured.value
    assert error.log_path == str(paths.log_file)
    assert paths.log_file.is_file()
    assert paths.log_file.read_text(encoding="utf-8", errors="replace").strip()
    assert error.log_tail.strip()
    assert not paths.state_file.exists()
