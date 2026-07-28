# Open-source Release Execution Status

- Status date: 2026-07-28
- Normative contract: [`OPEN_SOURCE_RELEASE_PLAN.md`](OPEN_SOURCE_RELEASE_PLAN.md) v2.3.3
- Complete task ledger: [`archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md`](archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md)
- Gate evidence: [`GATE-G0.md`](../testing/evidence/GATE-G0.md)
- Current decision: **G0 PASS upon merge of the G0 evidence PR**
- Current product maturity: **Experimental Preview**

> This file is the current status ledger. It does not replace the requirements, Work IDs, dependencies, file ownership or Gate definitions in the normative plan.

## M0 status

| Work ID | Issue | Delivery | Status |
|---|---|---|---|
| `REL-000` | #3 | PR #4 · `e18db7e` | Complete |
| `REL-001` | #5 | PR #6 · `a97dfe4` | Complete |
| `REL-002` | #7 | PR #8/#9 · `e7e1414e`/`61642f69` | Complete |
| `REL-004` | #10 | PR #11 · `7d52de9f` | Complete |
| `GOV-001` | #12 | PR #14 · `a0083ce1` | Complete |
| `REL-003` | #15 | PR #58 · `fd5c212f` | Complete |
| `REL-005` | #16 | PR #59 · `49ad479f` | Complete — GitHub-only Beta channel selected; PyPI disabled pending authenticated prerequisites |
| `COMPAT-000` | #17 | PR #60 · `c7f6212a` | Complete — Hermes v0.19.0 candidate and static contracts fixed; real E2E remains COMPAT-001 |

## G0 decision scope

G0 verifies that implementation can start without unresolved product-contract or governance ambiguity:

- versions, CLI, Tool denominator, data paths, security defaults and release flow are fixed;
- `develop` is the integration/default branch and protected PR/CI workflow is active;
- Security Policy, Issue Forms, PR template and Release Checklist exist;
- 48 Work IDs have 48 canonical Issues;
- 88 Requirements, 17 Code Review blockers and 100 Test IDs have primary ownership;
- PyPI uncertainty is resolved by a safe GitHub-only Beta decision;
- one real Hermes candidate and an executable compatibility plan are fixed;
- the current Context Engine statically exposes the required v0.19.0 ABC surface;
- real installation and lifecycle compatibility remains explicitly owned by `COMPAT-001`.

G0 does **not** assert that packaging, installation, Context integrity, Session isolation, 10-Tool implementation, migration, security hardening, real Hermes E2E or release artifacts are complete.

## Next authorized work

After the G0 evidence PR merges:

1. start `PKG-001` #18 on a dedicated branch from current `develop`;
2. preserve `COMPAT-000` findings:
   - full Hermes target = v0.19.0 / `v2026.7.20`;
   - full product Python = 3.11–3.12;
   - Python 3.10 = package/core CI only;
   - current Context Engine satisfies the static required ABC surface;
   - real discovery, selection and lifecycle E2E remain `COMPAT-001`;
3. do not start `PKG-002` until `PKG-001` passes and merges;
4. do not claim G1, Public Beta or Stable without their independent evidence.
