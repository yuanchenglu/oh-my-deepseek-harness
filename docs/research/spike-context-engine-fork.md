# Spike: Context Engine 独立 fork 可行性 + MCP 自动发现

## 结论

**ContextEngine 独立 fork 可行（大概率 90%）**

DeepSeekContextEngine 已在插件目录 `plugins/deepseek-context/` 中成功实现，
核心算法已从 Hermes ContextCompressor 成功 fork 为纯 Python 独立模块，
不依赖 `hermes_cli`/`hermes_core`/`hermes_constants`。

## 依赖分析详情

### Hermes ContextCompressor 的 import 依赖链

| 导入 | 来源 | 可移植性 | 替代方案 |
|------|------|---------|---------|
| `agent.auxiliary_client.call_llm` | Hermes agent | ❌ 2615 行复杂模块 | 直接使用 `openai` SDK |
| `agent.context_engine.ContextEngine` | Hermes agent | ✅ ABC 无额外依赖 | 直接导入 |
| `agent.model_metadata.MINIMUM_CONTEXT_LENGTH` | Hermes agent | ⚠️ 简单常量 | 本地定义 |
| `agent.model_metadata.get_model_context_length` | Hermes agent | ❌ 依赖 hermes_constants | 构造函数传入 |
| `agent.model_metadata.estimate_messages_tokens_rough` | Hermes agent | ✅ 1 行纯函数 | 已 fork |

### 核心压缩算法可移植性

**可移植（纯 Python）：**
- `_summarize_tool_result`, `_prune_old_tool_results`, `_serialize_for_summary`
- `_sanitize_tool_pairs`, `_find_tail_cut_by_tokens`, `_align_boundary_*`
- `_compute_summary_budget`, `compress()` 编排逻辑（除 LLM 调用）

**不可移植（需替换）：**
- `_generate_summary` 中的 `call_llm()` → `openai.ChatCompletion.create()`
- `get_model_context_length()` → 配置参数注入
- `update_model()` → 简化版本

## 文件结构

```
plugins/deepseek-context/
├── __init__.py       # DeepSeekContextEngine (extends ContextEngine)
├── compressor.py     # 独立算法模块（无 Hermes 依赖）
├── plugin.yaml       # type: context_engine
└── config.yaml       # 配置默认值

tests/
└── test_mcp_discovery.py  # MCP Server 启动/停止测试
```

## 测试结果

### compressor.py 独立 import
- ✅ 无 hermes_cli/hermes_core/hermes_constants 导入
- ✅ estimate_messages_tokens_rough 可独立工作
- ✅ DeepSeekCompressor 可独立实例化
- ✅ serialize_for_summary/prune/sanitize/find_tail 全部通过

### DeepSeekContextEngine 实现
- ✅ 通过 Hermes plugin path 可正常 import
- ✅ 实例化成功（含上下文长度计算）
- ✅ compress() 签名正确（messages, current_tokens）
- ✅ should_compress/update_from_response 正常
- ✅ 无 hermes_cli/hermes_core/hermes_constants 导入

### MCP Echo Server
- ✅ Initialize 握手成功
- ✅ tools/list 返回工具列表
- ✅ tools/call 正常调用并返回结果
- ✅ Server 正常停止

## 注意事项

1. **LLM 调用替代**：compressor.py 使用 openai SDK 直接调用 DeepSeek API，
   比 Hermes 的 call_llm（2615 行）轻量得多，但缺少 provider 自动回退。

2. **plugin type 注册路径**：当前 plugin.yaml 使用 type=context_engine，
   但 Hermes 的 run_agent.py 优先从 plugins/context_engine/<name>/ 加载。
   需确认 get_plugin_context_engine() 是否支持。

3. **Python 版本**：Hermes ≥ 3.11，本地系统 3.9，测试使用 Homebrew 3.13。
