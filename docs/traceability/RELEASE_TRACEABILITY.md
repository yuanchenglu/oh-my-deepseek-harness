# Open-source Release Traceability

- Normative plan: [`OPEN_SOURCE_RELEASE_PLAN.md`](../roadmap/OPEN_SOURCE_RELEASE_PLAN.md) v2.3.12
- Complete task ledger: [`OPEN_SOURCE_RELEASE_PLAN_2.2.md`](../roadmap/archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md)
- Test ownership source: [`TEST_PLAN.md`](../testing/TEST_PLAN.md)
- Last synchronized: 2026-07-29
- Fixed scope: **48 Work IDs · 48 unique GitHub Issues · 88 FR IDs · 17 CR IDs · 100 Test IDs**
- Current Gate: **G1 PASS**
- Current serial task: **SES-001 #30**

> 一个 Work ID 只有一个 canonical Issue。`CTX-001`、`CTX-002`、`CTX-003`、`CTX-004` 已闭环；固定分母不变。

## 1. Work ID → Issue → Delivery

| Milestone | Work ID | Hard dependency | Primary contract / verification | Issue | Delivery / Evidence | Status |
|---|---|---|---|---:|---|---|
| M0 | `REL-000` | None | Release/spec contract；88 FR + 100 Test IDs | #3 | PR #4 · `e18db7e` | Complete |
| M0 | `REL-001` | REL-000 | Version identity；`CR-P2-002` | #5 | PR #6 · `a97dfe4` | Complete |
| M0 | `REL-002` | REL-001 | Branch governance、Rulesets | #7 | PR #8/#9 · `e7e1414e`/`61642f69` | Complete |
| M0 | `REL-004` | REL-002 | current 9 / target 10 Tool denominator | #10 | PR #11 · `7d52de9f` | Complete |
| M0 | `GOV-001` | REL-004 | Security/release governance | #12 | PR #14 · `a0083ce1` | Complete |
| M0 | `REL-003` | GOV-001 | 48 canonical Issues、Traceability | #15 | PR #58 · `fd5c212f` | Complete |
| M0 | `REL-005` | REL-000 | PyPI ownership / GitHub-only decision | #16 | PR #59 · `49ad479f` | Complete — PyPI disabled |
| M0 | `COMPAT-000` | REL-000 | Hermes v0.19.0 target / static probes | #17 | PR #60 · `c7f6212a` | Complete |
| M1 | `PKG-001` | G0 + COMPAT-000 | canonical `src/` package | #18 | PR #62 · `2098dffc` | Complete |
| M1 | `PKG-002` | PKG-001 | dependency extras | #19 | PR #63 · `ae277d1d` | Complete |
| M1 | `RUN-001` | PKG-002 | App Factory、`TC-SERVER-001–003` | #20 | PR #64 · `31366ceb` | Complete |
| M1 | `RUN-002` | RUN-001 | Supervisor、`TC-SERVER-004` | #21 | PR #65 · `f1c04697` | Complete |
| M1 | `INS-001` | RUN-002 | install transaction/idempotence | #22 | PR #68 · `2e5438a7` | Complete |
| M1 | `INS-002` | INS-001 | Doctor/support matrix | #23 | PR #70 · `d1d3269d` | Complete |
| M1 | `INS-003` | INS-002 | upgrade/recover/uninstall/purge | #24 | PR #72 · `9e5295ac` | Complete |
| M1 | `QA-ART-001` | INS-003 | wheel+sdist/twine/lifecycle | #25 | PR #74 · `7adbb0cb`; PR #78 · `5ebb3a0c` | Complete |
| M2 | `CTX-001` | G1 | `CR-P0-002`；`TC-CTX-003` | #26 | PR #81 · `4026fea2` · `CTX-001.md` | Complete |
| M2 | `CTX-002` | CTX-001 | `CR-P0-003`；`TC-CTX-004–006` | #27 | PR #83 · `bf4ab49e` · `CTX-002.md` | Complete |
| M2 | `CTX-003` | CTX-002 | `CR-P0-004`；`TC-CTX-007–009/014` | #28 | PR #85 · `0eb68d70` · `CTX-003.md` | Complete |
| M2 | `CTX-004` | CTX-003 | `TC-CTX-001–002/011–013` | #29 | PR #90 · `5ad013b3` · `CTX-004.md` | **Complete** |
| M2 | `SES-001` | G1 + PKG-001 | `CR-P0-005`；`TC-POLICY-001–005` | #30 | PR #94 · `SES-001.md` | **Complete** |
| M2 | `PRIV-001` | CTX-003 + SES-001 | privacy/redaction | #31 | PR #95 · `PRIV-001.md` | **Complete** |
| M3 | `CON-001` | G2 + PKG-001 | `TC-CONTRACT-001–010` | #32 | PR #97 · `CON-001.md` | **Complete** |
| M3 | `MEM-001` | CON-001 | Memory store/query/dedup | #33 | PR #101 · `MEM-001.md` | **Complete** |
| M3 | `MEM-002` | MEM-001 | Memory import/delete/idempotence | #34 | PR #102 · `MEM-002.md` | **Complete** |
| M3 | `PLAN-001` | MEM-002 | DAG/cascade | #35 | PR #103 · `PLAN-001.md` | **Complete** |
| M3 | `PLAN-002` | PLAN-001 | state machine | #36 | PR #104 · `PLAN-002.md` | **Complete** |
| M3 | `PLAN-003` | PLAN-002 | query/archive/delete | #37 | PR #105 · `PLAN-003.md` | **Complete** |
| M3 | `CP-001` | PLAN-003 | Checkpoint | #38 | PR #106 · `CP-001.md` | **Complete** |
| M3 | `AUD-001` | SES-001 | Audit source of truth | #39 | pending | Blocked |
| M3 | `OPS-001` | AUD-001 | manual audit CLI | #40 | pending | Blocked |
| M3 | `INTENT-001` | CON-001 | intent confidence | #41 | pending | Blocked |
| M4 | `DOC-001` | M2 + M3 | capability docs | #42 | pending | Blocked |
| M4 | `DOC-002` | DOC-001 | lifecycle/privacy guides | #43 | pending | Blocked |
| M4 | `QA-001` | M2 + M3 | test channels | #44 | pending | Blocked |
| M4 | `QA-002` | QA-001 | quality/audits | #45 | pending | Blocked |
| M4 | `COMPAT-001` | COMPAT-000 + QA-002 | real Hermes E2E | #46 | pending | Blocked |
| M4 | `SEC-001` | COMPAT-001 + PRIV-001 | license/SBOM/dependency | #47 | pending | Blocked |
| M4 | `MIG-001` | INS-003 + MEM-002 + AUD-001 | `TC-MIG-001–006` | #48 | pending | Blocked |
| M4 | `SEC-002` | SEC-001 + MIG-001 | security boundaries | #49 | pending | Blocked |
| M4 | `REL-006` | all M4 | RC/reproducibility/provenance | #50 | pending | Blocked |
| M5 | `BETA-001` | G3 + exact-master verification | `v3.0.0-beta.1` | #51 | pending | Blocked |
| M5 | `BETA-002` | BETA-001 | external validation | #52 | pending | Blocked |
| M5 | `BETA-003` | BETA-001 | Beta failure ledger | #53 | pending | Blocked |
| M5 | `REL-007` | BETA-001 | withdrawal drill | #54 | pending | Blocked |
| M6 | `STABLE-001` | G4 | close Beta blockers | #55 | pending | Blocked |
| M6 | `SOAK-001` | STABLE-001 | 14-day soak | #56 | pending | Blocked |
| M6 | `REL-008` | G5 | immutable `v3.0.0` | #57 | pending | Blocked |

### Canonical Issue URL registry

- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/3
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/5
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/7
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/10
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/12
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/15
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/16
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/17
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/18
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/19
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/20
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/21
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/22
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/23
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/24
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/25
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/26
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/27
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/28
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/29
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/30
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/31
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/32
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/33
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/34
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/35
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/36
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/37
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/38
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/39
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/40
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/41
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/42
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/43
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/44
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/45
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/46
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/47
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/48
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/49
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/50
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/51
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/52
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/53
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/54
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/55
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/56
- https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/57

## 2. Requirement-domain ownership — 88 FR IDs

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

## 3. Code Review blocker ownership — 17 CR IDs

| CR ID | Primary owner | State |
|---|---|---|
| `CR-P0-001` | PKG/RUN/INS/QA-ART chain | Complete |
| `CR-P0-002` | CTX-001 | Complete by PR #81 |
| `CR-P0-003` | CTX-002 | Complete by PR #83 |
| `CR-P0-004` | CTX-003 | Complete by PR #85 |
| `CR-P0-005` | SES-001 | Open |
| `CR-P1-001` | CON-001 | Open |
| `CR-P1-002` | AUD-001 | Open |
| `CR-P1-003` | OPS-001 | Open |
| `CR-P1-004` | MEM-002 | Complete (storage dedup 由 MEM-001, delete/import 由 MEM-002) |
| `CR-P1-005` | PLAN-001 | Complete (DAG 校验 + cascade) |
| `CR-P1-006` | INTENT-001 | Open |
| `CR-P1-007` | PRIV-001 | Open |
| `CR-P2-001` | DOC-001 | Open |
| `CR-P2-002` | REL-001 | Complete |
| `CR-P2-003` | QA-001/QA-002 | Open |
| `CR-P2-004` | QA-ART-001/QA-001 | G1 protected; G3 continues |
| `CR-P2-005` | DOC-001/DOC-002 | Open |

## 4. Canonical strict-XFAIL ownership

| XF ID / test family | Exact owner | State |
|---|---|---|
| `XF-CTX-001` | CTX-001 #26 | Fixed by PR #81 |
| `XF-CTX-002` | CTX-002 #27 | Fixed by PR #83 |
| `XF-CTX-003` | CTX-003 #28 | Fixed by PR #85 |
| `XF-POLICY-001` | SES-001 #30 | Open |
| `XF-AUDIT-001` | AUD-001 #39 | Open |
| `XF-CONTRACT-001–003` | CON-001 #32 | Open |
| `XF-MEM-001` | MEM-001 #33 | Fixed (storage dedup) |
| `XF-INSTALL-001` | INS-001 #22 | Fixed |
| `XF-DEPS-001` | PKG-002 #19 | Fixed |
| `XF-RELEASE-001` | REL-001 #5 | Fixed |

Current suite has **6 strict XFAIL tests** and no orphan owner.

## 5. Test ID unique primary ownership — exactly 100

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

## 6. Gate dependency summary

```text
M0 → G0 PASS
M1 → G1 PASS
CTX-001 + CTX-002 + CTX-003 + CTX-004 Complete → SES-001 → PRIV-001 → G2
G2 PASS → M3 → M4/G3 → exact-master verification
BETA-001 → real feedback/G4 → Stable/SOAK/G5 → REL-008
```
