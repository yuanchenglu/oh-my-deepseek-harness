# BETA-002 Evidence - Beta Validation Framework

- Work ID: `BETA-002`
- Canonical Issue: #52
- Dependency: BETA-001 complete
- Status: **Complete (framework); data collection during 14-day Beta window**
- Next serial: G4 Gate (after BETA-002+BETA-003+REL-007 data)

## 1. Deliverables

- `docs/beta/METRICS_SCHEMA.md`: operational definitions (§9.1), min sample +
  thresholds (§9.2), 95% Wilson formula, dedup rules, privacy constraints (§9.3).
- `docs/beta/VALIDATION_LOG.csv`: raw de-identified opt-in rows (header only).
- `docs/beta/VALIDATION_REPORT.md`: honest 0/N state — no evidence yet.

## 2. Verification

- test_sec.py: schema/log/report exist + Wilson interval computable
  (x=18,n=20 straddles 0.90) — 11 passed total.

## 3. Honest residual

Real external validation data requires non-maintainer validators during the
14-day calendar observation window. No fabricated metrics.
