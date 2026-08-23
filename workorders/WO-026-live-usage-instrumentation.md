# WO-026 - Live Usage Instrumentation

**Status:** Partial — redacted export and validation are implemented; two valid live sessions remain required.
**Priority:** P0
**Parent:** WO-025
**Task rite:** [TR-026](../task-rites/TR-026-live-usage-instrumentation.md)

## Objective

Capture complete, per-call live usage evidence for MCP, plugin/host, and
provider execution without persisting prompts, secrets, or raw provider data.

## Required Evidence

- Every call has `session_id`, `parent_call_id`, `call_id`, tool, phase, status,
  latency, and usage status.
- Reported input/output tokens are distinguishable from `not_reported`.
- Missing attribution fails closed as an evidence error, never as zero usage.
- A redacted JSON export supports independent review.

## Promotion Gate

Two consecutive sessions achieve 100% attribution and 100% usage reporting for
all calls included in the proof set.

## Rollback

Disable export/reporting only; retain database rows and fail-closed health flags.

## Run Evidence (2026-08-08)

- Additive `call_id` persistence was added to requests, route events, and
  preflight events; existing databases migrate without destructive changes.
- Redacted export and validator tests pass, including rejection of missing
  attribution and sensitive fields.
- Focused verification: `16 passed`; Ruff and compilation passed.
- Empty-ledger export is valid, but historical live records remain invalid until
  new calls populate complete reported attribution.
