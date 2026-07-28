# 开源发布执行计划（Open-source Release Execution Plan）

> 文档版本：2.3.8（G1 Closed / CTX-001 Next）
>
> 状态日期：2026-07-29
>
> 当前事实基线：`develop@b0b9d2e0337a9f40f2abcdb0f91ce8b2865ea765`
>
> G1 复评 PR：#79（Merged）
>
> G1 PASS Squash：`b0b9d2e0337a9f40f2abcdb0f91ce8b2865ea765`
>
> G1 Final CI：Run #193 / ID `30384094675`
>
> 计划状态：`M1_COMPLETE / G1_PASS / M2_NEXT_CTX_001`
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

本文件记录当前事实、Gate 结论与唯一串行任务。v2.2 归档继续保存全部 48 个 Work ID、授权路径、硬依赖、88 FR、17 CR、100 Test IDs、G0–G5 与发布协议。

事实冲突优先级：

1. GitHub 当前远程事实；
2. 本文件当前版本；
3. `EXECUTION_STATUS.md`、Traceability 与独立 Gate Evidence；
4. PRD、架构、Test Plan、Hermes Matrix；
5. v2.2 中未被当前文件修正的条款。

## 1. 当前发布判断

当前产品仍是 **Experimental Preview**。G1 PASS 只解锁 M2，不表示 Public Beta、master、Tag、GitHub Release、PyPI 或 Stable Ready。

### 已完成

- M0 全部 Work ID；
- G0 独立 PASS；
- M1 8/8 Work ID；
- 唯一 `src/` 生产包、dependency extras、App Factory、loopback Runtime 与安全 Supervisor；
- installed-distribution install/Doctor/upgrade/recover/uninstall/purge；
- 同一 clean snapshot 的 wheel + sdist build；
- wheel/sdist SHA256 与 inventory；
- Required `python -m twine check dist/*`；
- final-wheel source-external full lifecycle；
- G1 初评 FAIL、canonical remediation 与独立 PASS 复评；
- G1 PASS PR #79 已合入 `develop`。

## 2. 固定 Work ID 进度

| 状态 | 数量 | 比例 |
|---|---:|---:|
| Complete | 16 | 33.3% |
| In progress | 0 | 0.0% |
| Not started / dependency blocked | 32 | 66.7% |
| Total | 48 | 100% |

启动 `CTX-001` 后状态转为 Complete 16 / In progress 1 / Not started 31。

## 3. Gate 状态

| Gate | 状态 | Evidence / 说明 |
|---|---|---|
| Plan Ready | PASS | 48 Issues、88 FR、17 CR、100 Test IDs |
| G0 | PASS | PR #61 · `ee516c9b` · `GATE-G0.md` |
| G1 | **PASS** | 初评 PR #77；remediation PR #78；复评 PR #79 · `b0b9d2e0` · Run #193 |
| G2 | NOT_STARTED | M2 尚未完成 |
| G3 | NOT_STARTED | 依赖 M2、M3、M4 与 RC Evidence |
| G4 | NOT_STARTED | 依赖 Beta 反馈闭环 |
| G5 | NOT_STARTED | 依赖 Stable 阶段与 soak |

G1 checklist：**10 PASS / 0 FAIL / 0 BLOCKED**。

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

## 5. M1 / G1 完成状态

| Work ID | Issue | Delivery | 状态 |
|---|---:|---|---|
| `PKG-001` | #18 | PR #62 · `2098dffc` | Complete |
| `PKG-002` | #19 | PR #63 · `ae277d1d` | Complete |
| `RUN-001` | #20 | PR #64 · `31366ceb` | Complete |
| `RUN-002` | #21 | PR #65 · `f1c04697` | Complete |
| `INS-001` | #22 | PR #68 · `2e5438a7` | Complete |
| `INS-002` | #23 | PR #70 · `d1d3269d` | Complete |
| `INS-003` | #24 | PR #72 · `9e5295ac` | Complete |
| `QA-ART-001` | #25 | PR #74 · `7adbb0cb`; PR #78 · `5ebb3a0c` | Complete |

QA remediation：

```text
Code acceptance: Run #183 / ID 30382373294
Final PR Head: 531aa0e3fd327dc9a096668432ebd1d0b2bff43b
Final CI: Run #184 / ID 30382668758
Squash: 5ebb3a0c9b44cd5f2a2be789f9224740d47894f8
Python 3.10/3.11/3.12: each 231 tests / 0 failures / 0 errors / 9 strict XFAIL
Artifact JUnit per job: 1 / 0 failures / 0 errors / 0 skipped
Wheel inventory: 39 files
sdist inventory: 75 files
Twine: wheel + sdist PASS in all Required jobs
```

G1 PASS：

```text
Final PR Head: e6e39b54040c5deba12d474daf596f7da4272a7c
Final CI: Run #193 / ID 30384094675
Python 3.10/3.11/3.12: success
Squash: b0b9d2e0337a9f40f2abcdb0f91ce8b2865ea765
```

## 6. G1 关键解释

### 6.1 Clean source 与正式 Tag

G1 以冻结 Commit 的 `git archive HEAD` 作为 clean-source 证据。正式不可变 Beta Tag 只能在精确 master artifact 与最终 `test-release` 通过后创建，不得为满足 G1 措辞提前 Tag。

### 6.2 Reproducibility

三版本独立构建的 wheel/sdist SHA256 不同。G1 不要求 byte-for-byte reproducibility；`REL-006` 负责 RC/final reproducibility、SBOM、provenance 与精确 master Commit 重建。

### 6.3 Real Hermes E2E

兼容候选固定为 **Hermes Agent v0.19.0 / Git tag `v2026.7.20`**。真实 Hermes discovery、enablement、Hook、Context Engine、Tool E2E 属于 `COMPAT-001`（M4/G3），不属于 G1。

### 6.4 strict XFAIL

当前 9 个 strict XFAIL 均有 canonical owner：`CTX-001`、`CTX-002`、`CTX-003`、`SES-001`、`AUD-001`、`CON-001`×3、`MEM-002`。不得改 skip、隐藏 XPASS 或弱化断言。

## 7. M2 强制串行顺序

归档硬依赖：

```text
CTX-001 → CTX-002 → CTX-003 → CTX-004
PKG-001 → SES-001
CTX-003 + SES-001 → PRIV-001
CTX-004 + PRIV-001 → G2
```

G1 PASS 后 `CTX-001` 与 `SES-001` 的阶段依赖均满足。为保持单一 Work ID 串行执行，按 canonical 表格与 Issue 顺序固定：

```text
CTX-001 → CTX-002 → CTX-003 → CTX-004 → SES-001 → PRIV-001 → G2
```

## 8. 后续完整路线

```text
CTX-001 → CTX-002 → CTX-003 → CTX-004 → SES-001 → PRIV-001 → G2
G2 PASS → M3
M2 + M3 Complete → M4 → G3 RC
G3 PASS → develop → master Release PR
精确 master Commit 重建 + test-release
PASS → BETA-001 v3.0.0-beta.1 GitHub Release
BETA-002 + BETA-003 + REL-007 → G4
G4 → STABLE-001 → SOAK-001 → G5 → REL-008 v3.0.0
```

PyPI 按 `REL-005` 保持禁用，直到 Owner 完成名称、权限、2FA 与 Trusted Publisher/OIDC 外部门禁。

## 9. 当前唯一合法下一步

1. 完成 docs-only G1 post-merge closure；
2. 重新读取最新 `develop`；
3. 读取 canonical Issue #26 与评论；
4. 创建 `fix/ctx-001-merge-uniqueness`；
5. 将 `TC-CTX-003` 从 strict XFAIL 转为普通失败测试；
6. 只修复 Merge 分支重复装配；
7. 创建 `docs/testing/evidence/CTX-001.md`；
8. 同一最终 Head Required CI 全绿后 expected-Head Squash Merge；
9. 自动进入 `CTX-002`。

## 10. 严格边界

- 不并行启动 `SES-001`；
- 不提前实施 CTX-002/003/004、Privacy 或 M3；
- 不合入 `master`；
- 不创建 Tag 或 GitHub Release；
- 不发布 PyPI；
- 不声称 Public Beta Ready；
- 不把 fake Hermes 描述为真实 Hermes E2E；
- 不改变目标 10 / 当前 Runtime 9 Tool 口径；
- 不读取或修改真实用户 HOME、DB、Memory、Secret；
- 不弱化 PID、symlink、traversal、rollback 或 destructive-operation 防线。
