"""Memory Tagger — 5 层关键词分类引擎

基于 I-12 §3.1–3.2 的层级定义，通过关键词匹配为记忆内容
自动分配层级标签（constraint / preference / style / decision / pattern）。
"""

from platform_core.memory_tagger.tagger import classify, extract_tags, detect_task_type
from platform_core.memory_tagger.config import LAMBDA_LEVELS, TASK_TYPE_MAPPINGS, DEFAULT_LAMBDA, resolve_layers, resolve_task_config
from platform_core.memory_tagger.models import MemoryLayer

# ── 类名别名（兼容期望模块级类名的调用方） ──
import platform_core.memory_tagger.tagger as MemoryTagger  # noqa: F401

__all__ = [
    "classify",
    "extract_tags",
    "detect_task_type",
    "LAMBDA_LEVELS",
    "TASK_TYPE_MAPPINGS",
    "DEFAULT_LAMBDA",
    "MemoryLayer",
    "resolve_layers",
    "resolve_task_config",
    "MemoryTagger",
]
