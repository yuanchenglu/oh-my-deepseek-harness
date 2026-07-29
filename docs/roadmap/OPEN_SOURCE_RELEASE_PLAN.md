# 开源发布执行计划（Open-source Release Execution Plan）

> 文档版本：2.3.10（CTX-002 Complete / CTX-003 Next）
>
> 状态日期：2026-07-29
>
> 当前事实基线：`develop@bf4ab49e1b3c5bbe752931d19460ad2de4243a6f`
>
> 计划状态：`M1_COMPLETE / G1_PASS / CTX_001_COMPLETE / CTX_002_COMPLETE / M2_NEXT_CTX_003`
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

## 0. 规范性说明

本文件记录当前事实、Gate 结论与唯一串行任务。v2.2 归档继续保存全部 48 Work ID、授权路径、硬依赖、88 FR、17 CR、100 Test IDs、G0–G5 与发布协议。

事实冲突时依次以 GitHub 远程事实、本文件、Execution Status/Traceability/Gate Evidence、产品与架构规范、v2.2 未修正条款为准。

## 1. 当前发布判断

当前产品仍是 **Experimental Preview**。G1 PASS 只解锁 M2，不表示 Public Beta、master、Tag、GitHub Release、PyPI 或 Stable Ready。

已完成：

- M0 全部 Work ID；
- G0 PASS；
- M1 8/8 Work ID；
- G1 初评、QA-ART remediation 与 PASS 复评；
- `CTX-001`：Merge 尾部消息唯一性；
- `CTX-002`：摘要 timeout、exception、空响应与 malformed response 的无损回退。

## 2. 固定 Work ID 进度

| 状态 | 数量 | 比例 |
|---|---:|---:|
| Complete | 18 | 37.5% |
| In progress | 0 | 0.0% |
| Not started / dependency blocked | 30 | 62.5% |
| Total | 48 | 100% |

启动 `CTX-003` 后：Complete 18 / In progress 1 / Not started 29。

## 3. Gate 状态

| Gate | 状态 | Evidence / 说明 |
|---|---|---|
| Plan Ready | PASS | 48 Issues、88 FR、17 CR、100 Test IDs |
| G0 | PASS | PR #61 · `ee516c9b` |
| G1 | PASS | PR #77 FAIL → PR #78 remediation → PR #79 PASS |
| G2 | NOT_STARTED | M2 尚未完成 |
| G3 | NOT_STARTED | 依赖 M2、M3、M4 与 RC Evidence |
| G4 | NOT_STARTED | 依赖 Beta 反馈闭环 |
| G5 | NOT_STARTED | 依赖 Stable 阶段与 soak |

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

G1 PASS：PR #79；Run #193 / ID `30384094675`；Squash `b0b9d2e0337a9f40f2abcdb0f91ce8b2865ea765`。

## 6. M2 当前状态

| Work ID | Issue | Dependency | Delivery | 状态 |
|---|---:|---|---|---|
| `CTX-001` | #26 | G1 | PR #81 · `4026fea226c16647c45d710993c9b4c1683e094e` | Complete |
| `CTX-002` | #27 | CTX-001 | PR #83 · `bf4ab49e1b3c5bbe752931d19460ad2de4243a6f` | Complete |
| `CTX-003` | #28 | CTX-002 | pending | **Next serial task** |
| `CTX-004` | #29 | CTX-003 | pending | Queued |
| `SES-001` | #30 | G1 + PKG-001 | pending | Dependency satisfied; serially queued |
| `PRIV-001` | #31 | CTX-003 + SES-001 | pending | Blocked |

### CTX-002 acceptance

```text
TDD red: Run #207 / ID 30414160582
Code acceptance: Run #208 / ID 30414258095
Final PR Head: 5b16121b1366180e640f8ca37f858f0464030453
Final CI: Run #209 / ID 30414491094
Squash: bf4ab49e1b3c5bbe752931d19460ad2de4243a6f
Python 3.10/3.11/3.12: each 239 tests / 0 failures / 0 errors / 7 strict XFAIL
Wheel inventory: 41 files
sdist inventory: 77 files
```

`TC-CTX-004–006` 已转为普通 PASS；失败摘要返回原输入列表，不插入占位文本，不泄露模拟 Secret 或 prompt fragment。

## 7. 固定支持边界

- Hermes 候选固定为 **Hermes Agent v0.19.0 / Git tag `v2026.7.20`**；
- Python 3.10 remains package/core/artifact-only after `PKG-001`; the complete Hermes v0.19.0 integration combination does not support Python 3.10；
- Python 3.11–3.12 是完整 Hermes 候选组合；
- real Hermes E2E 属于 `COMPAT-001` / M4 / G3；
- byte-for-byte reproducibility、SBOM、provenance 属于 `REL-006`；
- Runtime 当前 9 Tools，目标 10；不得添加 placeholder `memory_store`；
- 当前 7 strict XFAIL owners：`CTX-003`、`SES-001`、`AUD-001`、`CON-001`×3、`MEM-002`。

## 8. M2 固定串行顺序

```text
CTX-003 → CTX-004 → SES-001 → PRIV-001 → G2
```

`SES-001` 的硬依赖已满足，但禁止并行启动。

## 9. 当前唯一合法下一步

完成 docs-only CTX-002 post-merge closure 后：

1. 读取 Issue #28 与评论；
2. 从最新 `develop` 创建 `fix/ctx-003-protected-message-integrity`；
3. 将 `XF-CTX-003` 转为普通失败回归；
4. 实现 stable message IDs、protected-message classification 与 Tool Call/Result pair validation；
5. 验证 hard constraints 和 latest requests 逐字保留且 ID 恰好一次；
6. 增加 `TC-CTX-007–009`、`TC-CTX-014` 与 property tests；
7. 不提前实施 CTX-004、Session、Privacy；
8. 创建 `docs/testing/evidence/CTX-003.md`；
9. Final Head Required CI 全绿后 Squash Merge；
10. 自动进入 `CTX-004`。

## 10. 后续路线

```text
CTX-003 → CTX-004 → SES-001 → PRIV-001 → G2
G2 PASS → M3 → M4/G3 → exact-master RC
v3.0.0-beta.1 → Beta feedback/G4 → Stable prep/soak/G5 → v3.0.0
```

严格边界：不提前合入 master、Tag、Release 或 PyPI；不声称 Public Beta Ready；不访问真实 HOME/DB/Memory/Secret；不弱化安全防线。
