# Open-source Release Execution Status

- Status date: 2026-07-29
- Normative contract: [`OPEN_SOURCE_RELEASE_PLAN.md`](OPEN_SOURCE_RELEASE_PLAN.md) v2.3.8
- Complete task ledger: [`archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md`](archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md)
- Remote fact baseline: `develop@b0b9d2e0337a9f40f2abcdb0f91ce8b2865ea765`
- Current decision: **G0 PASS; M1 8/8 COMPLETE; G1 PASS**
- G1 PASS PR: #79（Merged）
- G1 Final Head: `e6e39b54040c5deba12d474daf596f7da4272a7c`
- G1 Final CI: Run #193 / ID `30384094675`
- G1 Squash: `b0b9d2e0337a9f40f2abcdb0f91ce8b2865ea765`
- Current product maturity: **Experimental Preview**
- Next serial Work ID: **CTX-001 / Issue #26**

## Progress

| Status | Work IDs | Ratio |
|---|---:|---:|
| Complete | 16 | 33.3% |
| In progress | 0 | 0.0% |
| Not started / dependency blocked | 32 | 66.7% |
| Total | 48 | 100% |

## Gate status

| Gate | Status | Evidence |
|---|---|---|
| Plan Ready | PASS | 48 Work IDs、48 Issues、88 FR、17 CR、100 Test IDs |
| G0 | PASS | PR #61 · `ee516c9b` |
| G1 | PASS | PR #77 FAIL → PR #78 remediation → PR #79 PASS |
| G2 | NOT_STARTED | M2 incomplete |
| G3 | NOT_STARTED | M2/M3/M4 and RC pending |
| G4 | NOT_STARTED | Beta feedback pending |
| G5 | NOT_STARTED | Stable soak pending |

G1 checklist: **10 PASS / 0 FAIL / 0 BLOCKED**.

## Completed M1

| Work ID | Issue | Delivery | Status |
|---|---:|---|---|
| `PKG-001` | #18 | PR #62 · `2098dffc` | Complete |
| `PKG-002` | #19 | PR #63 · `ae277d1d` | Complete |
| `RUN-001` | #20 | PR #64 · `31366ceb` | Complete |
| `RUN-002` | #21 | PR #65 · `f1c04697` | Complete |
| `INS-001` | #22 | PR #68 · `2e5438a7` | Complete |
| `INS-002` | #23 | PR #70 · `d1d3269d` | Complete |
| `INS-003` | #24 | PR #72 · `9e5295ac` | Complete |
| `QA-ART-001` | #25 | PR #74 · `7adbb0cb`; PR #78 · `5ebb3a0c` | Complete |

QA remediation final evidence: Run #184 / ID `30382668758`; Python 3.10/3.11/3.12 each 231 tests, 0 failures, 0 errors, 9 strict XFAIL; wheel 39 files; sdist 75 files; twine PASS.

## Current queue

```text
CTX-001 → CTX-002 → CTX-003 → CTX-004 → SES-001 → PRIV-001 → G2
```

G1 PASS does not establish Public Beta, master, Tag, Release, PyPI, real Hermes E2E, reproducibility, SBOM, provenance or Stable readiness.
