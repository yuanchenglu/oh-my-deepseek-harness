"""pytest configuration: isolate Hermes imports without source-path or symlink hacks."""

import sys
import types


_agent_mod = types.ModuleType("agent")
_agent_ce_mod = types.ModuleType("agent.context_engine")


class _MockContextEngine:
    """Minimal Hermes ContextEngine test double."""

    def on_session_start(self, session_id: str, **kwargs):
        return None


_agent_ce_mod.ContextEngine = _MockContextEngine
_agent_mod.context_engine = _agent_ce_mod
sys.modules.setdefault("agent", _agent_mod)
sys.modules.setdefault("agent.context_engine", _agent_ce_mod)
