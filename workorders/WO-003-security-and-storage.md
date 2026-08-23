# WO-003: Security, Storage, and Recovery Hardening

Status: complete; core hardening, migration coverage, and verification controls validated
Priority: P1

## Objective

Make credentials, SQLite state, tool execution, and dashboard telemetry safe
under malformed input, concurrent access, interruption, and partial failure.

## Scope

- Verify atomic secure `.env` writes and exact literal round trips.
- Add secret-redaction tests for logs, exceptions, dashboard payloads, and DB
  records.
- Audit path traversal, subprocess argument handling, input/output limits,
  rotation, backups, migrations, corruption recovery, and graceful shutdown.
- Add dry-run and offline behavior where existing interfaces support it.

## Acceptance checks

- [x] Credential and state permissions are enforced on fresh and existing homes.
- [x] Existing unrelated environment entries survive updates.
- [x] Generated scripts remain review-gated and use safe subprocess boundaries.
- [x] Migration and backup tests cover Castor/Pollux legacy state.
- [x] Provider response/error redaction covers adapter, catalog, quota, ledger,
  and repreflight paths.
- [x] Library script entrypoints are constrained and output is bounded.
