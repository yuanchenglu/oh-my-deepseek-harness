# oh-my-deepseek-harness

针对 DeepSeek 做了深度优化的 Agent 插件系统。15 项 Agent 工程模式已实现。

[English](README_EN.md) | 简体中文

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-green)](https://python.org)
[![Hermes Agent v0.18+](https://img.shields.io/badge/hermes-%3E%3D0.18.0-purple)](https://github.com/HermesAgent/hermes)
[![Tests](https://img.shields.io/badge/tests-142%20cases-brightgreen)](tests/)

---

## 为什么需要这个项目

DeepSeek V4 有多项独特的 API 层和模型层物理特性（reasoning_content 结构、DSML 工具调用格式、Quick Instruction 路由、推理强度控制等），但通用 Agent 框架没有为这些特性做专门优化。同时，Agent 工程实践（认知门控、约束免疫、意图路由等）也缺乏系统化落地。

这个项目以 Hermes Agent Plugin 系统为基础，通过插件层、独立上下文引擎和合并微服务三层架构，将 DeepSeek 的物理特性一一落地为可运行的 Agent 能力。不改一行 Hermes 核心代码。

## 已实现的核心功能

- ✅ **认知门控**（I-02 双向原语 + I-08 范围控制）：每轮对话自动注入 L1 荣辱观、L2 思维方式和 L3 排除清单
- ✅ **约束免疫系统**（I-01 硬约束检测 + 定期审计）：检测"不能/不要"等约束，自动记录违反日志，每日 cron 审计
- ✅ **意图路由**（I-10 7+1 分类 + 策略绑定）：关键词匹配识别 7+1 种用户意图，绑定不同的面谈深度、Plan 粒度、审查标准和执行模式
- ✅ **工具质量评估**（post_tool_call 内容完整性检查）：对 write/read/bash 等工具调用结果自动校验，拦截空结果和异常
- ✅ **会话学习**（I-09 Skill 提议）：长对话自动识别可复用的 Skill 模式，追加到 feedback-lessons.md
- ✅ **三省吾身**：每日 cron 读取 state.db 统计对话轮次和 Token 消耗，生成反思报告到 reflections/
- ✅ **意图→推理提示路由**（I-17 基于意图动态提示）：根据 I-10 意图分类结果，对 architecture/research/collaboration 类任务注入高复杂度推理提示，对 refactor/new/medium 类任务注入中等复杂度推理提示。注：因 Hermes hook 协议限制，未使用 API 参数 reasoning_effort，改为提示词注入
- ✅ **时效信息注入**（I-18 降级方案）：首轮对话自动注入当前日期时间信息。注：API 拒绝 role=latest_reminder（400），降级为 context 文本注入
- ✅ **子任务监控**：追踪 subagent_start/subagent_stop，记录每个子任务的起止和结果
- ✅ **上下文压缩引擎**（I-03/I-04/I-07/I-13 独立 Context Engine Plugin）：使用 DeepSeek API 独立压缩上下文，不依赖 Hermes auxiliary_client
- ✅ **Harness Server 合并服务**（I-06/I-11/I-12 三合一）：单 FastAPI 服务 + 单 SQLite，通过 ctx.register_tool() 注册 9 个工具暴露给 LLM：
  - plan_create/plan_update_step/plan_cascade/plan_status（I-06 级联规划）
  - memory_tag/memory_query/memory_filter（I-12 记忆标签 + λ 过滤）
  - checkpoint_create/checkpoint_review（I-11 快照审查）

## 架构（3 层）

```
┌──────────────────────────────────────────────────────────────┐
│  Layer 1: Hermes Plugin (plugins/deepseek-harness/)         │
│  9 个 Python 文件 · 8 个 Hook 注册点 · 9 个注册工具 · v2.2  │
│  pre_llm_call(5) + post_tool_call + on_session_end          │
│  + subagent_start + subagent_stop + 9 tools                 │
├──────────────────────────────────────────────────────────────┤
│  Layer 2: Context Engine Plugin (plugins/deepseek-context/) │
│  独立 LLM 客户端 · 不依赖 Hermes auxiliary_client           │
│  I-03/I-04/I-07/I-13 四个模式落地于此                       │
├──────────────────────────────────────────────────────────────┤
│  Layer 3: Harness Server (mcp/harness_server/)              │
│  单 FastAPI 服务 · 单 SQLite · 端口 8200                    │
│  I-06 级联规划 + I-12 记忆标签 + I-11 快照审查              │
│  通过 ctx.register_tool() 暴露 9 个工具给 LLM              │
└──────────────────────────────────────────────────────────────┘
```

### Layer 1: Hermes Plugin（主插件）

`plugins/deepseek-harness/` 包含 10 个文件，通过 8 个 Hook 点 + 9 个工具注入：

| 文件 | Hook | 触发时机 | 功能 |
|------|------|---------|------|
| gate.py | pre_llm_call | 每轮 LLM 调用前 | 认知提醒 + MAP 导航 |
| intent_router.py | pre_llm_call | 每轮 LLM 调用前 | 7+1 意图分类 + 策略绑定 + 排除清单 |
| reasoning_effort.py | pre_llm_call | 首轮 | 意图→推理提示路由（I-17） |
| latest_reminder.py | pre_llm_call | 首轮 | 时效信息注入（I-18 降级方案） |
| immune_audit.py | pre_llm_call | 首轮可选注入 | 约束违反检测提醒 |
| assessor.py | post_tool_call | 每个工具调用后 | 内容完整性检查 |
| learner.py | on_session_end | Session 结束时 | Skill 提议追加到反馈记录 |
| subagent_watch.py | subagent_start/stop | 子任务启停时 | 记录子任务状态和结果 |
| tools.py | register_tool(×9) | 插件注册时 | 9 个工具暴露给 LLM（I-06/I-11/I-12） |

### Layer 2: Context Engine Plugin（上下文引擎）

`plugins/deepseek-context/` 是一个独立的 LLM 客户端插件，使用 DeepSeek API 直接调用，绕过 Hermes 的 auxiliary_client 机制。负责上下文的压缩、摘要和结构化重组（I-03 外层压缩 / I-04 时间衰减 / I-07 内层压缩 / I-13 结构性压缩）。

### Layer 3: Harness Server（合并微服务）

`mcp/harness_server/` 是单一 FastAPI 服务，合并了原来的 plan-engine、memory-tagger、checkpoint-review 三个独立服务。通过 `ctx.register_tool()` 注册 9 个工具暴露给 LLM：

- **plan** 端点（I-06）：plan_create / plan_update_step / plan_cascade / plan_status
- **memory** 端点（I-12）：memory_tag / memory_query / memory_filter
- **checkpoint** 端点（I-11）：checkpoint_create / checkpoint_review

单 SQLite 持久化（~/.hermes/mcp/harness.db），插件注册时自动拉起。

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
│   └── harness_server/             # 合并服务（I-06+I-11+I-12, 端口 8200）
│       ├── server.py, models.py, storage.py, config.yaml
├── scripts/
│   ├── install.sh                 # 一键安装 + 自动备份
│   └── daily-reflection.sh        # 每日三省吾身（cron 用）
├── crons/
│   └── immune-audit.cron          # I-01 定期约束审计（每日 3:00）
├── tests/                         # pytest 单元测试（162 用例, 16 文件）
├── docs/research/                 # 调研文档
├── README.md
└── LICENSE                        # MIT
```

## 14 项 Agent 工程模式 + 即将到来的 DeepSeek V4 物理特性

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
| I-11 | Checkpoint 快照审查 | ✅ | harness_server checkpoint_create/review 工具，快照对比 + 调整建议 |
| I-12 | Memory λ 函数过滤 | ✅ | harness_server memory_tag/query/filter 工具，λ 表达式过滤非相关记忆 |
| I-13 | 结构性上下文压缩 | ✅ | Context Engine 按数据结构（代码/配置/文档）选择压缩策略 |
| I-14 | Provider 感知 Reasoning 剥离 | ❌ 已移除 | dead code（hook 传副本无效）+ 设计与 V4 API 冲突（tool-call 轮必须回传 reasoning_content） |
| I-15 | DSML 工具调用优化 | ⚪ 无需实现 | DeepSeek 服务器端自动转 OpenAI 格式，客户端无需解析（spike 验证） |
| I-16 | Quick Instruction 路由 | 🔲 不可实现 | V4 内部机制，OpenAI 兼容 API 不可用，由 I-10 意图路由替代 |
| I-17 | 意图→推理提示路由 | ✅ | 根据 I-10 意图分类注入推理提示。注：因 hook 限制未用 API 参数 reasoning_effort |
| I-18 | 时效信息注入（降级） | ✅ | 首轮注入时间信息。注：API 拒绝 role=latest_reminder（400），降级为 context 注入 |

全部可行模式已实现。I-14 因技术限制移除，I-15 服务器端已处理，I-16 API 不可用。

## 路线图

- ✅ **v1.0 基础插件**：认知门控 + 质量评估 + 学习总结 + 子任务监控（已完成）
- ✅ **v2.0 架构**：Plugin + Context Engine + 微服务（已完成）
- ✅ **v2.1 V4 特性验证**：Spike 验证 I-15~I-18 + 实现 I-17/I-18（已完成）
- ✅ **v2.2 修正与合并**：移除 I-14 dead code、合并 3 MCP 为 1 + ctx.register_tool 接通、修正 I-18 注释和 I-15 论文（已完成）
- 🔲 **更多创新模式**：持续挖掘 DeepSeek 的新 API 层特性，扩展 I-19 及以后
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

**Harness Server 怎么启动？**
插件注册时通过 `tools.py` 的 `_ensure_server_running()` 自动拉起后台进程（端口 8200）。工具调用时如果服务未运行会自动启动。

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
