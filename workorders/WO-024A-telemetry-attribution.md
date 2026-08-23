# WO-024A - Per-Session Telemetry Attribution

**Status:** Complete  
**Priority:** P0  
**Parent:** SITREP-024  
**Task rite:** [TR-024A](../task-rites/TR-024A-telemetry-attribution.md)

## Objective

Make every MCP/plugin and provider event measurable so usage percentages are
based on attributed evidence rather than missing data being treated as zero.

## Scope

- Add session, parent-call, tool, phase, cache, duplicate, token, cost, and
  latency fields to the local telemetry path.
- Distinguish preflight, approval, execution, synthesis, host display, and
  failure events.
- Expose compact dashboard/CLI counters for calls per answer, token overhead,
  duplicate calls, cache hits, and `not_reported` events.
- Preserve prompt hashes and secret redaction; never persist raw prompts,
  credentials, or provider payloads.

## Acceptance

- [x] Every preflight, route, and result event has session/call attribution.
- [x] `not_reported` is visible and never counted as reported usage.
- [x] Existing ledger and redaction tests remain green.
- [x] A fixture calculates total/reported/unreported tokens, cache hits, and redundant calls.
- [x] No provider behavior or consent boundary changes.

## Exit boundary

Telemetry only. No routing-policy change, provider enablement, credential
mutation, paid completion, or global MCP registration change is authorized.

## Evidence - 2026-08-08

- Added additive SQLite columns with migration support for existing databases.
- Added whitelisted session, parent-call, tool, phase, cache, duplicate, and
  usage-status fields.
- Added `dashboard_summary()["telemetry"]` counters.
- Added a redaction regression proving prompt bodies and arbitrary metadata do
  not enter the summary.
- Focused verification: `22 passed`; targeted Ruff and Python compilation pass.
