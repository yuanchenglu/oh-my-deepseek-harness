# 开源发布执行计划（Open-source Release Execution Plan）

> 文档版本：2.3.4（Execution Progress + Session Handoff）
>
> 审查基线：`develop@37e4016`
>
> 当前已合并实施基线：`develop@fc21430b54caac1a8de4cfb1a03940b2b83c25c4`
>
> 当前 incoming Work ID：`QA-ART-001`（PR #74）
>
> 代码验收 Head：`81195f844b681e85ccf2c0a15fc4935b2b396ed6`
>
> 代码验收 CI：Run #161 / ID `30342161995`
>
> 计划状态：`IN_IMPLEMENTATION`
>
> 当前 Gate：`G0 PASS`；`G1 READY_FOR_SEPARATE_EVALUATION ON MERGE`
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

当旧文档只写“Python 3.10–3.12”而未区分运行层级时，解释为包级/纯模块/制品生命周期 CI；完整 Hermes v0.19.0 集成支持仅为 Python 3.11–3.12。不得把 Python 3.10 的绿色 CI 描述为真实 Hermes E2E 通过。

## 更新记录（Update Log）

| 日期 | 版本 | 更新内容 |
|---|---|---|
| 2026-07-27 | 1.0–2.2 | 建立并严格化 48 Work ID、88 FR、17 CR、100 Test ID、Gate、Migration、Security 和 Release 基线 |
| 2026-07-28 | 2.3 | 合并 Errata，归档 v2.2 全量账本，修正 RC/Tag、Tool 分母、XFAIL 和 BETA-003 |
| 2026-07-28 | 2.3.1–2.3.3 | 完成治理/追踪并固定 Hermes v0.19.0、Python 支持分层和 COMPAT-001 矩阵 |
| 2026-07-28 | 2.3.4 | 记录 G0 PASS、M1 PKG/RUN/INS 完成以及 QA-ART-001 最终 wheel 验收；同步 G1 独立评估边界 |

## 1. 当前结论与整体进度

### 1.1 发布判断

当前产品仍是 **Experimental Preview**，尚未达到 Public Beta 或 Stable。G0、包布局、依赖分层、App Factory、本地单进程 Supervisor、installed-distribution 安装、read-only Doctor、安全 upgrade/uninstall/recovery，以及源码外最终 wheel 生命周期已经建立或达到 protected merge 条件。

以下仍未完成：G1 独立 Gate 判定、Context Integrity、Session Isolation、目标 10 Tool Contract、完整 Migration、安全强化、真实 Hermes E2E、最终 RC reproducibility/provenance 与 Release Artifact 验证。

QA-ART-001 绿色 CI **不等于** G1 PASS，也不等于 Public Beta、master 或 publication ready。

### 1.2 任务账本进度

PR #74 protected Squash Merge 且 Issue #25 关闭后，固定分母 48 个 Work ID 的状态为：

| 状态 | 数量 | 比例 |
|---|---:|---:|
| Complete | 16 | 33.3% |
| In progress | 0 | 0.0% |
| Not started / dependency blocked | 32 | 66.7% |
| Total | 48 | 100% |

该比例只表示 Work ID 账本进度，**不等于发布就绪度**。Gate 必须独立以 Evidence 判定。

### 1.3 Gate 状态

| Gate | 状态 | 说明 |
|---|---|---|
| Plan Ready | PASS | 48 Issue、88 FR、17 CR、100 Test ID 和执行协议已固定 |
| G0 | PASS | 治理、版本、发布渠道、Hermes 候选和实施基线已完成；G0 does not claim product release readiness |
| G1 | READY_FOR_EVALUATION on QA-ART merge | M1 8/8 Complete 后逐条核对规范 Gate 条款、P0 blocker 与 Evidence；不得自动 PASS |
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

| Work ID | Issue | 状态 | Delivery / remote evidence | 结果 |
|---|---:|---|---|---|
| `PKG-001` | #18 | Complete | PR #62 · `2098dffc` | 唯一 `src/` 生产实现；wheel/外部导入通过 |
| `PKG-002` | #19 | Complete | PR #63 · `ae277d1d` | dependency Extras；关闭 `XF-DEPS-001` |
| `RUN-001` | #20 | Complete | PR #64 · `31366ceb` | 无副作用 App Factory；health/ready/version |
| `RUN-002` | #21 | Complete | PR #65 · `f1c04697` | 安全 Supervisor、ownership、日志和进程 E2E |
| `INS-001` | #22 | Complete | PR #68 · `2e5438a7` | dry-run、clean/idempotent install、事务 rollback、关闭 `XF-INSTALL-001` |
| `INS-002` | #23 | Complete | PR #70 · `d1d3269d` | read-only Doctor、human/JSON、依赖/端口/支持矩阵诊断 |
| `INS-003` | #24 | Complete | PR #72 · `9e5295ac` | upgrade、rollback/recover、ordinary uninstall、confirmed purge、destructive boundaries |
| `QA-ART-001` | #25 | **Complete on protected merge** | PR #74 · [`QA-ART-001.md`](../testing/evidence/QA-ART-001.md) | clean snapshot final wheel 的源码外完整生命周期 |

PR #74 合并后，M1 为 **8/8 Complete**。这只使 G1 具备独立评估条件，G1 不得提前判定。

## 4. QA-ART-001 验收证据

QA-ART-001 代码验收 Head `81195f844b681e85ccf2c0a15fc4935b2b396ed6`，Required CI Run #161 / ID `30342161995`：

```text
Python 3.10: success — 230 tests / 0 failures / 0 errors / 9 strict XFAIL
Python 3.11: success — 230 tests / 0 failures / 0 errors / 9 strict XFAIL
Python 3.12: success — 230 tests / 0 failures / 0 errors / 9 strict XFAIL
artifact JUnit per job: 1 test / 0 failures / 0 errors / 0 skipped
```

核心验收：

- build input 只来自 clean `git archive HEAD`；
- fresh non-editable venv 只安装最终 wheel distribution 与其 `all` 依赖；
- `PYTHONPATH` 为空，执行 cwd 位于 repository 与 archived source 之外；
- product module `__file__` 和 `sys.path` 均无 source contamination；
- wheel 包含 39 files，不包含 `plugins/`、`mcp/` 或 `tests/`；
- install dry-run 零写入，clean install 启动一个 ready Server；
- Python 3.10 Doctor 按支持分层退出 5；Python 3.11/3.12 Doctor 退出 0；
- `/health`、`/ready`、`/version` 与 `POST /memory/tag` smoke 通过；
- same-version upgrade `up_to_date`、不变更、复用同 PID；
- ordinary uninstall 保留 distribution/config/DB，并只打印精确 pip uninstall command；
- 显式 pip uninstall 仅由测试脚本在临时 venv 执行；
- fake Secret 未出现在上传文本证据；
- 每个 Required job 上传 wheel、SHA256、inventory、JSON/log、pytest JUnit 和 artifact JUnit。

三个 job 的 wheel SHA256 不同。QA-ART-001 记录并验证每个实际制品，但**不声明 byte-for-byte reproducible-build PASS**。最终 reproducibility/provenance 仍由 `REL-006` 负责，除非 G1 的原始规范条款明确另有要求。

## 5. 固定发布契约

### 5.1 版本和 Python 分层

| Surface | Public Beta 1 | Stable |
|---|---|---|
| Git Tag / GitHub Release | `v3.0.0-beta.1` | `v3.0.0` |
| Python Distribution | `3.0.0b1` | `3.0.0` |
| Plugin Manifest | `3.0.0-beta.1` | `3.0.0` |

- Distribution metadata：`>=3.10,<3.13`；
- package/core/artifact lifecycle CI：Python 3.10、3.11、3.12；
- full Hermes v0.19.0 candidate：Python 3.11、3.12；
- Python 3.10 的完整 Hermes 组合必须由 install/doctor 明确拒绝。

### 5.2 发布渠道

首个 Beta 的必选渠道是 GitHub Release。PyPI 在名称归属、Owner/Maintainer、2FA 和 Trusted Publisher/OIDC 被认证验证前保持禁用。公开搜索缺失不构成名称可用或归属证据。

### 5.3 Tool Contract

Beta 目标为 10 个 Tool，当前 Runtime 为 9 个；`memory_store` 只能由 `CON-001 + MEM-001` 正式实现。禁止添加 placeholder Tool、Handler 或 Schema。

### 5.4 Hermes 候选

- Upstream：`NousResearch/hermes-agent`
- Hermes：`0.19.0`
- Tag：`v2026.7.20`
- Full product OS/Python：Linux/macOS × Python 3.11/3.12
- Python 3.10：package/core/artifact lifecycle 和预期拒绝验证

`COMPAT-001` 必须执行真实 discovery、selection、Hook、ContextEngine 和 Tool E2E。G1 是否要求该真实矩阵，必须依据 G1 原始规范条款判定，不得自行提前或豁免。

## 6. XFAIL 状态

- `XF-RELEASE-001`：已由 REL-001 修复；
- `XF-DEPS-001`：已由 PKG-002 修复；
- `XF-INSTALL-001`：已由 INS-001 关闭；
- QA-ART-001 完整套件为每版本 230 tests、0 failures、0 errors、9 个既有 strict XFAIL；
- 剩余 strict XFAIL 均必须由后续 canonical Work ID 关闭，不得重命名、复制、skip 或弱化。

## 7. 分支、CI 与执行协议

- 默认/集成分支：`develop`；
- 发布分支：`master`，仅接受 G3 PASS 后的 Release PR；
- 功能分支 → PR → Required CI → Squash Merge develop；
- develop Required Checks：`test (3.10)`、`test (3.11)`、`test (3.12)`；
- 每个 Required Check 均执行 pytest 和源码外 final-wheel artifact lifecycle；
- 单次只实施一个 Work ID 或一个 Gate 判定；
- 每个 Work ID 必须有 Issue、分支、PR、Evidence、回滚和 Required CI；
- 依赖未满足时不得启动后继；
- 不以直推 develop 绕过 Ruleset；
- 不创建 Tag、Release 或 PyPI publication，除非到达相应 Gate/Work ID。

## 8. 发布路径

```text
M0 → G0 PASS
M1 8/8 → 独立 G1 判定
G1 PASS → M2 → G2
G2 → M3
M2 + M3 → M4 → G3 RC
G3 PASS → develop → master Release PR
精确 master Commit 重建最终制品 + test-release
PASS → BETA-001 不可变 GitHub Tag/Release
BETA-002 + BETA-003 + REL-007 → G4
G4 → STABLE-001 → SOAK-001 → G5 → REL-008
```

## 9. 当前下一步

1. PR #74 final Required Checks 通过后标记 Ready，protected Squash Merge 到 `develop`；
2. 记录 QA-ART-001 Squash Commit、关闭 Issue #25，并同步 post-merge 状态；
3. QA-ART-001 post-merge 收口后，创建独立 G1 Gate Evidence，不得直接启动 CTX-001；
4. G1 逐条核对主计划/归档标准、M1 Evidence、P0 blocker、Python/Hermes 分层和 open XFAIL ownership；
5. 只有 G1 明确 PASS 后，才按固定依赖确定下一个唯一 Work ID；
6. 不合入 master，不创建 Tag/Release/PyPI，不提前声明 Public Beta。
