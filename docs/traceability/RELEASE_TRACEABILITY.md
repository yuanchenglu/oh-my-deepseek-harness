# Open-source Release Traceability

- Normative plan: [`OPEN_SOURCE_RELEASE_PLAN.md`](../roadmap/OPEN_SOURCE_RELEASE_PLAN.md) v2.3.6
- Complete task ledger: [`OPEN_SOURCE_RELEASE_PLAN_2.2.md`](../roadmap/archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md)
- Test ownership source: [`TEST_PLAN.md`](../testing/TEST_PLAN.md)
- Last synchronized: 2026-07-29
- Fixed scope: **48 Work IDs · 48 unique GitHub Issues · 88 FR IDs · 17 CR IDs · 100 Test IDs**
- Current Gate: **G1 FAIL**
- Gate evidence: [`GATE-G1.md`](../testing/evidence/GATE-G1.md)
- Gate PR: #77

> 一个 Work ID 只有一个 canonical Issue。G1 FAIL 不创建第 49 个 Work ID；缺口回收到原 canonical owner `QA-ART-001` #25。M2 在 G1 PASS 前保持阻塞。

## 1. Work ID → Issue → Delivery

| Milestone | Work ID | Hard dependency | Primary contract / verification | Issue | Delivery / Evidence | Status |
|---|---|---|---|---:|---|---|
| M0 | `REL-000` | None | Release/spec contract；88 FR + 100 Test IDs | #3 | PR #4 · `e18db7e` · `REL-000.md` | Complete |
| M0 | `REL-001` | REL-000 | Version identity；`CR-P2-002` | #5 | PR #6 · `a97dfe4` · `REL-001.md` | Complete |
| M0 | `REL-002` | REL-001 | Branch governance、Rulesets、active plan | #7 | PR #8/#9 · `e7e1414e`/`61642f69` | Complete |
| M0 | `REL-004` | REL-002 | current 9 / target 10 Tool denominator | #10 | PR #11 · `7d52de9f` | Complete |
| M0 | `GOV-001` | REL-004 | Security、Issue/PR forms、release governance | #12 | PR #14 · `a0083ce1` | Complete |
| M0 | `REL-003` | GOV-001 | 48 canonical Issues、完整 Traceability | #15 | PR #58 · `fd5c212f` | Complete |
| M0 | `REL-005` | REL-000 | PyPI ownership / GitHub-only decision | #16 | PR #59 · `49ad479f` | Complete — PyPI disabled |
| M0 | `COMPAT-000` | REL-000 | Hermes v0.19.0 target / static probes | #17 | PR #60 · `c7f6212a` | Complete |
| M1 | `PKG-001` | G0 + COMPAT-000 | canonical `src/` package、wheel inventory/import | #18 | PR #62 · `2098dffc` · `PKG-001.md` | Complete |
| M1 | `PKG-002` | PKG-001 | dependency extras、clean install matrix | #19 | PR #63 · `ae277d1d` · `PKG-002.md` | Complete |
| M1 | `RUN-001` | PKG-002 | App Factory、`TC-SERVER-001–003` | #20 | PR #64 · `31366ceb` · `RUN-001.md` | Complete |
| M1 | `RUN-002` | RUN-001 | Supervisor、PID/log、`TC-SERVER-004` | #21 | PR #65 · `f1c04697` · `RUN-002.md` | Complete |
| M1 | `INS-001` | RUN-002 | install dry-run/transaction/idempotence | #22 | PR #68 · `2e5438a7` · `INS-001.md` | Complete |
| M1 | `INS-002` | INS-001 | read-only Doctor、support matrix | #23 | PR #70 · `d1d3269d` · `INS-002.md` | Complete |
| M1 | `INS-003` | INS-002 | upgrade/recover/uninstall/purge safety | #24 | PR #72 · `9e5295ac` · `INS-003.md` | Complete |
| M1 | `QA-ART-001` | INS-003 | final artifact source isolation；G1 artifact owner | #25 | PR #74 · `7adbb0cb` · `QA-ART-001.md` | Complete implementation；**reopen for sdist/twine remediation** |
| M2 | `CTX-001` | G1 | `CR-P0-002`；`TC-CTX-003` | #26 | `CTX-001.md` when executed | Blocked by G1 |
| M2 | `CTX-002` | CTX-001 | `CR-P0-003`；`TC-CTX-004–006` | #27 | `CTX-002.md` when executed | Blocked |
| M2 | `CTX-003` | CTX-002 | `CR-P0-004`；`TC-CTX-007–009/014` | #28 | `CTX-003.md` when executed | Blocked |
| M2 | `CTX-004` | CTX-003 | compression/rollback invariants | #29 | `CTX-004.md` when executed | Blocked |
| M2 | `SES-001` | G1 + PKG-001 | `CR-P0-005`；`TC-POLICY-001–005` | #30 | `SES-001.md` when executed | Blocked by G1 |
| M2 | `PRIV-001` | CTX-003 + SES-001 | redaction/outbound/log privacy | #31 | `PRIV-001.md` when executed | Blocked |
| M3 | `CON-001` | G2 + PKG-001 | 10 Tool generated contract；`TC-CONTRACT-001–010` | #32 | `CON-001.md` when executed | Blocked |
| M3 | `MEM-001` | CON-001 | Memory store/query/dedup | #33 | `MEM-001.md` when executed | Blocked |
| M3 | `MEM-002` | MEM-001 | Memory import/delete/idempotence | #34 | `MEM-002.md` when executed | Blocked |
| M3 | `PLAN-001` | MEM-002 | DAG/cascade invariants | #35 | `PLAN-001.md` when executed | Blocked |
| M3 | `PLAN-002` | PLAN-001 | state machine/atomic mutations | #36 | `PLAN-002.md` when executed | Blocked |
| M3 | `PLAN-003` | PLAN-002 | query/archive/delete lifecycle | #37 | `PLAN-003.md` when executed | Blocked |
| M3 | `CP-001` | PLAN-003 | Checkpoint ownership/numbering/review | #38 | `CP-001.md` when executed | Blocked |
| M3 | `AUD-001` | SES-001 | JSONL audit source of truth | #39 | `AUD-001.md` when executed | Blocked |
| M3 | `OPS-001` | AUD-001 | manual audit CLI / no scheduler side effects | #40 | `OPS-001.md` when executed | Blocked |
| M3 | `INTENT-001` | CON-001 | intent low-confidence/negation/override | #41 | `INTENT-001.md` when executed | Blocked |
| M4 | `DOC-001` | M2 + M3 | evidence-backed capability status | #42 | `DOC-001.md` when executed | Blocked |
| M4 | `DOC-002` | DOC-001 | lifecycle/privacy/troubleshooting guides | #43 | `DOC-002.md` when executed | Blocked |
| M4 | `QA-001` | M2 + M3 | fast/integration/release channels | #44 | `QA-001.md` when executed | Blocked |
| M4 | `QA-002` | QA-001 | Ruff/type/ShellCheck/coverage/audits | #45 | `QA-002.md` when executed | Blocked |
| M4 | `COMPAT-001` | COMPAT-000 + QA-002 | Linux/macOS × Python × real Hermes E2E | #46 | `COMPAT-001.md` when executed | Blocked；G3 owner, not G1 |
| M4 | `SEC-001` | COMPAT-001 + PRIV-001 | license/SBOM/dependency/permission evidence | #47 | `SEC-001.md` when executed | Blocked |
| M4 | `MIG-001` | INS-003 + MEM-002 + AUD-001 | `TC-MIG-001–006` migration/rollback | #48 | `MIG-001.md` when executed | Blocked |
| M4 | `SEC-002` | SEC-001 + MIG-001 | local API/files/destructive boundaries | #49 | `SEC-002.md` when executed | Blocked |
| M4 | `REL-006` | all M4 | reproducible RC、test-release、SBOM/provenance | #50 | `REL-006.md` when executed | Blocked |
| M5 | `BETA-001` | G3 + exact-master verification | immutable `v3.0.0-beta.1` publication | #51 | `BETA-001.md` when executed | Blocked |
| M5 | `BETA-002` | BETA-001 | external validation metrics | #52 | `BETA-002.md` when executed | Blocked |
| M5 | `BETA-003` | BETA-001 | owned Beta failure ledger | #53 | `BETA-003.md` when executed | Blocked |
| M5 | `REL-007` | BETA-001 | withdrawal/rollback/notification drill | #54 | `REL-007.md` when executed | Blocked |
| M6 | `STABLE-001` | G4 | close P0/P1 and Beta waivers | #55 | `STABLE-001.md` when executed | Blocked |
| M6 | `SOAK-001` | STABLE-001 | unchanged final-RC 14-day soak | #56 | `SOAK-001.md` when executed | Blocked |
| M6 | `REL-008` | G5 | immutable `v3.0.0` publication | #57 | `REL-008.md` when executed | Blocked |

## 2. G1 trace and remediation ownership

| Gate clause | Current evidence | Result | Canonical owner |
|---|---|---|---|
| clean snapshot wheel + sdist | wheel built and lifecycle-tested；sdist absent | **FAIL** | `QA-ART-001` #25 |
| `python -m twine check dist/*` | no Required evidence | **FAIL** | `QA-ART-001` #25 |
| wheel package data | 39-file inventory / resources verified | PASS | closed by M1 |
| external public imports | non-editable venv / outside cwd / empty PYTHONPATH | PASS | closed by M1 |
| no source symlink/path dependency | module origin and sys.path assertions | PASS | closed by M1 |
| Console Server lifecycle | CLI/Supervisor/install/uninstall E2E | PASS | closed by M1 |
| health/ready/version | App Factory + process + artifact smoke | PASS | closed by M1 |
| empty-HOME full lifecycle | pip→install→doctor→smoke→uninstall→pip uninstall | PASS | closed by M1 |
| repeat/port/interruption/data preservation | INS-001–003 Required evidence | PASS | closed by M1 |
| no real `~/.hermes` access | isolated HOME/data/DB/port/fake secret | PASS | closed by M1 |

G1 conclusion: **FAIL (8 PASS / 2 FAIL / 0 BLOCKED)**.

## 3. Requirement-domain ownership — 88 FR IDs

| Domain | Count | Primary Work IDs |
|---|---:|---|
| `FR-INSTALL-001–006` | 6 | INS-001、INS-002、INS-003、QA-ART-001、MIG-001 |
| `FR-PLUGIN-001–005` | 5 | PKG-001、INS-001、INS-003、COMPAT-001 |
| `FR-POLICY-001–008` | 8 | SES-001、AUD-001、OPS-001 |
| `FR-INTENT-001–007` | 7 | INTENT-001、DOC-001 |
| `FR-CONTEXT-001–013` | 13 | CTX-001–004、PRIV-001 |
| `FR-SERVER-001–007` | 7 | PKG-001、RUN-001、RUN-002、CON-001、SEC-002 |
| `FR-PLAN-001–008` | 8 | CON-001、PLAN-001–003 |
| `FR-MEMORY-001–007` | 7 | CON-001、MEM-001、MEM-002 |
| `FR-CHECKPOINT-001–006` | 6 | CON-001、CP-001 |
| `FR-OBS-001–005` | 5 | RUN-002、INS-002、AUD-001、PRIV-001、DOC-002 |
| `FR-SEC-001–007` | 7 | PRIV-001、SEC-001、SEC-002、INS-001/003 |
| `FR-QA-001–009` | 9 | QA-ART-001、QA-001、QA-002、COMPAT-001、REL-006 |
| **Total** | **88** | **0 orphan domains** |

## 4. Code Review blocker ownership — 17 CR IDs

| CR ID | Primary owner | Gate / state |
|---|---|---|
| `CR-P0-001` Server install/start invalid | PKG-001；关联 PKG-002、RUN-001/002、INS-001–003、QA-ART-001 | G1 implementation closed；artifact remediation remains |
| `CR-P0-002` duplicate tail | CTX-001 | G2 open |
| `CR-P0-003` Summary failure loses history | CTX-002 | G2 open |
| `CR-P0-004` hard constraint not verbatim | CTX-003 | G2 open |
| `CR-P0-005` cross-Session contamination | SES-001 | G2 open |
| `CR-P1-001` Tool contract mismatch | CON-001 | G3 open |
| `CR-P1-002` Audit format mismatch | AUD-001 | G3 open |
| `CR-P1-003` Cron not installable | OPS-001 | G3 open |
| `CR-P1-004` Memory import not idempotent | MEM-002；关联 MEM-001 | G3 open |
| `CR-P1-005` DAG linear chain | PLAN-001；关联 PLAN-002 | G3 open |
| `CR-P1-006` Intent low-confidence | INTENT-001 | G3 open |
| `CR-P1-007` Summary privacy undefined | PRIV-001；关联 DOC-002 | G2/G3 open |
| `CR-P2-001` Skill naming mismatch | DOC-001 | G3 open |
| `CR-P2-002` version mismatch | REL-001 | Complete |
| `CR-P2-003` CI only pytest | QA-001/QA-002 | G3 open |
| `CR-P2-004` tests touch real HOME | QA-ART-001；关联 QA-001 | G1/G3 implementation protected |
| `CR-P2-005` README over-promises | DOC-001/DOC-002 | G3 open |

## 5. Canonical strict-XFAIL ownership

| XF ID / test family | Exact owner | State |
|---|---|---|
| `XF-CTX-001` | CTX-001 #26 | Open |
| `XF-CTX-002` | CTX-002 #27 | Open |
| `XF-CTX-003` | CTX-003 #28 | Open |
| `XF-POLICY-001` | SES-001 #30 | Open |
| `XF-AUDIT-001` | AUD-001 #39 | Open |
| `XF-CONTRACT-001–003` | CON-001 #32 | Open |
| `XF-MEM-001` | MEM-002 #34 | Open |
| `XF-INSTALL-001` | INS-001 #22 | Fixed by PR #68 |
| `XF-DEPS-001` | PKG-002 #19 | Fixed by PR #63 |
| `XF-RELEASE-001` | REL-001 #5 | Fixed by PR #6 |

Current suite has 9 strict XFAIL tests and no orphan owner.

## 6. Test ID unique primary ownership — exactly 100

| Test IDs | Count | Primary Work ID |
|---|---:|---|
| `TC-INSTALL-001–003` | 3 | INS-001 |
| `TC-INSTALL-004/005/009` | 3 | INS-002 |
| `TC-INSTALL-006–008/010` | 4 | INS-003 |
| `TC-POLICY-001–005` | 5 | SES-001 |
| `TC-POLICY-006–008` | 3 | AUD-001 |
| `TC-INTENT-001–008` | 8 | INTENT-001 |
| `TC-CTX-003` | 1 | CTX-001 |
| `TC-CTX-004–006` | 3 | CTX-002 |
| `TC-CTX-007–009/014` | 4 | CTX-003 |
| `TC-CTX-001/002/011–013` | 5 | CTX-004 |
| `TC-CTX-010` | 1 | PRIV-001 |
| `TC-CONTRACT-001–010` | 10 | CON-001 |
| `TC-PLAN-003–007/009` | 6 | PLAN-001 |
| `TC-PLAN-001/002/008/010` | 4 | PLAN-002 |
| `TC-PLAN-011–013` | 3 | PLAN-003 |
| `TC-MEM-001–004/007/008/010` | 7 | MEM-001 |
| `TC-MEM-005/006/009/011–013` | 6 | MEM-002 |
| `TC-CP-001–006` | 6 | CP-001 |
| `TC-SERVER-001–003` | 3 | RUN-001 |
| `TC-SERVER-004` | 1 | RUN-002 |
| `TC-SERVER-005` | 1 | SEC-002 |
| `TC-SEC-001` | 1 | PRIV-001 |
| `TC-SEC-002–006` | 5 | SEC-002 |
| `TC-AUDIT-CLI-001` | 1 | OPS-001 |
| `TC-MIG-001–006` | 6 | MIG-001 |
| **Total** | **100** | **100 unique primary assignments; 0 orphan IDs** |

## 7. Gate dependency summary

```text
M0 → G0 PASS
M1 8/8 → G1 evaluation FAIL
G1 FAIL → QA-ART-001 #25 remediation → independent G1 re-evaluation
G1 PASS → M2 → G2
G2 PASS → M3
M2 + M3 → M4 → G3
G3 → exact-master verification → BETA-001
BETA-001 → BETA-002 + BETA-003 + REL-007 → G4
G4 → STABLE-001 → SOAK-001 → G5 → REL-008
```

Real Hermes E2E is owned by `COMPAT-001` in M4/G3, not G1. No Issue creation, documentation completion or green package CI bypasses a Gate.
