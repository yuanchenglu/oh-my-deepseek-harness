# Open-source Release Execution Status

- Status date: 2026-07-29
- Normative contract: [`OPEN_SOURCE_RELEASE_PLAN.md`](OPEN_SOURCE_RELEASE_PLAN.md) v2.3.6
- Complete task ledger: [`archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md`](archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md)
- Remote fact baseline: `develop@8260c671786aa2ea994d61e6bde09ad57992ef36`
- G1 evaluation branch: `docs/gate-g1-evaluation`
- G1 evaluation PR: #77
- G1 evidence: [`GATE-G1.md`](../testing/evidence/GATE-G1.md)
- Current decision: **G0 PASS; M1 8/8 COMPLETE; G1 FAIL**
- Current product maturity: **Experimental Preview**
- Session handoff: [`SESSION_HANDOFF_PROMPT.md`](SESSION_HANDOFF_PROMPT.md)

> Work-ID completion is not release readiness. M1 remains 8/8 Complete, but the independent G1 evaluation found two missing artifact clauses. M2 remains blocked until remediation and a separate G1 re-evaluation produce PASS.

## 1. Overall progress

| Status | Work IDs | Ratio |
|---|---:|---:|
| Complete | 16 | 33.3% |
| In progress | 0 | 0.0% |
| Not started / dependency blocked | 32 | 66.7% |
| Total | 48 | 100% |

QA-ART-001 will be reopened for remediation after PR #77 merges. Reopening a canonical Issue to close Gate evidence does not change the fixed 48 Work ID denominator or erase its previously merged implementation.

## 2. Gate status

| Gate | Status | Evidence / blocker |
|---|---|---|
| Plan Ready | PASS | 48 Work IDs、48 Issues、88 FR、17 CR、100 Test IDs |
| G0 | PASS | PR #61 · `ee516c9b` · [`GATE-G0.md`](../testing/evidence/GATE-G0.md) |
| G1 | **FAIL** | PR #77 · [`GATE-G1.md`](../testing/evidence/GATE-G1.md)；sdist 未构建，`twine check` 未执行 |
| G2 | NOT_STARTED | 依赖 G1 PASS |
| G3 | NOT_STARTED | 依赖 M2、M3、M4 和 RC Evidence |
| G4 | NOT_STARTED | 依赖 Beta 反馈闭环 |
| G5 | NOT_STARTED | 依赖 Stable 阶段与 soak |

G1 checklist: **8 PASS / 2 FAIL / 0 BLOCKED**.

## 3. M0 / G0 status

| Work ID / Gate | Delivery | Status |
|---|---|---|
| `REL-000` | PR #4 · `e18db7e` | Complete |
| `REL-001` | PR #6 · `a97dfe4` | Complete |
| `REL-002` | PR #8/#9 · `e7e1414e`/`61642f69` | Complete |
| `REL-004` | PR #11 · `7d52de9f` | Complete |
| `GOV-001` | PR #14 · `a0083ce1` | Complete |
| `REL-003` | PR #58 · `fd5c212f` | Complete |
| `REL-005` | PR #59 · `49ad479f` | Complete — GitHub-only Beta; PyPI disabled |
| `COMPAT-000` | PR #60 · `c7f6212a` | Complete |
| G0 | PR #61 · `ee516c9b` | PASS |

## 4. M1 status

| Work ID | Issue | Delivery | Status |
|---|---:|---|---|
| `PKG-001` | #18 | PR #62 · `2098dffc` | Complete |
| `PKG-002` | #19 | PR #63 · `ae277d1d` | Complete |
| `RUN-001` | #20 | PR #64 · `31366ceb` | Complete |
| `RUN-002` | #21 | PR #65 · `f1c04697` | Complete |
| `INS-001` | #22 | PR #68 · `2e5438a7` | Complete |
| `INS-002` | #23 | PR #70 · `d1d3269d` | Complete |
| `INS-003` | #24 | PR #72 · `9e5295ac` | Complete |
| `QA-ART-001` | #25 | PR #74 · `7adbb0cb` | Complete implementation; remediation required by G1 FAIL |

M1 implementation progress: **8/8 Complete**.

## 5. QA-ART-001 existing acceptance

```text
Squash Commit: 7adbb0cb00e781e31fee0ee5d360f52c4bdce5eb
Final PR Head: 2a0263b3fe5dec75f6dae89203ecda6b6275ec9f
Final Required CI: Run #166 / ID 30343118259

Python 3.10: 230 tests / 0 failures / 0 errors / 9 strict XFAIL
Python 3.11: 230 tests / 0 failures / 0 errors / 9 strict XFAIL
Python 3.12: 230 tests / 0 failures / 0 errors / 9 strict XFAIL
artifact JUnit per job: 1 / 0 failures / 0 errors
```

Verified:

- build input from clean `git archive HEAD`;
- fresh non-editable venv and outside-source imports;
- 39-file wheel inventory and SHA256;
- install dry-run, clean install and ready Server;
- Doctor support/rejection matrix;
- `/health`, `/ready`, `/version`, minimal API smoke;
- same-version idempotent upgrade;
- ordinary uninstall preserving distribution/config/DB;
- explicit pip uninstall only inside the disposable test venv;
- temporary HOME/data/DB/port and fake Secret.

## 6. G1 failure detail

Original G1 artifact clauses not met:

1. **wheel and sdist from clean source** — wheel exists; sdist does not;
2. **`python -m twine check dist/*`** — no Required evidence exists.

The other eight original clauses PASS: wheel contents, external imports, no source symlink/path dependency, console lifecycle, runtime probes, empty-HOME full lifecycle, repeated install/port/interruption/uninstall preservation, and no real `~/.hermes` access.

## 7. Non-blocking findings

- Three independently built wheel hashes differ; byte-for-byte reproducibility remains `REL-006`, not G1.
- Real Hermes discovery/Hook/Context/Tool E2E remains `COMPAT-001` in M4/G3; it cannot be a G1 dependency without creating a cycle.
- Nine strict XFAIL all have canonical later owners; none is orphaned.
- Python 3.10 remains package/core/artifact-only with expected full-Hermes rejection; full candidate matrix is Python 3.11–3.12.

## 8. Current authorized work

1. Merge the independent G1 FAIL evaluation PR #77 after Required CI.
2. Reopen Issue #25 and comment the exact two failed clauses.
3. Create `test/qa-art-001-sdist-twine-remediation` from the resulting latest `develop`.
4. Add wheel+sdist build, SHA256/inventory, `twine check`, JUnit/log uploads and Required matrix evidence.
5. Merge remediation through PR + Required CI.
6. Re-evaluate G1 independently.
7. Do not start CTX-001, SES-001 or any M2 work before G1 PASS.
8. Do not merge to `master`, create Tag/Release or publish to PyPI.
