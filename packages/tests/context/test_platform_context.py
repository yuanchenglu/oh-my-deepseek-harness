"""PlatformContext 单元测试 — 验证 ABC 和 NullPlatformContext。

测试 platform_core.context 中的：
  - PlatformContext ABC 抽象方法
  - NullPlatformContext 默认实现
"""

import pytest

from platform_core.context import (
    PlatformContext,
    NullPlatformContext,
    compress_messages,
)


class TestPlatformContextABC:
    def test_is_abstract(self):
        """PlatformContext 不能直接实例化。"""
        with pytest.raises(TypeError):
            PlatformContext()

    def test_concrete_subclass_works(self):
        class MinimalContext(PlatformContext):
            def get_messages(self):
                return []

            def get_system_prompt(self):
                return ""

            def compress(self, messages=None, *, intent="default", summarizer=None, quiet=False, **kwargs):
                return messages or []

            def get_hard_constraints(self):
                return []

        ctx = MinimalContext()
        assert ctx.get_messages() == []
        assert ctx.get_system_prompt() == ""
        assert ctx.get_hard_constraints() == []


class TestNullPlatformContext:
    @pytest.fixture
    def ctx(self):
        return NullPlatformContext()

    def test_get_messages_default(self, ctx):
        assert ctx.get_messages() == []

    def test_get_system_prompt_default(self, ctx):
        assert ctx.get_system_prompt() == ""

    def test_get_hard_constraints_default(self, ctx):
        assert ctx.get_hard_constraints() == []

    def test_compress_empty(self, ctx):
        assert ctx.compress([]) == []

    def test_compress_too_few(self, ctx):
        msgs = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]
        assert ctx.compress(msgs) == msgs

    def test_compress_pipeline(self, ctx):
        """足够多的消息触发压缩。"""
        msgs = [{"role": "system", "content": "test"}]
        for i in range(30):
            msgs.append({"role": "user", "content": f"q{i}"})
            msgs.append({"role": "assistant", "content": f"a{i}"})
        compressed = ctx.compress(msgs, quiet=True)
        assert len(compressed) < len(msgs)

    def test_compress_with_custom_kwargs(self, ctx):
        msgs = [{"role": "system", "content": "test"}]
        for i in range(30):
            msgs.append({"role": "user", "content": f"q{i}"})
            msgs.append({"role": "assistant", "content": f"a{i}"})
        compressed = ctx.compress(
            msgs, quiet=True,
            threshold_tokens=96000, tail_token_budget=10000,
        )
        assert len(compressed) < len(msgs)

    def test_compress_with_intent(self, ctx):
        msgs = [{"role": "system", "content": "test"}]
        for i in range(30):
            msgs.append({"role": "user", "content": f"q{i}"})
            msgs.append({"role": "assistant", "content": f"a{i}"})
        compressed = ctx.compress(msgs, intent="convergent", quiet=True)
        assert len(compressed) < len(msgs)
