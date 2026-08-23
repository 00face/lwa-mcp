# TR-050 — Startup Latency and MCP Readiness Rite

**Purpose:** prove that Lwa is slow only where local warmup is required and
does not appear stuck at `lwa-mcp` while waiting for a stdio handshake.

**Current result (2026-08-21):** Promoted. Startup ordering, bounded
handshake, live static routes, and first router-backed operation pass. Absolute
import latency remains host-load dependent but no indefinite wait was observed.

## Entry

Use the project virtual environment on the target Linux Mint host. Record only
elapsed time, route state, process exit state, and test results.

## Action

1. Measure cold import, service construction, dashboard route readiness, and
   MCP handshake.
2. Start `lwa-web --no-browser` and request `/` and `/codex`.
3. Start `lwa-mcp` through the handshake fixture and confirm protocol readiness
   before any router-backed tool call.
4. Exercise one router-backed status operation to verify lazy construction.
5. Confirm no provider network call, raw prompt, credential, or token enters
   the evidence.

## Check

- MCP transport begins before `RouterService.initialize()`.
- Static dashboard routes work while service construction is deferred.
- First API/tool use remains correct and bounded.
- No process remains from the measurement harness.

## Promote when

Repeated cold starts show no indefinite wait and the focused/full suite has no
startup regression.

## Rollback

Use direct `lwa codex` and the existing dashboard process while preserving the
redacted timing report. Do not remove Lwa state or credentials.
