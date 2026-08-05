"""PKG-002 clean-install dependency matrix and metadata contracts."""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
import venv
from pathlib import Path

import pytest

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]


def _run(
    *args: str,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> str:
    completed = subprocess.run(
        list(args),
        cwd=cwd,
        env=env,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert completed.returncode == 0, completed.stdout
    return completed.stdout


@pytest.fixture(scope="session")
def dependency_wheel(tmp_path_factory: pytest.TempPathFactory) -> Path:
    wheel_dir = tmp_path_factory.mktemp("pkg002-wheel")
    _run(
        sys.executable,
        "-m",
        "pip",
        "wheel",
        "--disable-pip-version-check",
        "--no-deps",
        "--wheel-dir",
        str(wheel_dir),
        ".",
        cwd=ROOT,
    )
    wheels = list(wheel_dir.glob("oh_my_deepseek_harness-3.0.0b1-*.whl"))
    assert len(wheels) == 1
    return wheels[0]


def _dependency_names(requirements: list[str]) -> set[str]:
    names: set[str] = set()
    for requirement in requirements:
        name = requirement.split(";", 1)[0]
        for separator in ("<", ">", "=", "!", "~", "["):
            name = name.split(separator, 1)[0]
        names.add(name.strip().lower().replace("_", "-"))
    return names


def test_dependency_metadata_has_complete_extra_closure() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle)["project"]

    base = _dependency_names(project["dependencies"])
    extras = {
        name: _dependency_names(requirements)
        for name, requirements in project["optional-dependencies"].items()
    }

    assert base == {"pyyaml", "httpx"}
    assert extras["context"] == {"openai"}
    assert extras["server"] == {"fastapi", "uvicorn", "pydantic"}
    assert extras["all"] == extras["context"] | extras["server"]
    assert extras["mcp"] == extras["server"]
    assert extras["all"] <= extras["dev"]
    assert {"pytest", "pytest-cov", "tomli"} <= extras["dev"]


_VARIANTS = {
    "base": textwrap.dedent(
        """
        import importlib.util
        import deepseek_harness
        import httpx
        import yaml

        assert importlib.util.find_spec("openai") is None
        assert importlib.util.find_spec("fastapi") is None
        assert importlib.util.find_spec("uvicorn") is None
        assert importlib.util.find_spec("pydantic") is None
        """
    ),
    "context": textwrap.dedent(
        """
        import importlib.util
        import deepseek_context
        import deepseek_context.plugin
        import openai

        assert deepseek_context.HERMES_CONTEXT_AVAILABLE is False
        assert importlib.util.find_spec("fastapi") is None
        assert importlib.util.find_spec("uvicorn") is None

        class DummyContext:
            def register_context_engine(self, engine):
                raise AssertionError("registration must not run without Hermes")

        try:
            deepseek_context.plugin.register(DummyContext())
        except RuntimeError as exc:
            assert "requires the Hermes Agent host" in str(exc)
        else:
            raise AssertionError("context registration unexpectedly succeeded without Hermes")
        """
    ),
    "server": textwrap.dedent(
        """
        import importlib.util
        import fastapi
        import pydantic
        import uvicorn
        import harness_server.models
        import harness_server.storage
        import harness_server.server

        assert importlib.util.find_spec("openai") is None
        """
    ),
    "all": textwrap.dedent(
        """
        import deepseek_harness
        import deepseek_context
        import deepseek_context.plugin
        import harness_server.models
        import harness_server.storage
        import harness_server.server
        import fastapi
        import httpx
        import openai
        import pydantic
        import uvicorn
        import yaml

        assert deepseek_context.HERMES_CONTEXT_AVAILABLE is False
        """
    ),
}


@pytest.mark.parametrize("variant", ["base", "context", "server", "all"])
def test_clean_install_dependency_variant(
    variant: str,
    dependency_wheel: Path,
    tmp_path: Path,
) -> None:
    environment = tmp_path / f"venv-{variant}"
    venv.EnvBuilder(with_pip=True).create(environment)
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

    suffix = "" if variant == "base" else f"[{variant}]"
    requirement = (
        f"oh-my-deepseek-harness{suffix} @ {dependency_wheel.resolve().as_uri()}"
    )
    isolated_home = tmp_path / f"home-{variant}"
    isolated_home.mkdir()
    env = {
        **os.environ,
        "HOME": str(isolated_home),
        "USERPROFILE": str(isolated_home),
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        "PYTHONNOUSERSITE": "1",
    }

    _run(
        str(python),
        "-m",
        "pip",
        "install",
        requirement,
        cwd=tmp_path,
        env=env,
    )
    _run(
        str(python),
        "-I",
        "-c",
        _VARIANTS[variant],
        cwd=tmp_path,
        env=env,
    )
