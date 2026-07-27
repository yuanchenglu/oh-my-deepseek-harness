## Work ID / Issue

- Work ID: `<!-- e.g. CTX-001 -->`
- Issue: `<!-- #123 -->`
- Primary Requirement(s): `<!-- FR-* -->`
- Review / XFAIL ID(s): `<!-- CR-* / XF-* or N/A -->`

## Dependency Check

- [ ] All hard dependencies are complete and linked.
- [ ] This branch was created from the current `develop`.
- [ ] No active Work ID modifies overlapping authorized paths.

## Current Behavior

<!-- Describe the observed behavior and provide a reproducible command/test. -->

## Expected Behavior

<!-- State the fixed contract or invariant. -->

## Falsifiable Hypothesis

<!-- State what you believed was the root cause and what evidence would disprove it. -->

## Changes

<!-- List modified files and explain why each is within the Issue's allowed scope. -->

## Verification

Commands executed:

```bash
# Exact commands only; do not write "CI should pass".
```

Results:

| Layer | Evidence | Result |
|---|---|---|
| File | parse/build/install evidence | |
| Integration | real caller/import/process evidence | |
| Pipeline | user entry → observable result | |

Test counts:

- Passed:
- Failed:
- Errors:
- XPASS:
- XFAIL:
- Skipped:
- CI Run / Artifact:

## Data, Privacy and Security

- [ ] Tests use temporary HOME, DB, port and Fake Secret.
- [ ] No real user data was read or modified.
- [ ] No new undisclosed external data transfer was introduced.
- [ ] Logs and errors do not expose Prompt, Tool Result, Secret or sensitive absolute paths.
- [ ] Destructive operations have dry-run/confirmation and path-boundary tests, or are not applicable.

Details / N/A reason:

## Compatibility and Migration

- Python / OS / Hermes impact:
- Config / DB / JSONL / runtime-state impact:
- Upgrade / downgrade behavior:
- Required migration or fixture:

## Risk and Rollback

- Primary risk:
- Stop condition:
- Rollback command/procedure:
- Data recovery procedure:

## Documentation and Traceability

- [ ] Requirement → Test → PR trace updated.
- [ ] Evidence document updated.
- [ ] User-facing documentation matches actual behavior.
- [ ] Known Limitations updated when applicable.

Evidence path / links:

## Out of Scope

<!-- Explicitly list nearby work that this PR does not perform. -->

## Merge Checklist

- [ ] One Work ID only.
- [ ] No unauthorized file changes or unrelated formatting.
- [ ] strict XFAIL was removed only after the target assertion passed.
- [ ] Required CI is green.
- [ ] PR targets `develop` unless this is an authorized G3-passed Release PR to `master`.
- [ ] No Tag, GitHub Release or package was published without an authorized Release Work ID.
