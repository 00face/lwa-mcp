# WO-029 - Safety and Rollback Fault Injection

**Status:** Partial — executable fault gates pass offline; live fault injection remains required.
**Priority:** P1
**Parent:** WO-028
**Task rite:** [TR-029](../task-rites/TR-029-safety-rollback-fault-injection.md)

## Objective

Demonstrate that near-zero usage optimizations fail safely under provider,
quota, cache, timeout, stale-result, and telemetry failures.

## Required Evidence

- No dynamic rerouting after work begins.
- Stale or mismatched cache fails closed.
- Missing usage or quota data invalidates proof rather than passing.
- Failed execution requires repreflight and cannot silently retry provider work.
- Rollback restores standard response detail and disables result reuse.

## Promotion Gate

All injected failures produce bounded, attributed outcomes with zero hidden
provider executions and a reversible operator action.

## Rollback

Disable compact mode, cache reuse, and live proof automation while preserving
telemetry and failure records.

## Run Evidence (2026-08-08)

- Added `src/lwa_mcp/safety.py` and `scripts/validate_safety_faults.py`.
- Six scenarios pass: provider failure, stale cache, missing quota, missing
  usage, duplicate execution, and rollback.
- Reported provider calls are bounded to the injected provider-failure case;
  no hidden reroute or duplicate execution is permitted.
- Full offline verification: `111 passed`; Ruff clean.
