# TR-044 - Provider-Specific Probe Fixture Matrix Rite

**Entry:** WO-041 has generic manager tests but not provider-specific proof.
**Action:** Build deterministic offline fixtures for all 19 configured services
and their adapter families.
**Check:** Run with credentials absent and network disabled; assert no prompt,
completion endpoint, paid route, or user-pays route is invoked.
**Promote when:** 19/19 fixtures pass with explicit status, billing, timeout,
redaction, and call-count evidence.
**Rollback:** mark only the failing provider conditional and preserve its
failure artifact.
