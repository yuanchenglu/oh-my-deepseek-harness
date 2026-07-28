"""Side-effect-free Harness Server entry point and injectable App Factory."""

from __future__ import annotations

import importlib
import importlib.metadata
import os
import sys
import tempfile
from contextlib import asynccontextmanager
from types import ModuleType
from typing import Callable

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .config import RuntimeConfig
from .storage import HarnessStorage

StorageFactory = Callable[[str], HarnessStorage]
_LEGACY_MODULE = "harness_server.app"


def _distribution_version() -> str:
    try:
        return importlib.metadata.version("oh-my-deepseek-harness")
    except importlib.metadata.PackageNotFoundError:
        return "3.0.0b1"


def _load_domain_module(storage: HarnessStorage) -> ModuleType:
    """Load preserved domain routes only when the factory is invoked.

    The legacy module historically constructed storage and scanned the user's Memory
    directory at import time. During its first internal load, the constructor is
    injected and HOME points at an empty temporary directory. Public startup behavior
    is then governed exclusively by ``RuntimeConfig`` and the FastAPI lifespan below.
    """

    existing = sys.modules.get(_LEGACY_MODULE)
    if existing is not None:
        existing.storage = storage
        return existing

    storage_module = importlib.import_module("harness_server.storage")
    original_factory = storage_module.HarnessStorage
    old_home = os.environ.get("HOME")
    old_profile = os.environ.get("USERPROFILE")

    with tempfile.TemporaryDirectory(prefix="harness-app-load-") as isolated_home:
        os.environ["HOME"] = isolated_home
        os.environ["USERPROFILE"] = isolated_home
        storage_module.HarnessStorage = lambda *args, **kwargs: storage
        try:
            module = importlib.import_module(".app", __package__)
        finally:
            storage_module.HarnessStorage = original_factory
            if old_home is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = old_home
            if old_profile is None:
                os.environ.pop("USERPROFILE", None)
            else:
                os.environ["USERPROFILE"] = old_profile

    module.storage = storage
    return module


def create_app(
    config: RuntimeConfig | None = None,
    *,
    storage: HarnessStorage | None = None,
    storage_factory: StorageFactory = HarnessStorage,
) -> FastAPI:
    """Create one local Harness Server application with injectable storage."""

    runtime = config or RuntimeConfig.from_env()
    store = storage or storage_factory(runtime.db_path)
    domain = _load_domain_module(store)

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        if runtime.import_memories:
            domain.import_hermes_memories(runtime.memories_dir, store)
        yield

    application = FastAPI(
        title="Harness MCP Server",
        description="Plan Engine + Memory Tagger + Checkpoint Review local runtime",
        version=_distribution_version(),
        lifespan=lifespan,
    )
    application.state.runtime_config = runtime
    application.state.storage = store

    for route in domain.app.router.routes:
        path = getattr(route, "path", "")
        if path.startswith(("/plan/", "/memory/", "/checkpoint/")):
            application.router.routes.append(route)

    @application.get("/health", summary="Process liveness")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "harness-server"}

    @application.get("/ready", summary="Storage readiness")
    async def ready():
        connection = None
        try:
            connection = store._connection()
            connection.execute("SELECT 1").fetchone()
            return {"status": "ready"}
        except Exception:
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready", "reason": "storage_unavailable"},
            )
        finally:
            if connection is not None:
                connection.close()

    @application.get("/version", summary="Runtime version contract")
    async def version() -> dict[str, str]:
        return {
            "status": "ok",
            "service": "harness-server",
            "version": _distribution_version(),
            "api_version": "1",
        }

    return application


def main() -> None:
    """Start the local runtime through Uvicorn's factory mode."""

    import uvicorn

    runtime = RuntimeConfig.from_env()
    uvicorn.run(
        "harness_server.server:create_app",
        factory=True,
        host=runtime.host,
        port=runtime.port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
