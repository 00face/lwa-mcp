# TR-033 - Zai Authoritative Quota Capture Rite

**Entry:** The locked proof route is Zai, but no fresh matching snapshot exists.
**Action:** Capture and redact the provider/account quota evidence.
**Check:** Validate scope, units, freshness, reset time, and secret exclusion.
**Promote when:** WO-027 independently recomputes the same denominator.
**Rollback:** block all near-zero claims and retain the failure reason.

**Run evidence (2026-08-08):** Zai-scope verifier promoted; live promotion is
blocked until a fresh authoritative Zai/account snapshot is supplied.
