# TR-027 - Quota Denominator Reconciliation Rite

**Entry:** WO-026 supplies complete live usage records.
**Action:** Capture and reconcile provider quota, account scope, time window,
and control-plane numerator.
**Check:** Recompute the percentage independently and test stale/missing quota
failure paths.
**Promote when:** the denominator is authoritative and reproducible.
**Rollback:** mark quota proof conditional and block the 10/10 claim.

**Run evidence (2026-08-08):** offline reconciler promoted; live promotion is
blocked until an authoritative provider/account snapshot is captured.
