# 开源发布执行计划（Open-source Release Execution Plan）

> 文档版本：2.3.6（G1 Independent Evaluation FAIL）
>
> 状态日期：2026-07-29
>
> 当前事实基线：`develop@8260c671786aa2ea994d61e6bde09ad57992ef36`
>
> G1 评估分支：`docs/gate-g1-evaluation`
>
> G1 评估 PR：#77
>
> 计划状态：`M1_COMPLETE / G1_FAIL / QA_ART_001_REMEDIATION_REQUIRED`
>
> 当前产品成熟度：`Experimental Preview`
>
> 发布目标：`v3.0.0-beta.1` → 按需增加 Beta → `v3.0.0`
>
> 完整 48 Work ID 账本：[`archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md`](archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md)
>
> 当前状态：[`EXECUTION_STATUS.md`](EXECUTION_STATUS.md)
>
> 新会话交接：[`SESSION_HANDOFF_PROMPT.md`](SESSION_HANDOFF_PROMPT.md)
>
> G1 Evidence：[`GATE-G1.md`](../testing/evidence/GATE-G1.md)

## 0. 规范性说明

本文件记录当前事实、Gate 结论和唯一合法下一步。v2.2 归档继续保存全部 48 个 Work ID、文件所有权、硬依赖、88 FR、17 CR、100 Test IDs、G0–G5 与发布协议。

事实冲突时按以下优先级处理：

1. GitHub 当前远程事实；
2. 本文件当前版本；
3. `EXECUTION_STATUS.md`、Traceability 与 Gate Evidence；
4. `HERMES_MATRIX.md`、PRD、架构和 Test Plan；
5. v2.2 中未被当前文件修正的条款。

## 1. 当前发布判断

当前产品仍是 **Experimental Preview**，尚未达到 Public Beta、master、Tag、GitHub Release 或 Stable Ready。

### 已完成

- M0 全部 Work ID；
- G0 独立 PASS；
- M1 8/8 Work ID：`PKG-001`、`PKG-002`、`RUN-001`、`RUN-002`、`INS-001`、`INS-002`、`INS-003`、`QA-ART-001`；
- 唯一 `src/` 生产包布局与 dependency extras；
- App Factory、loopback Runtime 探针和安全单进程 Supervisor；
- installed-distribution install/Doctor/upgrade/recover/uninstall/purge；
- clean snapshot final-wheel source-external lifecycle；
- G1 独立证据评估。

### G1 实际结论

G1 checklist：**8 PASS / 2 FAIL / 0 BLOCKED**。

失败项：

1. Required artifact 路径只构建 wheel，尚未从同一 clean snapshot 构建并验证 sdist；
2. Required artifact 路径尚未执行 `python -m twine check dist/*`。

因此 G1 结论是 **FAIL**，不是 READY、PASS 或 BLOCKED。M2 仍被阻塞。

## 2. 固定 Work ID 进度

| 状态 | 数量 | 比例 |
|---|---:|---:|
| Complete | 16 | 33.3% |
| In progress | 0 | 0.0% |
| Not started / dependency blocked | 32 | 66.7% |
| Total | 48 | 100% |

Gate 失败不撤销已经真实完成的 Work ID，但对应 canonical owner 必须重新开启并完成 remediation，Gate 才能重新评估。

## 3. Gate 状态

| Gate | 状态 | Evidence / 说明 |
|---|---|---|
| Plan Ready | PASS | 48 Issues、88 FR、17 CR、100 Test IDs 已固定 |
| G0 | PASS | PR #61 · `ee516c9b` · `GATE-G0.md` |
| G1 | **FAIL** | PR #77 · `GATE-G1.md`；缺 sdist 与 twine check |
| G2 | NOT_STARTED | 依赖 G1 PASS |
| G3 | NOT_STARTED | 依赖 M2、M3、M4 与 RC Evidence |
| G4 | NOT_STARTED | 依赖 Beta 反馈闭环 |
| G5 | NOT_STARTED | 依赖 Stable 阶段与 soak |

G1 PASS 只解锁 M2，不表示 Public Beta、master 或 publication ready。

## 4. M0 / G0 完成状态

| Work ID / Gate | Delivery | 状态 |
|---|---|---|
| `REL-000` | PR #4 · `e18db7e` | Complete |
| `REL-001` | PR #6 · `a97dfe4` | Complete |
| `REL-002` | PR #8/#9 · `e7e1414e`/`61642f69` | Complete |
| `REL-004` | PR #11 · `7d52de9f` | Complete |
| `GOV-001` | PR #14 · `a0083ce1` | Complete |
| `REL-003` | PR #58 · `fd5c212f` | Complete |
| `REL-005` | PR #59 · `49ad479f` | Complete — GitHub-only Beta；PyPI disabled |
| `COMPAT-000` | PR #60 · `c7f6212a` | Complete |
| G0 | PR #61 · `ee516c9b` | PASS |

## 5. M1 完成状态与 G1 remediation

固定实现链路：

```text
PKG-001 → PKG-002 → RUN-001 → RUN-002 → INS-001 → INS-002 → INS-003 → QA-ART-001 → G1
```

| Work ID | Issue | Delivery | 状态 |
|---|---:|---|---|
| `PKG-001` | #18 | PR #62 · `2098dffc` | Complete |
| `PKG-002` | #19 | PR #63 · `ae277d1d` | Complete |
| `RUN-001` | #20 | PR #64 · `31366ceb` | Complete |
| `RUN-002` | #21 | PR #65 · `f1c04697` | Complete |
| `INS-001` | #22 | PR #68 · `2e5438a7` | Complete |
| `INS-002` | #23 | PR #70 · `d1d3269d` | Complete |
| `INS-003` | #24 | PR #72 · `9e5295ac` | Complete |
| `QA-ART-001` | #25 | PR #74 · `7adbb0cb` | Complete；因 G1 artifact 缺口须重新开启 remediation |

QA-ART-001 既有最终验收：

```text
Run #166 / ID 30343118259
Python 3.10: 230 tests / 0 failures / 0 errors / 9 strict XFAIL
Python 3.11: 230 tests / 0 failures / 0 errors / 9 strict XFAIL
Python 3.12: 230 tests / 0 failures / 0 errors / 9 strict XFAIL
artifact JUnit per job: 1 / 0 failures / 0 errors
```

既有证据仍有效：clean snapshot wheel、external import、install/Doctor/Server smoke、upgrade、ordinary uninstall、explicit temporary-venv pip uninstall、临时 HOME/DB/port/fake Secret。

remediation 只允许补齐：

- 同一 clean snapshot 的 wheel + sdist build；
- wheel/sdist SHA256 与 inventory；
- `python -m twine check dist/*`；
- Required Python 3.10/3.11/3.12 artifact evidence；
- QA Evidence、Traceability 和 Gate 重评。

不得借 remediation 修改 Context、Session、Tool/API/DB domain、真实 Hermes E2E、Migration 或发布流程。

## 6. G1 关键解释

### 6.1 clean Git Tag

正式不可变 Beta Tag 只能在精确 master 制品与最终 `test-release` 通过后创建。G1 的 clean-source 条款按当前发布顺序使用冻结 Commit 的 `git archive` 证据，不允许为了满足措辞提前创建 Beta Tag。

### 6.2 real Hermes E2E

真实 Hermes discovery、enablement、Hook、Context Engine 和 Tool E2E 的 canonical owner 是 `COMPAT-001`，位于 M4/G3。它不属于 G1；否则将形成 `G1 → M2 → M3 → M4/COMPAT-001 → G1` 的循环依赖。

### 6.3 reproducibility

三个独立 CI job 的 wheel SHA256 不同，不构成本次 G1 失败。原始 G1 不要求 byte-for-byte reproducibility；`REL-006` 负责 RC/final reproducibility、SBOM 和 provenance。

### 6.4 strict XFAIL

当前 9 个 strict XFAIL 均有 canonical owner：

- `CTX-001`、`CTX-002`、`CTX-003`；
- `SES-001`；
- `AUD-001`；
- `CON-001`（3 个）；
- `MEM-002`。

M1 没有无主 XFAIL；不得改 skip、弱化断言或隐藏 XPASS。

## 7. Python / Hermes 支持分层

- Python 3.10：package/core/artifact lifecycle，以及对 Hermes v0.19.0 完整组合的预期拒绝；
- Python 3.11–3.12：完整 Hermes v0.19.0 候选组合；
- 真实 Hermes E2E 仍由 `COMPAT-001` 验证；
- Python 3.10 绿色 CI 不得描述为完整 Hermes integration。

## 8. 后续完整路线

```text
G1 remediation → 独立 G1 re-evaluation
G1 PASS → M2 → G2
G2 PASS → M3
M2 + M3 Complete → M4 → G3 RC
G3 PASS → develop → master Release PR
精确 master Commit 重建 + test-release
PASS → BETA-001 v3.0.0-beta.1 GitHub Release
BETA-002 + BETA-003 + REL-007 → G4
G4 → STABLE-001 → SOAK-001 → G5 → REL-008 v3.0.0
```

PyPI 按 `REL-005` 保持禁用，直到 Owner 完成名称、权限、2FA 和 Trusted Publisher/OIDC 外部门禁。

## 9. 当前唯一合法下一步

1. 完成并合并 G1 FAIL 评估 PR #77；
2. 重新开启 canonical Issue #25；
3. 从最新 `develop` 创建 `test/qa-art-001-sdist-twine-remediation`；
4. 建立 Draft PR，补齐 sdist 和 twine Required evidence；
5. Required CI 全绿后 Squash Merge；
6. 独立重新评估 G1；
7. 只有 G1 明确 PASS 后，才启动唯一合法 M2 Work ID。

## 10. 严格边界

G1 PASS 前：

- 不启动 `CTX-001`、`SES-001` 或其他 M2；
- 不合入 `master`；
- 不创建 Tag 或 GitHub Release；
- 不发布 PyPI；
- 不声称 Public Beta Ready；
- 不把 fake Hermes 描述为真实 Hermes E2E；
- 不改变目标 10 / 当前 Runtime 9 Tool 口径；
- 不读取或修改真实用户 HOME、DB、Memory、Secret；
- 不弱化 PID、symlink、traversal、rollback 或 destructive-operation 防线。
