"""pytest conftest — 设置 sys.path 和包别名，mock Hermes 依赖。"""

import os
import sys
import types

# ── Mock Hermes agent 模块（deepseek-context 依赖） ────
# deepseek_context/__init__.py 从 agent.context_engine 导入 ContextEngine
# 在 CI 环境没有 Hermes，需要 mock
_agent_mod = types.ModuleType("agent")
_agent_ce_mod = types.ModuleType("agent.context_engine")


class _MockContextEngine:
    """mock Hermes ContextEngine 基类。"""
    def on_session_start(self, session_id: str, **kwargs):
        pass


_agent_ce_mod.ContextEngine = _MockContextEngine
_agent_mod.context_engine = _agent_ce_mod
sys.modules["agent"] = _agent_mod
sys.modules["agent.context_engine"] = _agent_ce_mod

# ── 添加 plugins 目录到 sys.path ────────────────────────
PLUGINS_DIR = os.path.join(os.path.dirname(__file__), "..", "plugins")
if PLUGINS_DIR not in sys.path:
    sys.path.insert(0, PLUGINS_DIR)

# ── 为 deepseek-harness 创建下划线 symlink ──────────────
# 纯 Python import 不支持连字符，创建一个 deepseek_harness -> deepseek-harness 链接
HARNESS_SRC = os.path.join(PLUGINS_DIR, "deepseek-harness")
HARNESS_LINK = os.path.join(PLUGINS_DIR, "deepseek_harness")
if not os.path.exists(HARNESS_LINK):
    try:
        os.symlink("deepseek-harness", HARNESS_LINK)
    except (OSError, PermissionError):
        pass

# ── 同样处理 deepseek-context ───────────────────────────
CONTEXT_SRC = os.path.join(PLUGINS_DIR, "deepseek-context")
CONTEXT_LINK = os.path.join(PLUGINS_DIR, "deepseek_context")
if not os.path.exists(CONTEXT_LINK):
    try:
        os.symlink("deepseek-context", CONTEXT_LINK)
    except (OSError, PermissionError):
        pass
