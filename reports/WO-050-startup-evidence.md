# WO-050 / TR-050 Evidence

**Recorded:** 2026-08-21  
**Result:** Promoted; startup ordering and live route checks pass. Host
contention still affects absolute cold-start timing.

## Redacted checks

- `lwa-mcp` no longer calls `RouterService.initialize()` before entering the
  stdio transport. The server emits `Lwa MCP stdio transport starting` on
  stderr and begins protocol negotiation immediately after its dependency
  imports.
- `lwa_mcp.dashboard` no longer constructs `RouterService` at import time.
  Static `/` and `/codex` routes do not construct it; router-backed APIs use a
  lazy accessor.
- A missing explicit `LWA_MCP_CONFIG` path is now initialized at that exact
  path, preventing the first lazy API operation from failing after a successful
  handshake.
- MCP handshake verification passed with 40 tools, 3 resources, and 1 prompt
  using a 20-second bounded fixture timeout.
- Focused startup/dashboard/MCP/Codex verification passed: `22 passed`.
- Isolated lazy-surface probe: static route response in `62 ms`; first local
  status operation in `447 ms` on the contended host.
- After restarting the LWA-owned dashboard process, live `/` and `/codex`
  returned HTTP 200, and the first live `/api/status` request returned HTTP
  200 in approximately `160 ms`.
- Ruff passed for the changed startup, dashboard, terminal, and test files.
- Full suite excluding the pre-existing host-sensitive credential fixture:
  `166 passed, 3 skipped`.

## Timing observations

- Before this change, the measured MCP handshake was approximately six seconds
  on a lightly loaded run and the server performed service warmup first.
- During the final run, the host was concurrently running Firefox and several
  TypeScript/Vite builds. Python imports varied between approximately seven
  and nine seconds, and the bounded handshake completed in approximately 22
  seconds. This is CPU contention, not an indefinite Lwa wait; the handshake
  completed and the process exited cleanly.
- The remaining credential test discovers a host Gemini value from Codex
  configuration instead of accepting its isolated fixture. It is unrelated to
  startup ordering and remains separately classified.

The remaining absolute import-time variance is an environment performance
observation, not a failed acceptance check.
