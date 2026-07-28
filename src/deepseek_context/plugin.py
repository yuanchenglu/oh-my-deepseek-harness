"""Hermes pip-plugin entry point for the DeepSeek Context Engine."""

from __future__ import annotations

from . import (
    HERMES_CONTEXT_AVAILABLE,
    HERMES_CONTEXT_IMPORT_ERROR,
    DeepSeekContextEngine,
)


def register(ctx) -> None:
    """Register the packaged ContextEngine through a real Hermes host."""
    if not HERMES_CONTEXT_AVAILABLE:
        raise RuntimeError(
            "deepseek-context requires the Hermes Agent host at registration time"
        ) from HERMES_CONTEXT_IMPORT_ERROR
    ctx.register_context_engine(DeepSeekContextEngine())
