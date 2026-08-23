# TR-036 - Provider Adapter Contract Hardening Rite

**Entry:** Provider matrix shows mixed adapter evidence and missing usage proof.
**Action:** Add per-adapter contract fixtures and common usage/error assertions.
**Check:** Run all 19 services offline without credentials or network calls.
**Current result:** partial promotion. Usage reporting is explicit, unknown
usage no longer counts as reported, malformed JSON and timeouts normalize to
`ProviderError`, and all 19 configured adapters construct offline.
**Promote when:** every service passes the complete common adapter contract
fixture matrix.
**Rollback:** disable the failing service; do not weaken the common contract.
