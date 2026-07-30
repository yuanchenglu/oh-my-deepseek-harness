"""adapter.py 单元测试 — 验证 PlatformAdapter ABC。

测试 platform_core.adapter 中：
  - PlatformAdapter ABC 抽象方法
  - 子类必须实现所有抽象方法
  - on_subagent_lifecycle() 存根默认行为
"""

from abc import ABC
from unittest import mock

import pytest

from platform_core.adapter import PlatformAdapter


class TestPlatformAdapterABC:
    def test_is_abstract(self):
        """PlatformAdapter 是抽象类，不能直接实例化。"""
        with pytest.raises(TypeError):
            PlatformAdapter()

    def test_requires_get_messages(self):
        """缺少 get_messages 子类不能实例化。"""
        with pytest.raises(TypeError):

            class BadAdapter(PlatformAdapter):
                pass

            BadAdapter()  # 应抛出 TypeError

    def test_concrete_subclass_works(self):
        """实现所有抽象方法的子类可实例化。"""

        class GoodAdapter(PlatformAdapter):
            def get_messages(self):
                return []

            def inject_system_prompt(self, prompt):
                pass

            def get_tool_results(self):
                return []

            def on_session_end(self):
                pass

            def dispatch_subtask(self, config):
                return "task-1"

        adapter = GoodAdapter()
        assert isinstance(adapter, PlatformAdapter)

    def test_default_on_subagent_lifecycle(self):
        """on_subagent_lifecycle 默认不抛异常。"""

        class GoodAdapter(PlatformAdapter):
            def get_messages(self):
                return []

            def inject_system_prompt(self, prompt):
                pass

            def get_tool_results(self):
                return []

            def on_session_end(self):
                pass

            def dispatch_subtask(self, config):
                return "task-1"

        adapter = GoodAdapter()
        # 不应抛异常
        adapter.on_subagent_lifecycle("started", {"task_id": "t1", "agent_type": "explore"})


class TestConcreteAdapter:
    """用具体子类验证所有方法的行为。"""

    @pytest.fixture
    def adapter(self):
        class TestAdapter(PlatformAdapter):
            def __init__(self):
                self.messages = []
                self.prompt = ""
                self.results = []
                self.session_ended = False
                self.tasks = []

            def get_messages(self):
                return self.messages

            def inject_system_prompt(self, prompt):
                self.prompt = prompt

            def get_tool_results(self):
                return self.results

            def on_session_end(self):
                self.session_ended = True

            def dispatch_subtask(self, config):
                task_id = f"task-{len(self.tasks) + 1}"
                self.tasks.append((task_id, config))
                return task_id

        return TestAdapter()

    def test_get_messages(self, adapter):
        assert adapter.get_messages() == []
        adapter.messages = [{"role": "user", "content": "hi"}]
        assert len(adapter.get_messages()) == 1

    def test_inject_system_prompt(self, adapter):
        adapter.inject_system_prompt("test prompt")
        assert adapter.prompt == "test prompt"

    def test_get_tool_results(self, adapter):
        assert adapter.get_tool_results() == []

    def test_on_session_end(self, adapter):
        assert adapter.session_ended is False
        adapter.on_session_end()
        assert adapter.session_ended is True

    def test_dispatch_subtask(self, adapter):
        task_id = adapter.dispatch_subtask({"goal": "探索", "agent_type": "explore"})
        assert task_id == "task-1"
        assert len(adapter.tasks) == 1
        assert adapter.tasks[0][1]["goal"] == "探索"
