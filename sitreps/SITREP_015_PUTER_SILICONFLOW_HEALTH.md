# SITREP 015 — Puter and SiliconFlow Provider Health

**Date:** 2026-08-02  
**Status:** Planned; documentation/feasibility only  
**Related work order:** [WO-017](../workorders/WO-017-puter-siliconflow-health.md)

## Situation

Initial discovery reported Puter model-discovery HTTP 404 and SiliconFlow
model-discovery HTTP 401. After the bounded Puter schema check, Puter is healthy
with native discovery; SiliconFlow remains unhealthy with HTTP 401. These are
distinct provider conditions, not evidence that the Lwa router is globally
unavailable.

## Rite

Record the failures, preserve redacted health reporting, and document the
existing paid-execution switches. Any live check must use a locked preflight,
explicit `allow_paid`/`allow_user_pays` authorization, and single execution.

## Boundary

No credentials, endpoints, or provider adapters are changed. Recovery remains
unverified until official endpoint/authentication evidence is obtained.

## Safe execution evidence — 2026-08-02

- `lwa-router doctor` completed and reported both providers configured.
- Redacted router health still reports Puter **unhealthy / model discovery HTTP
  404** and SiliconFlow **unhealthy / model discovery HTTP 401**.
- No paid or user-pays provider call was executed. Existing ready user-pays
  preflights were not consumed.

The first safe fix remains implemented: routing excludes seed models for a
provider explicitly marked unhealthy by live refresh. Puter discovery is now
repaired; SiliconFlow's 401 remains unresolved and gated.
