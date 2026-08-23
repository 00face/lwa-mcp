# WO-039 - Bounded Provider Operations

**Status:** Queued
**Priority:** P0
**Parent:** WO-036
**Task rite:** [TR-039](../task-rites/TR-039-bounded-provider-operations.md)

## Objective

Eliminate unbounded discovery and repeated control-plane work across all
provider services.

## Promotion Gate

Warm catalog/handshake paths use scoped caches, perform zero repeated discovery,
and emit separate discovery telemetry. Cold refresh requires explicit provider
allowlist, timeout, concurrency bound, and rollback.

## Rollback

Disable cache reads or a provider service, but never fall back to unbounded
`force=True` refresh in proof or normal warm paths.
