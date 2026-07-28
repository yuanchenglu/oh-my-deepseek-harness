# Open-source Release Execution Status

- Status date: 2026-07-29
- Normative contract: [`OPEN_SOURCE_RELEASE_PLAN.md`](OPEN_SOURCE_RELEASE_PLAN.md) v2.3.9
- Complete task ledger: [`archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md`](archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md)
- Remote fact baseline: `develop@4026fea226c16647c45d710993c9b4c1683e094e`
- Current decision: **G0 PASS; M1 8/8 COMPLETE; G1 PASS; CTX-001 COMPLETE**
- Current product maturity: **Experimental Preview**
- Next serial Work ID: **CTX-002 / Issue #27**

## Progress

| Status | Work IDs | Ratio |
|---|---:|---:|
| Complete | 17 | 35.4% |
| In progress | 0 | 0.0% |
| Not started / dependency blocked | 31 | 64.6% |
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

## M1 completed

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

## M2 status

| Work ID | Issue | Delivery | Status |
|---|---:|---|---|
| `CTX-001` | #26 | PR #81 · `4026fea2` | Complete |
| `CTX-002` | #27 | pending | Next serial task |
| `CTX-003` | #28 | pending | Queued |
| `CTX-004` | #29 | pending | Queued |
| `SES-001` | #30 | pending | Dependency satisfied; queued |
| `PRIV-001` | #31 | pending | Blocked |

CTX-001 final evidence:

```text
TDD red: Run #197 / ID 30384981106
Code acceptance: Run #201 / ID 30385826868
Final Head: bae32c861fc403896e0c1630b91457d1622e2737
Final CI: Run #202 / ID 30386119025
Squash: 4026fea226c16647c45d710993c9b4c1683e094e
Python 3.10/3.11/3.12: each 234 tests / 0 failures / 0 errors / 8 strict XFAIL
```

Current queue:

```text
CTX-002 → CTX-003 → CTX-004 → SES-001 → PRIV-001 → G2
```

Support boundary: Python 3.10 remains package/core/artifact-only after `PKG-001`; the complete Hermes v0.19.0 integration combination does not support Python 3.10. Full Hermes candidate support remains Python 3.11–3.12.

G1 PASS and CTX-001 completion do not establish Public Beta、master、Tag、Release、PyPI、real Hermes E2E、reproducibility、SBOM、provenance or Stable readiness.
