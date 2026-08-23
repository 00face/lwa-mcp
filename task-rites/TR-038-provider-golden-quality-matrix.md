# TR-038 - Provider Golden Quality Matrix Rite

**Entry:** Adapter and quota evidence are valid for a service.
**Action:** Execute its fixed task fixtures twice with stable prompt hashes and
record quality, tokens, calls, retries, latency, and billing.
**Check:** Compare against the canonical baseline and reject regressions.
**Promote when:** both runs pass all quality and telemetry gates.
**Rollback:** return to the prior provider route and mark the service below 10.
