# 产品架构：oh-my-deepseek-harness

- 文档状态：Open-source Beta Target Architecture
- 目标版本：`v3.0.0-beta.1` → `v3.0.0`
- 适用分支：`develop`
- 当前成熟度：Experimental Preview；G0 尚未通过

## 1. 产品定位

`oh-my-deepseek-harness` 是 Hermes Agent 周边的本地 Harness 增强层，不是第二个 Agent Runtime、模型 SDK、独立 UI 或云平台。它通过 Hermes Hook、Context Engine Adapter 和本地 Tool Server 提高遵约性、上下文完整性、可控性、可诊断性和成本效率。

## 2. 固定外部契约

- Git/GitHub：`v3.0.0-beta.1`；Python：`3.0.0b1`；Stable：`v3.0.0`。
- 当前运行时 9 个公共 Tool；Beta 目标 10 个，新增 `memory_store` 由 `CON-001 + MEM-001` 实现。
- pip 管理 distribution；`deepseek-harness` 管理 Hermes 部署、配置、数据、Server 和诊断。
- Linux/macOS、Python 3.10–3.12；Hermes 只承诺一个经真实 E2E 的正式版本。
- Server 默认 `127.0.0.1:8200`；Summary 默认关闭；Memory startup import 默认关闭。
- G3 验证冻结 Commit/RC Tag；正式不可变 Beta Tag 只在最终制品验证后由 `BETA-001` 创建。

## 3. 目标用户

- 个人开发者：希望低配置使用 Hermes + DeepSeek。
- 高强度 Agent 用户：需要长会话、计划、Memory 和诊断能力。
- 开源贡献者：需要稳定契约、可复现缺陷和分层测试。
- 维护者：需要 Gate、制品、迁移、回滚和发布证据。

非目标包括独立聊天 UI、企业多租户、云同步、复杂编排平台、未经确认的 Skill 自动执行和非 Hermes 平台适配。

## 4. 产品能力域

```text
Hermes Agent
  ├─ Hook Adapter
  │    └─ Session Policy / Intent / Reasoning Guidance / Audit
  ├─ Context Engine Adapter
  │    └─ Context Integrity Pipeline / Redaction / Summary Provider
  └─ Local Tool Client
       └─ Harness Server / Plan / Memory / Checkpoint / SQLite

Lifecycle Plane
  └─ pip distribution + deepseek-harness install/doctor/upgrade/server/audit/uninstall

Evidence Plane
  └─ fast / integration / release tests + Gate reports + traceability
```

## 5. 用户旅程

### 5.1 安装与首次验证

1. `python -m pip install "oh-my-deepseek-harness[all]==3.0.0b1"`。
2. `deepseek-harness install --dry-run` 查看影响。
3. `deepseek-harness install` 注册 Hermes 薄适配和数据目录。
4. `deepseek-harness doctor` 验证 Plugin、Context、Server、DB、Provider 和权限。

成功标准：无需源码目录、symlink 或维护者远程修改环境。

### 5.2 约束任务

约束按 Session 存储；高风险 Tool 调用产生可追踪告警；Session 结束清理内存状态，JSONL 事件继续保留。

### 5.3 长会话压缩

Normalize → Stable ID → Protected Messages → Safe Pruning → Redaction → Summary → Assemble → Integrity Validate → Commit/Rollback。任何失败返回原消息。

### 5.4 Plan / Memory / Checkpoint

Pydantic Model 是唯一契约源；目标 10 个 Tool 调用统一 Server envelope；Storage 保证 DAG、事务、去重、归属和并发编号不变量。

### 5.5 升级与卸载

升级先 dry-run、备份和迁移；失败恢复旧版本。普通卸载保留 distribution 和用户数据；purge 需显式确认并防路径越界。

## 6. 产品模块与成熟度

| 模块 | 当前 | Beta 目标 |
|---|---|---|
| Constraint Guard | 模块级共享状态 | SessionPolicyStore + JSONL |
| Intent Router | 规则原型 | 可解释、低置信回退、否定语义 |
| Context Engine | 存在重复/丢历史风险 | rollback-first 完整性管线 |
| Tool Contract | 9 个手写 Schema | 10 个 Pydantic 单一源 |
| Memory | 导入不幂等 | Store/Query/Delete/Import 闭环 |
| Plan | 线性链原型 | DAG、状态机、事务、Archive/Delete |
| Checkpoint | 规则原型 | 归属、并发编号、幂等、Chain |
| Runtime | 源码相对路径启动 | 标准 package + Supervisor |
| Lifecycle | 安装链不完整 | install/doctor/upgrade/uninstall 闭环 |
| Release | pytest 基线 | 制品、SBOM、provenance、Gate |

## 7. 版本策略

### `v3.0.0-beta.1`

只完成真实可安装、数据完整性、Session 隔离、Tool Contract、Migration、安全边界、文档真实性和 Public Beta 验证，不增加 Innovation。

### 后续 Beta

只修复 Beta 暴露的问题；不可覆盖 Tag 或制品，递增 `beta.2`、`beta.3`。

### `v3.0.0`

G5 通过后发布，P0/P1 必须为 0，并完成最终 RC 14 天观察。

## 8. 产品成功定义

陌生用户能从不可变制品安装、完成任务、诊断、升级和安全卸载；陌生贡献者能运行测试并提交可追踪变更；维护者用证据 Gate 而非宣传文案判断发布或回滚。

## 9. 详细 Persona 与边界

### Persona A：个人开发者

使用 Hermes + DeepSeek 完成代码、研究或自动化任务；希望安装简单、成本低、行为可诊断，不需要理解多个本地服务的实现细节。

### Persona B：Agent 高强度用户

运行长会话和复杂任务，关注 Context 漂移、计划变化、Memory 污染和外发数据边界，愿意使用 Doctor、Audit 和高级配置。

### Persona C：Harness 研究者/贡献者

关注 Context Engineering、Memory、Plan、Tool Use 和可复现实验；需要稳定模块边界、测试夹具和证据追踪。

### 产品内

Hermes Adapter、Session Policy、Intent/Reasoning Guidance、Context Integrity、Plan/Memory/Checkpoint、本地 Server、安装/诊断/迁移/卸载、日志和 Release Evidence。

### 产品外

Hermes 核心修改、模型训练、独立 UI、云账号与同步、企业权限、多 Agent 编排、未经确认的 Skill、远程 Server 安全承诺和非 Hermes 平台适配。

## 10. 产品原则

1. Integrity before compression。
2. Explicit over magical。
3. Session-scoped by default。
4. Single source of contract。
5. Local-first, transparent outbound。
6. Evidence-based claims。
7. Fewer features, complete loops。
8. Gate before date。

## 11. 成功指标

北极星指标是“有效 Harness 会话率”：用户从发布制品安装后，在无数据完整性错误、无未披露外发和可诊断故障的情况下完成任务的会话占比。

| 指标 | Beta 目标 |
|---|---:|
| Clean install | 支持矩阵 100% |
| Server readiness | 100% |
| Tool Contract | 10/10 |
| Context Integrity | 100% |
| Session 隔离 | 100% |
| Memory 重复导入 | 0% |
| 未解释外发 | 0 |
| P0 | 0 |

## 12. 产品决策记录

- ADR-P-001：停止扩展 Innovation，先完成开源闭环。
- ADR-P-002：版本使用 3.0.0 Beta，不回退到 0.x。
- ADR-P-003：Skill 自动创建不进入 Beta。
- ADR-P-004：Server 保持本地单进程。
- ADR-P-005：Cron 仅作 Experimental 示例，不由安装器修改。
- ADR-P-006：当前 9 Tool、目标 10 Tool；新增 Tool 不得在 M0 偷跑。
