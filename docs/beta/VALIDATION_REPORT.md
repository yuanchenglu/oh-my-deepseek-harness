# Beta Validation Report (BETA-002)

- Work ID: `BETA-002`
- Status: **In progress — 0/N collected** (honest: real external data pending)
- Release under validation: `v3.0.0-beta.1`
- Schema: `docs/beta/METRICS_SCHEMA.md`
- Raw log: `docs/beta/VALIDATION_LOG.csv`

## 1. Sample status (as of 2026-08-04)

| Metric | Min sample | Collected | Success | 95% Wilson | Gate met |
|---|---:|---:|---:|---|---|
| External validators | 10 | 0 | — | — | No |
| Independent install attempts | 20 | 0 | — | — | No |
| Docs self-service installs | 10 | 0 | — | — | No |
| Long sessions | 50 | 0 | — | — | No |
| Legal Tool calls | 200 | 0 | — | — | No |
| Context compression attempts | 50 | 0 | — | — | No |

## 2. Honest status

No external validator data has been collected yet. The Beta artifact
(v3.0.0-beta.1) is published and installable, but the 14-day calendar
observation period is the collection window. **Zero rows do not mean success
or failure — they mean no evidence yet.** Per plan §9.3 privacy constraints,
no telemetry is uploaded by default; collection is opt-in structured
diagnostics only.

## 3. Computation notes

- Wilson intervals recompute from raw (x, n) in VALIDATION_LOG.csv per
  METRICS_SCHEMA §3.
- No percentage-only rows: every metric keeps numerator, denominator,
  environment, failure class.

## 4. Next steps

1. Recruit 10 non-maintainer validators (Linux/macOS × Python 3.11/3.12).
2. Log every opt-in install/session/Tool-call/compression row.
3. Recompute metrics + Wilson intervals at G4.
