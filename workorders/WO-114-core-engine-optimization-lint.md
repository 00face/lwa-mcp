# WO-114 — Core-engine optimization lint

## Hypothesis

We believe focused static analysis and complexity checks on the terminal,
session, panel, renderer, and pipeline engines will expose avoidable hot-path
work before runtime tuning; confidence requires clean lint plus a reviewed
report for every high-complexity or allocation-heavy path.

## Scope

- Lint `terminal_frame`, `launch`, `codex_session`, panel contracts,
  `terminal_protocol`, `image_compositor`, `pet_renderer`, and pipeline engines.
- Identify repeated wrapping, full-buffer copies, synchronous subprocess calls,
  redundant redraws, and exception-heavy hot paths.
- Split functions that combine input, rendering, transport, and lifecycle work.
- Add targeted microbenchmarks for redraw, wrapping, prompt editing, and PTY
  chunk ingestion.
- Preserve behavior and privacy guarantees while optimizing.

## Acceptance gates

- Ruff and project lint pass with no new suppressions without rationale.
- Hot-path findings have either a measured fix or a documented reason to defer.
- Focused benchmarks do not regress beyond the declared budget.
- Full tests pass after each engine change.

