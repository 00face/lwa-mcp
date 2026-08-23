# TR-024C - Compact Control-Plane Rite

**Entry:** WO-024A telemetry can compare calls, bytes, tokens, and quality.  
**Action:** Add response detail modes, compact JSON, and single-evaluation
  library suggestions. Defer manifest deltas and catalog caching to the
  benchmark work order.  
**Check:** Compare schema snapshots and byte lengths in compact, standard, and
  debug modes; exercise one complete lifecycle.  
**Promote when:** semantic equivalence holds, duplicate suggestion work is
  gone, and measured overhead falls without quality regression.  
**Rollback:** set `LWA_MCP_RESPONSE_DETAIL=standard` while retaining the
  lifecycle and telemetry changes.

**Run evidence (2026-08-08):** targeted checks passed; full suite recorded 96
passes and 3 pre-existing Firefox screenshot failures in this sandbox.
