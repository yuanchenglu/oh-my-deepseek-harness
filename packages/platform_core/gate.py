"""
认知门控引擎（Cognitive Gate Engine）— 平台无关核心。

在 pre_llm_call 阶段被调用，在每轮 LLM 调用前注入认知检查提醒、
双向原语和范围控制提醒。

工作模式：
  - 首轮：注入完整 MAP.md + L1/L2 + I-02 双向原语 + I-08 范围控制
  - 后续轮：仅注入 L1/L2 + 简短 I-02 + 简短 I-08（避免上下文膨胀）

本模块不依赖任何 Hermes API，所有平台特定输入通过函数参数传入。
"""

import os
import re
from typing import Optional


_I02_FULL = """[I-02 双向原语]
你可以在需要时使用以下原语主动声明需求：

/propose_skill <name> <trigger> <steps>
  - 用途：完成任务后提议固化为可复用 Skill
  - 示例：/propose_skill python-migrate-setup-to-pyproject "检测到 setup.py" "1.读取setup.py 2.生成pyproject.toml 3.验证"
  - 注意：只建议有价值的可复用模式

/trigger_self_review <target> <reason>
  - 用途：在关键决策前请求独立审查
  - 示例：/trigger_self_review "数据库迁移计划" "涉及生产数据，影响范围大"
  - 注意：用于高风险决策"""

_I02_BRIEF = (
    "[I-02] 如需提议 Skill 或请求审查，请使用 "
    "/propose_skill 或 /trigger_self_review"
)

_I08_FULL = """[I-08 范围控制]
需求对齐层：不得超出用户显式声明的功能范围。如果任务描述中有"不要 X""只做 Y"等排除项，严格遵守。
技术规划层：新增步骤前先判断是"必要依赖"还是"范围蔓延"。
  判断标准：不加这个步骤，已承诺的 PlanStep 能否完成？
  → 能完成 = 范围蔓延，拒绝
  → 不能完成 = 必要依赖，可接受"""

_I08_BRIEF = (
    "[I-08] 注意范围控制：不加步骤能完成 = 拒绝"
)

# ── I-01: 硬约束横切状态通道 ──
# 模块级变量，由 set_hard_constraints() 写入，由 assessor 读取
_current_hard_constraints: set[str] = set()
_HARD_CONSTRAINT_PATTERN = re.compile(
    r'(?:不能|不要|不得|禁止|严禁|不允许|千万别|绝对不|必须)[^，。；、！？\n]{2,60}'
)


def extract_hard_constraints(user_message: str) -> set[str]:
    """从用户消息中提取硬约束关键词。

    Args:
        user_message: 用户消息原文

    Returns:
        匹配到的约束字符串集合。
    """
    if not isinstance(user_message, str) or not user_message.strip():
        return set()
    matches = _HARD_CONSTRAINT_PATTERN.findall(user_message)
    return {c.strip() for c in matches if c.strip()}


def set_hard_constraints(constraints: set[str]) -> None:
    """更新模块级硬约束状态通道。

    Args:
        constraints: 新的约束集合（会替换旧值）。
    """
    _current_hard_constraints.clear()
    _current_hard_constraints.update(constraints)


def get_hard_constraints() -> set[str]:
    """获取当前活跃的硬约束集合（只读快照）。"""
    return set(_current_hard_constraints)


def core_reminders() -> list[str]:
    """生成 L1 + L2 核心提醒列表。"""
    return [
        "[L1] 荣辱观：以知道自己的不足为荣、以提升认知为荣、以告诉实情为荣。"
        "回应前请用工具验证每个论断，不确定就说不确定。",
        "[L2] 思维方式：第一性原理、Step by Step、假设先行、找盲区、科研严谨。"
        "拆解到最小任务，假设先行验证。",
    ]


def build_map_navigation(map_path: str = "~/.hermes/MAP.md") -> str:
    """读取 MAP.md 导航内容。

    Args:
        map_path: MAP.md 文件路径，支持 ~ 扩展。

    Returns:
        "[MAP]\\n{content}" 格式字符串，文件不存在或读取失败时返回空字符串。
    """
    try:
        expanded = os.path.expanduser(map_path)
        if os.path.exists(expanded):
            with open(expanded, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if content:
                return f"[MAP]\n{content}"
    except Exception:
        pass
    return ""


def build_gate_context(
    is_first_turn: bool,
    user_message: str = "",
    map_path: str = "~/.hermes/MAP.md",
) -> dict:
    """构建认知门控上下文注入内容。

    首轮注入完整 MAP.md + L1/L2 + I-02 完整 + I-08 完整。
    后续轮仅注入 L1/L2 + 简短 I-02 + 简短 I-08。

    副作用：从 user_message 提取硬约束并更新 _current_hard_constraints。

    Args:
        is_first_turn: 是否为首轮调用
        user_message: 用户消息原文（用于提取硬约束）
        map_path: MAP.md 文件路径

    Returns:
        dict with 'context' key。至少包含纯 L1/L2，不会返回空 dict。
    """
    # 从用户消息提取硬约束
    if isinstance(user_message, str) and user_message.strip():
        constraints = extract_hard_constraints(user_message)
        if constraints:
            set_hard_constraints(constraints)

    parts: list[str] = core_reminders()

    if is_first_turn:
        map_content = build_map_navigation(map_path)
        if map_content:
            parts.append(map_content)
        parts.append(_I02_FULL)
        parts.append(_I08_FULL)
    else:
        parts.append(_I02_BRIEF)
        parts.append(_I08_BRIEF)

    return {"context": "\n".join(parts)}
