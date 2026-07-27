# Open-source Release Traceability

- Normative plan: [`OPEN_SOURCE_RELEASE_PLAN.md`](../roadmap/OPEN_SOURCE_RELEASE_PLAN.md)
- Complete task ledger: [`OPEN_SOURCE_RELEASE_PLAN_2.2.md`](../roadmap/archive/OPEN_SOURCE_RELEASE_PLAN_2.2.md)
- Test ownership source: [`TEST_PLAN.md`](../testing/TEST_PLAN.md)
- Last synchronized: 2026-07-28
- Fixed scope: **48 Work IDs · 48 unique GitHub Issues · 88 FR IDs · 17 CR IDs · 100 Test IDs**

> 一个 Work ID 只有一个 canonical Issue。表中 `Open/Blocked` 表示 Issue 已创建，但硬依赖尚未满足；不表示允许并行实施。PR、Commit 和 Evidence 只能在实际合并后填写。

## 1. Work ID → Issue → Delivery

| Milestone | Work ID | Hard dependency | Primary contract / blocker | Primary verification | Issue | Delivery | Evidence | Status |
|---|---|---|---|---|---|---|---|---|
| M0 | `REL-000` | None | Release/spec contract; 88 FR + 100 Test IDs | document consistency and unique-ID search | [#3](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/3) | PR #4 · `e18db7e` | [`REL-000.md`](../testing/evidence/REL-000.md) | Complete |
| M0 | `REL-001` | REL-000 | Version identity; `CR-P2-002`; `XF-RELEASE-001` | version/manifest SemVer regression | [#5](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/5) | PR #6 · `a97dfe4` | [`REL-001.md`](../testing/evidence/REL-001.md) | Complete |
| M0 | `REL-002` | REL-001 | Branch governance, Rulesets, v2.3 plan | repository metadata, CI, archive Blob identity | [#7](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/7) | PR #8/#9 · `e7e1414e`/`61642f69` | [`REL-002.md`](../testing/evidence/REL-002.md) | Complete |
| M0 | `REL-004` | REL-002 | Current 9 / target 10 Tool denominator | `TestToolContract`; registry-set equality | [#10](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/10) | PR #11 · `7d52de9f` | [`REL-004.md`](../testing/evidence/REL-004.md) | Complete |
| M0 | `GOV-001` | REL-004 | Security policy, Issue/PR forms, release governance | YAML parse, link/field checks, Required CI | [#12](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/12) | PR #14 · `a0083ce1` | [`GOV-001.md`](../testing/evidence/GOV-001.md) | Complete |
| M0 | `REL-003` | GOV-001 | 48 canonical Issues and complete traceability | 48/48 uniqueness; 0 orphan FR/CR/Test owners | [#15](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/15) | Current PR | [`REL-003.md`](../testing/evidence/REL-003.md) | In progress |
| M0 | `REL-005` | REL-000 | PyPI ownership, 2FA, Trusted Publisher | credential-free external status evidence | [#16](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/16) | — | `REL-005.md` when executed | Open — eligible |
| M0 | `COMPAT-000` | REL-000 | Select one real Hermes validation target | source/version/probe/E2E plan | [#17](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/17) | — | `COMPAT-000.md` when executed | Open — eligible |
| M1 | `PKG-001` | G0 + COMPAT-000 | `FR-PLUGIN-001–005`, `FR-SERVER-001`; `CR-P0-001`; `XF-INSTALL-001` | clean-archive wheel inventory and external imports | [#18](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/18) | — | `PKG-001.md` when executed | Blocked by G0 |
| M1 | `PKG-002` | PKG-001 | Dependency extras; `CR-P0-001`; `XF-DEPS-001` | clean install/import matrix | [#19](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/19) | — | `PKG-002.md` when executed | Blocked |
| M1 | `RUN-001` | PKG-002 | `FR-SERVER-001–007`; `CR-P0-001` | `TC-SERVER-001–003`; import-side-effect matrix | [#20](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/20) | — | `RUN-001.md` when executed | Blocked |
| M1 | `RUN-002` | RUN-001 | `FR-SERVER-003–005`, `FR-OBS-004–005`; `CR-P0-001` | `TC-SERVER-004`; process/PID/log E2E | [#21](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/21) | — | `RUN-002.md` when executed | Blocked |
| M1 | `INS-001` | RUN-002 | `FR-INSTALL-001–003`, Plugin/Security install contract | `TC-INSTALL-001–003` | [#22](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/22) | — | `INS-001.md` when executed | Blocked |
| M1 | `INS-002` | INS-001 | `FR-INSTALL-006`, `FR-OBS-003/005` | `TC-INSTALL-004/005/009`; human/JSON Doctor | [#23](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/23) | — | `INS-002.md` when executed | Blocked |
| M1 | `INS-003` | INS-002 | `FR-INSTALL-004–005`; safe lifecycle | `TC-INSTALL-006–008/010`; recovery fixtures | [#24](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/24) | — | `INS-003.md` when executed | Blocked |
| M1 | `QA-ART-001` | INS-003 | `FR-QA-005`; `CR-P2-004` | source-external artifact lifecycle E2E | [#25](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/25) | — | `QA-ART-001.md` when executed | Blocked |
| M2 | `CTX-001` | G1 | `FR-CONTEXT-002/003/009/010`; `CR-P0-002`; `XF-CTX-001` | `TC-CTX-003` | [#26](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/26) | — | `CTX-001.md` when executed | Blocked |
| M2 | `CTX-002` | CTX-001 | `FR-CONTEXT-007–010`; `CR-P0-003`; `XF-CTX-002` | `TC-CTX-004–006` | [#27](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/27) | — | `CTX-002.md` when executed | Blocked |
| M2 | `CTX-003` | CTX-002 | `FR-CONTEXT-003–005/009`; `CR-P0-004`; `XF-CTX-003` | `TC-CTX-007–009/014`; property tests | [#28](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/28) | — | `CTX-003.md` when executed | Blocked |
| M2 | `CTX-004` | CTX-003 | `FR-CONTEXT-001/002/008–010/013` | `TC-CTX-001/002/011–013` | [#29](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/29) | — | `CTX-004.md` when executed | Blocked |
| M2 | `SES-001` | G1 + PKG-001 | `FR-POLICY-001–007`; `CR-P0-005`; `XF-POLICY-001` | `TC-POLICY-001–005`; concurrency barrier | [#30](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/30) | — | `SES-001.md` when executed | Blocked |
| M2 | `PRIV-001` | CTX-003 + SES-001 | `FR-CONTEXT-006/012`, `FR-OBS-002`, `FR-SEC-001–002`; `CR-P1-007` | `TC-CTX-010`; `TC-SEC-001` | [#31](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/31) | — | `PRIV-001.md` when executed | Blocked |
| M3 | `CON-001` | G2 + PKG-001 | `FR-SERVER-006–007`, `FR-QA-003`; `CR-P1-001`; `XF-CONTRACT-001–003` | `TC-CONTRACT-001–010` | [#32](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/32) | — | `CON-001.md` when executed | Blocked |
| M3 | `MEM-001` | CON-001 | `FR-MEMORY-001–004/007`; `CR-P1-004` associated | `TC-MEM-001–004/007/008/010` | [#33](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/33) | — | `MEM-001.md` when executed | Blocked |
| M3 | `MEM-002` | MEM-001 | `FR-MEMORY-005–006`; `CR-P1-004`; `XF-MEM-001` | `TC-MEM-005/006/009/011–013` | [#34](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/34) | — | `MEM-002.md` when executed | Blocked |
| M3 | `PLAN-001` | MEM-002 | `FR-PLAN-003/005/006`; `CR-P1-005` | `TC-PLAN-003–007/009` | [#35](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/35) | — | `PLAN-001.md` when executed | Blocked |
| M3 | `PLAN-002` | PLAN-001 | `FR-PLAN-001/002/004/006`; `CR-P1-005` associated | `TC-PLAN-001/002/008/010` | [#36](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/36) | — | `PLAN-002.md` when executed | Blocked |
| M3 | `PLAN-003` | PLAN-002 | `FR-PLAN-007–008` | `TC-PLAN-011–013` | [#37](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/37) | — | `PLAN-003.md` when executed | Blocked |
| M3 | `CP-001` | PLAN-003 | `FR-CHECKPOINT-001–006` | `TC-CP-001–006` | [#38](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/38) | — | `CP-001.md` when executed | Blocked |
| M3 | `AUD-001` | SES-001 | `FR-POLICY-005/008`, `FR-OBS-001`; `CR-P1-002`; `XF-AUDIT-001` | `TC-POLICY-006–008` | [#39](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/39) | — | `AUD-001.md` when executed | Blocked |
| M3 | `OPS-001` | AUD-001 | `FR-POLICY-008`, `FR-OBS-005`; `CR-P1-003` | `TC-AUDIT-CLI-001` | [#40](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/40) | — | `OPS-001.md` when executed | Blocked |
| M3 | `INTENT-001` | CON-001 | `FR-INTENT-001–007`; `CR-P1-006` | `TC-INTENT-001–008`; quality report | [#41](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/41) | — | `INTENT-001.md` when executed | Blocked |
| M4 | `DOC-001` | M2 + M3 | `CR-P2-001`, `CR-P2-005`; capability evidence | README status/evidence tests | [#42](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/42) | — | `DOC-001.md` when executed | Blocked |
| M4 | `DOC-002` | DOC-001 | Lifecycle/Privacy guides; `CR-P1-007`, `CR-P2-005` | command/link/new-user rehearsal | [#43](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/43) | — | `DOC-002.md` when executed | Blocked |
| M4 | `QA-001` | M2 + M3 | `FR-QA-001/004–006/008–009`; `CR-P2-003/004` | fast/integration/release inventory | [#44](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/44) | — | `QA-001.md` when executed | Blocked |
| M4 | `QA-002` | QA-001 | `FR-QA-002/008–009`; `CR-P2-003` | Ruff/type/ShellCheck/coverage/audit/secret Required Checks | [#45](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/45) | — | `QA-002.md` when executed | Blocked |
| M4 | `COMPAT-001` | COMPAT-000 + QA-002 | `FR-PLUGIN-001–005`, `FR-QA-002/007` | Linux/macOS × Python × real Hermes E2E | [#46](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/46) | — | `COMPAT-001.md` when executed | Blocked |
| M4 | `SEC-001` | COMPAT-001 + PRIV-001 | `FR-SEC-005`, `FR-QA-008–009` | license/SBOM/dependency/permission evidence | [#47](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/47) | — | `SEC-001.md` when executed | Blocked |
| M4 | `MIG-001` | INS-003 + MEM-002 + AUD-001 | `FR-INSTALL-004`; migration contract | `TC-MIG-001–006` | [#48](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/48) | — | `MIG-001.md` when executed | Blocked |
| M4 | `SEC-002` | SEC-001 + MIG-001 | `FR-SERVER-002/007`, `FR-SEC-003/004/006/007` | `TC-SERVER-005`; `TC-SEC-002–006` | [#49](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/49) | — | `SEC-002.md` when executed | Blocked |
| M4 | `REL-006` | all M4 | RC build/publish-dry-run/rollback; `FR-QA-009` | reproducibility, test-release, provenance, withdrawal drill | [#50](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/50) | — | `REL-006.md` when executed | Blocked |
| M5 | `BETA-001` | G3 + master final artifact verification | immutable Beta publication | final Release Checklist and public smoke | [#51](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/51) | — | `BETA-001.md` when executed | Blocked |
| M5 | `BETA-002` | BETA-001 | external validation metrics | raw counts, Wilson intervals, privacy checks | [#52](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/52) | — | `BETA-002.md` when executed | Blocked |
| M5 | `BETA-003` | BETA-001 | owned Beta failure ledger | orphan/owner/severity/Gate checks | [#53](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/53) | — | `BETA-003.md` when executed | Blocked |
| M5 | `REL-007` | BETA-001 | withdrawal/rollback/notification drill | non-maintainer timeline and data inventory | [#54](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/54) | — | `REL-007.md` when executed | Blocked |
| M6 | `STABLE-001` | G4 | close P0/P1 and Beta waivers | reproducible Issue/waiver queries | [#55](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/55) | — | `STABLE-001.md` when executed | Blocked |
| M6 | `SOAK-001` | STABLE-001 | unchanged final-RC 14-day soak | duration/exposure/failure report | [#56](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/56) | — | `SOAK-001.md` when executed | Blocked |
| M6 | `REL-008` | G5 | immutable Stable publication | final artifact/docs/public smoke identity | [#57](https://github.com/yuanchenglu/oh-my-deepseek-harness/issues/57) | — | `REL-008.md` when executed | Blocked |

## 2. Requirement-domain ownership — 88 unique FR IDs

| Requirement domain | Count | Primary Work IDs / Issues | Primary test families |
|---|---:|---|---|
| `FR-INSTALL-001–006` | 6 | INS-001 [#22], INS-002 [#23], INS-003 [#24], QA-ART-001 [#25], MIG-001 [#48] | `TC-INSTALL-001–010`, `TC-MIG-001–006` |
| `FR-PLUGIN-001–005` | 5 | PKG-001 [#18], INS-001 [#22], INS-003 [#24], COMPAT-001 [#46] | Plugin lifecycle and real Hermes E2E |
| `FR-POLICY-001–008` | 8 | SES-001 [#30], AUD-001 [#39], OPS-001 [#40] | `TC-POLICY-001–008`, `TC-AUDIT-CLI-001` |
| `FR-INTENT-001–007` | 7 | INTENT-001 [#41], DOC-001 [#42] | `TC-INTENT-001–008`, docs evidence checks |
| `FR-CONTEXT-001–013` | 13 | CTX-001–004 [#26–#29], PRIV-001 [#31] | `TC-CTX-001–014` |
| `FR-SERVER-001–007` | 7 | PKG-001 [#18], RUN-001 [#20], RUN-002 [#21], CON-001 [#32], SEC-002 [#49] | `TC-SERVER-001–005`, Contract tests |
| `FR-PLAN-001–008` | 8 | CON-001 [#32], PLAN-001–003 [#35–#37] | `TC-PLAN-001–013` |
| `FR-MEMORY-001–007` | 7 | CON-001 [#32], MEM-001 [#33], MEM-002 [#34] | `TC-MEM-001–013` |
| `FR-CHECKPOINT-001–006` | 6 | CON-001 [#32], CP-001 [#38] | `TC-CP-001–006` |
| `FR-OBS-001–005` | 5 | RUN-002 [#21], AUD-001 [#39], PRIV-001 [#31], DOC-002 [#43] | log/status/audit/privacy tests |
| `FR-SEC-001–007` | 7 | PRIV-001 [#31], SEC-001 [#47], SEC-002 [#49], INS-001/003 [#22/#24] | `TC-SEC-001–006`, install security |
| `FR-QA-001–009` | 9 | QA-ART-001 [#25], QA-001 [#44], QA-002 [#45], COMPAT-001 [#46], REL-006 [#50] | Fast/Integration/Release/compatibility gates |
| **Total** | **88** | **0 orphan domains** | — |

## 3. Code Review blocker ownership — 17 unique CR IDs

| CR ID | Primary Issue | Associated Issues | Gate |
|---|---|---|---|
| `CR-P0-001` Server install/start invalid | PKG-001 [#18] | PKG-002 [#19], RUN-001 [#20], RUN-002 [#21], INS-001–003 [#22–#24], QA-ART-001 [#25] | G1 |
| `CR-P0-002` duplicate tail messages | CTX-001 [#26] | — | G2 |
| `CR-P0-003` Summary failure loses history | CTX-002 [#27] | — | G2 |
| `CR-P0-004` hard constraint not verbatim | CTX-003 [#28] | — | G2 |
| `CR-P0-005` cross-Session contamination | SES-001 [#30] | — | G2 |
| `CR-P1-001` Tool contract mismatch | CON-001 [#32] | — | G3 |
| `CR-P1-002` Audit format mismatch | AUD-001 [#39] | — | G3 |
| `CR-P1-003` Cron not installable | OPS-001 [#40] | — | G3 |
| `CR-P1-004` Memory import not idempotent | MEM-002 [#34] | MEM-001 [#33] | G3 |
| `CR-P1-005` DAG is a linear chain | PLAN-001 [#35] | PLAN-002 [#36] | G3 |
| `CR-P1-006` Intent low-confidence path broken | INTENT-001 [#41] | — | G3 |
| `CR-P1-007` external Summary privacy undefined | PRIV-001 [#31] | DOC-002 [#43] | G2/G3 |
| `CR-P2-001` Skill learning naming mismatch | DOC-001 [#42] | — | G3 |
| `CR-P2-002` version mismatch | REL-001 [#5] | — | G0/G3 — Complete |
| `CR-P2-003` CI only runs pytest | QA-001 [#44] | QA-002 [#45] | G3 |
| `CR-P2-004` tests touch real HOME | QA-ART-001 [#25] | QA-001 [#44] | G1/G3 |
| `CR-P2-005` README over-promises | DOC-001 [#42] | DOC-002 [#43] | G3 |

## 4. Canonical strict-XFAIL ownership

| XF ID | Exact owner Issue | Current state |
|---|---|---|
| `XF-CTX-001` | CTX-001 [#26] | Open |
| `XF-CTX-002` | CTX-002 [#27] | Open |
| `XF-CTX-003` | CTX-003 [#28] | Open |
| `XF-POLICY-001` | SES-001 [#30] | Open |
| `XF-AUDIT-001` | AUD-001 [#39] | Open |
| `XF-CONTRACT-001–003` | CON-001 [#32] | Open |
| `XF-INSTALL-001` | PKG-001 [#18] | Open |
| `XF-DEPS-001` | PKG-002 [#19] | Open; historical alias `XF-PKG-001` deprecated |
| `XF-RELEASE-001` | REL-001 [#5] | Fixed by PR #6; historical alias `XF-VERSION-001` deprecated |
| `XF-MEM-001` | MEM-002 [#34] | Open |

Historical reports remain immutable; new Issue/PR/Evidence uses only canonical IDs.

## 5. Test ID unique primary ownership — exactly 100

| Test IDs | Count | Primary Work ID / Issue |
|---|---:|---|
| `TC-INSTALL-001–003` | 3 | INS-001 [#22] |
| `TC-INSTALL-004/005/009` | 3 | INS-002 [#23] |
| `TC-INSTALL-006–008/010` | 4 | INS-003 [#24] |
| `TC-POLICY-001–005` | 5 | SES-001 [#30] |
| `TC-POLICY-006–008` | 3 | AUD-001 [#39] |
| `TC-INTENT-001–008` | 8 | INTENT-001 [#41] |
| `TC-CTX-003` | 1 | CTX-001 [#26] |
| `TC-CTX-004–006` | 3 | CTX-002 [#27] |
| `TC-CTX-007–009/014` | 4 | CTX-003 [#28] |
| `TC-CTX-001/002/011–013` | 5 | CTX-004 [#29] |
| `TC-CTX-010` | 1 | PRIV-001 [#31] |
| `TC-CONTRACT-001–010` | 10 | CON-001 [#32] |
| `TC-PLAN-003–007/009` | 6 | PLAN-001 [#35] |
| `TC-PLAN-001/002/008/010` | 4 | PLAN-002 [#36] |
| `TC-PLAN-011–013` | 3 | PLAN-003 [#37] |
| `TC-MEM-001–004/007/008/010` | 7 | MEM-001 [#33] |
| `TC-MEM-005/006/009/011–013` | 6 | MEM-002 [#34] |
| `TC-CP-001–006` | 6 | CP-001 [#38] |
| `TC-SERVER-001–003` | 3 | RUN-001 [#20] |
| `TC-SERVER-004` | 1 | RUN-002 [#21] |
| `TC-SERVER-005` | 1 | SEC-002 [#49] |
| `TC-SEC-001` | 1 | PRIV-001 [#31] |
| `TC-SEC-002–006` | 5 | SEC-002 [#49] |
| `TC-AUDIT-CLI-001` | 1 | OPS-001 [#40] |
| `TC-MIG-001–006` | 6 | MIG-001 [#48] |
| **Total** | **100** | **100 unique primary assignments; 0 orphan IDs** |

## 6. Gate dependency summary

```text
M0 serial: REL-000 → REL-001 → REL-002 → REL-004 → GOV-001 → REL-003
M0 parallel: REL-000 → REL-005
M0 parallel: REL-000 → COMPAT-000
REL-003 + REL-005 + COMPAT-000 → G0
G0 + COMPAT-000 → M1 → G1
G1 → M2 → G2
G2 → M3
M2 + M3 → M4 → G3
G3 → BETA-001
BETA-001 → BETA-002 + BETA-003 + REL-007 → G4
G4 → STABLE-001 → SOAK-001 → G5 → REL-008
```

No Issue creation or documentation completion bypasses a Gate. External publishing Work IDs still require explicit authorization at execution time.
