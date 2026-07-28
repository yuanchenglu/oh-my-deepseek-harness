# Open-source Release Execution Status

- Status date: 2026-07-29
- Normative contract: [`OPEN_SOURCE_RELEASE_PLAN.md`](OPEN_SOURCE_RELEASE_PLAN.md) v2.3.5
- Complete task ledger: [`archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md`](archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md)
- QA-ART-001 implementation baseline: `develop@7adbb0cb00e781e31fee0ee5d360f52c4bdce5eb`
- M1 plan/handoff closure baseline: `develop@ec81b11236843bb3ca10d6e1e1af72fa91a780f0`
- Latest completed Work ID: `QA-ART-001`
- Delivery: PR #74 · Squash Commit `7adbb0cb00e781e31fee0ee5d360f52c4bdce5eb`
- Code acceptance Head: `81195f844b681e85ccf2c0a15fc4935b2b396ed6`
- Final PR Head: `2a0263b3fe5dec75f6dae89203ecda6b6275ec9f`
- Code acceptance CI: Run #161 / ID `30342161995`
- Final PR-head CI: Run #166 / ID `30343118259`
- Plan/handoff closure: PR #75 · Run #168 / ID `30378398782` · Squash `ec81b11236843bb3ca10d6e1e1af72fa91a780f0`
- Current decision: **G0 PASS; M1 8/8 COMPLETE; G1 READY FOR SEPARATE EVALUATION**
- Current product maturity: **Experimental Preview**
- Session handoff: [`SESSION_HANDOFF_PROMPT.md`](SESSION_HANDOFF_PROMPT.md)

> Work-ID completion is not release readiness. QA-ART-001 and M1 completion do not automatically establish G1 PASS, Public Beta readiness, master readiness or publication readiness.

## 1. Overall progress

| Status | Work IDs | Ratio |
|---|---:|---:|
| Complete | 16 | 33.3% |
| In progress | 0 | 0.0% |
| Not started / dependency blocked | 32 | 66.7% |
| Total | 48 | 100% |

## 2. Gate status

| Gate | Status | Evidence / blocker |
|---|---|---|
| Plan Ready | PASS | 48 Work IDs、48 Issues、88 FR、17 CR、100 Test IDs |
| G0 | PASS | PR #61 · `ee516c9b` · [`GATE-G0.md`](../testing/evidence/GATE-G0.md) |
| G1 | READY_FOR_SEPARATE_EVALUATION | M1 8/8 Complete；尚无独立 `GATE-G1.md` 判定 |
| G2 | NOT_STARTED | 依赖 G1 PASS |
| G3 | NOT_STARTED | 依赖 M2、M3、M4 和 RC Evidence |
| G4 | NOT_STARTED | 依赖 Beta 反馈闭环 |
| G5 | NOT_STARTED | 依赖 Stable 阶段与 soak |

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
| `COMPAT-000` | PR #60 · `c7f6212a` | Complete — Hermes v0.19.0 fixed |
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
| `QA-ART-001` | #25 | PR #74 · `7adbb0cb` · [`QA-ART-001.md`](../testing/evidence/QA-ART-001.md) | **Complete** |

M1 progress: **8/8 Complete**. The only legal next action is a separate G1 Gate evaluation.

## 5. QA-ART-001 final acceptance

```text
Squash Commit: 7adbb0cb00e781e31fee0ee5d360f52c4bdce5eb
Final PR Head: 2a0263b3fe5dec75f6dae89203ecda6b6275ec9f
Final Required CI: Run #166 / ID 30343118259

Python 3.10: success — 230 tests / 0 failures / 0 errors / 9 strict XFAIL
Python 3.11: success — 230 tests / 0 failures / 0 errors / 9 strict XFAIL
Python 3.12: success — 230 tests / 0 failures / 0 errors / 9 strict XFAIL
artifact JUnit per job: 1 test / 0 failures / 0 errors / 0 skipped
```

Verified in every Required job:

- clean `git archive HEAD` wheel build;
- fresh non-editable temporary venv;
- no repository/archived-source import origin or `sys.path` contamination;
- 39-file wheel inventory and per-artifact SHA256;
- install dry-run, clean install and ready Server;
- Python 3.10 expected Doctor rejection; Python 3.11/3.12 Doctor success;
- `/health`, `/ready`, `/version` and `POST /memory/tag` smoke;
- same-version idempotent upgrade with PID reuse;
- ordinary uninstall preserving distribution/config/DB;
- exact manual pip uninstall command and explicit temporary-venv pip uninstall;
- fake Secret absent from uploaded text evidence;
- wheel, inventory, JSON/log, pytest JUnit and artifact JUnit uploads.

The three independently built wheels have different SHA256 values. QA-ART-001 records and validates each artifact but does not claim reproducible-build PASS. Final reproducibility/provenance remains `REL-006` scope unless the original G1 criteria say otherwise.

## 6. Open risks and boundaries

- G1 has not been evaluated and has no independent Evidence file yet.
- Real Hermes discovery/Hook/Context/Tool E2E remains outstanding.
- Runtime remains 9 Tools; target is 10 after the canonical contract/memory work.
- Nine strict XFAIL remain and must retain canonical later owners.
- Context, Session, Privacy, Audit, Migration, Security, SBOM and RC work remain blocked by the roadmap.
- PyPI remains disabled; no master merge, Tag or GitHub Release has occurred.

## 7. Next authorized work

1. From the latest remote `develop`, create `docs/gate-g1-evaluation` and a Draft PR.
2. Build `docs/testing/evidence/GATE-G1.md` from the original Gate criteria before writing a conclusion.
3. The G1 conclusion must be exactly PASS, FAIL or BLOCKED, with criterion-level evidence, residual risks and exclusions.
4. Synchronize the plan, execution status, traceability and guarded handoff in the same Gate PR.
5. Do not start CTX-001, SES-001 or another M2 Work ID before G1 PASS.
6. Do not merge to `master`, create Tag/Release or publish to PyPI.
