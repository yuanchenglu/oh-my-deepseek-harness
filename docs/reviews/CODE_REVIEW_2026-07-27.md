# oh-my-deepseek-harness Code Review

- 审查日期：2026-07-27
- 审查分支基线：`master`
- 文档落地分支：`develop`
- 基线最新提交：`c4cb581`
- 审查类型：仓库级静态审查 + 契约审查 + 可安装性审查 + 测试设计审查
- 说明：本阶段不修改业务实现，仅固化问题、补充测试和规划修复顺序。

## 1. 执行摘要

项目已经形成三层产品叙事：Hermes Plugin、Context Engine、Harness Server，并围绕约束、意图、上下文、记忆、规划、Checkpoint 等 Agent Harness 问题做了大量原型实现。

但当前代码仍属于 **功能原型/设计验证阶段**，尚不满足 README 所表达的“安装后完整可用”标准。最主要的问题不是功能数量不足，而是：

1. 安装、启动、工具调用三条链路没有形成可验证闭环；
2. Context Engine 存在消息重复和历史数据丢失风险；
3. Session 状态、工具 Schema、API Model 之间缺少统一契约；
4. 多项对外产品能力的实际实现深度低于文档描述；
5. 测试数量较多，但缺少真正覆盖安装、进程、跨模块协议和故障降级的 E2E 测试。

### 1.1 综合评价

| 维度 | 评分 | 结论 |
|---|---:|---|
| 产品方向 | 8/10 | DeepSeek + Hermes Harness 定位有差异化 |
| 架构表达 | 7/10 | 分层明确，但运行边界和职责仍交叉 |
| 核心正确性 | 3/10 | 存在上下文损坏、状态污染和契约不一致 |
| 可安装性 | 2/10 | 文档安装路径无法保证 Server 正常启动 |
| 测试可信度 | 4/10 | 单元覆盖存在，真实集成覆盖不足 |
| 安全与隐私 | 4/10 | 本地端口默认安全，但外部摘要数据边界未定义 |
| 文档一致性 | 4/10 | README、版本号和代码行为存在多处偏差 |
| 开源就绪度 | 3/10 | 不建议以稳定版发布 |

## 2. 严重度定义

- **P0 / Blocker**：可能造成无法安装、核心能力不可用、上下文数据损坏或用户数据错误。
- **P1 / Critical**：关键功能不可靠、跨模块协议错误、长期运行产生严重数据问题。
- **P2 / Major**：工程质量、产品表述、可维护性和可观测性问题。
- **P3 / Minor**：代码风格、重复实现和局部优化问题。

## 3. P0 问题

### CR-P0-001 Harness Server 安装与启动链路不成立

**相关文件**：

- `scripts/install.sh`
- `plugins/deepseek-harness/tools.py`
- `mcp/harness_server/server.py`

**问题**：

- 安装脚本只复制两个 Plugin，没有复制或安装 `mcp/harness_server`；
- `tools.py` 通过相对路径查找 Server，安装后该路径不存在；
- `server.py` 使用包内相对导入，却以 `python server.py` 方式启动；
- 启动方设置 `HARNESS_SERVER_PORT`，服务读取 `HARNESS_PORT`；
- stdout/stderr 均被丢弃，用户无法诊断失败原因；
- 每次工具调用都可能启动新进程，没有先做 `/health` 探测和端口占用判断。

**影响**：九个注册工具在标准安装后可能全部不可用。

**修复原则**：

1. Harness Server 必须成为可安装 Python package；
2. 使用 `python -m harness_server.server` 或 Console Script；
3. 安装脚本必须安装完整 runtime dependencies；
4. 启动前健康检查，启动后 readiness 检查；
5. 日志保留到用户可访问路径；
6. 提供停止、重启和卸载机制。

### CR-P0-002 Context Engine 合并分支重复追加尾部消息

**相关文件**：`plugins/deepseek-context/__init__.py`

当摘要角色与尾部第一条消息角色冲突，需要把摘要合并进尾部消息时，代码先追加处理后的尾部，又追加原始尾部，导致最新消息和工具结果重复。

**影响**：

- 最新请求可能被模型执行两次；
- Token 使用量增加；
- Tool call/result 顺序可能失真；
- 会话状态不可预测。

### CR-P0-003 摘要失败时丢弃原始历史

**相关文件**：

- `plugins/deepseek-context/__init__.py`
- `plugins/deepseek-context/compressor.py`

当 DeepSeek API 调用失败、缺少 `openai` 包、API Key 不存在或处于 cooldown 时，压缩器生成静态占位文本，但仍删除压缩区中的原始消息。

**正确降级策略**：摘要失败必须返回未压缩的原始消息，不能用“摘要失败”占位文本替代历史事实。

### CR-P0-004 硬约束没有真正保证逐字保留

受保护消息索引在工具结果裁剪前计算，裁剪后索引可能变化；边界调整逻辑仍会把受保护消息包含在压缩切片中。因此“保护”只降低了丢失概率，不能构成数据不变量。

**必须建立的不变量**：

- 所有硬约束原文必须在压缩输出中逐字存在；
- 压缩失败时原文完整存在；
- 任何消息不得重复；
- Tool call 与 Tool result 必须成对且顺序合法。

### CR-P0-005 硬约束状态跨 Session 污染

**相关文件**：

- `plugins/deepseek-harness/gate.py`
- `plugins/deepseek-harness/assessor.py`

硬约束保存在模块级全局 `set`，没有按 `session_id`、用户或任务隔离。普通新消息和 Session 结束也不会清空。

**影响**：

- 一个会话的约束可能影响另一个会话；
- 并发用户共享状态；
- 约束来源不可追踪；
- 产生错误告警或错误决策。

## 4. P1 问题

### CR-P1-001 Tool Schema 与 FastAPI Model 不一致

已确认的契约问题：

| 工具 | Tool Schema / Handler | API Model | 结果 |
|---|---|---|---|
| `memory_filter` | 发送 `lambda_value` | 接收别名 `lambda` | 可能 422 |
| `checkpoint_create` | 只要求 `plan_id` | 还要求 `plan_steps`、`completed_step_ids` | LLM 合法调用仍 422 |
| `plan_update_step.status` | 描述含 `blocked` | 枚举不支持 `blocked` | 422 |

**根因**：同一契约被手写在 Tool Schema、Pydantic Model 和 Handler 三处。

**修复原则**：单一契约源，优先从 Pydantic Model 自动生成 Tool JSON Schema。

### CR-P1-002 约束审计写入格式和解析格式不兼容

`assessor.py` 写入多行 Markdown；`immune_audit.py` 只解析单行管道格式。实际违反记录基本无法进入统计和 Skill 草案链路。

建议改为 JSONL 事件日志，Markdown 报告仅作为派生视图。

### CR-P1-003 Cron 文件未形成可安装定时任务

`crons/immune-audit.cron` 只有命令，没有 Cron schedule；安装脚本未注册 crontab/systemd/launchd。其 Python 导入路径还依赖测试期间创建的下划线软链接。

### CR-P1-004 Memory 启动导入不幂等

Server 默认每次启动扫描 `~/.hermes/memories/*.md` 并普通 INSERT，缺少内容哈希、唯一键、文件版本和导入批次，重启会持续生成重复数据。

同时 `/memory/tag` 只分类不持久化，导致“旧数据反复导入、新数据无法写入”的不对称行为。

### CR-P1-005 Plan Engine 名为 DAG，默认实现实际是线性链

任务分解基于标点，短任务会复制为三个相同步骤；每个步骤固定依赖前一步；关联强度由位置而非语义决定。

更新依赖后没有重新验证：

- 依赖是否存在；
- 是否跨 Plan；
- 是否自依赖；
- 是否形成循环。

### CR-P1-006 意图路由置信度阈值失效

当前 `confidence = best / (best + second)`。因为 `best >= second`，只要有匹配，置信度必然 `>= 0.5`；而回退条件是 `< 0.5`，所以低置信度回退基本不会触发。

此外多个类别共享“修改、更新、项目、方案、系统”等宽泛关键词，静态排除清单可能与用户显式需求冲突。

### CR-P1-007 外部摘要隐私边界未定义

Context Engine 会把会话、工具参数、工具结果发送给外部 DeepSeek API，但没有：

- Secret/Token 脱敏；
- 敏感路径过滤；
- 企业/离线模式；
- 用户明确提示；
- 数据发送审计。

此能力不能被描述为纯本地无副作用。

## 5. P2 问题

### CR-P2-001 Skill 学习能力名实不符

当前 `learner.py` 主要记录 Session 结束时间；超过 10 轮只输出日志，没有分析成功模式、生成结构化 Skill 候选或保存证据。

建议在真正实现前改名为“Session 结束记录与 Skill 候选提示”。

### CR-P2-002 版本号不一致

- 根项目：`2.0.0`
- Harness Plugin：`2.2.0`
- Context Plugin：`0.1.0`

需要确定 Mono-repo 独立版本还是统一版本策略，并写入 Release Policy。

### CR-P2-003 CI 只验证 pytest

缺少：

- clean-install smoke test；
- subprocess Server E2E；
- Plugin 与 Hermes 真实兼容测试；
- Ruff、类型检查、ShellCheck；
- 覆盖率阈值；
- 依赖安全扫描；
- Linux/macOS 安装测试。

### CR-P2-004 测试会接触真实 HOME 数据

Server 在模块 import 时创建默认数据库并导入用户 Memory。开发者本地跑测试可能污染真实 `~/.hermes` 数据。

测试必须设置临时 HOME 和临时数据库，应用需使用 factory + dependency injection。

### CR-P2-005 README 产品承诺超出代码证据

需要收敛以下绝对化表述：

- “唯一”；
- “一条命令、零配置开用”；
- “安全无副作用”；
- “对话多长都不卡”；
- “自动学习 Skill”；
- “不影响其他插件”。

开源项目应把已实现、实验性、降级实现和规划中功能分开标识。

## 6. 优点与可保留资产

1. Plugin / Context Engine / Harness Service 的分层方向合理；
2. Hook 机制避免修改 Hermes 核心代码，升级路径理论上较干净；
3. Pydantic Model、SQLite 参数绑定和 WAL 等基础工程选择合理；
4. 对 Context、Memory、Plan、Checkpoint 的问题拆解有研究价值；
5. 已有大量单元测试和中英文文档基础；
6. I-14/I-15/I-16 等不可行能力能够在验证后撤回，说明项目具备一定证伪意识。

## 7. 修复优先级

### Milestone A：Runtime Integrity

- 修复安装、Server package、进程生命周期；
- 修复 Context 重复和数据丢失；
- 修复 Session 状态隔离；
- 对齐 Tool/API 契约。

### Milestone B：Data Integrity

- Memory 导入幂等；
- JSONL 审计事件；
- DAG 更新不变量；
- 测试完全隔离 HOME。

### Milestone C：Open-source Readiness

- 统一版本、依赖、日志和错误码；
- 完成 clean-install E2E；
- 文档与实际能力对齐；
- 增加安全和隐私说明；
- 发布 `v0.3.0-beta`，而不是继续沿用不真实的 `v2.x stable` 叙事。

## 8. 发布门槛

在以下条件全部满足前，不建议发布稳定版：

- [ ] 干净 Linux 环境可一键安装；
- [ ] Harness Server 可启动、健康检查、停止和卸载；
- [ ] 九个 Tool 与 API 契约测试全部通过；
- [ ] 压缩失败不丢消息；
- [ ] 压缩输出无重复消息；
- [ ] 硬约束逐字保留；
- [ ] Session 并发隔离；
- [ ] Memory 导入幂等；
- [ ] 测试不读取或修改真实 HOME；
- [ ] README 不包含无法证实的绝对化承诺；
- [ ] Python 3.10/3.11/3.12 CI 全绿；
- [ ] 有至少一个真实 Hermes 版本的端到端验证记录。

## 9. 对应回归测试

本次已在 `develop` 新增：

- `tests/test_context_integrity_regressions.py`
- `tests/test_release_readiness_regressions.py`

已确认但尚未修复的缺陷使用 `pytest.mark.xfail(strict=True)`。修复后会产生 XPASS 并使 CI 失败，要求维护者移除 xfail，将其转为永久回归用例。
