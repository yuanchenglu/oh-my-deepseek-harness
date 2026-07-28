# Open-source Release Execution Status

- Status date: 2026-07-28
- Normative contract: [`OPEN_SOURCE_RELEASE_PLAN.md`](OPEN_SOURCE_RELEASE_PLAN.md) v2.3.4
- Complete task ledger: [`archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md`](archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md)
- Current incoming delivery: PR #68 (`INS-001`)
- INS-001 code acceptance Head: `48f547f9b3c3fae27fc5672c24f0ff5380c65583`
- INS-001 Required CI: Run #121 / ID `30333369939`
- Current decision on merge: **G0 PASS; M1 5/8 COMPLETE; G1 NOT EVALUATED**
- Current product maturity: **Experimental Preview**
- Session handoff: [`SESSION_HANDOFF_PROMPT.md`](SESSION_HANDOFF_PROMPT.md)

> 本文件中的 INS-001 完成状态在 PR #68 protected Squash Merge 到 `develop` 且 Issue #22 关闭时生效。本文件不替代主计划、v2.2 归档、PRD、Architecture、Test Plan 或 Traceability 中的规范契约。

## 1. Overall progress on merge

| Status | Work IDs | Ratio |
|---|---:|---:|
| Complete | 13 | 27.1% |
| In progress | 0 | 0.0% |
| Not started / dependency blocked | 35 | 72.9% |
| Total | 48 | 100% |

Work-ID progress does not represent release readiness. G0 **does not** claim product release readiness. Public Beta still requires G1–G3 and final artifact verification.

## 2. Gate status

| Gate | Status | Evidence / blocker |
|---|---|---|
| Plan Ready | PASS | 48 Work IDs、48 Issues、88 FR、17 CR、100 Test IDs |
| G0 | PASS | PR #61 · `ee516c9b` · [`GATE-G0.md`](../testing/evidence/GATE-G0.md) |
| G1 | NOT_EVALUATED | INS-002、INS-003、QA-ART-001 未完成；Hermes v0.19.0 完整支持仍限 Python 3.11–3.12 |
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

## 4. M1 status on merge

| Work ID | Issue | Delivery | Status |
|---|---:|---|---|
| `PKG-001` | #18 | PR #62 · `2098dffc` | Complete |
| `PKG-002` | #19 | PR #63 · `ae277d1d` | Complete |
| `RUN-001` | #20 | PR #64 · `31366ceb` | Complete |
| `RUN-002` | #21 | PR #65 · `f1c04697` | Complete |
| `INS-001` | #22 | PR #68 · [`INS-001.md`](../testing/evidence/INS-001.md) | **Complete on protected merge** |
| `INS-002` | #23 | — | **Open — eligible only after PR #68 merges and #22 closes** |
| `INS-003` | #24 | — | Blocked by INS-002 |
| `QA-ART-001` | #25 | — | Blocked by INS-003 |

M1 progress on merge: **5/8 Complete, 0/8 In progress, 1/8 Open eligible, 2/8 Blocked**.

## 5. INS-001 verified acceptance

Code Required CI Run #121 / ID `30333369939`, Head `48f547f9b3c3fae27fc5672c24f0ff5380c65583`：

```text
Python 3.10: success — package/core CI
Python 3.11: success
Python 3.12: success
206 tests / 0 failures / 0 errors / 9 pre-existing strict XFAIL per version
```

Verified:

- one canonical installed-distribution lifecycle; shell is only a CLI wrapper;
- CLI never invokes pip or manages the Python distribution;
- empty-HOME dry-run produces no persistent changes;
- clean git-archive wheel installs outside the repository and deploys packaged Plugin/Context adapters;
- product config/data/runtime/log paths initialize with private POSIX modes;
- one Supervisor-managed Server reaches health/ready/status;
- repeated same-version install preserves managed bytes/modes/mtimes and reuses one PID;
- no duplicate config, state, backup, migration report or startup Memory import;
- existing conflicting/symlink content is preserved and rejected;
- incomplete rollback retains ownership/deployment evidence and returns the P0 exit boundary;
- `XF-INSTALL-001` is closed by a stronger passing Installer→Supervisor contract;
- tests use temporary HOME/data/DB/port and fake secrets;
- 10 target Tool names / 9 current Runtime Tool names remain unchanged.

This acceptance does not establish Doctor, Upgrade, Uninstall, real Hermes compatibility, G1, Public Beta, master or publication readiness.

## 6. Next authorized work

1. Squash Merge PR #68 through protected `develop` only after final Required Checks pass.
2. Record the Squash Commit and final PR-head CI in Issue #22, then close #22.
3. Verify the new `develop` Head and synchronize post-merge records.
4. Only then is `INS-002` #23 legally unlocked; do not start it inside INS-001.
5. Do not merge to `master`, create Tag/Release or publish to PyPI.
