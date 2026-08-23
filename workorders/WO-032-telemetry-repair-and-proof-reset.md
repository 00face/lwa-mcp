# WO-032 - Telemetry Repair and Proof Reset

**Status:** Partial — proof-boundary verifier implemented; fresh reported sessions remain required.
**Priority:** P0
**Parent:** WO-031
**Task rite:** [TR-032](../task-rites/TR-032-telemetry-repair-and-proof-reset.md)

## Objective

Resolve or quarantine the `38` unreported/unattributed records and start a
fresh proof session with complete IDs and reported usage.

## Required Tests

- Export validates every new record with session, call, parent, tool, and phase.
- Provider usage is reported or the run is invalid.
- Historical invalid rows are retained and excluded from proof denominators.
- No prompt, secret, raw usage payload, or credential is backfilled.

## Promotion Gate

Two consecutive proof sessions export valid records with zero unreported and
zero unattributed calls.

## Rollback

Keep invalid rows quarantined; block proof and restore offline-only mode.

## Run Evidence (2026-08-08)

- Added `src/lwa_mcp/proof_telemetry.py` and
  `scripts/verify_telemetry_proof.py`.
- Invalid records are partitioned into an explicit quarantine output and are
  never deleted or silently excluded.
- The active configured ledger produced `2` records, `2` quarantined, and
  `proof_valid=false`; the prior broader ledger observation recorded `38`
  invalid calls.
- Full offline verification: `120 passed`; Ruff clean.
