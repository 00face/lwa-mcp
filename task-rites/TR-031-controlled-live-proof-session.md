# TR-031 - Controlled Live Proof Session Rite

**Entry:** WO-030 audit is blocked by telemetry and quota evidence.
**Action:** Lock one free route, capture prerequisites, run the golden set twice,
export telemetry, capture quota, and validate the bundle.
**Check:** Abort before completion if usage is unreported, IDs are missing,
quota is stale/mismatched, or billing is not free/free-quota.
**Promote when:** both runs pass WO-028 and WO-030 without paid/user-pays use.
**Rollback:** no provider execution; retain the blocked evidence bundle.

**Run evidence (2026-08-08):** aborted at prerequisite check. No proof run was
started because telemetry and quota gates failed.
