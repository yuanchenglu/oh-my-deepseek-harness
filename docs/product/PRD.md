# PRD：oh-my-deepseek-harness

- 产品名称：oh-my-deepseek-harness
- 文档版本：2.0
- 文档状态：Open-source Beta Execution Baseline
- 目标发布：Git/GitHub `v3.0.0-beta.1`；Python `3.0.0b1`；Stable `v3.0.0`
- 适用分支：`develop`
- Owner：Repository Maintainer
- 最后更新：2026-07-27

> 当前代码仍是 Experimental Preview；G0 尚未通过。本文件定义目标契约，不表示功能已经实现。

## 1. 产品定义

`oh-my-deepseek-harness` 是运行在 Hermes Agent 周边的本地 Harness 增强层，不是独立 Agent、模型 SDK、云平台或 UI 产品。目标是让 DeepSeek + Hermes 在长任务中保持约束、上下文、计划、记忆和 Checkpoint 的完整性。

## 2. 固定发布契约

### 2.1 版本与制品

- Git Tag / GitHub Release：`v3.0.0-beta.1`；
- Python Distribution：`3.0.0b1`；
- Plugin Manifest：`3.0.0-beta.1`；
- Beta 制品：wheel、sdist、SHA256SUMS、SBOM、provenance、Release Notes、Known Limitations；
- G3 使用冻结 Commit SHA 或可删除 RC Tag 验证；正式不可变 Beta Tag 仅由 `BETA-001` 在最终制品验证后创建。

### 2.2 Tool Contract

当前运行时注册 9 个公共 Tool；Beta 目标固定为 10 个。`memory_store` 只由 `CON-001 + MEM-001` 实现，M0 不得提前注册不可工作的 Tool。

| 领域 | 目标 Tool |
|---|---|
| Plan | `plan_create`、`plan_update_step`、`plan_cascade`、`plan_status` |
| Memory | `memory_tag`、`memory_store`、`memory_query`、`memory_filter` |
| Checkpoint | `checkpoint_create`、`checkpoint_review` |

### 2.3 安装与 CLI 边界

```bash
python -m pip install "oh-my-deepseek-harness[all]==3.0.0b1"
deepseek-harness install
deepseek-harness doctor
```

Python distribution 只由 pip 管理；`deepseek-harness` 只管理 Hermes 部署、配置、数据、Server 和诊断，不得调用 pip 安装、升级或卸载自身。

公开 CLI 固定为：

```text
install [--dry-run]
doctor [--json]
upgrade [--dry-run]
server start|status|stop|restart
audit [--json]
memory import PATH [--dry-run]
memory delete (--id ID | --source SOURCE) --confirm
plan show PLAN_ID [--include-archived]
plan archive PLAN_ID
plan delete PLAN_ID --confirm
uninstall [--dry-run] [--purge-data --confirm]
```

退出码：0 成功；2 参数或缺确认且无变化；3 环境前置失败；4 Runtime/DB/Provider 失败且无新增半状态；5 rollback 成功；6 rollback 不完整并按 P0 处理。

### 2.4 支持范围与安全默认值

- OS：Linux、macOS；Python：3.10–3.12；Hermes：由 `COMPAT-000` 固定一个正式版本；
- Server：`127.0.0.1:8200`，单机单进程；
- 数据根：`~/.hermes/oh-my-deepseek-harness/`；
- Summary：默认关闭，启用前明确告知，外发前脱敏，默认不发送 Tool 参数；
- Memory 启动导入：默认关闭；日志内容：默认不含用户内容；
- 环境变量只使用 `HARNESS_CONFIG_PATH`、`HARNESS_DATA_ROOT`、`HARNESS_DB_PATH`、`HARNESS_HOST`、`HARNESS_PORT`、`HARNESS_SUMMARY_ENABLED`、`HARNESS_SUMMARY_OUTBOUND_POLICY`、`HARNESS_SUMMARY_ALLOW_TOOL_ARGUMENTS`、`HARNESS_MEMORY_IMPORT_ON_STARTUP`、`HARNESS_LOG_INCLUDE_CONTENT`、`DEEPSEEK_API_KEY`、`DEEPSEEK_BASE_URL`。

## 3. 产品原则

1. 正确性优先于 Token 节省。
2. 用户显式要求优先于自动策略。
3. Session 默认隔离。
4. Tool/API/Storage 使用单一契约源。
5. 本地优先，外发透明、可关闭、可脱敏。
6. 少功能、完整闭环，不新增 Innovation。
7. 对外文案必须有测试或运行证据。

## 4. 目标用户与非目标

- 目标：Hermes + DeepSeek 个人开发者、高强度 Agent 用户、开源贡献者和维护者。
- 非目标：非 Hermes 用户、企业多租户平台、独立 UI、云同步、未经确认的 Skill 自动执行、复杂 LLM DAG 和分布式服务。

## 5. 产品目标

- O1 可从最终制品安装、诊断、升级和卸载。
- O2 Context 变换不丢失、重复或破坏 Tool Pair。
- O3 Session 和运行状态隔离。
- O4 10 个目标 Tool 契约闭环。
- O5 故障可诊断、可恢复。
- O6 仓库可贡献、可复现、可发布。

## 6. 产品范围总览

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

## 7. 功能需求

### EP-01 安装、升级和卸载

#### FR-INSTALL-001 Dry Run

`deepseek-harness install --dry-run` 必须展示 Python/Hermes 检测值、支持范围、部署路径、端口、外发开关、备份和缺失依赖；不得产生持久化变化。

#### FR-INSTALL-002 Clean Install

用户先由 pip 安装 distribution，再由 `deepseek-harness install` 注册 Hermes 薄适配入口、初始化产品数据根、启动或验证 Server，并执行 Doctor。CLI 不得调用 pip 安装自身。

#### FR-INSTALL-003 幂等安装

重复安装同一版本不得重复写配置、重复导入 Memory、创建双进程、删除用户文件或无限增长备份。

#### FR-INSTALL-004 Upgrade

`upgrade --dry-run` 先报告 Config/DB/JSONL/进程迁移；正式升级必须备份、显式迁移并在任一步失败时恢复可运行旧版本。

#### FR-INSTALL-005 Uninstall

普通卸载停止 Server 并移除 Hermes 注册、薄适配文件和 runtime state，保留 Python distribution 与用户数据；`--purge-data --confirm` 仅删除规范化数据根内的已知路径。

#### FR-INSTALL-006 Doctor

Doctor 检查 Python、Hermes、Plugin、Context、Server `/health`/`/ready`/`/version`、DB、Provider、端口、版本和权限；支持人类输出与单 JSON object 输出。

### EP-02 Plugin 注册与生命周期

#### FR-PLUGIN-001 Hook 注册

Plugin 必须明确列出 Hook、Handler、优先级和幂等注册规则。

#### FR-PLUGIN-002 Hook Context 校验

Hermes payload 必须转换为内部 DTO；缺失字段使用安全默认值或结构化错误。

#### FR-PLUGIN-003 Hook 失败降级

辅助 Hook 异常不得阻断 Hermes 主请求；必须记录组件、Session、异常类型和降级行为。

#### FR-PLUGIN-004 生命周期

支持 register、session start/end、pre LLM、post tool、subagent start/stop，以及目标 Hermes 支持时的 shutdown。

#### FR-PLUGIN-005 可配置开关

Cognitive Gate、Constraint Guard、Intent Router、Reasoning Guidance、Latest Reminder、Context Engine、Harness Tools 可独立启停。

### EP-03 Session Policy 和硬约束

#### FR-POLICY-001 Session 隔离

约束、意图、策略和更新时间必须按 `session_id` 隔离；缺失 `session_id` 时不得落入共享可变状态。

#### FR-POLICY-002 约束提取

约束保留原文、来源 Session/Turn、创建时间、标准化关键词和生命周期范围。

#### FR-POLICY-003 约束更新

用户可显式新增、替换或取消约束；不能因后续消息未重述而自动删除。

#### FR-POLICY-004 Tool Violation Evaluation

Tool 调用后按名称、参数、路径和命令评估疑似违反；Beta 只告警和记录，不声称绝对阻断。

#### FR-POLICY-005 Violation Event

事件以 JSONL 持久化，至少含 event ID、timestamp、session ID、constraint ID、tool、evidence、severity、evaluator version。

#### FR-POLICY-006 Session End Cleanup

Session 结束时清理内存状态；审计事件独立持久化。

#### FR-POLICY-007 范围控制

自动排除仅为建议，用户显式要求优先，并记录冲突。

#### FR-POLICY-008 审计报告

Markdown 报告只由 JSONL 事件派生，支持日期、约束、Tool 和 Session 汇总；报告失败不影响源事件。

### EP-04 意图和推理提示路由

#### FR-INTENT-001 意图类别

Beta 支持 simple、refactor、feature、architecture、research、collaboration、neutral/default。

#### FR-INTENT-002 可解释输出

返回 intent、confidence、matched evidence、alternative candidates 和 strategy ID。

#### FR-INTENT-003 低置信回退

低于阈值或第一、第二候选差距不足时返回 neutral/default。

#### FR-INTENT-004 用户显式优先

用户明确声明任务类型时覆盖自动分类。

#### FR-INTENT-005 Strategy Mapping

Strategy 只决定计划粒度、审查标准、推理深度提示和是否建议澄清。

#### FR-INTENT-006 Reasoning Guidance 命名

若 Hermes Hook 不能设置 API `reasoning_effort`，只能称为“推理深度提示”。

#### FR-INTENT-007 Time Reminder

时间注入包含 ISO 时间、时区和来源，默认只在首轮注入且可关闭。

### EP-05 Context Integrity

#### FR-CONTEXT-001 压缩触发

仅在估算 Token 达到阈值时触发，支持关闭和手动触发。

#### FR-CONTEXT-002 输入不可变

压缩不得原地修改输入 messages。

#### FR-CONTEXT-003 Stable Message ID

管线内部为消息分配稳定 ID，用于前后完整性验证。

#### FR-CONTEXT-004 受保护消息

System Prompt、硬约束、最新 N 条、Pending Ask、关键 Tool Error 和用户标记消息默认受保护。

#### FR-CONTEXT-005 Tool Result Pruning

只压缩旧 Tool Result，并保留 Tool 名、关键参数、成功/失败、输出规模和后续有用错误。

#### FR-CONTEXT-006 Secret Redaction

外发前脱敏 API Key、Bearer Token、Private Key、`.env` Secret、云凭证和用户正则。

#### FR-CONTEXT-007 Summary Provider

Provider 可替换并支持 Fake；缺 Key、网络或 SDK 时必须可诊断。

#### FR-CONTEXT-008 Summary Failure

Provider 错误、超时、空响应、cooldown 或校验失败时完整返回原始 messages。

#### FR-CONTEXT-009 输出完整性

提交前验证最新用户消息恰好一次、受保护原文存在、非压缩区顺序不变、Tool Pair 合法、ID 不重复、Token 下降、摘要不提升为当前指令。

#### FR-CONTEXT-010 Rollback

完整性失败自动 rollback，并记录不含原 Prompt 的原因事件。

#### FR-CONTEXT-011 前缀稳定性

只有真实捕获 System Prompt 时才记录指纹，不得用固定占位伪装。

#### FR-CONTEXT-012 数据发送提示

启用外部摘要前说明发送内容、Provider、关闭方式和脱敏边界，并获得明确选择。

#### FR-CONTEXT-013 Context Metrics

本地记录输入/输出 Token、裁剪数、延迟、压缩率、rollback 原因和脱敏计数，默认不上传。

### EP-06 Harness Server Runtime

#### FR-SERVER-001 Package 启动

Server 通过 Module 或 Console Script 启动，不依赖仓库相对路径。

#### FR-SERVER-002 Loopback 默认

默认绑定 `127.0.0.1`；Beta 对非 loopback 默认拒绝。

#### FR-SERVER-003 Process Supervisor

Supervisor 先探测健康、避免双进程、等待 readiness、保存 PID/版本、处理端口占用并提供幂等停止。

#### FR-SERVER-004 Health API

`/health` 只验证进程；`/ready` 验证 DB/migration/service；`/version` 返回 distribution/server/config/db/Hermes 版本。

#### FR-SERVER-005 App Factory

运行和测试通过 `create_app(settings, repositories)` 装配；import 不得读取真实 HOME、创建 DB 或导入 Memory。

#### FR-SERVER-006 统一错误 Envelope

API 与 Tool 共用 `ok/data/error/meta` envelope、request ID 和固定错误码映射。

#### FR-SERVER-007 输入限制

Task、Memory、Checkpoint、数组和文本长度设上限，拒绝资源滥用。

### EP-07 Plan 工具

#### FR-PLAN-001 Create Plan

接收任务描述或显式步骤；规则式分解标记 `decomposition_method=rule_based`。

#### FR-PLAN-002 Step Model

Step 含 ID、Plan ID、文本、状态、依赖、父级、关联强度、创建/更新时间。

#### FR-PLAN-003 DAG Validation

创建和更新后验证依赖存在、同 Plan、无自依赖、无循环、Parent 合法。

#### FR-PLAN-004 状态机

状态为 pending、in_progress、completed、blocked、pending_review、cancelled，并定义合法转换。

#### FR-PLAN-005 Cascade

返回受影响步骤和原因，不静默修改已完成步骤。

#### FR-PLAN-006 Transaction

Plan 创建、Step 更新和 Cascade 原子化，失败无半状态。

#### FR-PLAN-007 Query

`plan_status`/CLI 可查看 Plan、依赖图、更新时间和异常状态。

#### FR-PLAN-008 Delete/Archive

默认支持 Archive；Delete 需 `--confirm` 且只影响目标 Plan。

### EP-08 Memory 工具

#### FR-MEMORY-001 Classify

输入文本返回 layer、tags、confidence、evidence，不持久化。

#### FR-MEMORY-002 Store

`memory_store` 显式写入，自动分类并以 content hash + source identity 去重。

#### FR-MEMORY-003 Query

按 tags、layer、source、时间和 limit 查询。

#### FR-MEMORY-004 Lambda Filter

λ 映射来自统一配置，0.3/0.4/0.7/0.8 边界连续。

#### FR-MEMORY-005 Import

支持 dry-run、文件统计、幂等、变更检测、截断提示、错误列表和取消；默认不在启动时导入。

#### FR-MEMORY-006 Delete

按 ID 或 Source 删除，CLI 缺 `--confirm` 时拒绝。

#### FR-MEMORY-007 数据来源

每条记录保留 source、source identity、mtime 和 import batch。

### EP-09 Checkpoint 工具

#### FR-CHECKPOINT-001 Create

必须传合法 Plan ID，或显式 external snapshot；默认验证 completed IDs 归属。

#### FR-CHECKPOINT-002 Snapshot

包含目标、完成摘要、剩余计划、异常发现、规则版本和创建时间。

#### FR-CHECKPOINT-003 Numbering

编号在事务中生成，同 Plan 并发不重复。

#### FR-CHECKPOINT-004 Review

规则评估返回 alignment、progress、impact、adjustments、confidence、rule version。

#### FR-CHECKPOINT-005 Idempotency

同 Checkpoint 与同规则版本重复 Review 结果一致。

#### FR-CHECKPOINT-006 Chain

按 Plan 查询有序 Checkpoint 链和阶段变化。

### EP-10 日志、诊断和错误

#### FR-OBS-001 结构化日志

日志含 timestamp、level、component、event、session_id、request_id、duration、status、error_code。

#### FR-OBS-002 隐私日志

默认不记录完整 Prompt、API Key、Tool Result 和 Memory 原文。

#### FR-OBS-003 用户错误

说明发生了什么、组件、是否降级、恢复动作和日志位置。

#### FR-OBS-004 Server 日志

stdout/stderr 写入用户可访问日志，不得全部丢弃。

#### FR-OBS-005 Runtime Status

Doctor/status 显示 Plugin、Context、Server、DB、Provider 和版本。

### EP-11 安全与隐私

#### FR-SEC-001 Outbound Consent

Summary 默认关闭；只有展示说明并获得明确选择后才启用。

#### FR-SEC-002 Data Minimization

只发送摘要所需最小内容，默认不发送完整 Tool 参数。

#### FR-SEC-003 Local API

Beta 仅承诺 loopback 本地 API，不提供远程访问安全承诺。

#### FR-SEC-004 File Permission

数据根目录 `0700`；配置、DB、事件、日志和 runtime 文件 `0600`。

#### FR-SEC-005 Dependency Security

依赖漏洞扫描，未豁免 High/Critical 阻断 Release。

#### FR-SEC-006 Prompt Injection Boundary

摘要标记为参考材料，不提升权限，不绕过结构校验和显式确认。

#### FR-SEC-007 Destructive Operations

删除限制在规范化已知目录，支持 dry-run，并防 symlink/path traversal。

### EP-12 测试、兼容和发布

#### FR-QA-001 测试隔离

所有自动测试使用临时 HOME、DB、端口和 Fake Provider。

#### FR-QA-002 Python Matrix

Python 3.10、3.11、3.12 全部通过。

#### FR-QA-003 Contract Tests

10 个目标 Tool 的 Schema 从 Pydantic Model 生成并自动比对。

#### FR-QA-004 Process E2E

真实启动 Server，验证探针、Tool/API、日志和退出。

#### FR-QA-005 Install E2E

空环境完成 pip install → install → doctor → smoke → 普通 uninstall → pip uninstall。

#### FR-QA-006 Context Property Tests

生成消息序列验证完整性不变量和故障 rollback。

#### FR-QA-007 Compatibility Matrix

Linux/macOS、Python 3.10–3.12，并至少验证一个由 `COMPAT-000` 固定的 Hermes 正式版本。

#### FR-QA-008 Known Defects

已知缺陷必须有 Issue、精确复现和 strict XFAIL；修复后删除 XFAIL。

#### FR-QA-009 Release Gate

P0、未解释数据损坏、安装失败、隐私阻断或无证据 Gate 存在时不得发布。

## 8. 配置与数据生命周期

配置优先级固定为 CLI > Environment > User Config > Package Defaults。未知字段给出 warning；非法类型、危险监听或非法布尔值以退出码 3 拒绝。

```yaml
server: {host: 127.0.0.1, port: 8200}
summary: {enabled: false, outbound_policy: redact, allow_tool_arguments: false}
memory: {import_on_startup: false}
logging: {include_content: false}
```

| 数据 | 范围 | 默认保留 |
|---|---|---|
| Session Policy | Session | Session 结束清理 |
| Constraint Events | 本地用户 | 用户显式清理 |
| Plan/Memory/Checkpoint | 本地用户 | Archive/Delete |
| Runtime PID | 进程 | 停止时清理 |
| Logs | 本地用户 | 可轮转 |
| Summary 请求 | 外部 Provider | 由 Provider 政策决定，需文档披露 |

## 9. 关键验收场景

- AC-01：空 HOME 安装后 Plugin、Context、Server 就绪且 Doctor 全绿。
- AC-02：重复安装无重复配置、Memory 或进程。
- AC-03：Session A 的约束不影响 Session B。
- AC-04：Summary 超时、空响应、缺 Key 或异常时完整 rollback。
- AC-05：Merge 路径每条尾部消息恰好一次。
- AC-06：10 个目标 Tool 的最小合法 payload 不产生内部 422。
- AC-07：同一 Memory 输入重启三次不增加重复记录。
- AC-08：更新依赖形成环时返回 conflict 且 DB 不变。
- AC-09：含 Secret 的内容外发和日志均已脱敏。
- AC-10：普通卸载保留 distribution 和用户数据；purge 仅删除安全边界内路径。

## 10. Release Gate

### Public Beta 前置

- G0–G3 全部以证据报告 PASS；
- P0 = 0；P1 已关闭或具有有效 Beta Waiver；
- 100 个 Test ID 已登记，Release Test Failed/XPASS/XFAIL = 0；
- 10 个目标 Tool Contract、Context、Session、Migration、安全和真实 Hermes E2E 通过；
- 最终制品、SHA256、SBOM、provenance、Release Notes 一致。

### Stable 前置

- G0–G4 全部通过；P0 = 0、P1 = 0；
- 至少 10 名非维护者、20 次独立安装、50 次长会话、200 次合法 Tool 调用和 50 次压缩尝试达到计划阈值；
- 最终 RC 连续至少 14 个日历日且无数据完整性 P0；
- 安全、许可证、依赖和迁移审查完成。

## 11. Definition of Done

一个 Requirement 只有在实现、正常/边界/故障测试、HOME 隔离、文档配置、Required CI、Requirement→Test→PR 追踪、隐私披露和对外文案一致全部满足后才完成。
