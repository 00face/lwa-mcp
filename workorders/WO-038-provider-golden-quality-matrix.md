# WO-038 - Provider Golden Quality Matrix

**Status:** Queued
**Priority:** P1
**Parent:** WO-036, WO-037
**Task rite:** [TR-038](../task-rites/TR-038-provider-golden-quality-matrix.md)

## Objective

Run provider-specific golden fixtures across text, structured, image, video,
verification, and recovery behaviors without lowering quality tiers.

## Promotion Gate

Two repeated runs per eligible service preserve required fields/literals, stay
within one quality point of baseline, report tokens, and introduce zero
duplicate execution.

## Rollback

Remove only the failing provider from the affected task route and retain its
fixture evidence for remediation.
