# Open-source Release Execution Status

- Status date: 2026-07-28
- Normative contract: [`OPEN_SOURCE_RELEASE_PLAN.md`](OPEN_SOURCE_RELEASE_PLAN.md) v2.3.4
- Complete task ledger: [`archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md`](archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md)
- Current incoming delivery: PR #74 (`QA-ART-001`)
- QA-ART-001 code acceptance Head: `81195f844b681e85ccf2c0a15fc4935b2b396ed6`
- QA-ART-001 Required CI: Run #161 / ID `30342161995`
- Current decision on merge: **G0 PASS; M1 8/8 COMPLETE; G1 READY FOR SEPARATE EVALUATION**
- Current product maturity: **Experimental Preview**
- Session handoff: [`SESSION_HANDOFF_PROMPT.md`](SESSION_HANDOFF_PROMPT.md)

> 本文件中的 QA-ART-001 完成状态在 PR #74 protected Squash Merge 到 `develop` 且 Issue #25 关闭时生效。M1 完成不自动等于 G1 PASS；Gate 必须使用独立 Evidence 判定。

## 1. Overall progress on merge

| Status | Work IDs | Ratio |
|---|---:|---:|
| Complete | 16 | 33.3% |
| In progress | 0 | 0.0% |
| Not started / dependency blocked | 32 | 66.7% |
| Total | 48 | 100% |

Work-ID progress does not represent release readiness. G0 **does not** claim product release readiness. Public Beta still requires G1–G3 and final artifact verification.

## 2. Gate status

| Gate | Status | Evidence / blocker |
|---|---|---|
| Plan Ready | PASS | 48 Work IDs、48 Issues、88 FR、17 CR、100 Test IDs |
| G0 | PASS | PR #61 · `ee516c9b` · [`GATE-G0.md`](../testing/evidence/GATE-G0.md) |
| G1 | READY_FOR_EVALUATION on merge | M1 Work IDs complete；需独立核对 INS/Doctor/Lifecycle/Artifact Evidence 与 open P0 blockers |
| G2 | NOT_STARTED | 依赖 G1 PASS |
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
| `INS-001` | #22 | PR #68 · `2e5438a7` | Complete |
| `INS-002` | #23 | PR #70 · `d1d3269d` | Complete |
| `INS-003` | #24 | PR #72 · `9e5295ac` | Complete |
| `QA-ART-001` | #25 | PR #74 · [`QA-ART-001.md`](../testing/evidence/QA-ART-001.md) | **Complete on protected merge** |

M1 progress on merge: **8/8 Complete**. This only unlocks a separate G1 evaluation.

## 5. QA-ART-001 verified acceptance

Code Required CI Run #161 / ID `30342161995`, Head `81195f844b681e85ccf2c0a15fc4935b2b396ed6`：

```text
Python 3.10: success — 230 tests / 0 failures / 0 errors / 9 strict XFAIL
Python 3.11: success — 230 tests / 0 failures / 0 errors / 9 strict XFAIL
Python 3.12: success — 230 tests / 0 failures / 0 errors / 9 strict XFAIL
```

Verified in every Required job:

- wheel built only from clean `git archive HEAD`;
- non-editable fresh venv installs only the final wheel distribution with declared `all` dependencies;
- product module origins and `sys.path` exclude repository and archived source;
- wheel inventory has 39 files and no `plugins/`, `mcp/` or `tests/` tree;
- install dry-run, clean install, Server health/ready/version and `/memory/tag` smoke;
- Python 3.10 Doctor expected exit 5; Python 3.11/3.12 Doctor exit 0 with fake Hermes 0.19.0;
- same-version upgrade is idempotent and reuses the Server PID;
- ordinary uninstall preserves distribution/config/DB and prints the exact pip command;
- explicit pip uninstall occurs only in the temporary test venv;
- fake Secret does not appear in uploaded text evidence;
- each job uploads wheel, SHA256, inventory, JSON/log evidence, pytest JUnit and artifact JUnit.

Wheel hashes differ across independently built jobs; QA-ART-001 records each actual artifact but does not claim reproducible-build PASS. Final reproducibility remains owned by REL-006.

This acceptance does not establish G1, real Hermes compatibility, complete migration, Public Beta, master or publication readiness.

## 6. Next authorized work

1. Squash Merge PR #74 through protected `develop` only after final Required Checks pass.
2. Record the Squash Commit and final PR-head CI in Issue #25, then close #25.
3. Complete post-merge documentation closure.
4. Only then perform a separate G1 Evidence evaluation; do not start CTX-001 before G1 PASS.
5. Do not merge to `master`, create Tag/Release or publish to PyPI.
