# WO-027 - Quota Denominator Reconciliation

**Status:** Partial — fail-closed reconciliation is implemented; authoritative live provider snapshots remain required.
**Priority:** P0
**Parent:** WO-026
**Task rite:** [TR-027](../task-rites/TR-027-quota-denominator-reconciliation.md)

## Objective

Prove the denominator used for `<0.1%` quota overhead is authoritative,
time-bounded, and matched to the provider/account actually used.

## Required Evidence

- Provider/account identity is recorded without credentials.
- Available quota and unit are captured from an authoritative provider signal
  or explicitly marked unavailable.
- Numerator includes all control-plane tokens and excludes necessary answer
  content by a documented rule.
- Clock window, reset policy, and rounding are recorded.

## Promotion Gate

An independent reviewer can recompute quota overhead from exported records and
obtain the same result without guessing the denominator.

## Rollback

Reject the run and publish `denominator_unavailable`; never substitute a
nominal quota or cached stale quota silently.

## Run Evidence (2026-08-08)

- Added `src/lwa_mcp/quota.py` and `scripts/reconcile_quota.py`.
- Validates provider/account scope, token units, authoritative source,
  capture age, reset window, and nonnegative control-plane numerator.
- Mock proof example: `186 / 1,000,000 = 0.0186%`.
- Invalid, stale, nominal, missing, and wrong-unit snapshots fail closed.
- Full offline verification: `105 passed`; Ruff clean.
- The mock example is not live quota proof.
