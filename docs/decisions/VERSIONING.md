# Versioning Decision Record

- Decision ID: `REL-001`
- Status: Accepted for Open-source Beta
- Effective branch: `develop`
- Decision date: 2026-07-27

## 1. Release identity

The repository, Python distribution, Harness plugin, and Context plugin are one coordinated release identity. They use syntax appropriate to each ecosystem:

| Surface | Beta 1 | Stable |
|---|---|---|
| Git tag / GitHub Release | `v3.0.0-beta.1` | `v3.0.0` |
| Python distribution (PEP 440) | `3.0.0b1` | `3.0.0` |
| Plugin manifests (SemVer) | `3.0.0-beta.1` | `3.0.0` |

The mapping is semantic, not literal string equality:

```text
3.0.0b1 ⇔ 3.0.0-beta.1 ⇔ v3.0.0-beta.1
```

## 2. Why version 3

The current public identity already uses 2.x. The Beta stabilization changes package layout, installation lifecycle, runtime supervision, configuration/data schemas, migration and uninstall semantics. Resetting the same distribution to 0.x would break upgrade ordering; continuing at 3.0.0 preserves monotonic version semantics while clearly marking prerelease maturity.

## 3. Python support

`requires-python` is fixed to:

```text
>=3.10,<3.13
```

The upper bound prevents metadata from claiming Python versions that are not in the CI/support matrix. Expanding the range requires CI evidence and a separate decision update.

## 4. Prerelease increments

- First public Beta: `3.0.0b1` / `v3.0.0-beta.1`.
- Fixes requiring another Beta increment the prerelease number: `b2` / `beta.2`, then `b3` / `beta.3`.
- Existing tags and release artifacts are immutable and must never be moved or replaced.
- RC-only validation may use a frozen Commit SHA or disposable `v3.0.0-beta.1-rc.N` tag that is not a public Release or installation entry point.

## 5. Stable transition

Stable is `3.0.0` / `v3.0.0` only after G5 passes. Stable removes the prerelease suffix; it does not create a new major version.

## 6. Changelog policy

- Historical `v1.0.0` and `v2.0.0` records remain unchanged.
- Current stabilization work is recorded under `Unreleased` with the planned release identity.
- At release time, `Unreleased` is converted to the exact released version and date.

## 7. Migration policy

The first 3.0 Beta must provide an explicit upgrade path from the review baseline `develop@37e4016`, including Config, DB, JSONL and process state. A package version change alone does not constitute migration completion.

## 8. Non-goals

This decision does not publish a package or tag, add dependencies, implement package layout, assert Beta readiness, or change runtime behavior.
