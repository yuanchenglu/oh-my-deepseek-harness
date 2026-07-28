"""Artifact tests for the canonical src/ distribution and final wheel lifecycle."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tarfile
import textwrap
import venv
import zipfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _run(*args: str, cwd: Path, env: dict[str, str] | None = None) -> None:
    completed = subprocess.run(
        list(args),
        cwd=cwd,
        env=env,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=360,
    )
    assert completed.returncode == 0, completed.stdout


def _build_wheel_from_git_archive(tmp_path: Path) -> Path:
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

    wheel_dir = tmp_path / "wheelhouse"
    wheel_dir.mkdir()
    _run(
        sys.executable,
        "-m",
        "pip",
        "wheel",
        "--no-deps",
        "--wheel-dir",
        str(wheel_dir),
        ".",
        cwd=source,
    )
    wheels = list(wheel_dir.glob("oh_my_deepseek_harness-3.0.0b1-*.whl"))
    assert len(wheels) == 1
    return wheels[0]


def test_legacy_paths_are_thin_adapters_only() -> None:
    harness_dir = ROOT / "plugins" / "deepseek-harness"
    context_dir = ROOT / "plugins" / "deepseek-context"
    server_dir = ROOT / "mcp" / "harness_server"

    assert {path.name for path in harness_dir.iterdir() if path.is_file()} == {
        "__init__.py",
        "plugin.yaml",
    }
    assert {path.name for path in context_dir.iterdir() if path.is_file()} == {
        "__init__.py",
        "plugin.yaml",
    }
    assert {path.name for path in server_dir.iterdir() if path.is_file()} == {
        "__init__.py",
        "models.py",
        "server.py",
        "storage.py",
    }

    assert "from deepseek_harness import register" in (
        harness_dir / "__init__.py"
    ).read_text(encoding="utf-8")
    assert "from deepseek_context.plugin import register" in (
        context_dir / "__init__.py"
    ).read_text(encoding="utf-8")
    assert "from harness_server.server import" in (
        server_dir / "server.py"
    ).read_text(encoding="utf-8")

    conftest = (ROOT / "tests" / "conftest.py").read_text(encoding="utf-8")
    assert "os.symlink" not in conftest
    assert "PLUGINS_DIR" not in conftest


def test_git_archive_wheel_contains_all_packages_and_resources(tmp_path: Path) -> None:
    wheel = _build_wheel_from_git_archive(tmp_path)
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())

    required = {
        "deepseek_harness/__init__.py",
        "deepseek_harness/cli.py",
        "deepseek_harness/doctor.py",
        "deepseek_harness/installer.py",
        "deepseek_harness/lifecycle.py",
        "deepseek_harness/tools.py",
        "deepseek_harness/resources/plugin.yaml",
        "deepseek_harness/resources/strategies.yaml",
        "deepseek_context/__init__.py",
        "deepseek_context/compressor.py",
        "deepseek_context/plugin.py",
        "deepseek_context/resources/plugin.yaml",
        "deepseek_context/resources/config.yaml",
        "harness_server/__init__.py",
        "harness_server/runtime.py",
        "harness_server/server.py",
        "harness_server/supervisor.py",
        "harness_server/models.py",
        "harness_server/storage.py",
        "harness_server/config.yaml",
    }
    assert required <= names
    assert not any(name.startswith(("plugins/", "mcp/", "tests/")) for name in names)


def test_wheel_installs_and_imports_outside_repository(tmp_path: Path) -> None:
    wheel = _build_wheel_from_git_archive(tmp_path)
    environment = tmp_path / "venv"
    venv.EnvBuilder(with_pip=True, system_site_packages=True).create(environment)
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    _run(str(python), "-m", "pip", "install", "--no-deps", str(wheel), cwd=tmp_path)

    probe = tmp_path / "probe"
    probe.mkdir()
    script = textwrap.dedent(
        f"""
        import importlib.metadata
        import sys
        import types
        from importlib import resources
        from pathlib import Path

        agent = types.ModuleType("agent")
        context_engine = types.ModuleType("agent.context_engine")
        class ContextEngine:
            pass
        context_engine.ContextEngine = ContextEngine
        agent.context_engine = context_engine
        sys.modules["agent"] = agent
        sys.modules["agent.context_engine"] = context_engine

        import deepseek_harness
        import deepseek_context
        import harness_server
        import deepseek_harness.cli as cli
        import deepseek_harness.tools as tools
        from harness_server.runtime import RuntimePaths
        from harness_server.supervisor import Supervisor

        repository = Path({str(ROOT)!r}).resolve()
        for module in (deepseek_harness, deepseek_context, harness_server):
            location = Path(module.__file__).resolve()
            assert repository not in location.parents, (module.__name__, location)

        assert callable(cli.main)
        assert tools.Supervisor is Supervisor
        assert RuntimePaths.from_root("runtime-probe").state_file.name == "harness-server.json"
        assert not hasattr(tools, "_SERVER_SCRIPT")
        assert resources.files("deepseek_harness.resources").joinpath("plugin.yaml").is_file()
        assert resources.files("deepseek_harness.resources").joinpath("strategies.yaml").is_file()
        assert resources.files("deepseek_context.resources").joinpath("plugin.yaml").is_file()
        assert resources.files("deepseek_context.resources").joinpath("config.yaml").is_file()
        assert resources.files("harness_server").joinpath("config.yaml").is_file()

        entry_points = importlib.metadata.entry_points()
        selected = entry_points.select(group="hermes_agent.plugins")
        mapping = {{entry.name: entry for entry in selected}}
        assert {{"deepseek-harness", "deepseek-context"}} <= set(mapping)
        assert mapping["deepseek-harness"].load().__name__ == "deepseek_harness"
        assert mapping["deepseek-context"].load().__name__ == "deepseek_context.plugin"

        console = entry_points.select(group="console_scripts", name="deepseek-harness")
        assert len(console) == 1
        assert next(iter(console)).value == "deepseek_harness.cli:main"
        """
    )
    _run(str(python), "-c", script, cwd=probe)


def test_artifact_runner_has_no_editable_or_source_import_escape_hatch() -> None:
    runner = (ROOT / "scripts" / "test_artifact.sh").read_text(encoding="utf-8")
    assert "git -C \"${ROOT}\" archive" in runner
    assert "pip install -e" not in runner
    assert "PYTHONPATH=" in runner
    assert "repository not in location.parents" in runner
    assert "archived_source not in location.parents" in runner
    assert "python -m pip uninstall oh-my-deepseek-harness" in runner
    assert "${VENV_PY} -m pip uninstall" in runner


@pytest.mark.skipif(os.name == "nt", reason="QA-ART-001 release process matrix is POSIX")
def test_final_wheel_full_lifecycle_outside_source_tree(tmp_path: Path) -> None:
    configured = os.environ.get("QA_ARTIFACT_RESULTS_DIR")
    results = (
        (ROOT / configured).resolve()
        if configured and not Path(configured).is_absolute()
        else Path(configured).resolve()
        if configured
        else (tmp_path / "artifact-results").resolve()
    )
    env = {
        **os.environ,
        "QA_ARTIFACT_RESULTS_DIR": str(results),
        "PYTHONPATH": "",
    }
    completed = subprocess.run(
        ["bash", str(ROOT / "scripts" / "test_artifact.sh"), sys.executable],
        cwd=ROOT,
        env=env,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=600,
    )
    assert completed.returncode == 0, completed.stdout

    required = {
        "build.log",
        "wheel.sha256",
        "wheel-inventory.json",
        "import-probe.json",
        "install-dry-run.json",
        "install.json",
        "doctor.json",
        "server-smoke.json",
        "upgrade-dry-run.json",
        "upgrade.json",
        "uninstall.json",
        "explicit-pip-uninstall.log",
        "junit.xml",
    }
    assert required <= {path.name for path in results.iterdir()}
    assert len(list(results.glob("oh_my_deepseek_harness-3.0.0b1-*.whl"))) == 1

    import_probe = json.loads((results / "import-probe.json").read_text(encoding="utf-8"))
    assert import_probe["distribution_version"] == "3.0.0b1"
    assert set(import_probe["modules"]) >= {
        "deepseek_harness",
        "deepseek_context",
        "harness_server",
        "deepseek_harness.lifecycle",
    }

    smoke = json.loads((results / "server-smoke.json").read_text(encoding="utf-8"))
    assert smoke["health"]["status"] == "ok"
    assert smoke["ready"]["status"] == "ready"
    assert smoke["memory_tag"]["layer"] == "constraint"

    uninstall = json.loads((results / "uninstall.json").read_text(encoding="utf-8"))
    assert uninstall["pip_uninstall_command"] == (
        "python -m pip uninstall oh-my-deepseek-harness"
    )
