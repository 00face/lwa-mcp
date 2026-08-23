# WO-024E - 10/10 and 11/10 Efficiency Audit

**Status:** Partial — final audit and ratings are recorded; independent live evidence is still required for 10/10.  
**Priority:** P1  
**Parent:** WO-024A through WO-024D  
**Task rite:** [TR-024E](../task-rites/TR-024E-ten-eleven-rating.md)

## Objective

Re-rate Lwa MCP and the LWA Plugin after measured implementation work, and
separate a defensible 10/10 release bar from an evidence-gated 11/10 stretch.

## 10/10 bar

- Complete attribution with no unexplained `not_reported` events.
- Zero duplicate provider executions in the golden benchmark.
- Warm handshake/cache behavior is deterministic and fail-closed.
- Compact mode preserves schema, constraints, safety, and quality.
- Quality remains within 1 point of baseline.
- Quota overhead and redundant-call denominators are published.

## 11/10 stretch bar

- 10/10 is sustained across two independent benchmark runs.
- `<0.1%` redundant control-plane calls after warm-up is measured.
- `<0.1%` quota overhead is measured against a declared provider quota.
- Predictive caching or result reuse improves p95 latency without stale or
  incorrect answers.
- Every optimization has an observed rollback path and no safety exception.

## Acceptance

- [ ] Independent evidence review signs off the scores.
- [x] 10/10 is not awarded on architecture or offline evidence alone.
- [x] 11/10 is reported as a stretch target, not a default promise.

## Audit Result (2026-08-08)

- **Lwa MCP:** `9.0/10` — governed lifecycle, attribution fields, compact
  responses, duplicate-work regression, and offline quality benchmark verified.
- **LWA Plugin workflow:** `8.0/10` — cached handshake tooling and workflow
  records exist, but live handshake startup and host-owned telemetry are not
  independently verified.
- **Combined operational rating:** `8.5/10`.
- **10/10:** not awarded. Historical `not_reported` telemetry, live handshake
  timeout, and browser smoke limitations remain open evidence gaps.
- **11/10:** not achieved. Predictive result reuse with stale-answer safeguards
  and two independent live benchmark runs are not proven.
