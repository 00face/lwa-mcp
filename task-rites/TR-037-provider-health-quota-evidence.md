# TR-037 - Provider Health and Quota Evidence Rite

**Entry:** WO-036 proves adapter behavior.
**Action:** Collect redacted health, account scope, quota, reset, and billing
evidence per service.
**Check:** Reject stale, nominal, mismatched, or secret-bearing snapshots.
**Promote when:** each service has independently recomputable evidence.
**Rollback:** keep the service out of proof and preserve the failure reason.
