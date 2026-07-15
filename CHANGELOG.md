# Changelog

All notable changes to the oh-my-deepseek-harness project.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v2.0.0] - 2026-07-16

Major restructure from v1.0.0 with 4-layer architecture (Hermes Plugin + Context Engine + MCP Microservices + Platform Core) and 14 innovation patterns (I-01 through I-14) fully implemented.

### New Features

- **I-01 约束免疫**：硬约束检测 + 定期审计 cron，自动解析"不能/不要"类指令，记录违反日志，每日 3:00 cron 审计报告
- **I-02 双向原语**：L1 荣辱观 + L2 思维方式 + L3 排除清单三层认知架构
- **I-03 外层上下文压缩**：Context Engine 对原始对话历史做摘要压缩，降低 Token 消耗
- **I-04 时间衰减上下文排序**：近期内容保留细节，远期内容自动摘要化
- **I-05 Memory 标签化中间层**：Memory Tagger MCP 服务（后独立并演化为 I-12）
- **I-06 级联 Plan 修正**：Plan Engine MCP 服务，PlanStep 变更后自动级联影响分析
- **I-07 内层上下文压缩**：Context Engine 在 system prompt 级别做结构性压缩
- **I-08 范围控制**：Layer 1 Metis 反向追问，自动生成排除清单，防止范围蔓延
- **I-09 Skill 提议**：长对话结束前自动检测可复用 Skill 模式，追加到 feedback-lessons.md
- **I-10 7+1 意图分类**：refactor / new / medium / collaboration / architecture / research / simple + spec_driven 兜底，绑定不同的面谈深度、Plan 粒度、审查标准和执行模式
- **I-11 Checkpoint 快照审查**：Checkpoint Review MCP 服务，快照对比 + 回滚决策状态机
- **I-12 Memory λ 函数过滤**：Memory Tagger MCP 服务，λ 表达式过滤非相关记忆，提高检索精度
- **I-13 结构性上下文压缩**：Context Engine 按数据结构（代码/配置/文档）选择压缩策略
- **I-14 Provider 感知 Reasoning 剥离**：按 provider 类型选择性剥离 thinking tokens，DeepSeek / OpenAI 剥离（不计入 cache），Anthropic 保留（signed thinking block 需回传）

### Infrastructure

- **三台 MCP 微服务**：
  - `plan-engine`（端口 8200）：OKR PlanStep DAG 编排引擎，SQLite 持久化
  - `memory-tagger`（端口 8100）：Memory 标签中间层 + λ 过滤，SQLite 持久化
  - `checkpoint-review`（端口 8300）：Checkpoint 快照审查状态机，SQLite 持久化
- **平台无关核心**：`packages/platform_core/` 纯 Python 模块，零 Hermes 依赖，可独立 `pip install`
- **Hermes ↔ 平台适配层**：`adapter.py` 解耦插件与 Hermes 的依赖关系
- **上下文引擎插件**：`plugins/deepseek-context/` 独立 LLM 客户端，绕过 Hermes auxiliary_client 直接调用 DeepSeek API
- **install.sh**：从 v1 升级到完整安装，自动备份 SOUL.md / MEMORY.md / USER.md，创建插件软链接，注册 Hook，安装依赖
- **测试套件**：144 个 pytest 用例覆盖全部 14 个创新模式，7 个测试文件
- **类型安全修复**：修复 `immune_audit.py` 类型错误
- **Cron 自动化**：`crons/immune-audit.cron` 每日 3:00 约束审计；`scripts/daily-reflection.sh` 三省吾身

### Breaking Changes

- **移除 `sync-deepseek-harness.sh`**：个人多机同步脚本不属于核心功能，v2.0.0 不再提供
- **README 重写**：从 v1 单层插件结构更新为 v2 四层架构 + 14 创新模式表 + 路线图
- **插件目录重命名**：从 `plugins/digital-twin/` 更名为 `plugins/deepseek-harness/`
- **移除 git 跟踪的符号链接**：`deepseek_harness` 和 `deepseek_context` 软链接不再被 git 跟踪
- **README 中移除 digital-twin 引用**：全部替换为 deepseek-harness

### Full Commit History

```
7e8c268 docs: rewrite README.md with v2 architecture, 14 innovation patterns, roadmap checklist
fba8b0a fix: remove git-tracked symlinks for deepseek_harness and deepseek_context
379cff4 chore: remove sync script, clean artifacts, fix install.sh, type errors and author fields
ba7408a test: add comprehensive test suite for v2 all modules (144 test cases, 7 test files, 14 patterns)
948a720 feat(mcp): add checkpoint-review MCP server (I-11)
c434423 feat(mcp): add memory-tagger MCP server (I-12)
6c15e8a feat(mcp): add plan-engine MCP server (I-06)
a924e28 feat(context): add deepseek-context engine plugin (I-03/I-04/I-07/I-13)
e2bb2cf feat(plugin): add I-01 periodic immune audit cron
b3d3309 feat(plugin): add I-14 provider-aware reasoning content stripping
e6b6bfa feat(plugin): add I-10 7+1 intent classification and I-08 Metis reverse questioning
bfc9650 feat(plugin): add I-01 constraint violation detection (assessor) and I-09 skill proposal (learner)
5840935 feat(gate): add I-02 bidirectional primitives and I-08 scope creep detection
2120ca9 feat(plugin): upgrade plugin.yaml with v2 hooks, MCP declarations
53f81c8 Add .gitignore rules for AI agent runtime artifacts
```

---

## [v1.0.0] - 2026-07-14

Initial release of oh-my-deepseek-harness (originally scoped as digital-twin plugin).

### Features

- **认知门控**：`pre_llm_call` hook 注入 L1 / L2 认知提醒，每轮对话自动引导模型的思维方向
- **工具质量评估**：`post_tool_call` 对 write / read / bash 等工具调用结果做内容完整性检查，拦截空结果和异常输出
- **会话学习**：`on_session_end` 记录反馈，在对话结束时自动总结可复用的经验模式
- **子任务监控**：`subagent_start` / `subagent_stop` 追踪子任务生命周期，记录每个子任务的起止时间和结果状态
- **多机同步**：AIPC 到 MacBook Air 的单向同步脚本 `sync-deepseek-harness.sh`（v2.0.0 中移除）
- **每日反思**：`scripts/daily-reflection.sh` 读取 Hermes state.db，统计对话轮次和 Token 消耗，生成反思报告

### Plugin Architecture

```
plugins/deepseek-harness/
├── plugin.yaml        # 插件声明
├── __init__.py        # 注册入口
├── gate.py            # 认知门控（pre_llm_call）
├── assessor.py        # 工具质量评估（post_tool_call）
├── learner.py         # 会话学习（on_session_end）
└── subagent_watch.py  # 子任务监控（subagent_start/stop）
```

### Commits

```
4b0dc84 Update daily-reflection.sh: rename lock file from digital-twin to deepseek-harness
96b0625 Update test files: adjust sys.path to reference plugins/deepseek-harness/
2b90386 Update README.md: replace all digital-twin references with deepseek-harness
b2a26e0 Rename sync script: scripts/sync-digital-twin.sh → scripts/sync-deepseek-harness.sh
60d4505 Rename plugin directory: plugins/digital-twin/ → plugins/deepseek-harness/
7b0e424 Update install.sh: replace all digital-twin references with deepseek-harness
cabdd83 test(plugin): add unit tests for all four plugin modules
fdeff99 feat(scripts): add install.sh with backup, migration, and plugin install
a2269f8 feat(scripts): add sync and daily-reflection scripts
056c414 feat(plugin): add assessor, learner, subagent_watch modules
d05be4a feat(plugin): implement gate.py with pre_llm_call cognitive gate
1b30c1b feat(plugin): add digital-twin plugin skeleton
7cb15a8 feat(scaffold): init oh-my-deepseek-harness project skeleton
```

---

[v2.0.0]: https://github.com/yuanchenglu/oh-my-deepseek-harness/releases/tag/v2.0.0
[v1.0.0]: https://github.com/yuanchenglu/oh-my-deepseek-harness/releases/tag/v1.0.0
