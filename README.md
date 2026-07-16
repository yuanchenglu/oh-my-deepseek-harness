# oh-my-deepseek-harness

市面上唯一针对 DeepSeek 做了 14 项深度优化的 Agent 插件系统。

[English](README_EN.md) | 简体中文

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-green)](https://python.org)
[![Hermes Agent v0.18+](https://img.shields.io/badge/hermes-%3E%3D0.18.0-purple)](https://github.com/HermesAgent/hermes)
[![Tests](https://img.shields.io/badge/tests-144%20cases-brightgreen)](tests/)

---

## 为什么需要这个项目

DeepSeek 有 14 项独特的物理特性（推理能力、KV Cache 行为、上下文窗口结构、thinking token 格式等），但通用 Agent 框架没有为这些特性做专门优化。结果是：Token 浪费、上下文污染、推理能力无法充分发挥。

这个项目以 Hermes Agent Plugin 系统为基础，通过插件、独立上下文引擎、MCP 微服务和平台无关核心四层架构，将 DeepSeek 的物理特性一一落地为可运行的 Agent 能力。不改一行 Hermes 核心代码。

## 已实现的核心功能

- ✅ **认知门控**（I-02 双向原语 + I-08 范围控制）：每轮对话自动注入 L1 荣辱观、L2 思维方式和 L3 排除清单
- ✅ **约束免疫系统**（I-01 硬约束检测 + 定期审计）：检测"不能/不要"等约束，自动记录违反日志，每日 cron 审计
- ✅ **意图路由**（I-10 7+1 分类 + 策略绑定）：关键词匹配识别 7+1 种用户意图，绑定不同的面谈深度、Plan 粒度、审查标准和执行模式
- ✅ **Reasoning 剥离**（I-14 Provider 感知剥离）：对 DeepSeek/OpenAI 剥离 thinking tokens（不计入 cache，纯浪费），对 Anthropic 保留（signed thinking block 需回传）
- ✅ **工具质量评估**（post_tool_call 内容完整性检查）：对 write/read/bash 等工具调用结果自动校验，拦截空结果和异常
- ✅ **会话学习**（I-09 Skill 提议）：长对话自动识别可复用的 Skill 模式，追加到 feedback-lessons.md
- ✅ **三省吾身**：每日 cron 读取 state.db 统计对话轮次和 Token 消耗，生成反思报告到 reflections/
- ✅ **子任务监控**：追踪 subagent_start/subagent_stop，记录每个子任务的起止和结果
- ✅ **上下文压缩引擎**（I-03/I-04/I-07/I-13 独立 Context Engine Plugin）：使用 DeepSeek API 独立压缩上下文，不依赖 Hermes auxiliary_client
- ✅ **OKR Plan Engine MCP**（I-06 级联修正 FastAPI 服务）：PlanStep DAG 编排 + 级联修正，端口 8200
- ✅ **Memory Tagger MCP**（I-12 λ 过滤 FastAPI 服务）：Memory 标签中间层 + λ 函数过滤，端口 8100
- ✅ **Checkpoint Review MCP**（I-11 快照审查 FastAPI 服务）：Checkpoint 快照审查状态机，端口 8300
- ✅ **平台无关核心**（packages/platform_core/）：纯 Python 模块，抽取插件通用逻辑，可脱离 Hermes 独立使用

## 架构（4 层）

```
┌──────────────────────────────────────────────────────────────┐
│  Layer 1: Hermes Plugin (plugins/deepseek-harness/)         │
│  9 个 Python 文件 · 8 个 Hook 注册点 · v2.0.0              │
│  pre_llm_call(4) + post_tool_call + on_session_end          │
│  + subagent_start + subagent_stop                           │
├──────────────────────────────────────────────────────────────┤
│  Layer 2: Context Engine Plugin (plugins/deepseek-context/) │
│  独立 LLM 客户端 · 不依赖 Hermes auxiliary_client           │
│  I-03/I-04/I-07/I-13 四个模式落地于此                       │
├──────────────────────────────────────────────────────────────┤
│  Layer 3: MCP Servers (mcp/)                                │
│  plan-engine:8200 · memory-tagger:8100 · checkpoint:8300    │
│  三台独立 FastAPI 微服务 · SQLite 持久化 · MCP 协议通信     │
├──────────────────────────────────────────────────────────────┤
│  Layer 4: Platform Core (packages/platform_core/)           │
│  纯 Python · 无 Hermes 依赖 · 可 pip install                │
│  gate/adapter/assessor/intent_router/reasoning_strip ...    │
└──────────────────────────────────────────────────────────────┘
```

### Layer 1: Hermes Plugin（主插件）

`plugins/deepseek-harness/` 包含 9 个文件，通过 8 个 Hook 点注入：

| 文件 | Hook | 触发时机 | 功能 |
|------|------|---------|------|
| gate.py | pre_llm_call | 每轮 LLM 调用前 | 认知提醒 + MAP 导航 |
| reasoning_strip.py | pre_llm_call | 每轮 LLM 调用前 | Provider 感知的 thinking token 剥离 |
| intent_router.py | pre_llm_call | 每轮 LLM 调用前 | 7+1 意图分类 + 策略绑定 + 排除清单 |
| immune_audit.py | pre_llm_call | 首轮可选注入 | 约束违反检测提醒 |
| assessor.py | post_tool_call | 每个工具调用后 | 内容完整性检查 |
| learner.py | on_session_end | Session 结束时 | Skill 提议追加到反馈记录 |
| subagent_watch.py | subagent_start/stop | 子任务启停时 | 记录子任务状态和结果 |

### Layer 2: Context Engine Plugin（上下文引擎）

`plugins/deepseek-context/` 是一个独立的 LLM 客户端插件，使用 DeepSeek API 直接调用，绕过 Hermes 的 auxiliary_client 机制。负责上下文的压缩、摘要和结构化重组（I-03 外层压缩 / I-04 时间衰减 / I-07 内层压缩 / I-13 结构性压缩）。

### Layer 3: MCP Servers（微服务层）

三个独立运行的 FastAPI 微服务，通过 MCP 协议与 Hermes 通信：

- **plan-engine**（端口 8200）：OKR PlanStep DAG 编排引擎，支持多级 Plan 的级联修正（I-06）
- **memory-tagger**（端口 8100）：Memory 内容标签化和 λ 函数过滤（I-12）
- **checkpoint-review**（端口 8300）：Checkpoint 快照审查状态机，支持多轮 review 工作流（I-11）

所有服务使用 SQLite 持久化，插件启动时自动拉起（auto_start: true）。

### Layer 4: Platform Core（平台无关核心）

`packages/platform_core/` 是纯 Python 模块，从主插件中提取的平台无关逻辑。包含 gate、assessor、intent_router、reasoning_strip、learner、adapter 等模块，以及 checkpoint、memory_tagger、plan_engine、context 等子包。可单独 pip install，不依赖 Hermes 任何代码。

## 快速开始

```bash
git clone https://github.com/yuanchenglu/oh-my-deepseek-harness.git
cd oh-my-deepseek-harness

# 预览备份计划（不执行任何写操作）
bash scripts/install.sh --dry-run

# 执行安装（自动备份已有记忆，不覆盖不删除）
bash scripts/install.sh

# 验证插件已注册
hermes plugins list | grep deepseek
```

安装脚本会自动完成：备份 SOUL.md/MEMORY.md/USER.md → 创建插件软链接 → 注册 Hook → 安装依赖。

## 目录结构

```
oh-my-deepseek-harness/
├── plugins/
│   ├── deepseek-harness/          # 主插件（9 文件, 8 hooks, v2.0.0）
│   │   ├── plugin.yaml            # 插件声明 + I-01~I-14 映射
│   │   ├── __init__.py            # 注册入口（7 个 handler）
│   │   ├── gate.py                # 认知门控（I-02 + I-08）
│   │   ├── reasoning_strip.py     # Reasoning 剥离（I-14）
│   │   ├── intent_router.py       # 意图路由（I-10）
│   │   ├── immune_audit.py        # 约束审计（I-01）
│   │   ├── assessor.py            # 工具质量评估
│   │   ├── learner.py             # 会话学习（I-09）
│   │   ├── subagent_watch.py      # 子任务监控
│   │   └── strategies.yaml        # 7+1 意图策略配置
│   └── deepseek-context/          # 上下文引擎插件（独立 LLM 客户端）
│       ├── plugin.yaml
│       ├── __init__.py
│       ├── compressor.py          # I-03/I-04/I-07/I-13 压缩
│       └── config.yaml
├── mcp/
│   ├── plan-engine/               # OKR PlanStep DAG 引擎（I-06, 端口 8200）
│   │   ├── server.py, engine.py, models.py, storage.py
│   ├── memory-tagger/             # Memory λ 过滤（I-12, 端口 8100）
│   │   ├── server.py, tagger.py, models.py, storage.py, config.yaml
│   └── checkpoint-review/         # 快照审查状态机（I-11, 端口 8300）
│       ├── server.py, models.py, storage.py
├── packages/
│   └── platform_core/             # 平台无关核心（纯 Python, 0 Hermes 依赖）
│       ├── pyproject.toml
│       ├── gate.py, assessor.py, intent_router.py, ...
│       ├── adapter.py             # Hermes ↔ 平台 适配层
│       └── checkpoint/, context/, memory_tagger/, plan_engine/
├── scripts/
│   ├── install.sh                 # 一键安装 + 自动备份
│   └── daily-reflection.sh        # 每日三省吾身（cron 用）
├── crons/
│   └── immune-audit.cron          # I-01 定期约束审计（每日 3:00）
├── tests/                         # pytest 单元测试（144 用例, 14 文件）
├── docs/research/                 # 调研文档
├── README.md
└── LICENSE                        # MIT
```

## 14 个创新设计模式

| 编号 | 模式名称 | 状态 | 说明 |
|------|---------|------|------|
| I-01 | 硬约束检测与定期审计 | ✅ | 解析"不能/不要"类指令，记录违反日志，每日 cron 审计报告 |
| I-02 | 双向原语（肯定+否定） | ✅ | L1 荣辱观 + L2 思维方式 + L3 排除清单三层认知架构 |
| I-03 | 外层上下文压缩 | ✅ | Context Engine 对原始对话历史做摘要压缩 |
| I-04 | 时间衰减上下文排序 | ✅ | 近期内容保留细节，远期内容自动摘要化 |
| I-05 | Memory 标签化中间层 | ✅ | Memory Tagger MCP 服务（I-12 的原始编号，后独立为 MCP） |
| I-06 | 级联 Plan 修正 | ✅ | Plan Engine MCP 服务，PlanStep 变更后自动级联影响分析 |
| I-07 | 内层上下文压缩 | ✅ | Context Engine 在 system prompt 级别做结构性压缩 |
| I-08 | 范围控制（排除清单） | ✅ | Layer 1 Metis 反向追问，自动生成"本次不做"的排除清单 |
| I-09 | Skill 提议与自动学习 | ✅ | 长对话结束前检测可复用 Skill 模式，追加到反馈记录 |
| I-10 | 7+1 意图分类与策略绑定 | ✅ | refactor/new/medium/collaboration/architecture/research/simple + spec_driven 兜底 |
| I-11 | Checkpoint 快照审查 | ✅ | Checkpoint Review MCP 服务，快照对比 + 回滚决策 |
| I-12 | Memory λ 函数过滤 | ✅ | Memory Tagger MCP 服务，λ 表达式过滤非相关记忆 |
| I-13 | 结构性上下文压缩 | ✅ | Context Engine 按数据结构（代码/配置/文档）选择压缩策略 |
| I-14 | Provider 感知 Reasoning 剥离 | ✅ | 按 provider 类型选择性剥离 thinking tokens，DeepSeek/OpenAI 剥离，Anthropic 保留 |

全部 14 个模式已实现并在 v2.0.0 中落地。

## 路线图

- ✅ **v1.0 基础插件**：认知门控 + 质量评估 + 学习总结 + 子任务监控（已完成）
- ✅ **v2.0 四层架构**：Plugin + Context Engine + MCP 微服务 + Platform Core（已完成）
- ✅ **14 模式全实现**：I-01 到 I-14 全部落地（已完成）
- 🔲 **全特性稳定版**：将 DeepSeek 全部 14 项物理特性在一个版本中完全稳定落地，包括压力测试和边界场景覆盖
- 🔲 **平台适配**：将 platform_core 适配到 OpenCode、Claude Code 等其他 Agent 平台
- 🔲 **更多创新模式**：持续挖掘 DeepSeek 的新物理特性，扩展 I-15 及以后
- 🔲 **社区贡献指南**：完善 CONTRIBUTING.md 和开发者文档，降低参与门槛

## FAQ

**会修改 Hermes 核心代码吗？**
不会。全部使用 Hermes 官方 Plugin Hook 接口（pre_llm_call / post_tool_call / on_session_end / subagent_start / subagent_stop），这些接口已在源码中验证。Hermes 每日更新也不会产生 merge 冲突。

**会覆盖我已有的记忆吗？**
不会。安装前自动备份 SOUL.md、MEMORY.md、USER.md 为 `.bak.{timestamp}`，不删除原始内容。install.sh 默认启用 --dry-run 预览模式，安全无副作用。

**需要什么环境？**
- Hermes Agent ≥ v0.18.0
- Python ≥ 3.10
- rsync、sqlite3 CLI、pyyaml（部分功能需要，非必需）

**和 MemOS 插件冲突吗？**
不冲突。彼此使用不同的 Plugin Hook 和文件路径，独立工作。

**MCP 服务怎么启动？**
插件启动时自动拉起三个 MCP 服务（plan-engine:8200、memory-tagger:8100、checkpoint-review:8300）。也可以通过 plugin.yaml 中的 auto_start: true 控制。

**platform_core 能单独用吗？**
可以。`packages/platform_core/` 是纯 Python 模块，无 Hermes 依赖，可直接 pip install 或 import 使用。

## 卸载

```bash
hermes plugins disable deepseek-harness
rm -rf ~/.hermes/plugins/deepseek-harness/
```

安装时创建的备份文件（`*.bak.*`）会保留，需手动清理。

## License

MIT © 2026 yuanchenglu

---

*oh-my-deepseek-harness 是一个开源社区项目，与 DeepSeek 官方和 Hermes Agent 官方无直接关联。*
