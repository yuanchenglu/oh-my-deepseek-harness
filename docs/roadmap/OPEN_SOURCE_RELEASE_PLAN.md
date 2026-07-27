# 开源发布执行计划（Open-source Release Execution Plan）

> 文档版本：2.3.3（Hermes Compatibility Target）
>
> 审查基线：`develop@37e4016`
>
> 当前实施基线：`develop@fd5c212f`
>
> 计划状态：`IN_IMPLEMENTATION`
>
> 适用分支：`develop`
>
> 发布目标：`v3.0.0-beta.1` → 按需增加 Beta → `v3.0.0`
>
> 完整 v2.2 任务账本归档：[`archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md`](archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md)
>
> 关联文档：[`PRD`](../product/PRD.md) · [`技术架构`](../architecture/TECHNICAL_ARCHITECTURE.md) · [`Hermes 兼容矩阵`](../compatibility/HERMES_MATRIX.md) · [`测试计划`](../testing/TEST_PLAN.md) · [`追踪矩阵`](../traceability/RELEASE_TRACEABILITY.md)

## 0. 规范性说明

本文件是 Open-source Beta 发布周期的唯一主计划。v2.2 的完整任务表、文件所有权、依赖、测试入口、Gate、附录和 48 个 Work ID 已原样保存于只读归档；除本文件明确修正、完成或替代的内容外，归档中的未修改条款继续按引用纳入本计划，保持规范效力。

执行优先级固定为：

1. 本文件 v2.3.3 的明确规则；
2. `docs/compatibility/HERMES_MATRIX.md` 的候选版本、Python 分层和 COMPAT-001 验证计划；
3. `docs/product/PRD.md`、两份 Architecture 和 `docs/testing/TEST_PLAN.md` 的已同步契约；
4. v2.2 归档中的未修改任务细节；
5. 历史测试报告，仅作为不可变历史证据，不作为当前目标契约。

当旧文档只写“Python 3.10–3.12”而未区分运行层级时，按本文件解释为**包级/纯模块 CI 范围**；完整 Hermes 集成支持以 §2.5 为准。不得把 Python 3.10 的包级绿色 CI 描述为 Hermes v0.19.0 E2E 通过。

原 `OPEN_SOURCE_RELEASE_PLAN_ERRATA_2.3.md` 的四项修正已全部合并到本文件，临时 Errata 不再作为独立规范来源。

## 更新记录（Update Log）

| 日期 | 版本 | 更新内容 | 来源 |
|---|---|---|---|
| 2026-07-27 | 1.0 | 建立开源发布 Roadmap 初稿 | 产品、架构、Code Review 和测试基线 |
| 2026-07-27 | 2.0 | 修正版本、制品、Tool、分支、指标与 Gate | 严格计划审查 |
| 2026-07-27 | 2.1 | 补充代理执行协议、文件边界、命令、证据与停止条件 | 实施可执行性审查 |
| 2026-07-27 | 2.2 | 固定 48 个 Work ID、100 个 Test ID、Migration、Ruleset、provenance 与安全验收 | 三层闭环校验 |
| 2026-07-28 | 2.3 | 合并 RC/正式 Tag、REL-004、XFAIL ID、BETA-003 修正；记录 REL-000/001 完成和 REL-002 治理状态；将 v2.2 全文无损归档 | Plan audit + execution evidence |
| 2026-07-28 | 2.3.1 | 记录 REL-002 完成；恢复 `REL-002 → REL-004 → GOV-001 → REL-003` 强制顺序；标识 Tool 目标常量 | REL-004 dependency verification |
| 2026-07-28 | 2.3.2 | 记录 REL-004/GOV-001 完成和 48 个 canonical Issue；同步 88 FR、17 CR、100 Test ID 追踪；修正 `M2 → G2 → M3 → M4 → G3` 摘要顺序 | REL-003 Issue/traceability verification |
| 2026-07-28 | 2.3.3 | 选择 Hermes v0.19.0 / `v2026.7.20`；区分 Python 3.10–3.12 包级 CI 与 Python 3.11–3.12 完整 Hermes 集成；冻结 Hook、Plugin、ContextEngine 与 COMPAT-001 矩阵 | COMPAT-000 upstream release/interface verification |

## 1. 当前结论与实施状态

### 1.1 发布判断

当前产品仍是 **Experimental Preview**，不满足 Public Beta Gate，更不满足 Stable Gate。版本元数据统一、Issue 建账、静态接口探针或仓库治理完成，不等于 Runtime、Context、Tool、Migration、安全和真实 Hermes E2E 已经完成。

### 1.2 Plan Ready Gate

Plan Ready 维持 `PASS`。本计划具备：

- 48 个固定 Work ID 和 48 个唯一 canonical Issue；
- 88 个 `FR-*`、100 个 Test ID；
- 5 个 P0、7 个 P1、5 个 P2 追踪基线；
- G0–G5 证据 Gate；
- 每项任务的依赖、文件边界、验证、风险和回滚；
- 唯一 Hermes 候选、Python 支持分层和真实 E2E 计划。

### 1.3 当前 M0 状态

| Work ID | 状态 | 合并/Issue 证据 | 说明 |
|---|---|---|---|
| `REL-000` | Complete | PR #4 / `e18db7e` / Issue #3 | 规格契约、88 FR、100 Test ID 同步 |
| `REL-001` | Complete | PR #6 / `a97dfe4` / Issue #5 | Python/Plugin/Git 版本语义统一 |
| `REL-002` | Complete | PR #8 + #9 / `e7e1414e` + `61642f69` / Issue #7 | 默认分支、保护规则、治理和 v2.3 主计划 |
| `REL-004` | Complete | PR #11 / `7d52de9f` / Issue #10 | 唯一 10 Tool 目标源；Runtime 仍为 9 Tool |
| `GOV-001` | Complete | PR #14 / `a0083ce1` / Issue #12 | Security、Issue/PR Forms 和 Release Checklist |
| `REL-003` | Complete | PR #58 / `fd5c212f` / Issue #15 | 48 Issue、88 FR、17 CR、100 Test ID 追踪 |
| `REL-005` | In review | Issue #16 / PR #59 | 首个 Beta 固定 GitHub Release；PyPI 在私有权限验证前禁用 |
| `COMPAT-000` | In progress | Issue #17 | Hermes v0.19.0 候选、静态 probes 与 E2E 计划 |

G0 只有在 `REL-003 + REL-005 + COMPAT-000` 全部完成并生成独立 Gate Evidence 后才可判定；Issue、文档或静态 probe 本身不使 G0 通过。

## 2. 固定发布契约

### 2.1 版本与包级 Python 范围

| Surface | Public Beta 1 | Stable |
|---|---|---|
| Git Tag / GitHub Release | `v3.0.0-beta.1` | `v3.0.0` |
| Python Distribution | `3.0.0b1` | `3.0.0` |
| Plugin Manifest | `3.0.0-beta.1` | `3.0.0` |

Python distribution metadata 保持 `>=3.10,<3.13`，包级/纯模块 CI 保持 Python 3.10、3.11、3.12。该范围不等同于完整 Hermes 集成支持；完整支持见 §2.5。

Beta 修订递增 `beta.2` / `b2`、`beta.3` / `b3`，不得移动或覆盖已有 Tag/制品。

### 2.2 发布制品和渠道

Public Beta 最小集合：wheel、sdist、`SHA256SUMS`、SBOM、Artifact Attestation/provenance、Release Notes、Known Limitations 和不可变 Git Tag。

首个 Beta 的必选发布渠道为 GitHub Release。PyPI 在 `REL-005` 认证验证项目名称、Owner/Maintainer、2FA 和 Trusted Publisher/OIDC 前保持禁用；公开搜索缺失不构成名称可用或归属证据。

### 2.3 安装与 CLI

```bash
python -m pip install "oh-my-deepseek-harness[all]==3.0.0b1"
deepseek-harness install
deepseek-harness doctor
```

pip 管理 Python distribution；`deepseek-harness` 只管理 Hermes 部署、配置、数据、Server、迁移和诊断，不调用 pip 管理自身。

在 Python 3.10 上，完整 Hermes v0.19.0 集成必须被 Doctor/install 识别为不支持的前置环境；不得把包可安装或单元测试通过解释为产品已可用。

公开 CLI、退出码、JSON 输出、数据路径和环境变量以 PRD 与 v2.2 归档 §2.3/§2.8 为准。

### 2.4 Tool Contract：当前 9，目标 10

Beta 目标清单固定为：

| 领域 | Tool |
|---|---|
| Plan | `plan_create`、`plan_update_step`、`plan_cascade`、`plan_status` |
| Memory | `memory_tag`、`memory_store`、`memory_query`、`memory_filter` |
| Checkpoint | `checkpoint_create`、`checkpoint_review` |

唯一机器可读目标源是 `plugins/deepseek-harness/tools.py::TARGET_PUBLIC_TOOL_NAMES`。当前 Runtime 清单必须由该目标常量减去 `PENDING_PUBLIC_TOOL_NAMES` 派生。

当前运行时注册 9 个公共 Tool，尚无 `memory_store`。这一现状在 `CON-001 + MEM-001` 完成前不构成 G0 失败。

### 2.5 Hermes 集成支持

唯一 Beta 验证候选固定为：

| Field | Value |
|---|---|
| Upstream | `NousResearch/hermes-agent` |
| Hermes version | `0.19.0` |
| Git tag | `v2026.7.20` |
| Upstream Python | `>=3.11,<3.14` |
| Full product Python | `3.11`, `3.12` |
| OS | Linux, macOS |
| Python 3.10 | 包级/纯模块 CI；完整 Hermes 集成不支持 |

选择依据、Hook 列表、Plugin/ContextEngine 接口和 E2E 计划以 `docs/compatibility/HERMES_MATRIX.md` 为准。

COMPAT-000 只冻结候选与静态契约；COMPAT-001 必须在 Linux/macOS × Python 3.11/3.12 上从精确 release source 运行真实 Plugin、Hook、ContextEngine 和 Tool E2E。Python 3.10 必须执行预期拒绝/诊断测试，而非支持通过测试。

## 3. 规范性修正一：RC、test-release 与正式 Tag

发布候选验证固定分为：

1. **G3 RC 验证**：对冻结 Commit SHA 构建，或使用可删除临时 RC Tag；不创建 GitHub Release、不上传 PyPI、不作为公开安装入口。
2. **正式 Beta 发布验证**：G3 通过并合入 `master` 后，对精确 `master` Commit 重建最终制品并运行 `test-release`；通过后 `BETA-001` 才创建不可变 Tag 和 Release。

正式 Tag 必须指向最终验证的同一 Commit，所有 hash/SBOM/provenance/notes 必须一致；失败时不创建半套 Release，已有 Tag/Artifact 不移动、不覆盖。

## 4. 规范性修正二：REL-004 边界

`REL-004` 只冻结 10 个目标 Tool 的名称、领域、分母和迁移状态，不注册不可工作的 `memory_store`，不提前实现 Memory、Handler、FastAPI Model 或 Storage。

第 10 个 Tool 的职责固定为：

- `CON-001`：Pydantic 生成 10 Tool Schema 与统一 Contract/Envelope；
- `MEM-001`：`memory_store` 领域逻辑、持久化与测试。

## 5. 规范性修正三：XFAIL ID

| 规范 ID | pytest node | 主责 | 历史别名 |
|---|---|---|---|
| `XF-DEPS-001` | `test_runtime_dependencies_include_openai` | `PKG-002` | `XF-PKG-001` |
| `XF-RELEASE-001` | `test_project_versions_are_consistent` | `REL-001` | `XF-VERSION-001` |

新 Issue/PR/Evidence 只使用规范 ID；历史报告不回写。`XF-RELEASE-001` 已修复，`XF-DEPS-001` 仍开放。

## 6. 规范性修正四：BETA-003

```text
G3 → BETA-001
BETA-001 → BETA-002
BETA-001 → BETA-003
BETA-001 → REL-007
BETA-002 + BETA-003 + REL-007 → G4
```

BETA-003 必须保证每个失败有环境、复现、严重度、根因、Owner 和下一步；代码失败创建独立 Issue；P0 暂停推广；P1 关闭或有有效 Waiver；修复重跑受影响 Gate；重发递增版本；Ledger 无未分类/无 Owner/无下一步记录。

## 7. G0 仓库治理契约

- 默认分支 `develop`；普通 PR 回 `develop`；`master` 只收 G3 通过后的 Release PR；
- `develop`/`master` 要求 PR，禁止强推和删除；
- `develop` Required Checks：`test (3.10)`、`test (3.11)`、`test (3.12)`；
- 这些三版本检查是包级 CI。后续 QA-002/COMPAT-001 必须增加并保护完整 Hermes 3.11/3.12 E2E contexts。

## 8. 任务账本与执行协议

以下内容完整继承 v2.2 归档：

| 归档范围 | 继续生效的内容 |
|---|---|
| §3 | 实施协议、串并行、文件所有权、三层证据、停止条件 |
| §4 | Issue 结构、严重度、Waiver、DoD |
| §5 | G0–G5 Gate（受本文件兼容/G3/M5 修正覆盖） |
| §6 | M0–M6 的 48 Work ID、依赖、路径、测试和证据 |
| §7 | 需求/Test/XFAIL 追踪（受规范 ID 修正覆盖） |
| §8 | CI、Release、Rollback、Artifact Flow |
| §9–§11 | 风险、里程碑、检查表和交付格式 |
| 附录 A–Q | 文件所有权、逐任务细节、命令与问题回答 |

实施代理必须同时读取本文件、兼容矩阵和归档中目标 Work ID 条目。

## 9. 发布与回滚流程

```text
M0 完成 → G0
M1 完成 → G1
M2 完成 → G2
M3 + M4 完成 → G3 RC 验证
G3 PASS → develop → master Release PR
精确 master Commit 最终制品重建 + test-release
PASS → BETA-001 不可变 GitHub Tag/Release
Beta 反馈 → BETA-002 + BETA-003 + REL-007 → G4
M6 → G5 → v3.0.0
```

回滚遵循单 Work ID Squash Commit、数据备份恢复、RC 不公开、正式 Tag/制品不可变和 P0 暂停推广原则。

## 10. 附录问题的规范答案

### Q#1：为何是 3.0.0？

现有 distribution 已使用 2.x，本周期包含 package、生命周期、配置、数据和迁移的破坏性变化，使用 3.0.0 保持单调版本。

### Q#2：G3 如何验证而正式 Tag 尚未创建？

从冻结 Commit 或临时 RC Tag 构建；合入 `master` 后重建最终制品；通过后才创建不可变正式 Tag/Release。

### Q#3：为什么目标 10 而当前 9 Tool？

10 是 Beta Contract 分母；9 是当前事实。REL-004 冻结目标，CON-001 + MEM-001 实现 `memory_store`。

### Q#4：为什么 CI 仍有 Python 3.10，而完整产品只支持 3.11–3.12？

3.10 保留包级、纯模块和回归价值；Hermes v0.19.0 上游 metadata 要求 ≥3.11，因此完整 Plugin/Context/Tool E2E 只能在 3.11–3.12。Doctor 必须明确拒绝不兼容组合。

## 11. 当前下一步

1. 合并 `REL-005` PR #59，固定 GitHub-only Beta 渠道；
2. 完成 `COMPAT-000` #17 的静态 probes、规范同步、PR/CI/合并；
3. 生成 `docs/testing/evidence/GATE-G0.md`，独立核对 REL-003、REL-005、COMPAT-000 和全部 G0 条件；
4. 只有 G0 Evidence = PASS 后才启动 `PKG-001` #18；
5. `COMPAT-001` #46 后续执行 Linux/macOS × Python 3.11/3.12 真实 E2E，Python 3.10 执行预期拒绝测试。
