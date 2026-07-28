"""INS-001 source-external lifecycle tests for TC-INSTALL-001 through 003."""

from __future__ import annotations

import hashlib
import json
import os
import socket
import stat
import subprocess
import sys
import tarfile
import venv
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _run(
    *args: str,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: float = 90,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args),
        cwd=cwd,
        env=env,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )


def _build_installed_environment(tmp_path: Path) -> tuple[Path, Path]:
    archive = tmp_path / "source.tar"
    with archive.open("wb") as handle:
        subprocess.run(
            ["git", "archive", "--format=tar", "HEAD"],
            cwd=ROOT,
            check=True,
            stdout=handle,
        )

    source = tmp_path / "source"
    source.mkdir()
    with tarfile.open(archive) as handle:
        handle.extractall(source, filter="data")

    wheelhouse = tmp_path / "wheelhouse"
    wheelhouse.mkdir()
    built = _run(
        sys.executable,
        "-m",
        "pip",
        "wheel",
        "--no-deps",
        "--wheel-dir",
        str(wheelhouse),
        ".",
        cwd=source,
    )
    assert built.returncode == 0, built.stdout + built.stderr
    wheels = list(wheelhouse.glob("oh_my_deepseek_harness-3.0.0b1-*.whl"))
    assert len(wheels) == 1

    environment = tmp_path / "venv"
    venv.EnvBuilder(with_pip=True, system_site_packages=True).create(environment)
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    installed = _run(
        str(python),
        "-m",
        "pip",
        "install",
        "--no-deps",
        str(wheels[0]),
        cwd=tmp_path,
    )
    assert installed.returncode == 0, installed.stdout + installed.stderr
    console = environment / (
        "Scripts/deepseek-harness.exe" if os.name == "nt" else "bin/deepseek-harness"
    )
    assert console.is_file()
    return python, console


def _isolated_env(
    *, home: Path, data_root: Path, db_path: Path, memories: Path, port: int
) -> dict[str, str]:
    return {
        **os.environ,
        "HOME": str(home),
        "USERPROFILE": str(home),
        "HARNESS_DATA_ROOT": str(data_root),
        "HARNESS_DB_PATH": str(db_path),
        "HARNESS_MEMORIES_DIR": str(memories),
        "HARNESS_IMPORT_MEMORIES": "0",
        "HARNESS_HOST": "127.0.0.1",
        "HARNESS_PORT": str(port),
        "PYTHONNOUSERSITE": "1",
        "PYTHONUNBUFFERED": "1",
        "DEEPSEEK_API_KEY": "fake-ins-001-key",
    }


def _payload(completed: subprocess.CompletedProcess[str]) -> dict:
    rendered = completed.stdout.strip() or completed.stderr.strip()
    assert rendered, (completed.returncode, completed.stdout, completed.stderr)
    return json.loads(rendered.splitlines()[-1])


def _snapshot(root: Path) -> tuple[tuple[str, str, str, int], ...]:
    if not root.exists():
        return ()
    rows: list[tuple[str, str, str, int]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        mode = stat.S_IMODE(path.lstat().st_mode)
        if path.is_symlink():
            rows.append((relative, "symlink", os.readlink(path), mode))
        elif path.is_dir():
            rows.append((relative, "directory", "", mode))
        else:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            rows.append((relative, "file", digest, mode))
    return tuple(rows)


def _managed_file_snapshot(paths: list[Path]) -> dict[str, tuple[bytes, int, int]]:
    return {
        str(path): (
            path.read_bytes(),
            stat.S_IMODE(path.stat().st_mode),
            path.stat().st_mtime_ns,
        )
        for path in paths
    }


@pytest.mark.skipif(os.name == "nt", reason="Windows install process matrix is later work")
def test_install_dry_run_leaves_empty_home_and_persistent_state_unchanged(
    tmp_path: Path,
) -> None:
    """TC-INSTALL-001: dry-run reports the full plan without any persistent write."""
    _, console = _build_installed_environment(tmp_path)
    home = tmp_path / "home"
    home.mkdir()
    data_root = home / ".hermes" / "oh-my-deepseek-harness"
    env = _isolated_env(
        home=home,
        data_root=data_root,
        db_path=data_root / "data" / "harness.db",
        memories=home / ".hermes" / "memories",
        port=_free_port(),
    )
    before = _snapshot(home)

    completed = _run(
        str(console),
        "install",
        "--dry-run",
        "--json",
        cwd=tmp_path,
        env=env,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    payload = _payload(completed)

    assert payload["state"] == "planned"
    assert payload["dry_run"] is True
    assert payload["changed"] is False
    assert payload["data_root"] == str(data_root.resolve())
    assert payload["port"] == int(env["HARNESS_PORT"])
    assert payload["summary_enabled"] is False
    assert payload["summary_allow_tool_arguments"] is False
    assert payload["memory_import_on_startup"] is False
    assert len(payload["deployment_paths"]) == 2
    assert _snapshot(home) == before
    assert not data_root.exists()


@pytest.mark.skipif(os.name == "nt", reason="Windows install process matrix is later work")
def test_clean_wheel_install_deploys_plugins_config_and_ready_server(
    tmp_path: Path,
) -> None:
    """TC-INSTALL-002: an installed wheel deploys Plugin/Context and a ready Server."""
    _, console = _build_installed_environment(tmp_path)
    home = tmp_path / "home"
    home.mkdir()
    data_root = home / ".hermes" / "oh-my-deepseek-harness"
    db_path = data_root / "data" / "harness.db"
    memories = home / ".hermes" / "memories"
    env = _isolated_env(
        home=home,
        data_root=data_root,
        db_path=db_path,
        memories=memories,
        port=_free_port(),
    )

    completed = _run(
        str(console), "install", "--json", cwd=tmp_path, env=env, timeout=120
    )
    payload = _payload(completed)
    try:
        assert completed.returncode == 0, completed.stdout + completed.stderr
        assert payload["state"] == "installed"
        assert payload["changed"] is True
        assert payload["healthy"] is True
        assert payload["ready"] is True
        assert isinstance(payload["server_pid"], int)

        harness_plugin = home / ".hermes" / "plugins" / "deepseek-harness"
        context_plugin = home / ".hermes" / "plugins" / "deepseek-context"
        assert "from deepseek_harness import register" in (
            harness_plugin / "__init__.py"
        ).read_text(encoding="utf-8")
        assert "from deepseek_context.plugin import register" in (
            context_plugin / "__init__.py"
        ).read_text(encoding="utf-8")
        assert yaml.safe_load((harness_plugin / "plugin.yaml").read_text())["name"] == (
            "deepseek-harness"
        )
        assert yaml.safe_load((context_plugin / "plugin.yaml").read_text())["name"] == (
            "deepseek-context"
        )

        config_path = data_root / "config" / "config.yaml"
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        assert config["runtime"]["host"] == "127.0.0.1"
        assert config["runtime"]["port"] == int(env["HARNESS_PORT"])
        assert config["runtime"]["db_path"] == str(db_path)
        assert config["runtime"]["memory_import_on_startup"] is False
        assert config["privacy"]["summary_enabled"] is False
        assert config["privacy"]["summary_allow_tool_arguments"] is False
        assert db_path.is_file()

        for directory in (
            data_root,
            data_root / "config",
            data_root / "data",
            data_root / "runtime",
            data_root / "logs",
            harness_plugin,
            context_plugin,
        ):
            assert stat.S_IMODE(directory.stat().st_mode) == 0o700
        for file_path in (
            config_path,
            harness_plugin / "__init__.py",
            harness_plugin / "plugin.yaml",
            context_plugin / "__init__.py",
            context_plugin / "plugin.yaml",
            data_root / "runtime" / "harness-server.json",
            data_root / "runtime" / "harness-server.lock",
            data_root / "logs" / "harness-server.log",
        ):
            assert stat.S_IMODE(file_path.stat().st_mode) == 0o600

        status = _run(
            str(console),
            "server",
            "status",
            "--data-root",
            str(data_root),
            "--json",
            cwd=tmp_path,
            env=env,
        )
        status_payload = _payload(status)
        assert status.returncode == 0, status.stdout + status.stderr
        assert status_payload["pid"] == payload["server_pid"]
        assert status_payload["healthy"] is True
        assert status_payload["ready"] is True
    finally:
        _run(
            str(console),
            "server",
            "stop",
            "--data-root",
            str(data_root),
            "--json",
            cwd=tmp_path,
            env=env,
        )


@pytest.mark.skipif(os.name == "nt", reason="Windows install process matrix is later work")
def test_repeated_same_version_install_is_idempotent_and_reuses_one_server(
    tmp_path: Path,
) -> None:
    """TC-INSTALL-003: repeated install creates no duplicate files, backup or process."""
    _, console = _build_installed_environment(tmp_path)
    home = tmp_path / "home"
    home.mkdir()
    data_root = home / ".hermes" / "oh-my-deepseek-harness"
    db_path = data_root / "data" / "harness.db"
    env = _isolated_env(
        home=home,
        data_root=data_root,
        db_path=db_path,
        memories=home / ".hermes" / "memories",
        port=_free_port(),
    )

    first = _run(str(console), "install", "--json", cwd=tmp_path, env=env, timeout=120)
    first_payload = _payload(first)
    managed_files = [
        home / ".hermes" / "plugins" / "deepseek-harness" / "__init__.py",
        home / ".hermes" / "plugins" / "deepseek-harness" / "plugin.yaml",
        home / ".hermes" / "plugins" / "deepseek-context" / "__init__.py",
        home / ".hermes" / "plugins" / "deepseek-context" / "plugin.yaml",
        data_root / "config" / "config.yaml",
        data_root / "runtime" / "harness-server.json",
    ]
    try:
        assert first.returncode == 0, first.stdout + first.stderr
        assert first_payload["changed"] is True
        before = _managed_file_snapshot(managed_files)

        second = _run(
            str(console), "install", "--json", cwd=tmp_path, env=env, timeout=120
        )
        second_payload = _payload(second)
        assert second.returncode == 0, second.stdout + second.stderr
        assert second_payload["state"] == "installed"
        assert second_payload["changed"] is False
        assert second_payload["server_pid"] == first_payload["server_pid"]
        assert _managed_file_snapshot(managed_files) == before
        assert not list(home.rglob("*.bak.*"))
        assert not list(home.rglob("migration-report.md"))
        assert len(list((data_root / "runtime").glob("harness-server.json"))) == 1
        assert yaml.safe_load((data_root / "config" / "config.yaml").read_text())[
            "runtime"
        ]["memory_import_on_startup"] is False
    finally:
        stopped = _run(
            str(console),
            "server",
            "stop",
            "--data-root",
            str(data_root),
            "--json",
            cwd=tmp_path,
            env=env,
        )
        assert stopped.returncode == 0, stopped.stdout + stopped.stderr


def test_install_implementation_never_manages_the_python_distribution() -> None:
    """The canonical lifecycle path must not invoke pip or maintain a second shell implementation."""
    installer = (ROOT / "src" / "deepseek_harness" / "installer.py").read_text(
        encoding="utf-8"
    )
    shell = (ROOT / "scripts" / "install.sh").read_text(encoding="utf-8")
    assert "subprocess" not in installer
    assert "pip install" not in installer
    assert "pip uninstall" not in installer
    assert "cp -r" not in shell
    assert "deepseek_harness.cli install" in shell
