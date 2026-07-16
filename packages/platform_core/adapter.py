"""
PlatformAdapter — 平台适配器抽象基类。

定义所有 Agent 平台（Hermes / OpenCode / Claude Code / Codex CLI）的统一适配器接口。
每个平台实现此 ABC 以提供标准化的消息获取、提示注入、工具结果检索、
会话生命周期管理和子任务编排能力。
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class PlatformAdapter(ABC):
    """Agent 平台适配器的抽象基类。

    作为 Hermes / OpenCode / Claude Code / Codex CLI 等 Agent 平台的统一接口，
    隐藏平台间的 API 差异，为上层的 Harness 层（认知门控、质量评估、
    学习总结等）提供一致的调用契约。

    子类必须实现的抽象方法：
        - get_messages()
        - inject_system_prompt()
        - get_tool_results()
        - on_session_end()
        - dispatch_subtask()

    可选覆盖的存根方法：
        - on_subagent_lifecycle()  — 默认 no-op + 日志，平台无需强制实现
    """

    @abstractmethod
    def get_messages(self) -> List[Dict[str, Any]]:
        """获取当前对话的消息列表。

        Returns:
            消息 dict 列表，每条消息至少包含 "role" 和 "content" 字段。
            格式与 OpenAI Chat Completion API 的 messages 参数兼容：
                [{"role": "system", "content": "..."},
                 {"role": "user",   "content": "..."},
                 {"role": "assistant", "content": "..."}]

        Raises:
            NotImplementedError: 子类未实现此方法。
        """

    @abstractmethod
    def inject_system_prompt(self, prompt: str) -> None:
        """向当前会话注入系统提示内容。

        各平台注入时机不同：
            - Hermes: 通过 pre_llm_call hook 的 context 返回值注入
            - OpenCode: 通过 event hook 修改 system prompt
            - Claude Code: 通过 project instruction 追加
            - Codex CLI: 通过 system prompt 注入

        Args:
            prompt: 要注入的系统提示文本。

        Raises:
            NotImplementedError: 子类未实现此方法。
        """

    @abstractmethod
    def get_tool_results(self) -> List[Dict[str, Any]]:
        """获取最近一次工具调用的结果列表。

        Returns:
            工具结果 dict 列表，每个结果至少包含：
                - tool_name (str): 工具名称，如 "write", "bash", "read"
                - args (dict): 工具调用的原始参数
                - result (Any): 工具返回的结果
                - status (str): "success" 或 "error"
            可能还包含 execution_time_ms (int) 等扩展字段。

        Raises:
            NotImplementedError: 子类未实现此方法。
        """

    @abstractmethod
    def on_session_end(self) -> None:
        """会话结束时的回调。

        在此处执行清理工作（保存状态、记录摘要、关闭连接等）。
        由平台在会话自然结束或用户中断时调用。

        实现应保证幂等性：多次调用不应产生副作用。

        Raises:
            NotImplementedError: 子类未实现此方法。
        """

    @abstractmethod
    def dispatch_subtask(self, config: Dict[str, Any]) -> str:
        """派发一个子任务到子 Agent。

        Args:
            config: 子任务配置 dict，至少包含：
                - goal (str): 子任务的目标描述
                - agent_type (str): 子 Agent 类型，如 "explore", "librarian"
                - max_retries (int, optional): 最大重试次数，默认 3
                - timeout_ms (int, optional): 超时时间（毫秒）
                - depends_on (list[str], optional): 依赖的子任务 ID 列表
                各平台可定义自己的扩展字段。

        Returns:
            str: 子任务的唯一标识符（task_id），用于后续跟踪和结果收集。

        Raises:
            NotImplementedError: 子类未实现此方法。
        """

    def on_subagent_lifecycle(self, event: str, data: Dict[str, Any]) -> None:
        """子 Agent 生命周期事件回调（存根方法，默认 no-op）。

        当平台支持子 Agent 生命周期监听时，此方法由平台在
        子 Agent 的各个阶段（创建、启动、完成、失败）自动调用。
        不支持的平台可忽略此方法（默认实现仅记录日志）。

        Args:
            event: 生命周期事件类型。
                建议值: "created", "started", "completed", "failed", "cancelled"
            data: 事件相关数据 dict，至少包含：
                - task_id (str): 子任务 ID
                其他字段因平台和事件类型而异：
                - "started": 含 agent_type, goal
                - "completed": 含 summary, result
                - "failed": 含 error, retry_count
        """
        task_id = data.get("task_id", "unknown")
        logger.warning(
            "on_subagent_lifecycle not supported on this platform — "
            "ignored event=%s task_id=%s",
            event,
            task_id,
        )
