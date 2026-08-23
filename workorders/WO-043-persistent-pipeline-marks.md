# WO-043 - Persistent Operator Pipeline Marks

**Status:** Queued
**Priority:** P1
**Parent:** WO-041
**Task rite:** [TR-043](../task-rites/TR-043-persistent-pipeline-marks.md)

## Objective

Persist operator pipeline marks across process restarts without storing
credentials, prompts, or provider response bodies.

## Promotion Gate

- Marks persist in the local SQLite ledger with provider, state, reason,
  operator/source, timestamp, and schema version.
- Allowed states are validated and invalid marks are rejected.
- Marks are redacted, bounded in size, and independently exportable.
- Expired marks and configuration/provider identity changes are visible.
- `blocked` and `maintenance` marks gate execution; `degraded` is observable
  but does not silently change consent or billing policy.
- Concurrent writers do not corrupt or lose marks.

## Rollback

Ignore corrupted or incompatible marks and return to local computed status;
never treat an unreadable mark as approval to send data.

## Evidence

Restart, migration, redaction, invalid-state, and concurrent-write tests must
pass against a temporary database.
