"""Hermes pip-plugin entry point for the DeepSeek Context Engine."""

from __future__ import annotations

from . import DeepSeekContextEngine


def register(ctx) -> None:
    """Register the packaged ContextEngine through Hermes PluginContext."""
    ctx.register_context_engine(DeepSeekContextEngine())
