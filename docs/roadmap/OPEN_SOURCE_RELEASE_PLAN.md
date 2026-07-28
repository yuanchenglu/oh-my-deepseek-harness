# 开源发布执行计划（Open-source Release Execution Plan）

> 文档版本：2.3.4（Execution Progress + Session Handoff）
>
> 审查基线：`develop@37e4016`
>
> 当前已合并实施基线：`develop@d9b7c2610b1d87499242ed3dca6ad9f182454f2e`
>
> 当前 incoming Work ID：`INS-003`（PR #72）
>
> 代码验收 Head：`e2b82c727a3dedaa1c8cc71de38a54dec3c079b6`
>
> 代码验收 CI：Run #149 / ID `30339801279`
>
> 计划状态：`IN_IMPLEMENTATION`
>
> 当前 Gate：`G0 PASS`；`G1 NOT_EVALUATED`
>
> 产品成熟度：`Experimental Preview`
>
> 发布目标：`v3.0.0-beta.1` → 按需增加 Beta → `v3.0.0`
>
> 完整 v2.2 任务账本归档：[`archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md`](archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md)
>
> 当前状态账本：[`EXECUTION_STATUS.md`](EXECUTION_STATUS.md)
>
> 新会话交接提示词：[`SESSION_HANDOFF_PROMPT.md`](SESSION_HANDOFF_PROMPT.md)

## 0. 规范性说明

本文件是 Open-source Beta 发布周期的唯一主计划。v2.2 的完整任务表、文件所有权、依赖、测试入口、Gate、附录和 48 个 Work ID 已原样保存在只读归档中；除本文件明确修正、完成或替代的内容外，归档中的未修改条款继续按引用纳入本计划并保持规范效力。

执行优先级固定为：

1. 本文件 v2.3.4 的明确规则和当前进展；
2. `docs/compatibility/HERMES_MATRIX.md` 的 Hermes 候选、Python 分层和 COMPAT-001 验证计划；
3. PRD、Product/Technical Architecture、Test Plan 和 Traceability 的已同步契约；
4. v2.2 归档中的未修改任务细节；
5. 历史测试报告，仅作为不可变历史证据。

当旧文档只写“Python 3.10–3.12”而未区分运行层级时，解释为包级/纯模块 CI；完整 Hermes v0.19.0 集成支持仅为 Python 3.11–3.12。不得把 Python 3.10 的包级绿色 CI 描述为真实 Hermes E2E 通过。

## 更新记录（Update Log）

| 日期 | 版本 | 更新内容 |
|---|---|---|
| 2026-07-27 | 1.0–2.2 | 建立并严格化 48 Work ID、88 FR、17 CR、100 Test ID、Gate、Migration、Security 和 Release 基线 |
| 2026-07-28 | 2.3 | 合并 Errata，归档 v2.2 全量账本，修正 RC/Tag、Tool 分母、XFAIL 和 BETA-003 |
| 2026-07-28 | 2.3.1–2.3.3 | 完成治理/追踪并固定 Hermes v0.19.0、Python 支持分层和 COMPAT-001 矩阵 |
| 2026-07-28 | 2.3.4 | 记录 G0 PASS、PKG/RUN/INS-001/002 完成及 INS-003 生命周期验收；同步进度、下一项和交接 |

## 1. 当前结论与整体进度

### 1.1 发布判断

当前产品仍是 **Experimental Preview**，尚未达到 Public Beta 或 Stable。G0、包布局、依赖分层、App Factory、本地单进程 Supervisor、installed-distribution 安装事务、read-only Doctor，以及安全 upgrade/uninstall/recovery 生命周期已建立或达到 protected merge 条件；artifact 全生命周期、Context Integrity、Session Isolation、10 Tool Contract、完整 Migration、安全强化、真实 Hermes E2E 和最终 Release Artifact 仍未完成。

### 1.2 任务账本进度

PR #72 protected Squash Merge 且 Issue #24 关闭后，固定分母 48 个 Work ID 的状态为：

| 状态 | 数量 | 比例 |
|---|---:|---:|
| Complete | 15 | 31.3% |
| In progress | 0 | 0.0% |
| Not started / dependency blocked | 33 | 68.8% |
| Total | 48 | 100% |

该比例只表示 Work ID 账本进度，**不等于发布就绪度**。Gate 必须独立以 Evidence 判定。

### 1.3 Gate 状态

| Gate | 状态 | 说明 |
|---|---|---|
| Plan Ready | PASS | 48 Issue、88 FR、17 CR、100 Test ID 和执行协议已固定 |
| G0 | PASS | 治理、版本、发布渠道、Hermes 候选和实施基线已完成；G0 does not claim product release readiness |
| G1 | NOT_EVALUATED | M1 尚有 QA-ART-001 未完成 |
| G2–G5 | NOT_STARTED | 必须按硬依赖串行推进 |

## 2. 已完成的 M0 / G0

| Work ID | 状态 | Delivery | 核心结果 |
|---|---|---|---|
| `REL-000` | Complete | PR #4 · `e18db7e` | 规格、88 FR、100 Test ID 同步 |
| `REL-001` | Complete | PR #6 · `a97dfe4` | Distribution/Manifest/Git 版本语义统一 |
| `REL-002` | Complete | PR #8/#9 · `e7e1414e`/`61642f69` | develop 默认分支、Ruleset、治理和主计划 |
| `REL-004` | Complete | PR #11 · `7d52de9f` | 唯一 10 Tool 目标分母；Runtime 保持真实 9 Tool |
| `GOV-001` | Complete | PR #14 · `a0083ce1` | Security、Issue/PR Forms、Release Checklist |
| `REL-003` | Complete | PR #58 · `fd5c212f` | 48 Issue、88 FR、17 CR、100 Test ID 追踪 |
| `REL-005` | Complete | PR #59 · `49ad479f` | 首个 Beta 使用 GitHub Release；PyPI 安全禁用 |
| `COMPAT-000` | Complete | PR #60 · `c7f6212a` | Hermes v0.19.0 候选和静态契约 |
| `G0` | PASS | PR #61 · `ee516c9b` | 独立 Gate Evidence 完成 |

G0 不表示产品可发布，只授权 M1 实施。

## 3. 当前 M1 状态

```text
PKG-001 → PKG-002 → RUN-001 → RUN-002 → INS-001 → INS-002 → INS-003 → QA-ART-001 → G1
```

| Work ID | Issue | 状态 | Delivery / remote evidence | 结果或下一步 |
|---|---:|---|---|---|
| `PKG-001` | #18 | Complete | PR #62 · `2098dffc` | 唯一 `src/` 生产实现；wheel/外部导入通过 |
| `PKG-002` | #19 | Complete | PR #63 · `ae277d1d` | dependency Extras；关闭 `XF-DEPS-001` |
| `RUN-001` | #20 | Complete | PR #64 · `31366ceb` | 无副作用 App Factory；health/ready/version |
| `RUN-002` | #21 | Complete | PR #65 · `f1c04697` | 安全 Supervisor、ownership、日志和进程 E2E |
| `INS-001` | #22 | Complete | PR #68 · `2e5438a7` | dry-run、clean/idempotent install、事务 rollback、关闭 `XF-INSTALL-001` |
| `INS-002` | #23 | Complete | PR #70 · `d1d3269d` · [`INS-002.md`](../testing/evidence/INS-002.md) | read-only Doctor、human/JSON、依赖/端口/支持矩阵诊断 |
| `INS-003` | #24 | **Complete on protected merge** | PR #72 · [`INS-003.md`](../testing/evidence/INS-003.md) | upgrade、rollback/recover、ordinary uninstall、confirmed purge、destructive boundaries |
| `QA-ART-001` | #25 | **Open — eligible only after #24 closes** | — | source-external 完整 artifact lifecycle；完成后生成 G1 Evidence |

PR #72 合并后，M1 为 **7/8 Complete、0/8 In progress、1/8 Open eligible**。G1 不得提前判定。

## 4. INS-003 验收证据

INS-003 代码验收 Head `e2b82c727a3dedaa1c8cc71de38a54dec3c079b6`，Required CI Run #149 / ID `30339801279`：

```text
Python 3.10: success — package/core CI
Python 3.11: success
Python 3.12: success
228 tests / 0 failures / 0 errors / 9 strict XFAIL per version
```

核心验收：

- upgrade dry-run 报告 Config/DB/JSONL/process/backup 影响且零写入；
- same-version upgrade 幂等、无备份增长、复用同一 PID；
- version change 在 mutation 前备份 adapters/config/SQLite DB/events；
- 普通失败自动恢复 prior deployment/data/process state；
- 中断事务保留 private marker/backup，支持显式 recover 与重试；
- ordinary uninstall 移除 managed deployment/runtime，保留 distribution 和用户数据；
- CLI 只打印、不执行 `python -m pip uninstall oh-my-deepseek-harness`；
- purge 缺 `--confirm` 返回 2 且任何 process/file mutation 前终止；
- confirmed purge 仅限 lexical canonical product root 和 known owned children；
- `.hermes`/product/descendant symlink、unknown path、noncanonical root、manifest traversal 均 fail-closed；
- external DB 保留，external DB symlink 在 process change 前拒绝；
- 测试只使用临时 HOME/data/DB/port 与 fake secret。

该证据仍不表示 QA-ART-001、完整 Beta Migration、G1、真实 Hermes E2E、Public Beta、master 或 publication ready。

## 5. 固定发布契约

### 5.1 版本和 Python 分层

| Surface | Public Beta 1 | Stable |
|---|---|---|
| Git Tag / GitHub Release | `v3.0.0-beta.1` | `v3.0.0` |
| Python Distribution | `3.0.0b1` | `3.0.0` |
| Plugin Manifest | `3.0.0-beta.1` | `3.0.0` |

- Distribution metadata：`>=3.10,<3.13`；
- package/core CI：Python 3.10、3.11、3.12；
- full Hermes v0.19.0：Python 3.11、3.12；
- Python 3.10 的完整 Hermes 组合必须由 install/doctor 明确拒绝。

### 5.2 发布渠道

首个 Beta 的必选渠道是 GitHub Release。PyPI 在名称归属、Owner/Maintainer、2FA 和 Trusted Publisher/OIDC 被认证验证前保持禁用。

### 5.3 Tool Contract

Beta 目标为 10 个 Tool，当前 Runtime 为 9 个；`memory_store` 只能由 `CON-001 + MEM-001` 正式实现。禁止添加 placeholder Tool、Handler 或 Schema。

### 5.4 Hermes 候选

- Upstream：`NousResearch/hermes-agent`
- Hermes：`0.19.0`
- Tag：`v2026.7.20`
- Full product OS/Python：Linux/macOS × Python 3.11/3.12
- Python 3.10：package/core 和预期拒绝验证

`COMPAT-001` 必须执行真实 discovery、selection、Hook、ContextEngine 和 Tool E2E。

## 6. XFAIL 状态

- `XF-RELEASE-001`：已由 REL-001 修复；
- `XF-DEPS-001`：已由 PKG-002 修复；
- `XF-INSTALL-001`：已由 INS-001 关闭；
- INS-003 完整套件为每版本 228 tests、0 failures、0 errors、9 个既有 strict XFAIL；
- 其余 XFAIL 必须由各自 canonical Work ID 修复，不得重命名、复制或弱化。

## 7. 分支、CI 与执行协议

- 默认/集成分支：`develop`；
- 发布分支：`master`，仅接受 G3 PASS 后的 Release PR；
- 功能分支 → PR → Required CI → Squash Merge develop；
- develop Required Checks：`test (3.10)`、`test (3.11)`、`test (3.12)`；
- 单次只实施一个 Work ID；
- 每个 Work ID 必须有 Issue、分支、PR、Evidence、回滚和 Required CI；
- 依赖未满足时不得启动后继；
- 不以直推 develop 绕过 Ruleset；
- 不创建 Tag、Release 或 PyPI publication，除非到达相应 Gate/Work ID。

## 8. 发布路径

```text
M0 → G0 PASS
M1 → G1
M2 → G2
M3 + M4 → G3 RC
G3 PASS → develop → master Release PR
精确 master Commit 重建最终制品 + test-release
PASS → BETA-001 不可变 GitHub Tag/Release
BETA-002 + BETA-003 + REL-007 → G4
M6 → G5 → v3.0.0
```

## 9. 当前下一步

1. PR #72 final Required Checks 通过后标记 Ready，protected Squash Merge 到 `develop`；
2. 记录 INS-003 Squash Commit、关闭 Issue #24，并同步 post-merge 状态；
3. 只有该收口完成后，下一项唯一可启动 Work ID 为 `QA-ART-001` #25；
4. QA-ART-001 必须从 source-external final artifacts 执行 install → doctor → upgrade → uninstall/purge 生命周期；
5. G1 只在 QA-ART-001 Evidence 完整后评估，不因 INS-003 绿色 CI 自动通过；
6. 不合入 master，不创建 Tag/Release/PyPI，不提前声明 G1/Public Beta。
