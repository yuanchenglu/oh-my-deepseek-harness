# GATE-G0 Evidence：仓库与执行契约基线

- Gate：`G0`
- Decision：**PASS upon merge of this evidence PR**
- Decision date：2026-07-28
- Source branch：`docs/gate-g0-evidence-v2`
- Normative plan：`docs/roadmap/OPEN_SOURCE_RELEASE_PLAN.md` v2.3.3
- Current status ledger：`docs/roadmap/EXECUTION_STATUS.md`
- Product maturity after PASS：**Experimental Preview**

## 1. Gate question

G0 只回答：

> 仓库治理、外部契约、任务账本、责任归属和外部事实是否已固定到足以开始 M1，而无需实施代理猜测？

G0 不回答 Runtime 是否可发布，也不替代 G1–G5。

## 2. M0 dependency completion

| Work ID | Issue | Result |
|---|---|---|
| `REL-000` | #3 | Complete — 规格、88 FR、100 Test ID 同步 |
| `REL-001` | #5 | Complete — Python/Plugin/Git 版本语义固定 |
| `REL-002` | #7 | Complete — `develop` 默认分支、Ruleset、贡献治理与 v2.3 主计划 |
| `REL-004` | #10 | Complete — 10 Tool 目标、9 Tool 当前迁移状态固定 |
| `GOV-001` | #12 | Complete — Security、Issue/PR Forms、Release Checklist |
| `REL-003` | #15 | Complete — 48 canonical Issues 和完整追踪 |
| `REL-005` | #16 | Complete — GitHub-only Beta；PyPI 未认证前禁用 |
| `COMPAT-000` | #17 | Complete — PR #60 / `c7f6212a`；Hermes v0.19.0 候选和静态契约固定 |

Hard dependency result：`REL-003 + REL-005 + COMPAT-000` is satisfied by the merged repository state validated by this branch.

## 3. Repository governance

### 3.1 Default and integration branch

- default branch was machine-verified as `develop` after REL-002;
- ordinary work branches from and targets `develop`;
- `master` is release-only after G3.

### 3.2 Protection workflow

Repository administrator configuration and subsequent protected merges demonstrated:

- Pull Request required;
- approvals set to 0 for the current solo-maintainer phase;
- force push prohibited;
- branch deletion prohibited;
- `develop` Required Checks use the actual matrix contexts:
  - `test (3.10)`;
  - `test (3.11)`;
  - `test (3.12)`.

This G0 PR must pass the same checks before merge. The matrix is package/core CI; later QA/compatibility work adds stronger Required Checks and real Hermes E2E.

### 3.3 Governance files

Required governance artifacts exist:

- `SECURITY.md`;
- `.github/ISSUE_TEMPLATE/config.yml`;
- `.github/ISSUE_TEMPLATE/bug_report.yml`;
- `.github/ISSUE_TEMPLATE/work_item.yml`;
- `.github/pull_request_template.md`;
- `docs/release/RELEASE_CHECKLIST.md`.

Security reports are routed to private vulnerability reporting; public forms prohibit secrets/private data.

## 4. Fixed external contracts

### 4.1 Version identity

```text
Python distribution: 3.0.0b1
Plugin manifests: 3.0.0-beta.1
Git/GitHub target: v3.0.0-beta.1
Stable target: 3.0.0 / v3.0.0
Package/core Python metadata: >=3.10,<3.13
```

The release-version regression is a normal passing test; the historical version XFAIL is closed.

### 4.2 Tool denominator

```text
TARGET_PUBLIC_TOOL_NAMES: 10 unique names
PENDING_PUBLIC_TOOL_NAMES: {memory_store}
Current Runtime: 9 derived working Tool names
```

`memory_store` is not registered as a placeholder. `CON-001` and `MEM-001` own the generated contract and domain implementation.

### 4.3 Publishing channel

```text
First Public Beta mandatory channel: GitHub Release
PyPI: disabled until authenticated name/role/2FA/Trusted Publisher evidence
```

Public search absence is not treated as PyPI name availability. No package, tag or release is authorized by G0.

### 4.4 Hermes candidate and support layers

```text
Hermes candidate: 0.19.0
Tag: v2026.7.20
Upstream Python: >=3.11,<3.14
Package/core CI: Python 3.10, 3.11, 3.12
Full integrated product target: Python 3.11, 3.12; Linux/macOS
Python 3.10 + Hermes v0.19.0: expected unsupported precondition
```

Static verification confirms:

- the project Hook set is a subset of the selected Hermes Hook set;
- the 10-target / 9-runtime Tool contract is preserved;
- `DeepSeekContextEngine` exposes the required `name` property, core methods and token counters.

This static result does not claim real Hermes compatibility. `COMPAT-001` #46 still owns clean installation, discovery, explicit selection, lifecycle payload and Tool E2E evidence.

## 5. Traceability completeness

The canonical matrix records:

```text
Work IDs: 48
Unique canonical Issues: 48
Requirements: 88 / 88 mapped
Code Review blockers: 17 / 17 mapped
Test IDs: 100 / 100 unique primary owners
Orphan Work/FR/CR/Test IDs: 0
Duplicate primary Test owners: 0
```

Publishing Work IDs remain blocked by later Gates and explicit execution-time authorization.

## 6. Executable validation

`tests/test_g0_gate_contract.py` validates offline repository invariants:

- required governance/specification/evidence paths exist;
- version mapping is fixed;
- target 10 / pending 1 / current 9 Tool constants are exact;
- canonical Issue ledger contains 48 unique Work IDs and 48 unique Issue URLs;
- fixed-scope declarations include 88 FR, 17 CR and 100 Test IDs;
- publishing decision is GitHub-only with PyPI disabled;
- Hermes fixture is v0.19.0 and full Python is 3.11–3.12;
- the current Context Engine statically provides the required property and methods;
- main/status documents do not claim Public Beta or Stable completion.

Required CI must pass on Python 3.10, 3.11 and 3.12 before this Gate evidence can enter `develop`.

## 7. Residual risks accepted by later Work IDs

G0 intentionally leaves implementation blockers open, with owners:

- standard installable package: `PKG-001` #18;
- dependencies: `PKG-002` #19;
- Runtime/installer: #20–#25;
- Context/Session/privacy: #26–#31;
- Contract/Data integrity: #32–#41;
- real Hermes E2E: `COMPAT-001` #46;
- security/migration/release: #47–#57.

These are not G0 exceptions; they are the reason G1–G5 exist.

## 8. Decision

### PASS conditions

- this branch is based on current `develop` containing REL-005 and COMPAT-000 assets;
- offline G0 contract tests pass;
- existing complete suite passes on Python 3.10, 3.11 and 3.12;
- protected PR merge succeeds.

When this PR is merged, G0 is **PASS** and `PKG-001` #18 is the only next serial implementation task authorized.

### Prohibited interpretations

G0 PASS does not mean:

- the product is installable from a final artifact;
- Hermes E2E passed;
- Context, Session, Tool, Memory, Plan or Checkpoint defects are fixed;
- Public Beta or Stable may be published;
- any tag, Release or PyPI upload is authorized.
