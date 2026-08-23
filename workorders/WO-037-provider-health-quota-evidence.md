# WO-037 - Provider Health and Quota Evidence

**Status:** Queued
**Priority:** P0
**Parent:** WO-036
**Task rite:** [TR-037](../task-rites/TR-037-provider-health-quota-evidence.md)

## Objective

Capture fresh, provider/account-scoped health and authoritative quota evidence
for every service, with billing-aware proof rules.

## Promotion Gate

Free-quota services have fresh token denominators and two reported quality
runs. Paid/user-pays services have cost/consent evidence and are never labeled
free-quota compliant.

## Required Exceptions

SiliconFlow must clear its known health/auth condition. Zai must supply the
locked-route quota snapshot. Puter must retain user-pays classification.

## Rollback

Mark the service conditional or unavailable; never substitute another provider's
quota or stale snapshots.
