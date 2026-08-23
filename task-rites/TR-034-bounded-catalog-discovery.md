# TR-034 - Bounded Catalog Discovery Rite

**Entry:** doctor performed `1,720` live catalog refreshes.
**Action:** Gate provider catalog access with the reviewed handshake guard and
separate discovery telemetry from completion telemetry.
**Check:** Test cache hit, stale cache, scope mismatch, and invalid cache.
**Promote when:** warm proof runs show zero repeated discovery calls.
**Rollback:** disable cache reads but retain explicit scope and call counts.
