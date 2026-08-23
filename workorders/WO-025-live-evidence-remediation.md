# WO-025 - Live Evidence Remediation

**Status:** Partial — offline evidence quality improved; live handshake and
historical unreported usage remain open.
**Priority:** P1
**Parent:** WO-024E
**Task rite:** [TR-025](../task-rites/TR-025-live-evidence-remediation.md)

## Objective

Close the evidence gaps preventing the Lwa MCP / LWA Plugin workflow from
reaching the 10/10 release bar without weakening fail-closed behavior.

## Delivered

- Added `telemetry_health` with usage-reporting, attribution, and 10/10 gate
  status to the persistent dashboard summary.
- Added elapsed time and `provider_calls: 0` to bounded handshake failures.
- Added offline regression coverage for unreported usage and timeout reporting.

## Evidence (2026-08-08)

- Focused tests: `6 passed`.
- Ruff and Python compilation passed for touched files.
- No provider calls were made by the handshake timeout test.

## Remaining Gates

- Re-run the live MCP handshake successfully in a non-crashing environment.
- Eliminate or explain historical `not_reported` records with real usage data.
- Re-run the host/plugin smoke path and independently review the resulting
  attribution report.

## Score Impact

Evidence quality improves the combined operational score from `8.5/10` to
`8.7/10`; 10/10 remains blocked until the remaining live gates pass.
