# WO-017 — Puter and SiliconFlow Provider Health

**Status:** partial; Puter recovered, SiliconFlow remains unhealthy  
**Priority:** P1

## Objective

Document a safe, feasible diagnostic path for the remaining Puter HTTP 404 and
SiliconFlow HTTP 401 health failures. Any live or paid check must be an explicit
operator switch; no endpoint or credential change is claimed here.

## Known evidence

- Puter model discovery: HTTP 404.
- SiliconFlow model discovery: HTTP 401.
- ZAI free-quota execution succeeded, so Lwa routing is not globally offline.

## Feasible scope

1. Record redacted configured/enabled/provider health state.
2. Preserve the existing `allow_paid` and `allow_user_pays` controls as the
   only authorization switches for paid/user-pays execution.
3. Document the exact preflight → optional approval → single execution path for
   any approved live check.
4. Separate configured, unhealthy, blocked, and healthy states.
5. Defer endpoint repair, credential rotation, and provider-specific fixes until
   official contract evidence is available.

## Acceptance

- [ ] Documentation identifies both failures and their evidence class.
- [ ] A live check is impossible unless the operator explicitly enables the
      relevant paid/user-pays switch and approves the locked preflight.
- [ ] No secret, endpoint rewrite, or provider-health claim is introduced.
- [ ] A later provider-specific diagnostic can record 404/401/healthy outcomes
      without changing this work order's safety boundary.

## Exit boundary

This order closes only as a documentation/feasibility rite. Provider recovery
requires a separately authorized implementation order.

## Safe execution evidence — 2026-08-02

Initial `lwa-router doctor` and redacted router status reported Puter discovery
HTTP 404 and SiliconFlow discovery HTTP 401. No paid/user-pays call or
credential change occurred.

## Baseline implementation slice — 2026-08-02

Routing now gates seed models for any provider whose live catalog refresh has
explicitly recorded `healthy=false`. This prevents stale Puter/SiliconFlow
seed entries from winning a route after discovery or authentication failure.
Puter-specific discovery is now implemented and verified in WO-019. SiliconFlow
credential remediation remains unimplemented; its redacted authorized check is
recorded in WO-020.
