# WO-021 — Provider Health-Gate Regression Preservation

**Status:** complete; regression assurance verified  
**Priority:** P1  
**Parent:** WO-017 / Rite 10

## Objective

Preserve the implemented rule that a provider explicitly marked unhealthy by a
live refresh cannot route through stale seed models.

## Scope

1. Keep the `healthy=false` routing gate in the scoring path.
2. Cover Puter and SiliconFlow seed entries with explicit unhealthy fixtures.
3. Verify healthy live providers and offline/no-health-record behavior remain
   eligible under their existing contracts.
4. Run focused and full regression tests after provider-adapter changes.

## Acceptance

- [ ] Unhealthy Puter and SiliconFlow seeds are skipped.
- [ ] Healthy providers remain routable when otherwise eligible.
- [ ] No dynamic mid-execution reroute is introduced.
- [ ] Full suite is green and evidence is recorded in the SITREP.

## Exit boundary

This work order does not declare either provider repaired; it protects routing
correctness while diagnostics remain open.

## Completion evidence — 2026-08-02

- Focused suite: **55 passed**.
- Full suite: **89 passed**, with two existing FastAPI deprecation warnings.
- Live refresh reports Puter healthy and SiliconFlow unhealthy; stale unhealthy
  provider seeds remain gated by the implemented routing rule.
