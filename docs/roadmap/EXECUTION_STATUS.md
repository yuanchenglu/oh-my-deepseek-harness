# Open-source Release Execution Status

- Status date: 2026-07-29
- Normative contract: [`OPEN_SOURCE_RELEASE_PLAN.md`](OPEN_SOURCE_RELEASE_PLAN.md) v2.3.7
- Complete task ledger: [`archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md`](archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md)
- Remote fact baseline: `develop@5ebb3a0c9b44cd5f2a2be789f9224740d47894f8`
- G1 re-evaluation branch: `docs/gate-g1-pass-re-evaluation`
- G1 re-evaluation PR: #79
- G1 evidence: [`GATE-G1.md`](../testing/evidence/GATE-G1.md)
- Current decision: **G0 PASS; M1 8/8 COMPLETE; G1 PASS**
- Current product maturity: **Experimental Preview**
- Next serial Work ID after PR #79: **CTX-001 / Issue #26**
- Session handoff: [`SESSION_HANDOFF_PROMPT.md`](SESSION_HANDOFF_PROMPT.md)

> G1 PASS closes only artifact、Runtime、install lifecycle and isolation readiness. It does not establish Public Beta、master、Tag、Release、PyPI or Stable readiness.

## 1. Overall progress

| Status | Work IDs | Ratio |
|---|---:|---:|
| Complete | 16 | 33.3% |
| In progress | 0 | 0.0% |
| Not started / dependency blocked | 32 | 66.7% |
| Total | 48 | 100% |

PR #79 合并并启动 CTX-001 后，状态将变为 Complete 16 / In progress 1 / Not started 31。

## 2. Gate status

| Gate | Status | Evidence / blocker |
|---|---|---|
| Plan Ready | PASS | 48 Work IDs、48 Issues、88 FR、17 CR、100 Test IDs |
| G0 | PASS | PR #61 · `ee516c9b` · [`GATE-G0.md`](../testing/evidence/GATE-G0.md) |
| G1 | **PASS** | 初评 PR #77；remediation PR #78；复评 PR #79 · [`GATE-G1.md`](../testing/evidence/GATE-G1.md) |
| G2 | NOT_STARTED | M2 尚未完成 |
| G3 | NOT_STARTED | 依赖 M2、M3、M4 和 RC Evidence |
| G4 | NOT_STARTED | 依赖 Beta 反馈闭环 |
| G5 | NOT_STARTED | 依赖 Stable 阶段与 soak |

G1 checklist: **10 PASS / 0 FAIL / 0 BLOCKED**.

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
| `QA-ART-001` | #25 | PR #74 · `7adbb0cb`; remediation PR #78 · `5ebb3a0c` | Complete |

M1 progress: **8/8 Complete**.

## 5. QA-ART-001 remediation acceptance

```text
Issue #25: Closed / completed
Remediation PR #78: Merged
Code acceptance Head: 7dbe10bef7035a5ce948fd9202c995a303c084b3
Code acceptance CI: Run #183 / ID 30382373294
Final PR Head: 531aa0e3fd327dc9a096668432ebd1d0b2bff43b
Final Required CI: Run #184 / ID 30382668758
Squash Commit: 5ebb3a0c9b44cd5f2a2be789f9224740d47894f8

Python 3.10: 231 tests / 0 failures / 0 errors / 9 strict XFAIL
Python 3.11: 231 tests / 0 failures / 0 errors / 9 strict XFAIL
Python 3.12: 231 tests / 0 failures / 0 errors / 9 strict XFAIL
artifact JUnit per job: 1 / 0 failures / 0 errors / 0 skipped
wheel inventory: 39 files
sdist inventory: 75 files
twine check: wheel + sdist PASS in all jobs
```

## 6. G1 PASS basis

All original clauses pass:

1. one clean frozen snapshot builds wheel + sdist;
2. twine check passes for both artifacts;
3. package data/inventory is complete;
4. public packages import outside source;
5. no editable/source symlink/path dependency;
6. Console Server lifecycle works;
7. health/ready/version satisfy contract;
8. empty-HOME full lifecycle succeeds;
9. repeat install/port/interruption/uninstall preservation passes;
10. no real `~/.hermes` access.

Non-blocking later scope:

- byte reproducibility/SBOM/provenance → `REL-006`;
- real Hermes E2E → `COMPAT-001` / G3;
- 9 strict XFAIL → canonical M2/M3 owners;
- Python 3.10 remains package/core/artifact-only with expected full-Hermes rejection.

## 7. M2 serial queue

```text
CTX-001 → CTX-002 → CTX-003 → CTX-004 → SES-001 → PRIV-001 → G2
```

`SES-001` also has satisfied hard dependencies, but is deliberately queued to preserve the one-Work-ID-at-a-time rule.

## 8. Current authorized work

1. Complete PR #79 through final Required CI and expected-Head Squash Merge.
2. Re-read latest `develop`.
3. Fetch Issue #26 and comments.
4. Start only `CTX-001` from latest `develop`.
5. Convert only `TC-CTX-003` from strict XFAIL to an ordinary failing regression.
6. Fix Merge-path duplicate assembly without implementing later Context tasks.
7. Record `docs/testing/evidence/CTX-001.md` and merge through Required CI.
8. Automatically continue to `CTX-002`.
9. Do not merge to master, create Tag/Release or publish PyPI.
