# TR-029 - Safety and Rollback Fault Injection Rite

**Entry:** WO-028 has a captured live benchmark candidate.
**Action:** Inject timeout, stale cache, quota-missing, usage-missing, and
provider-failure conditions.
**Check:** Confirm fail-closed behavior, repreflight boundaries, attribution,
and rollback effectiveness.
**Promote when:** every fault has deterministic evidence and no hidden call.
**Rollback:** return to standard responses and offline-only verification.

**Run evidence (2026-08-08):** six-scenario offline fault report passes;
live promotion remains blocked until WO-028 supplies real run evidence.
