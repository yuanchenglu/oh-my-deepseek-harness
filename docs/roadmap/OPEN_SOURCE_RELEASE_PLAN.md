# 开源发布执行计划（Open-source Release Execution Plan）

> 文档版本：2.3.14（PRIV-001 Complete / G2 Ready）
>
> 状态日期：2026-08-03
>
> 当前实现事实基线：`develop@d7fd12f`
>
> 计划状态：`M1_COMPLETE / G1_PASS / CTX_001_002_003_004_COMPLETE / SES_001_COMPLETE / PRIV_001_COMPLETE / G2_READY`
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

当前产品仍是 **Experimental Preview**。G1 PASS、CTX-004 Complete 与 SES-001 Complete 只推进 M2，不表示 Public Beta、master、Tag、GitHub Release、PyPI 或 Stable Ready。

已完成：

- M0 全部 Work ID；
- G0 PASS；
- M1 8/8 Work ID；
- G1 初评、QA-ART remediation 与 PASS 复评；
- `CTX-001`：Merge 尾部消息唯一性；
- `CTX-002`：摘要失败无损回退；
- `CTX-003`：稳定 ID、硬约束/最新请求逐字保留、Tool Pair 完整性与属性测试；
- `CTX-004`：压缩事务、实际输入 Token 减量、per-Session Compressor 状态、拒绝候选回滚与 Provider 失败 cooldown；
- `SES-001`：SessionPolicyStore 按 session_id 隔离硬约束状态、显式取消、Session end cleanup、两线程并发 barrier。
- `PRIV-001`：外发前 Secret Redaction、Summary 默认关闭、数据发送提示、日志隐私默认关闭。

## 2. 固定 Work ID 进度

| 状态 | 数量 | 比例 |
|---|---:|---:|
| Complete | 22 | 45.8% |
| In progress | 0 | 0.0% |
| Not started / dependency blocked | 26 | 54.2% |
| Total | 48 | 100% |

G2 评估启动后：Complete 22 / G2 in progress / Not started 26。

## 3. Gate 状态

| Gate | 状态 | Evidence / 说明 |
|---|---|---|
| Plan Ready | PASS | 48 Issues、88 FR、17 CR、100 Test IDs |
| G0 | PASS | PR #61 · `ee516c9b` |
| G1 | PASS | PR #77 FAIL → PR #78 remediation → PR #79 PASS |
| G2 | READY | SES-001 + PRIV-001 complete; evaluation pending |
| G3 | NOT_STARTED | 依赖 M2、M3、M4 与 RC Evidence |
| G4 | NOT_STARTED | 依赖真实 Beta 反馈闭环 |
| G5 | NOT_STARTED | 依赖 Stable 阶段与真实 soak |

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
| `CTX-003` | #28 | CTX-002 | PR #85 · `0eb68d7077a0b8b8898b61f20bb209175619ec42` | Complete |
| `CTX-004` | #29 | CTX-003 | PR #90 · `5ad013b3e121aa53eddce65a300e8ae737e14d21` · `CTX-004.md` | **Complete** |
| `SES-001` | #30 | G1 + PKG-001 | PR #94 · `SES-001.md` | **Complete** |
| `PRIV-001` | #31 | CTX-003 + SES-001 | PR #95 · `PRIV-001.md` | **Complete** |

### CTX-004 final acceptance

```text
Governance prerequisite: PR #89 / squash dec84237c305fd8fa3e4dcf1b52002da5a8e7f7d
Original P1 Red: Run #231 / ID 30462655418
Stable-ID accounting Red: Run #239 / ID 30465675428
Provider-cooldown Red: Run #242 / ID 30466881933
Final PR Head: e01c7fcc771460423628ebcf08b791cc927cb4c0
Final CI: Run #243 / ID 30467133399
Squash: 5ad013b3e121aa53eddce65a300e8ae737e14d21
Python 3.10/3.11/3.12: each PASS
Pytest: 251 passed / 6 strict XFAIL / 0 failures / 0 errors / 0 XPASS
Wheel inventory: 42 files
sdist inventory: 81 files
Review Threads: 0 unresolved
Codex exact-final-Head review: +1
```

## 7. G2 Gate evaluation

G2 is now ready for evaluation. All M2 Work IDs are complete.

Before declaring G2 PASS:

1. verify all M2 evidence files exist (CTX-001 through CTX-004, SES-001, PRIV-001);
2. run full test suite on Python 3.10/3.11/3.12;
3. confirm no unresolved review threads on any M2 PR;
4. confirm develop is clean and CI is green;
5. create `docs/testing/evidence/GATE-G2.md`;
6. update Plan/Status/Traceability/Handoff.

## 8. 固定支持边界

- Hermes 候选固定为 **Hermes Agent v0.19.0 / Git tag `v2026.7.20`**；
- Python 3.10 remains package/core/artifact-only after `PKG-001`; the complete Hermes v0.19.0 integration combination does not support Python 3.10；
- Python 3.11–3.12 是完整 Hermes 候选组合；
- real Hermes E2E 属于 `COMPAT-001` / M4 / G3；
- byte-for-byte reproducibility、SBOM、provenance 属于 `REL-006`；
- Runtime 当前 9 Tools，目标 10；不得添加 placeholder `memory_store`；
- 当前 5 strict XFAIL owners：`AUD-001`、`CON-001`×3、`MEM-002`；
- PyPI 按 `REL-005` 保持禁用。

## 9. 固定串行顺序

```text
G2 evaluation -> G2 PASS -> M3 -> M4/G3 -> exact-master RC
v3.0.0-beta.1 -> real Beta feedback/G4 -> Stable prep/SOAK/G5 -> v3.0.0
```

严格边界：不提前合入 master、Tag、Release 或 PyPI；不声称 Public Beta Ready；不访问真实 HOME/DB/Memory/Secret；不弱化 PID、symlink、traversal、rollback 或 destructive-operation 防线。
