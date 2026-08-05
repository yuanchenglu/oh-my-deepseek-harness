# Beta Metrics Schema (BETA-002)

Sources of truth: OPEN_SOURCE_RELEASE_PLAN_2.2.md §9.1–9.3 (operational
definitions, minimum sample, thresholds, privacy constraints).

## 1. Operational definitions (summary)

| Metric | Definition |
|---|---|
| Independent install attempt | clean env + immutable Beta artifact → install + Doctor + ≥1 Tool smoke + normal uninstall; retries in same env don't add to denominator |
| Install success | all four steps above succeed, no maintainer direct env modification |
| Docs self-service success | user completes install using only public docs; no maintainer remote operation |
| Long session | ≥20 user/assistant turns OR ≥10 legal Tool calls, with ≥1 Context compression attempt |
| Legal Tool call | input satisfies registered Schema and Server ready; 5xx/timeout/invalid envelope = product failure; schema reject + user cancel reported separately |
| Data corruption | missing/duplicate/out-of-order messages, broken Tool pairs, wrong Memory writes, unrecoverable migration |

## 2. Minimum sample & thresholds

| Metric | Min sample | Gate |
|---|---:|---|
| External validators | 10 non-maintainers | covers Linux/macOS + supported Python |
| Independent install attempts | 20 | success ≥ 90%; report 95% Wilson interval |
| Docs self-service installs | 10 people | success ≥ 80% |
| Long sessions | 50 | 0 confirmed corruption / cross-session contamination |
| Legal Tool calls | 200 | overall ≥ 95%; each Tool ≥ 10 calls and ≥ 90% |
| Context compression attempts | 50 | every attempt passes integrity check or full rollback |

## 3. Wilson interval (95%)

For observed success `p̂ = x/n`, 95% Wilson lower/upper bound:

```text
z = 1.96
denom = 1 + z²/n
center = (p̂ + z²/(2n)) / denom
half = z * sqrt(p̂(1−p̂)/n + z²/(4n²)) / denom
lower = center − half
upper = center + half
```

Recomputable from raw x (numerator) and n (denominator) in VALIDATION_LOG.csv.

## 4. Deduplication rules

- Same environment repeated retry of install → count once (first attempt only).
- Same validator multiple sessions → each long session counts separately; each
  validator counts once in "external validators".
- Same Tool call logged twice → dedupe by (session_id, timestamp, tool, result).

## 5. Privacy constraints

- No telemetry upload by default.
- Never collect: Prompt text, full Tool arguments, full Tool results, secrets,
  user files.
- Only user-submitted opt-in structured diagnostics; support preview + re-redaction.
- Every metric keeps numerator, denominator, environment, failure class — not
  just a percentage.

## 6. Files

- `docs/beta/VALIDATION_LOG.csv` — raw de-identified rows (opt-in only).
- `docs/beta/VALIDATION_REPORT.md` — computed metrics, Wilson intervals, links to raw counts.
