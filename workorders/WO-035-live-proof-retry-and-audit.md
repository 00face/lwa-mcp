# WO-035 - Live Proof Retry and Audit

**Status:** Queued
**Priority:** P0
**Parent:** WO-032 through WO-034
**Task rite:** [TR-035](../task-rites/TR-035-live-proof-retry-and-audit.md)

## Objective

Re-run the two-session near-zero proof only after telemetry, Zai quota, and
catalog discovery gates pass, then issue the final mechanical audit result.

## Required Tests

- Two identical fixture manifests and prompt hashes.
- Complete reported telemetry for both sessions.
- Fresh matching Zai quota at start and end.
- Zero repeated catalog discovery on the warm run.
- Quality within one point, zero duplicate execution, safety rollback pass.

## Promotion Gate

WO-030 returns `ten_of_ten=true`; 11/10 additionally requires independent
reproduction and safe predictive reuse.

## Rollback

Abort before provider completion on any failed prerequisite and publish the
specific failed gate.
