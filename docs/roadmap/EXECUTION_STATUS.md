# Open-source Release Execution Status

- Status date: 2026-07-28
- Normative contract: [`OPEN_SOURCE_RELEASE_PLAN.md`](OPEN_SOURCE_RELEASE_PLAN.md) v2.3.4
- Complete task ledger: [`archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md`](archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md)
- Current merged baseline: `develop@31366ceb1cb1ff375496bed2cdaf504ac11763ae`
- Current remote WIP: `feat/run-002-supervisor@5e0e9eaf11da28a0b181981b8c4ebd30b26d199e`
- Current decision: **G0 PASS; M1 IN PROGRESS; G1 NOT EVALUATED**
- Current product maturity: **Experimental Preview**
- Session handoff: [`SESSION_HANDOFF_PROMPT.md`](SESSION_HANDOFF_PROMPT.md)

> 本文件是当前执行状态账本，不替代主计划、v2.2 归档、PRD、Architecture、Test Plan 或 Traceability 中的规范契约。

## 1. Overall progress

| Status | Work IDs | Ratio |
|---|---:|---:|
| Complete | 11 | 22.9% |
| In progress | 1 | 2.1% |
| Not started / dependency blocked | 36 | 75.0% |
| Total | 48 | 100% |

Work-ID progress does not represent release readiness. Public Beta still requires G0–G3 and final artifact verification.

## 2. Gate status

| Gate | Status | Evidence / blocker |
|---|---|---|
| Plan Ready | PASS | 48 Work IDs、48 Issues、88 FR、17 CR、100 Test IDs |
| G0 | PASS | PR #61 · `ee516c9b` · [`GATE-G0.md`](../testing/evidence/GATE-G0.md) |
| G1 | NOT_EVALUATED | RUN-002、INS-001/002/003、QA-ART-001 未完成 |
| G2 | NOT_STARTED | 依赖 G1 |
| G3 | NOT_STARTED | 依赖 M2、M3、M4 和 RC Evidence |
| G4 | NOT_STARTED | 依赖 Beta 反馈闭环 |
| G5 | NOT_STARTED | 依赖 Stable 阶段 |

## 3. M0 status

| Work ID | Issue | Delivery | Status |
|---|---:|---|---|
| `REL-000` | #3 | PR #4 · `e18db7e` | Complete |
| `REL-001` | #5 | PR #6 · `a97dfe4` | Complete |
| `REL-002` | #7 | PR #8/#9 · `e7e1414e`/`61642f69` | Complete |
| `REL-004` | #10 | PR #11 · `7d52de9f` | Complete |
| `GOV-001` | #12 | PR #14 · `a0083ce1` | Complete |
| `REL-003` | #15 | PR #58 · `fd5c212f` | Complete |
| `REL-005` | #16 | PR #59 · `49ad479f` | Complete — GitHub-only Beta; PyPI disabled |
| `COMPAT-000` | #17 | PR #60 · `c7f6212a` | Complete — Hermes v0.19.0 fixed |
| G0 | — | PR #61 · `ee516c9b` | PASS |

## 4. M1 status

| Work ID | Issue | Delivery | Status |
|---|---:|---|---|
| `PKG-001` | #18 | PR #62 · `2098dffc` | Complete |
| `PKG-002` | #19 | PR #63 · `ae277d1d` | Complete |
| `RUN-001` | #20 | PR #64 · `31366ceb` | Complete |
| `RUN-002` | #21 | branch `feat/run-002-supervisor` · WIP `5e0e9eaf` | **In progress — remote preservation point** |
| `INS-001` | #22 | — | Blocked by RUN-002 |
| `INS-002` | #23 | — | Blocked by INS-001 |
| `INS-003` | #24 | — | Blocked by INS-002 |
| `QA-ART-001` | #25 | — | Blocked by INS-003 |

M1 progress: **3/8 Complete, 1/8 In progress, 4/8 Blocked**.

## 5. Latest verified baseline

RUN-001 final Required CI Run #88 / ID `30326830920`:

```text
Python 3.10: success
Python 3.11: success
Python 3.12: success
189 tests / 0 failures / 0 errors / 10 pre-existing strict XFAIL
```

Verified on the merged baseline:

- standard `src/` package layout and clean wheel imports;
- base/context/server/all dependency isolation;
- side-effect-free Server import;
- loopback-only environment contract;
- distinct `/health`, `/ready`, `/version` semantics;
- real child-process readiness;
- 10 target Tool names / 9 current Runtime Tool names.

## 6. RUN-002 WIP scope

Remote WIP `5e0e9eaf` contains:

- atomic runtime state and cross-process lock;
- private data root/runtime/log permissions;
- process ownership using PID + random instance ID;
- start/status/stop/restart Supervisor;
- port/probe/version validation;
- user-accessible combined stdout/stderr log;
- console script and CLI JSON output;
- Tool auto-start routed through the same Supervisor;
- concurrent start, restart, idempotent stop, foreign PID, port conflict and permission tests.

This WIP has **not yet been accepted as RUN-002 complete**. It requires code review, CI, Evidence and protected merge.

## 7. Next authorized work

1. Continue only `RUN-002` #21 on `feat/run-002-supervisor`.
2. Review WIP `5e0e9eaf` before changing it.
3. Create/refresh a draft PR to `develop` and run Required CI.
4. Fix failures without weakening process ownership or removing concurrency/failure tests.
5. Complete RUN-002 Evidence and Traceability.
6. Merge only after Python 3.10/3.11/3.12 Required Checks succeed.
7. Start `INS-001` #22 only after RUN-002 is merged and Issue #21 is closed.
8. Do not merge to `master`, create Tag/Release or publish to PyPI.
