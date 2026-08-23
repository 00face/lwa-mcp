# WO-005: Documentation and Operator Readiness

Status: complete; documentation, operator quick-start, verification scripts, and SITREP records reconciled
Priority: P2

## Objective

Keep project doctrine, release records, operator instructions, and current
implementation behavior synchronized.

## Scope

- Update README, doctrine, version-control record, history, testcase, release
  manifest, current SITREP, and relevant docs after each completed work order.
- Add a concise operator quick-start covering installation, credentials,
  Codex registration, dashboard, caps, approvals, tool review, backup,
  recovery, troubleshooting, and uninstall.
- Record architecture decisions when behavior or storage contracts change.

## Acceptance checks

- [x] No outward-facing document presents legacy consent aliases as canonical.
- [x] Upgrade and migration notes identify compatibility behavior.
- [x] Current SITREP names tested, untested, and blocked checks accurately.
