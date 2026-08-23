# WO-042 - Bounded Zero-Payload Probe Cache

**Status:** Queued
**Priority:** P0
**Parent:** WO-041
**Task rite:** [TR-042](../task-rites/TR-042-bounded-probe-cache.md)

## Objective

Cache successful and failed zero-payload pipeline probes with a bounded TTL so
normal execution does not repeat provider metadata checks or create unbounded
control-plane traffic.

## Promotion Gate

- Cache key includes provider, endpoint/config fingerprint, probe schema version,
  and credential/account identity without storing secrets.
- Warm reads make zero network calls.
- Success and failure entries have separate bounded TTLs.
- Provider/config changes invalidate entries.
- Concurrent checks coalesce into one in-flight probe.
- Expired or malformed entries fail closed and never authorize a provider.
- Probe telemetry records cache hit, miss, age, and network call count.

## Rollback

Disable cache reuse for the affected provider and retain explicit bounded
probes. Never fall back to repeated `force=True` discovery or task execution.

## Evidence

Two cold/warm/invalidation runs per provider class, with zero-payload and
network-call assertions, are required before promotion.
