# WO-033 - Zai Authoritative Quota Capture

**Status:** Partial — Zai-scope verifier and pipeline quality report implemented; fresh authoritative Zai input remains unavailable.
**Priority:** P0
**Parent:** WO-032
**Task rite:** [TR-033](../task-rites/TR-033-zai-authoritative-quota-capture.md)

## Objective

Capture a fresh authoritative token quota snapshot for the exact locked Zai
provider/account, including capture time and reset window.

## Required Tests

- Provider and account scope match the locked proof route.
- Snapshot is token-denominated, authoritative, fresh, and not nominal.
- Reset window is unexpired and independently recomputable.
- Credentials never enter the snapshot or exported proof bundle.

## Promotion Gate

WO-027 reconciliation returns valid for the Zai snapshot at proof start and
end, with a reproducible `<0.1%` overhead calculation.

## Rollback

Mark `denominator_unavailable`; do not use stale snapshots or another
provider's quota as a substitute.

## Run Evidence (2026-08-08)

- Added `scripts/verify_zai_quota.py`, which rejects non-Zai providers and
  account-scope mismatches before quota reconciliation.
- Added [PIPELINE_QUALITY_2026-08-08](../reports/PIPELINE_QUALITY_2026-08-08.md)
  covering all 12 canonical pipelines.
- Added [PROVIDER_SERVICE_QUALITY_2026-08-08](../reports/PROVIDER_SERVICE_QUALITY_2026-08-08.md)
  covering all 19 configured provider services, including Gemini and Puter.
- Pipeline report mean: `7.9/10`; measured offline pipelines rate `8.5/10`,
  provisional contract/test-only pipelines range `7.0-7.5/10`.
- Full verification: `121 passed`; Ruff clean.
- No live Zai snapshot was available; no quota proof claim is made.
