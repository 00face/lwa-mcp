# TR-032 - Telemetry Repair and Proof Reset Rite

**Entry:** WO-031 found `38` invalid historical calls.
**Action:** Repair attribution at the source, quarantine legacy invalid rows,
and create a clean proof-session boundary.
**Check:** Validate redacted export and prove no sensitive backfill occurred.
**Promote when:** two fresh sessions have complete reported telemetry.
**Rollback:** preserve the invalid ledger and fail the proof gate.

**Run evidence (2026-08-08):** verifier promoted for quarantine accounting;
fresh proof-session promotion remains blocked by invalid active records.
