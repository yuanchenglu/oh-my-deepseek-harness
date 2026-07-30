"""Public package boundary for the DeepSeek Context Engine.

The package can be inspected in a clean environment without installing the Hermes host.
Actual registration still requires Hermes and is enforced by ``deepseek_context.plugin``.
"""

from __future__ import annotations

import sys
import types

HERMES_CONTEXT_AVAILABLE = True
HERMES_CONTEXT_IMPORT_ERROR: ModuleNotFoundError | None = None
_created_agent = False
_created_context_engine = False

try:
    from agent.context_engine import ContextEngine as _HermesContextEngine  # noqa: F401
except ModuleNotFoundError as exc:
    if exc.name not in {"agent", "agent.context_engine"}:
        raise
    HERMES_CONTEXT_AVAILABLE = False
    HERMES_CONTEXT_IMPORT_ERROR = exc

    agent_module = sys.modules.get("agent")
    if agent_module is None:
        agent_module = types.ModuleType("agent")
        agent_module.__path__ = []  # type: ignore[attr-defined]
        sys.modules["agent"] = agent_module
        _created_agent = True

    context_engine_module = sys.modules.get("agent.context_engine")
    if context_engine_module is None:
        context_engine_module = types.ModuleType("agent.context_engine")

        class ContextEngine:
            """Import-only fallback; never registered as a Hermes engine."""

        context_engine_module.ContextEngine = ContextEngine
        sys.modules["agent.context_engine"] = context_engine_module
        agent_module.context_engine = context_engine_module
        _created_context_engine = True

try:
    from ._public_engine import DeepSeekContextEngine
finally:
    if _created_context_engine:
        sys.modules.pop("agent.context_engine", None)
        if "agent" in sys.modules:
            try:
                delattr(sys.modules["agent"], "context_engine")
            except AttributeError:
                pass
    if _created_agent:
        sys.modules.pop("agent", None)

__all__ = [
    "DeepSeekContextEngine",
    "HERMES_CONTEXT_AVAILABLE",
    "HERMES_CONTEXT_IMPORT_ERROR",
]
