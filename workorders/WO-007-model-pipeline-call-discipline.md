# WO-007: Model and Pipeline Call Discipline

Status: partial
Priority: P1

## Objective

Ensure every model and pipeline is called only with parameters, service tiers,
and transport assumptions that the target actually supports.

## Scope

- Per-model capability matrix for service tier, reasoning level, context
  window, and supported request parameters.
- Per-pipeline contract checks for text, consensus, image, video, library
  execution, and startup surfaces.
- Explicit route-intent selection for `free`, `free_quota`, `user_pays`, and
  `paid` paths.
- Startup validation that rejects unsupported combinations before any provider
  call is attempted.
- Runtime evidence that the selected model, billing class, and pipeline match
  the requested task before execution begins.

## Failure modes to eliminate

- A configured service tier is emitted for a model that does not advertise it.
- A pipeline receives request parameters that the provider contract rejects.
- A text task silently lands on a different billing class than the route
  requested.
- A consensus, image, or video path inherits generic text-only assumptions.
- A startup probe or handshake path hides unsupported metadata warnings until
  after launch.

## Acceptance checks

- [x] A model capability matrix test covers every configured model and records
  only advertised service tiers and supported parameters.
- [x] A pipeline contract test covers text, consensus, image, video, and
  library routes without relying on unsupported defaults.
- [x] A route-intent test proves each task kind maps to the intended billing
  class or fails clearly when that class is unavailable.
- [x] Unsupported model/pipeline combinations fail during preflight rather
  than at provider execution time.
- [x] Startup and handshake tests complete without emitting unsupported tier
  warnings for the default model selection.
- [ ] The model/pipeline evidence ledger records the exact provider, model,
  route intent, and gating outcome for each validated path.

## Exit criteria

Close WO-007 only after the matrix and pipeline tests exist, the warnings are
eliminated or explained by validated metadata, and the rite ledger records a
fresh pass/fail summary for each individual model and pipeline.

## Implementation note

The repo-side contract layer now validates task/pipeline shape before routing,
rejects unsupported media metadata during preflight, and hardens the dashboard
launcher used by the legacy command shortcuts. The local Codex config was also switched
to `gpt-5.6-luna` with `priority`, which matches the advertised tier set and
removes the boot warning in this environment.
