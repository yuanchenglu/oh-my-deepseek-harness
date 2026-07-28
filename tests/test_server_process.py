"""RUN-001 process, import-side-effect and environment-contract tests."""

from __future__ import annotations

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
from harness_server.server import create_app


class BrokenStorage:
    db_path = "/secret/path/that/must/not/leak.db"

    def _connection(self):
        raise RuntimeError("sensitive storage failure detail")


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


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
        [
            sys.executable,
            "-I",
            "-c",
            "import harness_server.server; print('import-ok')",
        ],
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
    }
    runtime = RuntimeConfig.from_env(env)
    assert RUNTIME_ENV_VARS == frozenset(env)
    assert runtime.host == "127.0.0.1"
    assert runtime.port == 9123
    assert runtime.server_url == "http://127.0.0.1:9123"
    assert runtime.import_memories is True
    assert runtime.db_path == str(tmp_path / "runtime.db")

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
        {
            legacy_port: "9999",
            legacy_url: "http://127.0.0.1:9999",
        }
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
    assert ready.json() == {
        "status": "not_ready",
        "reason": "storage_unavailable",
    }
    assert version.status_code == 200

    rendered = json.dumps(
        [health.json(), ready.json(), version.json()],
        ensure_ascii=False,
    )
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
