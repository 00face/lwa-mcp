# TR-024A - Telemetry Attribution Rite

**Entry:** WO-024A is queued; current ledger and redaction tests are green.  
**Action:** Add correlation fields, event phases, compact counters, fixtures,
and unreported-usage detection.  
**Check:** Run focused DB/service/dashboard tests and inspect redacted rows.  
**Promote when:** every event is attributable and quota/call SLOs calculate
without treating missing usage as zero.  
**Rollback:** disable new fields at the serialization boundary; preserve old
ledger columns and prompt hashes.

**Result - 2026-08-08:** Complete. SQLite migration, correlation IDs,
whitelisted metadata, `reported`/`not_reported` accounting, dashboard counters,
and redaction tests are implemented. Focused verification passed: `22 passed`.
