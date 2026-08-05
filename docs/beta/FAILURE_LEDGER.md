# Beta Failure Ledger (BETA-003)

- Work ID: `BETA-003`
- Status: **In progress — 0 failures recorded** (honest: Beta observation window open)
- Release under observation: `v3.0.0-beta.1`
- Started: 2026-08-04 (v3.0.0-beta.1 published)

## 1. Rules

- Every Beta failure gets a row: environment, reproduction, severity,
  root-cause class, owner, next action.
- Every code-requiring failure gets a separate Work ID / GitHub Issue.
- P0 pauses promotion immediately; affected Gates rerun; replacement release
  increments the prerelease number.
- Failure records are redacted: no private advisory details, prompts, secrets,
  or user files in public Issues.
- Never erase a real failure to improve metrics; corrections get an audit note.

## 2. Severity / waiver policy

| Severity | Action |
|---|---|
| P0 / Critical | Pause promotion; containment + rerun affected Gates; block next Gate until verified |
| P1 / High | Fix or explicit time-bounded waiver; Stable cannot carry open P1 |
| P2 / Medium | Track with owner, test, target milestone |
| P3 / Low | Track when actionable |

## 3. Ledger

| ID | Date | Environment | Severity | Root-cause class | Owner | Next action | Status |
|---|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — | — |

## 4. Orphan checks

- No open row is unclassified, unowned, or without a next action.
- Every code-requiring failure links to its Issue.

## 5. Honest status

Zero failures recorded as of 2026-08-04. Zero rows mean no Beta failures
reported yet — not a claim of zero defects. All future rows must be added
here with environment, reproduction, severity, class, owner and next action,
redacted per §1.
