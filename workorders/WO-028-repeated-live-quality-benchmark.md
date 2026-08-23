# WO-028 - Repeated Live Quality Benchmark

**Status:** Partial — repeated-run validator is implemented; approved live runs remain required.
**Priority:** P1
**Parent:** WO-026, WO-027
**Task rite:** [TR-028](../task-rites/TR-028-repeated-live-quality-benchmark.md)

## Objective

Run the golden set through the real approved route twice, comparing baseline
and compact control-plane variants without lowering quality or bypassing gates.

## Required Evidence

- Same fixture seeds, prompt hashes, required fields, and literals as WO-024D.
- Reported provider input/output tokens, tool calls, retries, cache hits, and
  p50/p95 latency for every run.
- Quality delta remains within one percentage point.
- No duplicate provider execution or unapproved paid route occurs.

## Promotion Gate

Both runs satisfy quality, attribution, and safety gates; compact overhead is
measured against the reconciled quota denominator.

## Rollback

Use standard responses and disable optimization for failed cases; retain the
failed evidence for diagnosis.

## Run Evidence (2026-08-08)

- Added `src/lwa_mcp/live_benchmark.py` and
  `scripts/validate_live_benchmark.py`.
- Validator requires exactly two runs, matching fixture seeds/prompt hashes,
  quality delta within one point, complete reported telemetry, valid quota,
  zero duplicate provider executions, free billing classes, and latency/token
  metrics.
- Offline fixtures are explicitly rejected as live proof unless the operator
  selects fixture mode.
- Full offline verification: `108 passed`; Ruff clean.
