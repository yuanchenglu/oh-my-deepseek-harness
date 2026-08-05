# Rollback Guide (REL-007)

How to withdraw a bad Beta and roll back users to the prior working version
without touching published tags/artifacts. Verified by a non-maintainer drill.

## 1. Principles

- Never move/overwrite/delete a published tag or GitHub Release.
- A bad Beta is replaced by a **new prerelease** (incremented number), not by
  editing the old one.
- User data is preserved: rollback restores the previous deployment + backup,
  never destroys user data.

## 2. Steps

1. **Stop promotion.** Pause any further release work; record the incident
   in `docs/beta/FAILURE_LEDGER.md` with severity P0/P1 and next action.
2. **Notify users.** Publish a notice on the Release page + Issues: affected
   version, severity, recommended action. No private details.
3. **User rollback** (each user, from published docs only):
   - `deepseek-harness doctor` to confirm current state.
   - Install the previous known-good release:
     `pip install oh-my-deepseek-harness==<previous-version>`
     or reinstall from the previous GitHub Release wheel.
   - `deepseek-harness upgrade --dry-run` to preview, then `upgrade` (backup +
     migrate + rollback-on-failure built in).
   - Verify `deepseek-harness doctor` green + `deepseek-harness server status`.
4. **Preserve evidence.** Keep install logs, doctor output, before/after data
   inventories. Never erase a real failure.

## 3. Timeline template (drill)

| Step | Expected | Actual | By |
|---|---|---|---|
| Detect bad Beta | — | — | — |
| Pause promotion | ≤1 day | — | — |
| User notification | ≤1 day | — | — |
| Rollback drill (non-maintainer) | ≤1 day | — | — |
| Data inventory before/after | identical | — | — |
| New prerelease decision | per plan | — | — |

## 4. Data preservation

- `upgrade` already creates a backup (`backups/upgrade-<txid>/`) and restores
  it on failure (MIG-001).
- Rollback must restore Config/DB/events/process from the tested backup.
- Incomplete rollback is P0: output manual recovery instructions.

## 5. Drill (REL-007)

`scripts/release/rollback_drill.sh` runs the drill in a disposable environment:
install current → install previous → upgrade → verify doctor green + data intact.

**Honest status:** drill script is provided; a real non-maintainer execution
requires the Beta observation window. The drill result will be recorded here.
