# PRD：oh-my-deepseek-harness

- 产品名称：oh-my-deepseek-harness
- 文档版本：1.0
- 文档状态：Open-source Beta Baseline
- 目标发布：`v0.3.0-beta`
- 适用分支：`develop`
- Owner：Repository Maintainer
- 最后更新：2026-07-27

---

## 1. 背景

DeepSeek 模型接入 Hermes Agent 后，模型本身只解决推理和生成问题。Agent 是否能够持续遵守用户约束、管理长上下文、选择合适的任务策略、维护计划和记忆，主要由 Harness 决定。

当前仓库已经原型化实现以下方向：

- 认知门控；
- 硬约束提取和违规检测；
- 意图分类和策略提示；
- 推理深度文本提示；
- 时效信息注入；
- 上下文压缩；
- Plan、Memory、Checkpoint 本地服务；
- Session 结束记录和子任务状态检查。

但现有实现缺少统一产品规格，导致：

1. 功能名称、实际行为和 README 承诺不一致；
2. 各模块独立实现，跨模块契约没有定义；
3. 安装、运行、故障和卸载流程不完整；
4. 关键的数据完整性、安全和隐私要求没有进入验收标准；
5. 测试偏向代码单元，不足以证明产品可用。

本 PRD 的目标是把项目从“创新点集合”转化为一个边界明确、可验证、可开源发布的产品。

---

## 2. 产品愿景

让 Hermes Agent + DeepSeek 在长任务中表现得更可靠、更可控、更节省上下文，同时确保任何优化都不能以损坏用户事实、约束和执行状态为代价。

### 产品一句话

> 一个面向 Hermes Agent + DeepSeek 的本地 Harness 增强套件，为 Session 约束、任务策略、上下文完整性、计划、记忆和 Checkpoint 提供可测试的运行时能力。

---

## 3. 产品原则

1. **正确性优先于 Token 节省**：压缩失败时保留原文。
2. **显式优先于魔法**：文本提示降级不能包装为原生 API 参数控制。
3. **用户指令优先**：自动策略和排除项不得覆盖用户显式需求。
4. **Session 默认隔离**：任何运行时状态不得无意跨会话传播。
5. **单一契约源**：Tool、API 和 Storage 使用同一数据模型。
6. **本地优先、外发透明**：所有外部数据发送可见、可关闭、可脱敏。
7. **少功能、完整闭环**：Beta 不新增 Innovation 编号，只修完整性。
8. **文档必须可证实**：对外能力需有测试、日志或运行结果支撑。

---

## 4. 产品目标

### O1：可安装

全新支持环境能够按照 README 完成安装，并验证 Plugin、Context Engine、Harness Server 状态。

### O2：不损坏上下文

任何 Context 压缩或故障降级都不得丢失受保护事实、重复最新消息或破坏 Tool call/result 配对。

### O3：可控且隔离

约束、意图和策略绑定到 Session；并发或连续会话之间没有状态污染。

### O4：Tool 闭环可用

Plan、Memory、Checkpoint 工具的 Schema、API 和持久化一致，合法 Tool 调用不会因内部契约不一致而失败。

### O5：可诊断

用户能够理解安装、Server、外部 API、数据库和工具调用失败的原因。

### O6：真实开源

仓库具备准确 README、贡献路径、测试基线、隐私说明、版本策略和发布门槛。

---

## 5. 非目标

Beta 不提供：

- 独立 Agent UI 或桌面客户端；
- 非 Hermes 平台适配；
- 企业级多租户、RBAC、SSO；
- 云端控制台和数据同步；
- 自动创建和执行未经用户确认的 Skill；
- LLM 驱动的复杂 DAG 自动规划；
- 分布式微服务、消息队列或容器编排；
- 对 DeepSeek 内部编码器机制的不可验证封装；
- 修改 Hermes 核心源码；
- “绝对不会与其他插件冲突”的承诺。

---

## 6. 用户角色

### U1 个人开发者

需要一键安装和默认可靠行为，不希望理解内部服务细节。

### U2 高级 Agent 用户

需要策略、约束、Memory 和 Context 的可配置能力，关注 Token 和长期任务质量。

### U3 开源贡献者

需要清晰模块边界、测试规范和可复现缺陷。

### U4 维护者

需要版本、兼容性、日志、Release Gate 和故障定位能力。

---

## 7. 使用前提

### 支持环境

- Python 3.10、3.11、3.12；
- Hermes Agent 兼容版本，具体范围必须在兼容矩阵中标注；
- Linux 和 macOS 为 Beta 支持目标；
- Windows 暂不承诺，WSL 可作为实验环境；
- 若启用 DeepSeek Context Summary，需要 DeepSeek API Key 和网络访问。

### 默认端口与路径

- Harness Server：`127.0.0.1:8200`；
- 数据目录：`~/.hermes/oh-my-deepseek-harness/`；
- 默认不得使用仓库目录存储用户运行数据。

---

## 8. 产品范围总览

| Epic | 名称 | Beta 优先级 |
|---|---|---|
| EP-01 | 安装、升级和卸载 | P0 |
| EP-02 | Plugin 注册与生命周期 | P0 |
| EP-03 | Session Policy 和硬约束 | P0 |
| EP-04 | 意图和推理提示路由 | P1 |
| EP-05 | Context Integrity | P0 |
| EP-06 | Harness Server Runtime | P0 |
| EP-07 | Plan 工具 | P1 |
| EP-08 | Memory 工具 | P1 |
| EP-09 | Checkpoint 工具 | P1 |
| EP-10 | 日志、诊断和错误 | P0 |
| EP-11 | 安全与隐私 | P0 |
| EP-12 | 测试、兼容和发布 | P0 |

---

# 9. 功能需求

## EP-01 安装、升级和卸载

### FR-INSTALL-001 Dry Run

用户执行 `scripts/install.sh --dry-run` 时，系统必须展示：

- Python/Hermes 版本；
- 将安装的 Python package；
- 将创建或修改的路径；
- 将使用的端口；
- 是否启用外部摘要；
- 将备份的文件；
- 缺失依赖；
- 不执行任何写操作。

**验收**：在临时 HOME 中运行前后文件树完全一致。

### FR-INSTALL-002 Clean Install

正式安装必须：

1. 检查依赖；
2. 备份已有用户配置；
3. 安装完整 runtime package 和 extras；
4. 注册 Harness Plugin；
5. 注册 Context Engine；
6. 初始化数据目录；
7. 启动或验证 Harness Server；
8. 执行 Doctor；
9. 输出下一步命令。

### FR-INSTALL-003 幂等安装

重复安装同一版本不得：

- 重复写入配置；
- 重复导入 Memory；
- 创建多个 Server；
- 删除用户文件；
- 产生不可控备份增长。

### FR-INSTALL-004 Upgrade

升级必须识别当前版本和配置版本，执行显式 migration。失败时保留原版本和备份。

### FR-INSTALL-005 Uninstall

提供卸载命令或脚本，能够：

- 禁用 Plugin；
- 停止 Server；
- 删除已安装程序文件；
- 默认保留用户数据库和备份；
- 支持 `--purge-data` 显式清理数据；
- 输出清理结果。

### FR-INSTALL-006 Doctor

Doctor 至少检查：

- Python 版本；
- Hermes 命令和版本；
- Plugin 注册；
- Context Engine import；
- Harness Server `/health` 和 `/ready`；
- 数据库可读写；
- DeepSeek API 配置；
- 端口冲突；
- 关键 package 版本。

---

## EP-02 Plugin 注册与生命周期

### FR-PLUGIN-001 Hook 注册

Plugin 注册必须明确列出每个 Hook、Handler 和优先级。重复注册不得产生重复注入。

### FR-PLUGIN-002 Hook Context 校验

每个 Hook payload 必须转换为内部类型；缺失字段使用安全默认值或返回结构化错误。

### FR-PLUGIN-003 Hook 失败降级

辅助 Hook 异常不得阻断 Hermes 主请求。必须记录组件、Session、异常类型和降级行为。

### FR-PLUGIN-004 生命周期

必须支持：

- plugin register；
- session start；
- pre LLM call；
- post tool call；
- session end；
- subagent start/stop；
- plugin shutdown（若 Hermes 支持）。

### FR-PLUGIN-005 可配置开关

用户可独立启用/禁用：

- Cognitive Gate；
- Constraint Guard；
- Intent Router；
- Reasoning Guidance；
- Latest Reminder；
- Context Engine；
- Harness Tools。

---

## EP-03 Session Policy 和硬约束

### FR-POLICY-001 Session 隔离

每个 `session_id` 拥有独立约束、意图、策略和更新时间。不存在 `session_id` 时不得使用共享可变状态。

### FR-POLICY-002 约束提取

系统从用户消息中识别明确的禁止、必须、范围和文件边界。每条约束必须保留：

- 原始文本；
- 来源 Session；
- 来源 Turn；
- 创建时间；
- 标准化关键词；
- 生命周期范围。

### FR-POLICY-003 约束更新

用户可新增、替换或取消约束。取消必须通过明确语义，不得仅因为下一条消息未提及而自动删除。

### FR-POLICY-004 Tool Violation Evaluation

Tool 调用后系统检查 Tool 名称、参数、路径和命令是否疑似违反约束。

Beta 只提供警告和记录，不声称绝对阻断。

### FR-POLICY-005 Violation Event

事件必须写入结构化 JSONL，包含：

- event ID；
- timestamp；
- session ID；
- constraint ID；
- tool name；
- evidence；
- severity；
- evaluator version。

### FR-POLICY-006 Session End Cleanup

Session 结束后清理内存状态。需要保留的审计事件单独持久化。

### FR-POLICY-007 范围控制

自动排除项只能作为建议，不得否定用户显式要求。若自动策略与用户要求冲突，用户要求优先并记录冲突。

### FR-POLICY-008 审计报告

审计报告从结构化事件派生，支持日期范围、约束、Tool 和 Session 汇总。报告生成失败不影响运行数据。

---

## EP-04 意图和推理提示路由

### FR-INTENT-001 意图类别

Beta 支持：

- simple；
- refactor；
- feature；
- architecture；
- research；
- collaboration；
- neutral/default。

不得使用含义不清的 `spec_driven` 作为所有未知任务的强策略。

### FR-INTENT-002 可解释输出

分类结果必须提供：

- intent；
- confidence；
- matched evidence；
- alternative candidates；
- strategy ID。

### FR-INTENT-003 低置信回退

低于阈值或一二名差距不足时，返回 neutral/default。

### FR-INTENT-004 用户显式优先

若用户明确说明“这是简单修改”或“需要深度研究”，可直接覆盖自动分类。

### FR-INTENT-005 Strategy Mapping

Strategy 只决定提示级参数：

- 建议计划粒度；
- 建议审查标准；
- 建议推理深度；
- 是否需要澄清。

### FR-INTENT-006 Reasoning Guidance 命名

如果 Hermes Hook 无法设置 API `reasoning_effort`，产品必须明确称为“推理深度提示”，不得称为 API 参数控制。

### FR-INTENT-007 Time Reminder

时间注入必须包含 ISO 时间、时区和来源。默认只在首轮注入，用户可关闭。

---

## EP-05 Context Integrity

### FR-CONTEXT-001 压缩触发

只在估算 Token 达到配置阈值时触发。必须支持关闭和手动触发。

### FR-CONTEXT-002 输入不可变

压缩不得原地修改输入 messages。

### FR-CONTEXT-003 Stable Message ID

管线内部为消息分配稳定 ID，用于压缩前后完整性验证。

### FR-CONTEXT-004 受保护消息

以下默认受保护：

- System Prompt；
- 用户硬约束；
- 最新 N 条消息；
- 未完成任务和明确 Pending Ask；
- 关键 Tool Error；
- 用户标记为不可压缩的消息。

### FR-CONTEXT-005 Tool Result Pruning

只允许把旧 Tool Result 压缩为可解释摘要，必须保留：

- Tool 名称；
- 关键参数；
- 成功/失败；
- 输出规模；
- 对后续有用的错误信息。

### FR-CONTEXT-006 Secret Redaction

发送外部 Summary Provider 前，检测并脱敏：

- API Key；
- Bearer Token；
- Private Key；
- `.env` Secret；
- 常见云凭证；
- 用户配置的正则模式。

### FR-CONTEXT-007 Summary Provider

Provider 必须可替换，支持 fake provider 用于测试。缺少 API Key 时必须在首次使用前给出可诊断错误。

### FR-CONTEXT-008 Summary Failure

任何 Provider 错误、超时、空响应、cooldown 或校验失败，必须返回原始消息。

### FR-CONTEXT-009 输出完整性

提交压缩结果前验证：

- 最新用户消息恰好一次；
- 受保护原文存在；
- 非压缩区顺序不变；
- Tool Pair 合法；
- 无重复 message ID；
- 输出 Token 小于输入；
- 摘要不能作为新用户指令执行。

### FR-CONTEXT-010 Rollback

校验失败自动 rollback，并记录 `compression_rolled_back` 事件和原因。

### FR-CONTEXT-011 前缀稳定性

系统可观测 System Prompt 指纹，但不得用固定占位字符串伪装真实指纹。只有真实捕获到 Prompt 时才声明“前缀已冻结”。

### FR-CONTEXT-012 数据发送提示

启用外部摘要时，安装和配置文档必须说明会发送哪些内容、到哪个 Provider、如何关闭。

### FR-CONTEXT-013 Context Metrics

记录但默认不上传：

- 输入/输出估算 Token；
- 裁剪 Tool Result 数；
- Summary 延迟；
- 压缩率；
- Rollback 原因；
- Secret Redaction 数量。

---

## EP-06 Harness Server Runtime

### FR-SERVER-001 Package 启动

Server 必须通过 Module 或 Console Script 启动，不允许依赖仓库相对路径。

### FR-SERVER-002 Loopback 默认

默认绑定 `127.0.0.1`。绑定其他地址需要显式配置和风险提示。

### FR-SERVER-003 Process Supervisor

Supervisor 必须：

- 先探测健康状态；
- 避免重复进程；
- 等待 readiness；
- 保存 PID 和版本；
- 处理端口占用；
- 提供停止操作。

### FR-SERVER-004 Health API

- `/health`：进程存活；
- `/ready`：数据库和 Service 可用；
- `/version`：Server/Schema 版本。

响应不得暴露 Secret；默认不暴露绝对数据库路径。

### FR-SERVER-005 App Factory

测试和运行必须通过 `create_app(settings, repositories)` 创建应用，禁止 import 时读取真实 HOME 和导入 Memory。

### FR-SERVER-006 统一错误 Envelope

所有 Tool API 返回统一错误类型、request ID 和可读信息。

### FR-SERVER-007 输入限制

对 Task、Memory、Checkpoint 和数组长度设置合理上限，防止本地资源滥用。

---

## EP-07 Plan 工具

### FR-PLAN-001 Create Plan

接收任务描述或显式步骤列表。规则式分解必须标记 `decomposition_method=rule_based`。

### FR-PLAN-002 Step Model

Step 包含：ID、Plan ID、文本、状态、依赖、父级、关联强度、创建/更新时间。

### FR-PLAN-003 DAG Validation

创建和每次更新后验证：

- 依赖存在；
- 同 Plan；
- 无自依赖；
- 无循环；
- Parent 合法。

### FR-PLAN-004 状态机

合法状态：

- pending；
- in_progress；
- completed；
- blocked；
- pending_review；
- cancelled。

状态转换规则必须显式定义。

### FR-PLAN-005 Cascade

Cascade 返回受影响步骤和原因，不直接静默修改已完成步骤。

### FR-PLAN-006 Transaction

Plan 创建、Step 更新和 Cascade 必须使用事务，失败不产生半完成状态。

### FR-PLAN-007 Query

支持查看 Plan、依赖图、更新时间和异常状态。

### FR-PLAN-008 Delete/Archive

Beta 至少支持 Archive，避免数据库无限增长。

---

## EP-08 Memory 工具

### FR-MEMORY-001 Classify

输入文本，返回 layer、tags、confidence 和 evidence，不持久化。

### FR-MEMORY-002 Store

显式写入 Memory，自动分类、生成内容哈希并去重。

### FR-MEMORY-003 Query

按 tags、layer、source、时间和 limit 查询。

### FR-MEMORY-004 Lambda Filter

λ 值和层级映射必须来自统一配置，边界连续，不允许配置存在 `0.3–0.4`、`0.7–0.8` 未定义区间。

### FR-MEMORY-005 Import

导入支持：

- dry run；
- 文件级统计；
- 幂等；
- 变更检测；
- 截断提示；
- 错误列表；
- 可取消默认启动导入。

### FR-MEMORY-006 Delete

用户可按 ID 或 Source 删除导入数据。

### FR-MEMORY-007 数据来源

每条 Memory 保留 source、source identity、mtime 和 import batch。

---

## EP-09 Checkpoint 工具

### FR-CHECKPOINT-001 Create

必须传入合法 Plan ID，或显式允许 external snapshot。默认验证 completed IDs 属于 Plan。

### FR-CHECKPOINT-002 Snapshot

快照包含：目标、完成步骤摘要、剩余计划、异常发现、规则版本和创建时间。

### FR-CHECKPOINT-003 Numbering

编号在事务中生成；同一 Plan 并发创建不得产生重复 number。

### FR-CHECKPOINT-004 Review

Review 是可解释规则评估，返回：alignment、progress、impact、adjustments、confidence、rule version。

### FR-CHECKPOINT-005 Idempotency

相同 Checkpoint 和相同规则版本重复 Review，结果应一致。

### FR-CHECKPOINT-006 Chain

支持按 Plan 查询 Checkpoint 链和阶段变化。

---

## EP-10 日志、诊断和错误

### FR-OBS-001 结构化日志

日志至少包含：timestamp、level、component、event、session_id、request_id、duration、status、error_code。

### FR-OBS-002 隐私日志

默认不记录完整 Prompt、API Key、Tool Result 和 Memory 原文。

### FR-OBS-003 用户错误

用户可见错误必须说明：

- 发生了什么；
- 哪个组件；
- 是否已降级；
- 如何修复；
- 日志位置。

### FR-OBS-004 Server 日志

Server stdout/stderr 写入日志文件，不得全部丢弃。

### FR-OBS-005 Runtime Status

Doctor 或状态命令显示 Plugin、Context、Server、DB、Provider 和版本。

---

## EP-11 安全与隐私

### FR-SEC-001 Outbound Consent

外部 Summary Provider 默认配置必须在安装文档中显式说明。用户可关闭。

### FR-SEC-002 Data Minimization

只发送完成摘要所需的最小内容，默认不发送完整 Tool 参数。

### FR-SEC-003 Local API

非 loopback 监听必须显式允许。Beta 不提供远程访问安全承诺。

### FR-SEC-004 File Permission

数据、事件和日志文件应仅当前用户可读写。

### FR-SEC-005 Dependency Security

CI 运行依赖漏洞扫描，严重漏洞阻断 Release。

### FR-SEC-006 Prompt Injection Boundary

压缩摘要必须带“参考材料”标记，不能把历史用户指令重新变成当前指令。模型提示不能代替结构校验。

### FR-SEC-007 Destructive Operations

Installer 和 Uninstaller 的删除操作必须限制在已知目录，并支持 dry run。

---

## EP-12 测试、兼容和发布

### FR-QA-001 测试隔离

所有自动测试使用临时 HOME、临时数据库和 Fake Provider。

### FR-QA-002 Python Matrix

Python 3.10、3.11、3.12 全部通过。

### FR-QA-003 Contract Tests

每个 Tool 的 Schema 必须与 Pydantic Model 自动比对。

### FR-QA-004 Process E2E

真实启动 Harness Server，调用所有 API，验证日志和退出。

### FR-QA-005 Install E2E

空环境执行 dry run、install、doctor、uninstall。

### FR-QA-006 Context Property Tests

使用生成消息序列验证完整性不变量和故障回退。

### FR-QA-007 Compatibility Matrix

至少验证一个明确 Hermes Release；不支持的版本给出可读错误。

### FR-QA-008 Known Defects

已知缺陷必须有 Issue 或 strict xfail；不能只写在文档中。

### FR-QA-009 Release Gate

任何 P0、未解释的数据损坏、安装失败或隐私阻断问题存在时，不得发布 stable。

---

# 10. 配置需求

## 10.1 配置文件

```yaml
config_version: 1

features:
  cognitive_gate: true
  constraint_guard: true
  intent_router: true
  reasoning_guidance: true
  latest_reminder: true
  context_engine: true
  harness_tools: true

server:
  host: 127.0.0.1
  port: 8200
  startup_timeout_seconds: 10

context:
  threshold_percent: 0.75
  fail_mode: preserve_original
  protect_first_n: 3
  protect_last_n: 20

summary:
  enabled: true
  provider: deepseek
  base_url: https://api.deepseek.com
  outbound_policy: redact
  allow_tool_arguments: false

memory:
  import_on_startup: false
  default_lambda: 0.5

logging:
  level: INFO
  include_content: false
```

## 10.2 配置优先级

CLI > Environment > User Config > Defaults。

## 10.3 配置校验

未知字段给出 warning；非法类型或危险远程监听配置必须拒绝启动。

---

# 11. 状态与数据生命周期

| 数据 | 范围 | 默认保留 |
|---|---|---|
| Session 约束 | Session | Session 结束清理 |
| Constraint Events | 用户本地 | 长期，用户可清理 |
| Plan | 用户本地 | 直到 Archive/Delete |
| Memory | 用户本地 | 直到 Delete |
| Checkpoint | 用户本地 | 随 Plan 生命周期 |
| Server Runtime PID | 进程 | 进程结束清理 |
| Logs | 用户本地 | 可配置轮转 |
| Summary API 内容 | 外部 Provider | 由 Provider 政策决定，需文档说明 |

---

# 12. 核心状态机

## 12.1 Server

```text
STOPPED → STARTING → READY
              ├→ FAILED
READY → STOPPING → STOPPED
```

## 12.2 Compression

```text
IDLE → PLANNED → SUMMARIZING → VALIDATING → COMMITTED
                    ├───────────────→ ROLLED_BACK
                    └→ FAILED → ROLLED_BACK
```

## 12.3 Plan Step

```text
pending → in_progress → completed
   │          ├→ blocked
   │          └→ pending_review
   └→ cancelled
blocked → in_progress | cancelled
pending_review → pending | in_progress | cancelled
```

---

# 13. 关键交互

## 13.1 Context Failure

用户不应看到对话中断。系统继续使用原始上下文，并在日志中记录：

```text
Context compression rolled back: summary_provider_timeout
```

## 13.2 Tool Server Unavailable

Tool 返回：

```json
{
  "ok": false,
  "error": {
    "code": "server_unavailable",
    "message": "Harness Server 未就绪",
    "recovery": "运行 harness doctor"
  }
}
```

不得返回 Python traceback 给模型。

## 13.3 Constraint Suspected Violation

Beta 默认不强行阻断 Hermes Tool；返回 warning context，记录结构化事件，并让上层决定是否需要用户确认。

---

# 14. 非功能需求

## NFR-001 性能

- Hook 纯本地处理 P95 < 20ms；
- `/health` P95 < 100ms；
- 非摘要 Tool API P95 < 500ms；
- Summary 超时可配置，默认不超过 30s；
- SQLite 常规查询在 10,000 条 Memory 下 P95 < 200ms。

## NFR-002 可靠性

- 辅助组件失败不影响 Hermes 主会话；
- Context 数据损坏事故为 0；
- 安装过程可重复；
- DB 更新具备事务一致性。

## NFR-003 可移植性

不得硬编码仓库路径、用户名和绝对安装目录。

## NFR-004 可维护性

- 业务函数有类型注解；
- Tool Contract 自动生成；
- 单文件建议不超过 500 行，超出需拆分理由；
- 领域逻辑与 FastAPI/Hook Adapter 分离。

## NFR-005 可观测性

所有降级行为都有日志事件和错误码。

## NFR-006 安全性

默认只监听 loopback；Secret 不进入日志；外部发送有脱敏。

## NFR-007 可测试性

所有外部依赖可注入；禁止 import 时产生用户数据副作用。

## NFR-008 向后兼容

配置和数据库 Schema 变更必须有版本和 migration。

---

# 15. 产品指标

## 15.1 发布前指标

- Clean install：3/3 Python 版本成功；
- Tool contract：100%；
- Context integrity：100%；
- Session isolation：100%；
- Memory import duplicate：0；
- P0：0；
- 未关闭 P1：有明确 Release Waiver 才允许 Beta，不允许 stable。

## 15.2 运行指标（本地、默认不上传）

- 压缩尝试/成功/回滚次数；
- Tool 调用成功率；
- Server 启动失败原因；
- 约束疑似违反数量；
- Memory 去重数量；
- Doctor 检查结果。

项目不在 Beta 中建设云端遥测系统。

---

# 16. 文案和能力分级

README 中每项能力标记：

- **Stable**：E2E 和回归测试通过；
- **Beta**：核心路径通过，存在兼容限制；
- **Experimental**：原型或算法验证；
- **Degraded**：由于平台限制使用替代实现；
- **Removed**：验证不可行后移除。

禁止使用未经证实的：

- 唯一；
- 完美；
- 零副作用；
- 永不冲突；
- 对话多长都不卡；
- 自动变聪明。

---

# 17. 依赖需求

正式运行依赖必须覆盖实际 import：

- PyYAML；
- FastAPI；
- Uvicorn；
- Pydantic；
- HTTP Client；
- OpenAI-compatible SDK（仅 Context extra）；
- 其他实际运行库。

CI 必须从空环境安装 package，不允许依赖开发机已有包。

---

# 18. 迁移需求

从当前版本升级到 Beta 时：

1. 备份原 `~/.hermes/mcp/harness.db`；
2. 检测重复 Memory，提供 dry-run 去重报告；
3. 迁移约束 Markdown 日志为 JSONL，无法解析条目保留原文件；
4. 统一配置路径；
5. 停止旧 Server 进程；
6. 安装新 package；
7. 运行 Doctor；
8. 失败时恢复原配置和 DB。

---

# 19. 验收场景

## AC-01 全新安装

Given 空 HOME 和支持版本 Python/Hermes，When 安装，Then Plugin、Context、Server 全部就绪，Doctor 全绿。

## AC-02 重复安装

Given 已安装同版本，When 再次安装，Then 无重复进程、配置和 Memory。

## AC-03 Session 隔离

Given Session A 有“不能删除 DB”，Session B 无此约束，When B 调用相关 Tool，Then 不使用 A 的约束。

## AC-04 Summary API 失败

Given Provider 超时，When 触发压缩，Then 输出 messages 与输入语义和顺序一致，不删除历史。

## AC-05 合并路径

Given 摘要角色和尾部消息角色冲突，When 组装压缩结果，Then每条尾部消息只出现一次。

## AC-06 Tool Contract

Given LLM 按注册 Schema 生成合法参数，When 调用九个 Tool，Then不出现内部 422。

## AC-07 Memory 重启

Given同一批 Memory 文件，When Server 重启三次，Then数据库条目数不增加。

## AC-08 DAG 更新

Given更新依赖形成环，When提交，Then返回 conflict，数据库保持原状态。

## AC-09 隐私

Given Tool Result 含 API Key，When摘要，Then外部请求中 Key 被脱敏，日志不含 Key。

## AC-10 卸载

Given已安装并有用户数据，When普通卸载，Then程序停止并移除，用户数据保留。

---

# 20. 需求追踪矩阵

| Requirement | Test Layer | Release Blocking |
|---|---|---|
| FR-INSTALL-002 | Install E2E | Yes |
| FR-INSTALL-003 | Install E2E | Yes |
| FR-POLICY-001 | Unit + Concurrency | Yes |
| FR-POLICY-005 | Integration | Yes |
| FR-INTENT-003 | Dataset Test | No（Beta） |
| FR-CONTEXT-008 | Fault Injection | Yes |
| FR-CONTEXT-009 | Property/Regression | Yes |
| FR-SERVER-003 | Process E2E | Yes |
| FR-SERVER-005 | Test Isolation | Yes |
| FR-PLAN-003 | Unit + Storage Integration | Yes |
| FR-MEMORY-002 | Storage Integration | Yes |
| FR-MEMORY-005 | Import E2E | Yes |
| FR-CHECKPOINT-003 | Concurrency | No（Beta） |
| FR-SEC-002 | Security Test | Yes |
| FR-QA-005 | Install E2E | Yes |

完整用例见 `docs/testing/TEST_PLAN.md`。

---

# 21. Release Gate

## Beta Gate

- [ ] 所有 P0 关闭；
- [ ] Python 3.10/3.11/3.12 CI 通过；
- [ ] 安装 E2E 通过；
- [ ] 九个 Tool Contract 通过；
- [ ] Context 完整性测试通过；
- [ ] Session 隔离通过；
- [ ] Memory 幂等通过；
- [ ] 外部发送说明和脱敏测试完成；
- [ ] README 能力分级完成；
- [ ] 有明确 Known Limitations。

## Stable Gate

除 Beta Gate 外：

- [ ] Linux/macOS 均有真实环境验证；
- [ ] 至少一个 Hermes 正式 Release E2E；
- [ ] 至少 5 名外部用户完成安装；
- [ ] 连续 14 天无 P0 数据完整性缺陷；
- [ ] 版本、配置和 DB Migration 流程稳定；
- [ ] 安全审查完成。

---

# 22. 未决策事项

| ID | 问题 | 建议 |
|---|---|---|
| OQ-01 | 是否将版本从 2.x 重置为 0.x Beta | 建议重置，避免成熟度误导 |
| OQ-02 | Constraint Guard 是否阻断 Tool | Beta 只告警，后续增加 confirm mode |
| OQ-03 | Memory 默认是否启动导入 | 建议默认关闭，安装时显式选择 |
| OQ-04 | 是否保留 HTTP Server | Beta 保留，后续评估进程内调用 |
| OQ-05 | 是否支持非 DeepSeek Summary Provider | 接口预留，Beta 只测试 DeepSeek + Fake |
| OQ-06 | Hermes 最低兼容版本 | 必须通过真实 E2E 决定，不能只写 README |

---

# 23. Definition of Done

一个需求只有同时满足以下条件才算完成：

1. 代码实现；
2. 类型和错误处理完整；
3. 自动测试覆盖正常、边界和故障路径；
4. 不访问真实用户 HOME；
5. 文档和配置更新；
6. CI Python Matrix 通过；
7. 对应 Requirement ID 写入测试或 PR；
8. 无新增未披露数据发送；
9. 对外文案与实现一致。
