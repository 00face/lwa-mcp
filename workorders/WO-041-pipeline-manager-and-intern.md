# WO-041 - Pipeline Manager and Data-Free Pipeline Intern

**Status:** Partial — manager, MCP tools, execution gate, and offline tests are
implemented; provider-specific probe policies and persistent marks remain.
**Priority:** P0
**Parent:** WO-039, WO-040
**Task rite:** [TR-041](../task-rites/TR-041-pipeline-manager-and-intern.md)

## Objective

Track per-provider pipeline state and check basic accessibility before any
user prompt or task payload is sent to a provider.

## Contract

- `pipeline_status` defaults to a local-only check.
- `pipeline_status(probe=true)` may call only the adapter health/model-metadata
  endpoint; it never creates a `RouteRequest` or forwards user data.
- Execution blocks disabled providers, missing credentials, missing endpoints,
  known unhealthy providers, and unknown providers.
- `mark_pipeline` records operator state without exposing credentials or prompt
  content.
- A probe is zero-payload and no-cost with respect to provider completion;
  provider billing/quota policies still require independent proof.

## Remaining Work

- [WO-042](WO-042-bounded-probe-cache.md): cache probes with bounded TTL and
  explicit invalidation.
- [WO-043](WO-043-persistent-pipeline-marks.md): persist operator marks in the
  local ledger.
- [WO-044](WO-044-provider-probe-fixture-matrix.md): add provider-specific
  endpoint policy fixtures for all 19 services.
