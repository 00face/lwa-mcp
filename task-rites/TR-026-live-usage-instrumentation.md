# TR-026 - Live Usage Instrumentation Rite

**Entry:** WO-025 exposes telemetry health but the current ledger has
unreported and unattributed calls.
**Action:** Instrument the live proof harness and export redacted call records.
**Check:** Verify IDs, phases, usage status, prompt-hash-only persistence, and
no secrets/raw prompts.
**Promote when:** two sessions have complete attribution and reported usage.
**Rollback:** preserve raw ledger rows and mark the proof run invalid.

**Run evidence (2026-08-08):** promoted for offline instrumentation. Live proof
promotion remains blocked until two sessions export valid reported records.
