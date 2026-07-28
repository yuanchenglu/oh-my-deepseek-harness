# Open-source Release Execution Status

- Status date: 2026-07-28
- Normative contract: [`OPEN_SOURCE_RELEASE_PLAN.md`](OPEN_SOURCE_RELEASE_PLAN.md) v2.3.4
- Complete task ledger: [`archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md`](archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md)
- Incoming develop delivery: PR #65 (`RUN-002`); Squash Commit is recorded in Issue #21 after merge
- Code acceptance head: `65d5d0039a3ffa0899d93ee7e5d99eef35f03abd`
- Code acceptance CI: Run #104 / ID `30330399378`
- Current decision on merge: **G0 PASS; M1 4/8 COMPLETE; G1 NOT EVALUATED**
- Current product maturity: **Experimental Preview**
- Session handoff: [`SESSION_HANDOFF_PROMPT.md`](SESSION_HANDOFF_PROMPT.md)

> 本文件内容在 PR #65 Squash Merge 到 `develop` 时生效。它是当前执行状态账本，不替代主计划、v2.2 归档、PRD、Architecture、Test Plan 或 Traceability 中的规范契约。

## 1. Overall progress

| Status | Work IDs | Ratio |
|---|---:|---:|
| Complete | 12 | 25.0% |
| In progress | 0 | 0.0% |
| Not started / dependency blocked | 36 | 75.0% |
| Total | 48 | 100% |

Work-ID progress does not represent release readiness. Public Beta still requires G0–G3 and final artifact verification.

## 2. Gate status

| Gate | Status | Evidence / blocker |
|---|---|---|
| Plan Ready | PASS | 48 Work IDs、48 Issues、88 FR、17 CR、100 Test IDs |
| G0 | PASS | PR #61 · `ee516c9b` · [`GATE-G0.md`](../testing/evidence/GATE-G0.md) |
| G1 | NOT_EVALUATED | INS-001/002/003、QA-ART-001 未完成；Hermes v0.19.0 完整支持仍限 Python 3.11–3.12 |
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
| `RUN-002` | #21 | PR #65 · [`RUN-002.md`](../testing/evidence/RUN-002.md) | **Complete on protected squash merge** |
| `INS-001` | #22 | — | **Open — eligible only after PR #65 merges and #21 closes** |
| `INS-002` | #23 | — | Blocked by INS-001 |
| `INS-003` | #24 | — | Blocked by INS-002 |
| `QA-ART-001` | #25 | — | Blocked by INS-003 |

M1 progress on merge: **4/8 Complete, 0/8 In progress, 1/8 Open eligible, 3/8 Blocked**.

## 5. Latest verified acceptance

RUN-002 code Required CI Run #104 / ID `30330399378`, Head `65d5d0039a3ffa0899d93ee7e5d99eef35f03abd`:

```text
Python 3.10: success — package/core CI
Python 3.11: success
Python 3.12: success
200 tests / 0 failures / 0 errors / 10 pre-existing strict XFAIL per version
```

Verified:

- one Supervisor shared by CLI and Tool auto-start;
- concurrent independent CLI starts resolve to one PID;
- PID reuse protection with OS process-start identity, exact child argv and random instance ID;
- foreign PID no-signal and SIGKILL ownership revalidation;
- atomic state and fail-closed stale/corrupt/failed-start handling;
- port, `/health`, `/ready`, `/version` validation;
- idempotent stop and restart with new instance identity;
- private POSIX directory/file permissions and user-accessible stderr log;
- clean-archive external wheel installation, imports and console-script contract;
- temporary HOME/DB/data-root/port test isolation;
- 10 target Tool names / 9 current Runtime Tool names; no placeholder `memory_store`.

This acceptance does not establish G1, Hermes real-environment compatibility, Public Beta readiness, master readiness or publication readiness.

## 6. Next authorized work

1. Squash Merge PR #65 through the protected `develop` flow only after its final Required Checks pass.
2. Record the Squash Commit and final PR-head CI in Issue #21, then close #21.
3. Verify the new `develop` Head and post-merge CI.
4. Only then is `INS-001` #22 legally unlocked; do not start it inside RUN-002.
5. Do not merge to `master`, create Tag/Release or publish to PyPI.
