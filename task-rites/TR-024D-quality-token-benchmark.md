# TR-024D - Quality/Token Benchmark Rite

**Entry:** WO-024A through WO-024C are implemented or explicitly partial with
known limits.  
**Action:** Run the golden set across cold/warm, compact/standard, ordinary
route, verification, and consensus cases.  
**Check:** Record prompt hashes, tokens, calls, retries, latency, schema
validity, and quality outcomes for two runs.  
**Promote when:** quality delta is within 1 point, no duplicate provider
 execution exists, and the target denominator is published.  
**Rollback:** reject the optimization variant; retain baseline route behavior.

**Run evidence (2026-08-08):** promoted. The offline benchmark records two
deterministic runs, seven cases, prompt hashes, fixture seeds, p50/p95 token
estimates, quality checks, and explicit quota/redundant-call denominators.
