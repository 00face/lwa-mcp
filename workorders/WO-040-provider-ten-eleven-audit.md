# WO-040 - Provider 10/11 Audit

**Status:** Queued
**Priority:** P0
**Parent:** WO-036 through WO-039
**Task rite:** [TR-040](../task-rites/TR-040-provider-ten-eleven-audit.md)

## Objective

Issue a separate evidence-gated rating for every configured provider service.

## 10/10 Gate

Adapter contract, health, authoritative quota/cost evidence, two quality runs,
complete telemetry, bounded discovery, safety rollback, and independent
reproduction all pass.

## 11/10 Gate

10/10 is sustained, predictive reuse improves p95, stale-result safeguards are
proven, and an independent operator reproduces the result without a safety
exception.

## Rollback

Publish the lower service rating and reopen only the failed provider order.
