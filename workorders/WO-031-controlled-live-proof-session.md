# WO-031 - Controlled Live Proof Session

**Status:** Blocked — proof prerequisites are unavailable; no completion call was made.
**Priority:** P0
**Parent:** WO-030
**Task rite:** [TR-031](../task-rites/TR-031-controlled-live-proof-session.md)

## Objective

Execute two approved free-route golden runs only when complete telemetry and an
authoritative, fresh quota snapshot are available for the same provider/account.

## Preflight Evidence (2026-08-08)

- Locked route: `zai/glm-4.7-flash`, `free_quota`, paid and user-pays disabled.
- Telemetry health: `38` total calls, `0` reported, `38` unreported, `38`
  unattributed, `10/10 ready=false`.
- Available quota snapshots are stale records from 2026-07-25 and do not cover
  the locked Zai route/account.
- Provider catalog doctor showed configured free providers, but catalog refresh
  is not quota proof and cannot substitute for a fresh authoritative snapshot.
- The doctor path performed `1,720` live catalog refreshes while reporting
  `1,731` models; these were discovery calls, not completions, but are material
  control-plane overhead and must be excluded from a near-zero proof run.
- Result: aborted before provider completion; no live proof claim made.

## Promotion Gate

Run twice only after WO-026 export validates complete reported attribution and
WO-027 validates a fresh authoritative quota snapshot for the selected route.

## Rollback

Do not run. Preserve the invalid evidence and return to offline validation.
