# TR-047 — Credential rotation and controlled live prompt proof

**Purpose:** restore credential trust and prove a minimal real prompt route
without turning a health check into an uncontrolled benchmark.

## Phase A — operator rotation handoff

1. Record only credential names, source paths, file mode, and rotation time.
2. Revoke or rotate each exposed provider credential at its provider console.
3. Remove unused provider entries rather than keeping stale material.
4. Run `./.venv/bin/lwa-router keys` interactively. Never pass secrets as CLI
   arguments or write them into a project file.
5. Confirm mode `0600`, restart long-running LWA/MCP/dashboard processes, and
   run the secret-pattern scan against the evidence directory.

Stop immediately if a value appears in stdout, stderr, a prompt, a log, a
telemetry record, or a saved artifact.

## Phase B — control-plane recheck

Run TR-045 from:

- the LWA repository;
- PuffPuffPass;
- one additional registered project root.

Require zero-payload discovery and a passing MCP handshake before any prompt
execution. A restricted DNS result must remain `execution_boundary=restricted`
and cannot be promoted to provider failure.

## Phase C — minimal free-route proof

Use only these prompts unless the operator expands the authorization:

1. `quick_response`: `Reply with exactly READY.`
2. `query`: `Name the primary color in: blue.`
3. `verification`: `Verify this claim: 2 + 2 = 4.`
4. `coding_aux`: `Identify the missing null check in: value.name.`

For each prompt:

1. prepare and inspect the locked provider/model and billing class;
2. approve only if the route is free/free-quota and expected;
3. execute the single-use plan token;
4. record the normalized result and provenance without storing the full prompt
   or credential;
5. stop on the first provider failure and repreflight before another attempt.

## Acceptance

- Four prompts complete, or the first failure is preserved as a typed,
  actionable provider result.
- Actual provider/model/billing class is recorded; provider preference is not
  treated as provider selection.
- No paid, user-pays, consensus, image, or video route runs.
- No old credential value appears in any artifact.
- The same bounded subset is repeatable from a second project root.

## Evidence artifact

`credential-rotation-live-proof.json` containing rotation metadata (not values),
project roots, route lifecycle fields, provider/model/billing provenance,
usage, redacted failure class, and explicit completion count.

