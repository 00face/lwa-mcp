# TR-025 - Live Evidence Remediation Rite

**Entry:** WO-024E identified historical unreported telemetry and live
handshake timeout as the remaining 10/10 blockers.
**Action:** Expose explicit telemetry health and bounded handshake failure
metadata; test both offline.
**Check:** Confirm no prompt/secret leakage, no provider calls, fail-closed
cache behavior, and deterministic failure evidence.
**Promote when:** live handshake succeeds and all subsequent calls are
attributed with reported usage.
**Rollback:** retain the prior telemetry fields and fail-closed handshake
behavior; do not suppress failure records.

**Run evidence (2026-08-08):** offline checks passed; promotion remains
blocked by the live environment.
