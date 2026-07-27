# 开源发布执行计划（Open-source Release Execution Plan）

> 文档版本：2.3.1（Execution Status Correction）
>
> 审查基线：`develop@37e4016`
>
> 当前实施基线：`develop@61642f69`
>
> 计划状态：`IN_IMPLEMENTATION`
>
> 适用分支：`develop`
>
> 发布目标：`v3.0.0-beta.1` → 按需增加 Beta → `v3.0.0`
>
> 完整 v2.2 任务账本归档：[`archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md`](archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md)
>
> 关联文档：[`PRD`](../product/PRD.md) · [`技术架构`](../architecture/TECHNICAL_ARCHITECTURE.md) · [`Code Review`](../reviews/CODE_REVIEW_2026-07-27.md) · [`测试计划`](../testing/TEST_PLAN.md) · [`追踪矩阵`](../traceability/RELEASE_TRACEABILITY.md)

## 0. 规范性说明

本文件是 Open-source Beta 发布周期的唯一主计划。v2.2 的完整任务表、文件所有权、依赖、测试入口、Gate、附录和 48 个 Work ID 已原样保存于只读归档；除本文件明确修正、完成或替代的内容外，归档中的未修改条款继续按引用纳入本计划，保持规范效力。

执行优先级固定为：

1. 本文件 v2.3.1 的明确规则；
2. `docs/product/PRD.md`、两份 Architecture 和 `docs/testing/TEST_PLAN.md` 的已同步契约；
3. v2.2 归档中的未修改任务细节；
4. 历史测试报告，仅作为不可变历史证据，不作为当前目标契约。

原 `OPEN_SOURCE_RELEASE_PLAN_ERRATA_2.3.md` 的四项修正已全部合并到本文件，临时 Errata 不再作为独立规范来源。

## 更新记录（Update Log）

| 日期 | 版本 | 更新内容 | 来源 |
|---|---|---|---|
| 2026-07-27 | 1.0 | 建立开源发布 Roadmap 初稿 | 产品、架构、Code Review 和测试基线 |
| 2026-07-27 | 2.0 | 修正版本、制品、Tool、分支、指标与 Gate | 严格计划审查 |
| 2026-07-27 | 2.1 | 补充代理执行协议、文件边界、命令、证据与停止条件 | 实施可执行性审查 |
| 2026-07-27 | 2.2 | 固定 48 个 Work ID、100 个 Test ID、Migration、Ruleset、provenance 与安全验收 | 三层闭环校验 |
| 2026-07-28 | 2.3 | 合并 RC/正式 Tag、REL-004、XFAIL ID、BETA-003 修正；记录 REL-000/001 完成和 REL-002 治理状态；将 v2.2 全文无损归档 | Plan audit + execution evidence |
| 2026-07-28 | 2.3.1 | 记录 REL-002 完成；恢复归档规定的 `REL-002 → REL-004 → GOV-001 → REL-003` 强制顺序；标识 Tool 目标常量 | REL-004 dependency verification |

## 1. 当前结论与实施状态

### 1.1 发布判断

当前产品仍是 **Experimental Preview**，不满足 Public Beta Gate，更不满足 Stable Gate。版本元数据统一、文档契约统一或仓库治理完成，不等于 Runtime、Context、Tool、Migration、安全和 Release 制品已经完成。

### 1.2 Plan Ready Gate

Plan Ready 维持 `PASS`。本计划具备：

- 48 个固定 Work ID；
- 88 个 `FR-*` 需求；
- 100 个 Test ID；
- 5 个 P0、7 个 P1、5 个 P2 追踪基线；
- G0–G5 证据 Gate；
- 每项任务的依赖、文件边界、验证、风险和回滚。

### 1.3 当前 M0 状态

| Work ID | 状态 | 合并证据 | 说明 |
|---|---|---|---|
| `REL-000` | Complete | PR #4 / `e18db7e` | 规格契约、88 FR、100 Test ID 同步 |
| `REL-001` | Complete | PR #6 / `a97dfe4` | Python/Plugin/Git 版本语义统一 |
| `REL-002` | Complete | PR #8 + #9 / `e7e1414e` + `61642f69` | `develop` 默认分支、保护规则、贡献治理和 v2.3 主计划合并完成 |
| `REL-004` | In progress | Issue #10 | 冻结唯一 10 Tool 目标源，Runtime 仍注册 9 个 Tool |
| `GOV-001` | Blocked by REL-004 | — | 增加 Security、Issue/PR 和 Release 治理文件 |
| `REL-003` | Blocked by GOV-001 | — | 48 个执行 Issue 与完整追踪矩阵 |
| `REL-005` | Eligible, not started | — | 可与主串行并行验证 PyPI 名称和权限 |
| `COMPAT-000` | Eligible, not started | — | 可与主串行并行选择 Hermes 验证候选版本 |

M0 主串行固定为 `REL-000 → REL-001 → REL-002 → REL-004 → GOV-001 → REL-003`。`REL-005` 与 `COMPAT-000` 在 `REL-000` 后可并行，但 G0 只有在 `REL-003 + REL-005 + COMPAT-000` 全部完成后才可判定。

## 2. 固定发布契约

### 2.1 版本

| Surface | Public Beta 1 | Stable |
|---|---|---|
| Git Tag / GitHub Release | `v3.0.0-beta.1` | `v3.0.0` |
| Python Distribution | `3.0.0b1` | `3.0.0` |
| Plugin Manifest | `3.0.0-beta.1` | `3.0.0` |

Python 支持范围为 `>=3.10,<3.13`。Beta 修订递增 `beta.2` / `b2`、`beta.3` / `b3`，不得移动或覆盖已有 Tag/制品。

### 2.2 发布制品

Public Beta 最小集合：wheel、sdist、`SHA256SUMS`、SBOM、Artifact Attestation/provenance、Release Notes、Known Limitations 和不可变 Git Tag。PyPI 只有在名称所有权、Trusted Publisher 与维护者权限验证后启用。

### 2.3 安装与 CLI

```bash
python -m pip install "oh-my-deepseek-harness[all]==3.0.0b1"
deepseek-harness install
deepseek-harness doctor
```

pip 管理 Python distribution；`deepseek-harness` 只管理 Hermes 部署、配置、数据、Server、迁移和诊断，不调用 pip 管理自身。

公开 CLI、退出码、JSON 输出、数据路径和环境变量以 PRD 与 v2.2 归档 §2.3/§2.8 为准。

### 2.4 Tool Contract：当前 9，目标 10

Beta 目标清单固定为：

| 领域 | Tool |
|---|---|
| Plan | `plan_create`、`plan_update_step`、`plan_cascade`、`plan_status` |
| Memory | `memory_tag`、`memory_store`、`memory_query`、`memory_filter` |
| Checkpoint | `checkpoint_create`、`checkpoint_review` |

唯一机器可读目标源是 `plugins/deepseek-harness/tools.py::TARGET_PUBLIC_TOOL_NAMES`。当前 Runtime 清单必须由该目标常量减去 `PENDING_PUBLIC_TOOL_NAMES` 派生。

当前运行时注册 9 个公共 Tool，尚无 `memory_store`。这一现状在 `CON-001 + MEM-001` 完成前不构成 G0 失败；G0 要求目标 Contract、名称、领域归属、迁移状态和测试分母已冻结。

统一 API/Tool envelope、错误码和 Runtime probes 以 PRD、技术架构和 v2.2 归档 §2.4 为准。

## 3. 规范性修正一：RC、test-release 与正式 Tag

### 3.1 两层发布验证

发布候选验证固定分为：

1. **G3 RC 验证**：对冻结的精确 Commit SHA 构建，或使用可删除临时 RC Tag，例如 `v3.0.0-beta.1-rc.1`。RC Tag 不创建 GitHub Release、不上传 PyPI、不作为公开安装入口。
2. **正式 Beta 发布验证**：G3 通过并合入 `master` 后，对 `master` 的精确 Commit 重建最终制品并运行 `test-release`。只有该次验证通过，`BETA-001` 才创建不可变 `v3.0.0-beta.1` Tag 和 GitHub Release。

### 3.2 正式 Tag 不变量

- 指向最终验证的同一 Commit；
- wheel、sdist、SHA256、SBOM、provenance 和 Release Notes 均引用该 Commit；
- 不覆盖、不移动、不复用已有 Tag；
- 最终验证失败时不创建 Tag 或半套 Release；
- 需要重新发布时递增预发布号。

### 3.3 G3 解释

G3 中“Release 制品生成成功”指 RC 制品。`test-release` 在 G3 阶段允许从冻结 Commit SHA 或临时 RC Tag 构建，不要求正式不可变 Beta Tag 已存在。

## 4. 规范性修正二：REL-004 边界

`REL-004` 只负责：

- 冻结 10 个目标 Tool 的名称、领域归属和 Contract 分母；
- 建立单一目标清单或常量；
- 同步 PRD、Test Plan、README 和追踪口径；
- 明确“当前 9、目标 10”的迁移状态。

`REL-004` 不得：

- 注册不可工作的 `memory_store`；
- 提前实现 Memory 持久化；
- 提前重构 Tool Handler、FastAPI Model 或 Storage；
- 提前关闭 `TC-CONTRACT-*` 或 Memory Gate。

第 10 个 Tool 的职责固定为：

- `CON-001`：从 Pydantic Model 生成 10 个 Tool Schema，建立统一 Contract/Envelope；
- `MEM-001`：实现 `memory_store` 领域逻辑、持久化和测试。

## 5. 规范性修正三：XFAIL ID

规范 ID 固定为：

| 规范 ID | pytest node | 主责 Work ID | 历史废弃别名 |
|---|---|---|---|
| `XF-DEPS-001` | `tests/test_release_readiness_regressions.py::test_runtime_dependencies_include_openai` | `PKG-002` | `XF-PKG-001` |
| `XF-RELEASE-001` | `tests/test_release_readiness_regressions.py::test_project_versions_are_consistent` | `REL-001` | `XF-VERSION-001` |

执行规则：

- 新 Issue、PR、Evidence 和 Traceability 只使用规范 ID；
- 历史别名只用于定位 v2.2 原文；
- 历史测试报告不回写；
- `XF-RELEASE-001` 已由 REL-001 修复并转换为永久普通回归测试；
- `XF-DEPS-001` 仍由 `PKG-002` 负责。

## 6. 规范性修正四：BETA-003

M5 强制依赖为：

```text
G3 → BETA-001
BETA-001 → BETA-002
BETA-001 → BETA-003
BETA-001 → REL-007
BETA-002 + BETA-003 + REL-007 → G4
```

`BETA-003` 完成条件：

1. Beta 期间每个失败记录环境、复现、严重度和根因分类；
2. 每个需要代码修改的失败创建独立 Work ID/Issue；
3. P0 立即暂停推广并阻断 G4；
4. P1 已关闭或有符合计划 Waiver 规则的有效豁免；
5. 修复后重跑全部受影响 Gate；
6. 需要重新发布时递增预发布号；
7. Failure Ledger 中不存在“未分类、无 Owner、无下一步”的开放记录。

## 7. G0 仓库治理契约

- 默认分支：`develop`；
- 普通开发分支从 `develop` 创建，PR 回 `develop`；
- `master` 只接收 G3 通过后的授权 Release PR；
- `develop` 和 `master` 均要求 PR 与当前 CI，禁止强推和删除；
- 默认分支已通过 GitHub 连接器机器确认；
- Ruleset 由仓库管理员在 GitHub 设置中完成并于 2026-07-28 明确确认；当前连接器没有 Ruleset 枚举接口，因此该项以管理员人工验证作为证据，并在 `REL-002` Evidence 中披露验证边界。

该人工验证不替代后续 `QA-002` 对 Required Checks 的自动审计；当连接器或 `gh` 可用时应补充机器证据，但不重复阻断已确认的仓库设置。

## 8. 任务账本与执行协议

以下内容完整继承 v2.2 归档：

| 归档范围 | 继续生效的内容 |
|---|---|
| §3 | 实施协议、串行/并行规则、文件所有权、三层证据、停止条件 |
| §4 | Issue 结构、严重度、Waiver、Definition of Done |
| §5 | G0–G5 Gate（受本文件 G3/M5 修正覆盖） |
| §6 | M0–M6 的 48 个 Work ID、依赖、允许文件、测试入口和完成证据 |
| §7 | 需求/Test/XFAIL 追踪（受本文件规范 ID 修正覆盖） |
| §8 | CI、Release、Rollback 和 Artifact Flow（受本文件 RC/Tag 修正覆盖） |
| §9–§11 | 风险、里程碑、执行检查表与交付格式 |
| 附录 A–Q | 文件所有权、逐任务细节、命令和问题回答（受本文件 Q#2/Q#3 修正覆盖） |

实施代理必须同时读取本文件和归档中目标 Work ID 的原始条目。不得因主文件采用引用归档而省略原任务的允许路径、测试、风险或回滚。

## 9. 发布与回滚流程

### 9.1 正常流程

```text
M0 完成 → G0
M1 完成 → G1
M2/M3 完成 → G2
M4 完成 → G3 RC 验证
G3 PASS → develop → master Release PR
精确 master Commit 最终制品重建 + test-release
PASS → BETA-001 不可变 Tag/Release
Beta 反馈/修复 → BETA-002 + BETA-003 + REL-007 → G4
M6 Stable 收口 → G5 → v3.0.0
```

### 9.2 回滚

- Work ID 失败：回滚该 Squash Commit，不跨任务批量回退；
- Migration 失败：恢复旧 Config、DB、事件和可运行版本；
- G3 RC 失败：删除临时 RC Tag/制品，不创建正式 Release；
- 最终 Beta 验证失败：不创建正式 Tag，修复后递增 RC 或 Beta 号；
- 已发布 Beta 出现 P0：暂停推广，创建独立 Work ID，不移动原 Tag/制品；
- Ruleset 阻断恢复：只允许有记录的紧急治理恢复，不把 bypass 视为 Gate PASS。

## 10. 附录问题的规范答案

### Q#1：为何是 3.0.0？

现有 distribution 已使用 2.x，本周期包含 package、生命周期、配置、数据和迁移的破坏性变化。使用 3.0.0 保持版本单调性；只有新 distribution 身份才允许从 0.x 起步。

### Q#2：G3 如何验证制品而正式 Tag 尚未创建？

G3 从冻结 Commit SHA 或可删除 RC Tag 构建 RC 制品。G3 通过并合入 `master` 后，对精确 `master` Commit 重建最终制品；通过后才由 `BETA-001` 创建不可变正式 Tag/Release。

### Q#3：为什么计划写 10 Tool，而当前只有 9？

10 是 Beta 目标 Contract 分母；9 是当前运行时事实。`REL-004` 只冻结目标，不注册假 Tool；`CON-001 + MEM-001` 实现 `memory_store` 后运行时达到 10。

## 11. 当前下一步

1. 完成 `REL-004` 的测试、PR、CI、Evidence 和合并；
2. `REL-004` 完成后执行 `GOV-001`；
3. `GOV-001` 完成后执行 `REL-003`，创建 48 个真实 Issue 并补齐完整追踪矩阵；
4. `REL-005` 与 `COMPAT-000` 可在不与主串行文件冲突时并行实施；
5. `REL-003 + REL-005 + COMPAT-000` 全部完成并生成 G0 Evidence 前，不进入 M1。
