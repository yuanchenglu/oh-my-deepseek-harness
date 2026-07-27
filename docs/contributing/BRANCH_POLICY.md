# Branch and Repository Governance Policy

- Work ID: `REL-002`
- Status: Target policy; repository-file portion in implementation
- Integration branch: `develop`
- Release branch: `master`
- Effective release cycle: `v3.0.0-beta.1` → `v3.0.0`

## 1. First Principle

`develop` is the only branch where ordinary product, test, documentation and governance work is integrated. `master` is not a development branch; it is a release-gated baseline.

The policy separates two questions:

1. **Can a change be integrated for continued validation?** → PR to `develop`.
2. **Is the exact commit release-ready?** → G3 evidence, then an authorized `develop → master` Release Candidate PR.

## 2. Branch Roles

| Branch / Pattern | Role | Base | Normal PR Target |
|---|---|---|---|
| `develop` | Single integration/default branch | — | — |
| `master` | Release-gated baseline | — | — |
| `fix/<work-id>-<scope>` | P0/P1 or correctness fix | `develop` | `develop` |
| `test/<work-id>-<scope>` | Test infrastructure/regression | `develop` | `develop` |
| `docs/<work-id>-<scope>` | Documentation/governance | `develop` | `develop` |
| `chore/<work-id>-<scope>` | Build/version/CI/tooling | `develop` | `develop` |
| `feat/<work-id>-<scope>` | Explicitly approved requirement only | `develop` | `develop` |

A branch without a Work ID is not eligible for the current stabilization cycle unless it is an emergency recovery branch authorized by the maintainer and documented afterward.

## 3. Normal Contribution Flow

```text
develop
  └─ scoped Work-ID branch
       └─ Pull Request to develop
            └─ Required CI + review + evidence
                 └─ Squash Merge to develop
```

Rules:

- Fetch and fast-forward from the current `develop` before creating a branch.
- One branch and one PR implement one Work ID.
- A Work ID may not start before all hard dependencies complete.
- Overlapping authorized file sets may not be modified concurrently.
- Squash Merge is preferred so each Work ID has one rollback commit on `develop`.
- Direct business-code pushes to `develop` are prohibited by target Ruleset.

## 4. Release Flow

```text
G3 PASS on frozen develop commit / disposable RC tag
  → authorized PR: develop → master
  → exact master commit final artifact rebuild + test-release
  → BETA-001 creates immutable Beta tag and GitHub Release
```

Only the Gate coordinator or explicitly authorized release maintainer opens the `develop → master` PR. Ordinary changes never target `master`.

Merging to `master` does not itself authorize publishing. The final artifact test on the exact `master` commit must pass before an immutable tag or Release is created.

## 5. Required GitHub Repository Settings

### 5.1 Default Branch

Target:

```text
default_branch = develop
```

Observed at REL-002 start:

```text
default_branch = master
```

The setting is not complete until queried after mutation and preserved in `docs/testing/evidence/REL-002.md`.

### 5.2 Ruleset for `develop`

Required:

- branch deletion prohibited;
- force push prohibited;
- Pull Request required;
- current CI workflow required as a status check;
- unresolved review conversations addressed when supported by repository policy;
- bypass restricted to documented emergency recovery roles;
- direct business-code pushes prohibited.

### 5.3 Ruleset for `master`

Required:

- branch deletion prohibited;
- force push prohibited;
- Pull Request required;
- current CI workflow required as a status check;
- only an authorized release PR from `develop` is permitted by process;
- bypass restricted to documented emergency recovery roles.

The current CI check is the minimum G0 requirement. `QA-002` later adds Ruff, format, type, ShellCheck, coverage, dependency and secret checks as Required Checks.

## 6. Pull Request Contract

Every PR must include:

- Work ID and Issue;
- Requirement/Test/CR/XF trace;
- hard-dependency confirmation;
- falsifiable hypothesis;
- authorized file scope;
- file/integration/pipeline evidence;
- exact test commands and counts;
- data/privacy/security/compatibility/migration impact;
- rollback and recovery;
- out-of-scope list.

The canonical template is `.github/pull_request_template.md`.

## 7. Emergency Recovery

A protected-branch bypass may be used only when all of the following hold:

1. the repository is unable to accept ordinary PRs or execute recovery CI;
2. the action is required to restore the protected workflow, not to ship product behavior;
3. the maintainer records the reason, affected refs, exact commands and rollback;
4. a follow-up Issue/PR reconstructs review and evidence;
5. no existing tag or release artifact is moved or replaced.

Emergency bypass does not count as a passed Release Gate.

## 8. Verification Checklist

`REL-002` cannot close until all items are proven:

- [x] `CONTRIBUTING.md` directs ordinary branches and PRs through `develop`.
- [x] PR template contains the execution evidence and rollback contract.
- [ ] Repository default branch is `develop`.
- [ ] `develop` Ruleset requires PR and current CI; force push/deletion prohibited.
- [ ] `master` Ruleset requires PR and current CI; force push/deletion prohibited.
- [ ] Repository settings evidence is saved without credentials or secrets.
- [ ] Main release plan incorporates Errata 2.3 without content loss, or the unresolved consolidation blocker remains explicit.

Until every unchecked item is complete, G0 remains incomplete and serial successor `REL-004` must not start.

## 9. Tooling Limitation Recorded During REL-002

The connected GitHub integration can read repository metadata and confirms the authenticated account has Admin permission, but it does not currently expose mutations for default branch or Rulesets. Therefore the repository-file PR may be merged independently, while Issue #7 remains open pending external settings mutation and verification through a supported interface.
