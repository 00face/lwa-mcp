# TR-042 - Bounded Zero-Payload Probe Cache Rite

**Entry:** WO-041 probes are safe but currently repeatable on every check.
**Action:** Add a redacted fingerprinted cache, bounded TTLs, invalidation, and
single-flight coalescing.
**Check:** Cold probe calls once; warm probe calls zero times; stale/configured
changes re-probe exactly once; no prompt enters cache keys or values.
**Promote when:** provider-class fixtures prove bounded network behavior and
telemetry distinguishes cache work from provider work.
**Rollback:** bypass cache reads while preserving probe timeouts and limits.
