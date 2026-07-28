# Open-source Release Execution Status

- Status date: 2026-07-28
- Normative contract: [`OPEN_SOURCE_RELEASE_PLAN.md`](OPEN_SOURCE_RELEASE_PLAN.md) v2.3.4
- Complete task ledger: [`archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md`](archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md)
- INS-002 implementation baseline: `develop@d1d3269de389258cc988c04b682de465d2da77c7`
- Latest completed Work ID: `INS-002`
- Delivery: PR #70 · Squash Commit `d1d3269de389258cc988c04b682de465d2da77c7`
- Code acceptance Head: `ef4363cd8972c0e9bba64ae91a84a6efa8806e2e`
- Final PR Head: `92d6cf2bd97763089809efa4130c187dd55e5456`
- Final Required CI: Run #139 / ID `30335805610`
- Current decision: **G0 PASS; M1 6/8 COMPLETE; G1 NOT EVALUATED**
- Current product maturity: **Experimental Preview**
- Session handoff: [`SESSION_HANDOFF_PROMPT.md`](SESSION_HANDOFF_PROMPT.md)

> 本文件是当前执行状态账本，不替代主计划、v2.2 归档、PRD、Architecture、Test Plan 或 Traceability 中的规范契约。

## 1. Overall progress

| Status | Work IDs | Ratio |
|---|---:|---:|
| Complete | 14 | 29.2% |
| In progress | 0 | 0.0% |
| Not started / dependency blocked | 34 | 70.8% |
| Total | 48 | 100% |

Work-ID progress does not represent release readiness. G0 **does not** claim product release readiness. Public Beta still requires G1–G3 and final artifact verification.

## 2. Gate status

| Gate | Status | Evidence / blocker |
|---|---|---|
| Plan Ready | PASS | 48 Work IDs、48 Issues、88 FR、17 CR、100 Test IDs |
| G0 | PASS | PR #61 · `ee516c9b` · [`GATE-G0.md`](../testing/evidence/GATE-G0.md) |
| G1 | NOT_EVALUATED | INS-003、QA-ART-001 未完成；Hermes v0.19.0 完整支持仍限 Python 3.11–3.12 |
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
| `RUN-002` | #21 | PR #65 · `f1c04697` | Complete |
| `INS-001` | #22 | PR #68 · `2e5438a7` | Complete |
| `INS-002` | #23 | PR #70 · `d1d3269d` · [`INS-002.md`](../testing/evidence/INS-002.md) | **Complete** |
| `INS-003` | #24 | — | **Open — dependency eligible; not started** |
| `QA-ART-001` | #25 | — | Blocked by INS-003 |

M1 progress: **6/8 Complete, 0/8 In progress, 1/8 Open eligible, 1/8 Blocked**.

## 5. INS-002 verified acceptance

Final PR-head Required CI：

```text
Run #139 / ID 30335805610 / head 92d6cf2bd97763089809efa4130c187dd55e5456
Python 3.10: success — package/core CI
Python 3.11: success
Python 3.12: success
215 tests / 0 failures / 0 errors / 9 strict XFAIL per version
```

Verified:

- one immutable structured DoctorReport renders both human and single JSON object output;
- fixed exits: generic 1, missing dependency 3, unmanaged port 4, unsupported matrix 5;
- Python, Hermes 0.19.0, package/full support matrix and runtime dependencies;
- packaged Plugin/Context adapter and managed config checks;
- Server state, PID ownership, configured port, health/ready/version probes;
- DB read-only, Provider presence and private permission checks;
- empty HOME Doctor produces no persistent changes;
- Doctor never starts/stops Server, invokes pip or performs repair/migration;
- output excludes Secret values and managed absolute paths;
- Python 3.10 + Hermes is explicitly rejected as full support;
- Linux zombie liveness is classified as exited without weakening PID-reuse/foreign ownership safety;
- tests use temporary HOME/data/DB/port and fake executables/secrets;
- 10 target Tool names / 9 current Runtime Tool names remain unchanged.

This acceptance does not establish Upgrade, Uninstall, real Hermes compatibility, G1, Public Beta, master or publication readiness.

## 6. Next authorized work

1. `INS-002` is closed; do not reopen its scope without a new defect Issue.
2. `INS-003` #24 is dependency eligible but remains not started.
3. A new feature branch may start only `INS-003`, from current `develop`, through protected PR and Required CI.
4. Do not start QA-ART-001 until INS-003 merges and Issue #24 closes.
5. Do not merge to `master`, create Tag/Release or publish to PyPI.
