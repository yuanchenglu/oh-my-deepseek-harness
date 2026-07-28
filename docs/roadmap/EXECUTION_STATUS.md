# Open-source Release Execution Status

- Status date: 2026-07-28
- Normative contract: [`OPEN_SOURCE_RELEASE_PLAN.md`](OPEN_SOURCE_RELEASE_PLAN.md) v2.3.4
- Complete task ledger: [`archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md`](archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md)
- INS-003 implementation baseline: `develop@9e5295ac7ec51e87d1051857d676cc13f478d063`
- Latest completed Work ID: `INS-003`
- Delivery: PR #72 · Squash Commit `9e5295ac7ec51e87d1051857d676cc13f478d063`
- Code acceptance Head: `e2b82c727a3dedaa1c8cc71de38a54dec3c079b6`
- Final PR Head: `28576a408a2ac6e2954178b9cc8dc09c5035ea10`
- Final Required CI: Run #154 / ID `30340534593`
- Current decision: **G0 PASS; M1 7/8 COMPLETE; G1 NOT EVALUATED**
- Current product maturity: **Experimental Preview**
- Session handoff: [`SESSION_HANDOFF_PROMPT.md`](SESSION_HANDOFF_PROMPT.md)

> 本文件是当前执行状态账本，不替代主计划、v2.2 归档、PRD、Architecture、Test Plan 或 Traceability 中的规范契约。

## 1. Overall progress

| Status | Work IDs | Ratio |
|---|---:|---:|
| Complete | 15 | 31.3% |
| In progress | 0 | 0.0% |
| Not started / dependency blocked | 33 | 68.8% |
| Total | 48 | 100% |

Work-ID progress does not represent release readiness. G0 **does not** claim product release readiness. Public Beta still requires G1–G3 and final artifact verification.

## 2. Gate status

| Gate | Status | Evidence / blocker |
|---|---|---|
| Plan Ready | PASS | 48 Work IDs、48 Issues、88 FR、17 CR、100 Test IDs |
| G0 | PASS | PR #61 · `ee516c9b` · [`GATE-G0.md`](../testing/evidence/GATE-G0.md) |
| G1 | NOT_EVALUATED | QA-ART-001 未完成；Hermes v0.19.0 完整支持仍限 Python 3.11–3.12 |
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
| `INS-002` | #23 | PR #70 · `d1d3269d` | Complete |
| `INS-003` | #24 | PR #72 · `9e5295ac` · [`INS-003.md`](../testing/evidence/INS-003.md) | **Complete** |
| `QA-ART-001` | #25 | — | **Open — dependency eligible; not started** |

M1 progress: **7/8 Complete, 0/8 In progress, 1/8 Open eligible**.

## 5. INS-003 verified acceptance

Final PR-head Required CI：

```text
Run #154 / ID 30340534593 / head 28576a408a2ac6e2954178b9cc8dc09c5035ea10
Python 3.10: success — package/core CI
Python 3.11: success
Python 3.12: success
228 tests / 0 failures / 0 errors / 9 strict XFAIL per version
```

Verified:

- canonical upgrade, recovery, ordinary uninstall and confirmed purge lifecycle;
- backup-first version-changing upgrade and idempotent same-version reuse;
- rollback and interrupted-transaction recovery of deployment/data/process state;
- ordinary uninstall preserves distribution and user data;
- CLI prints but never executes the exact pip uninstall command;
- confirmation is checked before destructive mutation;
- canonical-root allowlist and symlink/traversal/unknown-path fail-closed boundaries;
- external DB preservation and external DB symlink rejection;
- temporary HOME/data/DB/port and fake secrets only;
- 10 target Tool names / 9 current Runtime Tool names unchanged.

This acceptance does not establish QA-ART-001, full Beta migration, real Hermes compatibility, G1, Public Beta, master or publication readiness.

## 6. Next authorized work

1. `INS-003` is closed; do not reopen its scope without a new defect Issue.
2. `QA-ART-001` #25 is dependency eligible but remains not started until this post-merge closure is merged.
3. The next feature branch may implement only `QA-ART-001`, from latest `develop`, through protected PR and Required CI.
4. QA-ART-001 completion does not automatically pass G1; create a separate G1 Evidence decision afterward.
5. Do not merge to `master`, create Tag/Release or publish to PyPI.
