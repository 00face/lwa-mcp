# WO-034 - Bounded Catalog Discovery

**Status:** Partial — guard script implemented; doctor integration and cache promotion remain.
**Priority:** P0
**Parent:** WO-031
**Task rite:** [TR-034](../task-rites/TR-034-bounded-catalog-discovery.md)

## Objective

Prevent doctor or proof setup from fanning out into thousands of live catalog
refreshes when a scoped, fresh catalog cache is available.

## Required Tests

- Fresh scoped cache returns a cache hit with zero network calls.
- Missing, stale, invalid, or provider-mismatched cache fails closed.
- Live refresh requires an explicit provider allowlist and bounded concurrency.
- Doctor reports discovery calls separately from provider completions.

## Promotion Gate

The proof path performs zero repeated catalog discovery on warm runs and never
refreshes providers outside the locked route scope.

## Rollback

Disable catalog cache use and return to explicit, bounded discovery; never use
unbounded `force=True` refresh in the proof path.
