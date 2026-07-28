# 开源发布执行计划（Open-source Release Execution Plan）

> 文档版本：2.3.5（M1 Closure + G1 Handoff）
>
> 状态日期：2026-07-29
>
> 规范审查基线：`develop@37e4016`
>
> QA-ART-001 实施基线：`develop@7adbb0cb00e781e31fee0ee5d360f52c4bdce5eb`
>
> 最新完成 Work ID：`QA-ART-001`（Issue #25 / PR #74）
>
> 最终 PR Head：`2a0263b3fe5dec75f6dae89203ecda6b6275ec9f`
>
> 最终 Required CI：Run #166 / ID `30343118259`
>
> 计划状态：`M1_COMPLETE / G1_EVALUATION_PENDING`
>
> 当前 Gate：`G0 PASS`；`G1 READY_FOR_SEPARATE_EVALUATION`
>
> 产品成熟度：`Experimental Preview`
>
> 发布目标：`v3.0.0-beta.1` → 按需增加 Beta → `v3.0.0`
>
> 完整 v2.2 任务账本：[`archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md`](archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md)
>
> 当前状态账本：[`EXECUTION_STATUS.md`](EXECUTION_STATUS.md)
>
> 新会话交接提示词：[`SESSION_HANDOFF_PROMPT.md`](SESSION_HANDOFF_PROMPT.md)

## 0. 规范性说明

本文件是 Open-source Beta 发布周期的当前执行计划。v2.2 归档保留 48 个 Work ID、文件所有权、硬依赖、FR/CR/Test ID、Gate 和发布协议的完整细节；本文件负责记录最新事实、当前阶段、执行边界和下一步授权。

执行依据优先级：

1. 本文件 v2.3.5 的当前事实、Gate 状态和执行规则；
2. `docs/compatibility/HERMES_MATRIX.md` 的 Hermes/Python 支持分层；
3. PRD、Product/Technical Architecture、Test Plan 和 Traceability；
4. v2.2 归档中的未被本文件修正的条款；
5. 历史测试报告，仅作为不可变证据，不作为当前状态源。

Python 支持口径固定为：

- Python 3.10：package/core/source-external artifact lifecycle，以及对完整 Hermes 组合的预期拒绝；
- Python 3.11–3.12：完整 Hermes v0.19.0 候选组合；
- 不得把 Python 3.10 的绿色 CI 描述为真实 Hermes integration E2E。

## 1. 当前结论与整体进度

### 1.1 发布判断

当前产品仍为 **Experimental Preview**，尚未达到 Public Beta 或 Stable。

已经完成：

- M0 治理、版本、发布渠道、Traceability 与 Hermes 候选固定；
- G0 独立 Gate PASS；
- 唯一 `src/` 生产包布局和 dependency extras；
- 无导入副作用的 App Factory；
- 安全单进程 Supervisor、PID ownership、状态与日志边界；
- installed-distribution dry-run、事务安装、幂等安装与 rollback；
- read-only Doctor；
- upgrade、recover、ordinary uninstall、confirmed purge 与破坏性路径防线；
- clean source snapshot 构建最终 wheel，并在源码树外完成安装、Doctor、Server/API smoke、upgrade、uninstall 和显式临时 venv pip uninstall。

仍未完成：

- G1 独立 Gate 判定；
- Context Integrity、Session Isolation、Privacy 与 Audit；
- 目标 10 Tool Contract（当前 Runtime 仍为 9）；
- 完整 Migration 与真实 Hermes discovery/Hook/Context/Tool E2E；
- Security/SBOM/License/Dependency 审计；
- RC reproducibility/provenance、master Release PR、Tag、GitHub Release 和发布后闭环。

M1 全绿只表示 G1 **具备评估条件**，不等于 G1 PASS、Public Beta Ready、master Ready 或 publication Ready。

### 1.2 固定 Work ID 进度

| 状态 | 数量 | 比例 |
|---|---:|---:|
| Complete | 16 | 33.3% |
| In progress | 0 | 0.0% |
| Not started / dependency blocked | 32 | 66.7% |
| Total | 48 | 100% |

该比例只反映 Work ID 账本，不反映发布就绪度。Gate 必须独立以 Evidence 判定。

### 1.3 Gate 状态

| Gate | 状态 | 说明 |
|---|---|---|
| Plan Ready | PASS | 48 Issues、88 FR、17 CR、100 Test IDs 与执行协议已固定 |
| G0 | PASS | PR #61 · `ee516c9b` · `GATE-G0.md` |
| G1 | READY_FOR_SEPARATE_EVALUATION | M1 8/8 Complete；尚未形成独立 Gate Evidence |
| G2 | NOT_STARTED | 依赖 G1 PASS |
| G3 | NOT_STARTED | 依赖 M2、M3、M4 与 RC Evidence |
| G4 | NOT_STARTED | 依赖 Beta 反馈闭环 |
| G5 | NOT_STARTED | 依赖 Stable 阶段与 soak |

## 2. M0 / G0 完成状态

| Work ID / Gate | Delivery | 状态 | 核心结果 |
|---|---|---|---|
| `REL-000` | PR #4 · `e18db7e` | Complete | 规格、88 FR、100 Test IDs 同步 |
| `REL-001` | PR #6 · `a97dfe4` | Complete | Distribution/Manifest/Git 版本语义统一 |
| `REL-002` | PR #8/#9 · `e7e1414e`/`61642f69` | Complete | develop、Ruleset、治理与主计划 |
| `REL-004` | PR #11 · `7d52de9f` | Complete | 目标 10 Tool / 当前 Runtime 9 Tool 分母固定 |
| `GOV-001` | PR #14 · `a0083ce1` | Complete | Security、Issue/PR Forms、Release Checklist |
| `REL-003` | PR #58 · `fd5c212f` | Complete | 48 Issues 与完整 Traceability |
| `REL-005` | PR #59 · `49ad479f` | Complete | 首个 Beta 采用 GitHub Release；PyPI 保持禁用 |
| `COMPAT-000` | PR #60 · `c7f6212a` | Complete | Hermes v0.19.0 候选与支持矩阵 |
| `G0` | PR #61 · `ee516c9b` | PASS | 独立 Gate Evidence 完成 |

G0 不表示产品可发布，只授权 M1 实施。

## 3. M1 完成状态

固定链路：

```text
PKG-001 → PKG-002 → RUN-001 → RUN-002 → INS-001 → INS-002 → INS-003 → QA-ART-001 → G1
```

| Work ID | Issue | Delivery | 状态 | 核心结果 |
|---|---:|---|---|---|
| `PKG-001` | #18 | PR #62 · `2098dffc` | Complete | 唯一 `src/` 生产实现；wheel/外部导入 |
| `PKG-002` | #19 | PR #63 · `ae277d1d` | Complete | dependency extras；关闭 `XF-DEPS-001` |
| `RUN-001` | #20 | PR #64 · `31366ceb` | Complete | App Factory；health/ready/version |
| `RUN-002` | #21 | PR #65 · `f1c04697` | Complete | 安全 Supervisor、ownership、日志和进程 E2E |
| `INS-001` | #22 | PR #68 · `2e5438a7` | Complete | dry-run、事务安装、幂等与 rollback |
| `INS-002` | #23 | PR #70 · `d1d3269d` | Complete | read-only Doctor 与支持矩阵诊断 |
| `INS-003` | #24 | PR #72 · `9e5295ac` | Complete | upgrade/recover/uninstall/purge 与 destructive boundaries |
| `QA-ART-001` | #25 | PR #74 · `7adbb0cb` | **Complete** | 源码外最终 wheel 全生命周期与 Required artifact evidence |

M1：**8/8 Complete**。

## 4. QA-ART-001 最终验收

- Squash Commit：`7adbb0cb00e781e31fee0ee5d360f52c4bdce5eb`
- Code acceptance Head：`81195f844b681e85ccf2c0a15fc4935b2b396ed6`
- Final PR Head：`2a0263b3fe5dec75f6dae89203ecda6b6275ec9f`
- Code acceptance CI：Run #161 / ID `30342161995`
- Final PR-head CI：Run #166 / ID `30343118259`

```text
Python 3.10: success — 230 tests / 0 failures / 0 errors / 9 strict XFAIL
Python 3.11: success — 230 tests / 0 failures / 0 errors / 9 strict XFAIL
Python 3.12: success — 230 tests / 0 failures / 0 errors / 9 strict XFAIL
artifact JUnit per job: 1 test / 0 failures / 0 errors / 0 skipped
```

已证明：

- build input 仅来自 clean `git archive HEAD`；
- fresh non-editable venv 仅安装最终 wheel 与声明依赖；
- `PYTHONPATH` 为空，执行目录位于 repository/source snapshot 之外；
- product import origins 和 `sys.path` 无源码树污染；
- wheel 为 39 files，不包含 `plugins/`、`mcp/`、`tests/`；
- install dry-run 零写入，clean install 启动一个 ready Server；
- Python 3.10 Doctor 按支持分层退出 5，Python 3.11/3.12 退出 0；
- `/health`、`/ready`、`/version` 与 `POST /memory/tag` smoke 通过；
- same-version upgrade 幂等并复用 PID；
- ordinary uninstall 保留 distribution/config/DB，只打印精确 pip uninstall command；
- 实际 pip uninstall 仅由测试脚本在临时 venv 执行；
- fake Secret 未进入上传文本证据；
- 每个 Required job 上传 wheel、SHA256、inventory、JSON/log 与两类 JUnit。

三个独立 job 的 wheel SHA256 不同。本 Work ID 不声明 byte-for-byte reproducible-build PASS；最终 reproducibility/provenance 仍由 `REL-006` 负责，除非 G1 原始条款明确将其前置。

## 5. G1 独立评估要求

G1 不是 Work ID 数量统计。必须先读取主计划、v2.2 归档、Test Plan、Traceability 和全部 M1 Evidence，建立逐条 Gate checklist，再判定：`PASS`、`FAIL` 或 `BLOCKED`。

至少核对：

1. M1 八个 Work ID 的 Issue、PR、Squash Commit、Evidence 与 Required CI 是否闭环；
2. `CR-P0-001` 是否已关闭，是否仍有属于 G1 的开放 P0 blocker；
3. package/import/Server/Supervisor/install/Doctor/lifecycle/final-wheel 证据是否来源明确；
4. 9 个 strict XFAIL 是否全部归属于后续 canonical Work IDs，M1 是否没有无主 XFAIL；
5. Python 3.10 与 3.11–3.12 支持分层是否一致；
6. wheel hash 差异是否属于 G1 blocker，必须按原始 Gate 条款判断；
7. 真实 Hermes E2E 是否属于 G1，必须按规范依赖判断，不得擅自提前或豁免；
8. 是否存在真实 HOME/DB/Secret 污染、foreign PID、symlink/traversal 或 destructive-operation 未闭环风险；
9. Gate Evidence 必须列出每条标准、证据、判定、风险与 exclusions。

G1 PASS 只解锁 M2 的合法入口，不表示 Public Beta Ready。

## 6. 后续路线

```text
M0 → G0 PASS
M1 8/8 Complete → 独立 G1 判定
G1 PASS → 按硬依赖启动唯一 M2 Work ID → G2
G2 PASS → M3
M2 + M3 Complete → M4 → G3 RC
G3 PASS → develop → master Release PR
精确 master Commit 重建最终制品 + test-release
PASS → BETA-001 不可变 GitHub Tag/Release
BETA-002 + BETA-003 + REL-007 → G4
G4 → STABLE-001 → SOAK-001 → G5 → REL-008
```

当前不得启动 CTX-001、SES-001 或其他 G1 后继任务，直到独立 `GATE-G1.md` 明确 PASS。

## 7. 分支、CI 与执行协议

### 7.1 正常路径：PR 优先

1. 从最新 `develop` 创建功能/文档分支；
2. 建立 Pull Request，标题和描述清楚说明 Work ID、范围、风险与验证；
3. 执行 Required CI：`test (3.10)`、`test (3.11)`、`test (3.12)`；
4. CI 全绿后 Squash Merge 到 `develop`；
5. 更新 Issue、Evidence、Traceability、状态账本和 post-merge 事实；
6. `master` 仅接受达到相应 Release Gate 后的发布 PR。

### 7.2 异常路径：直推 develop 仅作兜底

`develop` 已取消 PR 强制保护，但直推不是默认方案。只有 PR 流程持续因环境、依赖、规则冲突或平台故障无法完成时，才允许：

1. 先定位根因，区分代码缺陷与环境缺陷；
2. 能修复则修复并继续 PR；
3. 当前环境确实无法解决时，才可直推 `develop`，不得直推 `master`；
4. Commit message 必须包含：

```text
<type>(<scope>): <变更说明>

## 问题原因
<PR/CI 无法完成的真实根因>

## 技术债务
- <未解决事项或后续工作>
```

5. 技术债务可记录在 Commit message，或记录到 `docs/TECH_DEBT.md`；格式：`[日期] 描述 | 遗留原因 | 状态`；
6. 直推后仍需补齐 Evidence、状态账本和可追溯性。

核心原则：能走 PR 就走 PR；直推必须说明原因和债务；不得以直推绕过安全、测试或发布 Gate。

## 8. 当前唯一下一步

1. 以 `develop@7adbb0cb00e781e31fee0ee5d360f52c4bdce5eb` 为 QA-ART 实施基线，完成本次 post-merge 文档收口；
2. 从收口后的最新 `develop` 创建独立 `docs/gate-g1-evaluation` 分支和 Draft PR；
3. 创建 `docs/testing/evidence/GATE-G1.md`，逐条评估 G1，结论只能为 PASS、FAIL 或 BLOCKED；
4. 同步 Execution Status、主计划、Traceability 与下一会话 handoff；
5. G1 未明确 PASS 前，不启动任何 M2 实现；
6. 不合入 `master`，不创建 Tag/GitHub Release，不发布 PyPI。

## 9. 明确边界

当前完成状态不代表：

- 真实 Hermes integration E2E 已通过；
- 10 Tool Runtime Contract 已完成；
- Context/Session/Privacy/Migration/Security 已完成；
- reproducible build、SBOM、RC 或最终 Release Artifact 已完成；
- Public Beta、master、Tag、GitHub Release 或 PyPI 已就绪。
