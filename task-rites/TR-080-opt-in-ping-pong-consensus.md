# TR-080 — Opt-In Ping-Pong Consensus

Status: ready

1. Define the bounded ping-pong state machine and persisted run identifier.
2. Add explicit enablement and budget controls to LWA.
3. Route only the reviewed LWA result into Codex.
4. Capture Codex response and return it to LWA consensus.
5. Stop in a reviewable LWA state with cancel/retry controls.
6. Test limits, errors, reconnects, duplicate events, and redaction.
