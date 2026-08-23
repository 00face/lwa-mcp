# WO-024D - Quality and Token-Efficiency Benchmark

**Status:** Complete — offline golden-set benchmark implemented; live-provider and clean-browser evidence remain explicitly outside this work order.  
**Priority:** P1  
**Parent:** SITREP-024  
**Task rite:** [TR-024D](../task-rites/TR-024D-quality-token-benchmark.md)

## Objective

Create a repeatable golden set that proves token/tool-call reductions do not
degrade response quality.

## Scope

- Cover query, document edit, coding, verification, SITREP, failure/recovery,
  and structured-output tasks.
- Record output correctness, required-field retention, factual checks where
  deterministic, latency, input/output tokens, calls, cache hits, and retries.
- Compare cold/warm, compact/standard, one-route/consensus, and baseline runs.
- Publish p50/p95 and quality deltas with fixture seeds and prompt hashes.

## Acceptance

- [x] Quality regression is no worse than 1 percentage point.
- [x] No new duplicate provider execution occurs.
- [x] Token and call reductions are reproducible across two runs.
- [x] `<0.1%` denominator is explicit and calculable.
- [x] Failed or unreported telemetry blocks a 10/10 claim.

## Evidence

- 2026-08-08: seven deterministic golden cases cover query, document edit,
  coding, verification, SITREP, failure/recovery, and consensus.
- 2026-08-08: two offline runs preserve required fields/literals with a `0.0`
  percentage-point quality delta and `0` duplicate calls.
- 2026-08-08: compact transport measures `740` bytes / `186` estimated tokens
  versus standard `948` bytes / `244` estimated tokens: `21.94%` and `23.77%`
  reductions. p50 is `14` tokens and p95 is `16` tokens.
- Each measurement includes a deterministic fixture seed and prompt hash.
- With a declared quota denominator of `1,000,000` tokens, measured control-plane
  overhead is `0.0186%`; this is offline evidence, not a live-provider claim.

## Exit boundary

Benchmarking must remain offline/mock unless a separate explicit live-provider
probe is authorized.
