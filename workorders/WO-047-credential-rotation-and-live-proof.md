# WO-047 — Credential rotation and controlled live prompt proof

**Status:** BLOCKED / rotation freshness unverified; controlled proof recorded  
**Priority:** P0  
**Parent:** WO-045, WO-046, WO-003  
**Task rite:** [TR-047](../task-rites/TR-047-credential-rotation-and-live-proof.md)

## Objective

Restore trust in the LWA credential namespace after provider key material was
exposed by a diagnostic, then run a bounded free-route prompt proof from two
projects. Rotation is an operator action; this order must not invent, copy, or
print replacement credentials.

## Required operator action

Rotate every provider credential that was present in the exposed LWA env file,
or explicitly remove unused credentials and disable their providers. Use the
interactive governed path:

```sh
./.venv/bin/lwa-router keys
```

The new file must remain outside repositories and mode `0600`. Restart any
long-running MCP/dashboard process after rotation so it cannot retain old
process-environment values.

## Acceptance

- Old exposed credentials are revoked or confirmed unused and removed.
- The replacement env file contains no values in logs, source, telemetry,
  prompt fixtures, or evidence artifacts.
- TR-045 passes from the LWA root and two project roots.
- TR-046 prepare-only coverage remains green from the same roots.
- TR-047 completes only a small, explicit free/free-quota prompt subset and
  records actual provider, model, billing class, usage, request ID when
  available, and response provenance.
- Paid and user-pays routes remain disabled unless separately authorized.
- A failed completion stops the locked run and requires repreflight; no hidden
  fallback is accepted.

## Rollback

If a replacement key fails, stop live proof, restore only the last operator-
approved configuration metadata, and re-enter the credential through the
governed wizard. Never restore exposed key material from shell history, logs,
chat transcripts, or diagnostic output.

## Exit criteria

Close when revocation/rotation evidence is recorded, two project roots pass
TR-045 and TR-046, and the approved free prompt subset completes with truthful
provenance. Otherwise remain BLOCKED with the exact provider and recovery step.

## Controlled proof record

TR-047's four-prompt subset completed from the LWA root and from PuffPuffPass.
All eight completed calls selected `free_quota`; paid, user-pays, consensus,
image, and video routes were not run. The redacted evidence is recorded in
[`credential-rotation-live-proof.json`](../credential-rotation-live-proof.json).

The order remains BLOCKED because the governed env file is still mode `0600`
but its mtime is unchanged from the July 25 baseline. The operator's
conversation confirmation is preserved, but credential freshness is not
independently verified. Re-run the governed key path or provide fresh rotation
metadata, then recheck the env-file metadata before closing this order.
