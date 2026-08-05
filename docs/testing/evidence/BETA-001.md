# BETA-001 Evidence - Public Beta Publication v3.0.0-beta.1

- Work ID: `BETA-001`
- Canonical Issue: #51
- Dependency: G3 PASS + exact-master verification
- Status: **Complete**
- Release: https://github.com/yuanchenglu/oh-my-deepseek-harness/releases/tag/v3.0.0-beta.1
- Tag: `v3.0.0-beta.1` (immutable, annotated)
- Commit: `a45eee092b003ac24700a2923f212fb3fe11b4a5` (master)
- Next serial Work ID: `BETA-002` / #52

## 1. Publication flow

1. develop→master Release PR #126 merged (a45eee0)
2. exact-master rebuild from a45eee0
3. Wheel: `oh_my_deepseek_harness-3.0.0b1-py3-none-any.whl` (132497 bytes)
4. Tag `v3.0.0-beta.1` created (annotated) + pushed
5. GitHub Release created (prerelease) with wheel asset + Release Notes

## 2. exact-master verification

- Wheel installs clean in fresh venv
- `import deepseek_harness` OK
- Target Tool contract: 10 (9 runtime + memory_store pending)
- Doctor: python PASS, dependencies PASS (after server extra)
- Remaining doctor FAILs (hermes/plugin/config/server/database/provider) are
  expected in a bare environment (need real Hermes install + credentials)

## 3. Artifact identity

- Commit: a45eee092b003ac24700a2923f212fb3fe11b4a5
- Wheel: oh_my_deepseek_harness-3.0.0b1-py3-none-any.whl
- Release Notes: docs/release/RELEASE_NOTES_v3.0.0-beta.1.md
- SHA256: computed at build (see release asset)

## 4. Authorized paths

| Path | Status |
|---|---|
| `docs/release/RELEASE_NOTES_v3.0.0-beta.1.md` | Added |
| External Git Tag + GitHub Release | Created (authorized) |
| PyPI | Not used (REL-005 disabled) |

## 5. Definition of Done

- [x] Immutable v3.0.0-beta.1 tag + GitHub Release
- [x] Wheel + Release Notes referencing same commit
- [x] exact-master rebuild + smoke test
- [x] Prerelease flag, no PyPI

## 6. Residual

M5 observation period (at least 14 calendar days) starts now. Beta user
metrics (BETA-002), failure triage (BETA-003), withdrawal drill (REL-007)
follow after publication.