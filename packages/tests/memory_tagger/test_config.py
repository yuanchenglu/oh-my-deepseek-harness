"""Memory Tagger 配置测试 — 验证 λ 层级映射和任务类型解析。

测试 platform_core.memory_tagger.config 中的：
  - LAMBDA_LEVELS 常量
  - TASK_TYPE_MAPPINGS 常量
  - resolve_layers()
  - resolve_task_config()
"""

from platform_core.memory_tagger.config import (
    LAMBDA_LEVELS,
    TASK_TYPE_MAPPINGS,
    DEFAULT_LAMBDA,
    resolve_layers,
    resolve_task_config,
)


class TestLambdaLevels:
    def test_contains_three_levels(self):
        assert len(LAMBDA_LEVELS) == 3

    def test_weak_level_min(self):
        assert LAMBDA_LEVELS[0]["min"] == 0.0

    def test_strong_level_max(self):
        assert LAMBDA_LEVELS[-1]["max"] == 1.0


class TestTaskTypeMappings:
    def test_convergent_has_keywords(self):
        assert len(TASK_TYPE_MAPPINGS["convergent"]["keywords"]) > 0

    def test_divergent_has_keywords(self):
        assert len(TASK_TYPE_MAPPINGS["divergent"]["keywords"]) > 0

    def test_mixed_has_keywords(self):
        assert len(TASK_TYPE_MAPPINGS["mixed"]["keywords"]) > 0


class TestResolveLayers:
    def test_low_lambda_weak(self):
        layers = resolve_layers(0.0)
        assert "constraint" in layers
        assert "pattern" not in layers

    def test_mid_lambda_mixed(self):
        layers = resolve_layers(0.5)
        assert "constraint" in layers
        assert "preference" in layers
        assert "decision" in layers

    def test_high_lambda_strong(self):
        layers = resolve_layers(1.0)
        assert "constraint" in layers
        assert "preference" in layers
        assert "style" in layers
        assert "decision" in layers
        assert "pattern" in layers

    def test_out_of_range_lambda_falls_to_weak(self):
        layers = resolve_layers(-0.1)
        assert "constraint" in layers


class TestResolveTaskConfig:
    def test_convergent_config(self):
        cfg = resolve_task_config("convergent")
        assert cfg["suggested_lambda"] == 1.0

    def test_divergent_config(self):
        cfg = resolve_task_config("divergent")
        assert cfg["suggested_lambda"] == 0.0

    def test_mixed_config_default(self):
        cfg = resolve_task_config("mixed")
        assert cfg["suggested_lambda"] == 0.5

    def test_unknown_type_falls_to_mixed(self):
        cfg = resolve_task_config("unknown_type")
        assert cfg["suggested_lambda"] == 0.5
