# WO-018 — Interactive TUI and Global MCP Startup

**Status:** partial; native evidence captured, separate open concern under WO-005/TR-007  
**Priority:** P1

## Objective

Document a reversible, feasible investigation of native interactive TUI startup
and global MCP initialization. Existing bounded CLI timing must not be treated
as native TUI acceptance.

## Known evidence

- Direct bounded startup: 5.42s, `STARTUP_OK`.
- Lwa-disabled bounded startup: 5.34s, `STARTUP_NO_LWA`.
- Fast-start wrapper: 6.06s, `FAST_OK`.
- Native TUI still initializes unrelated MCP servers and has reported startup
  failures/provider-stream disconnects.

## Feasible scope

1. Use reversible profiles or transient overrides; do not delete registrations.
2. Record process start, MCP handshake, prompt acceptance, and first response
   timestamps for a fresh TUI session.
3. Compare direct, fast-start, and auxiliary-MCP-disabled profiles.
4. Keep Lwa dashboard startup opt-in and separate from stdio readiness.
5. Record a host-level blocker if native TUI evidence cannot be obtained.

## Acceptance

- [ ] A native TUI timing record or phase-specific host-level blocker exists.
- [ ] The three migrated plugin workflows remain available.
- [ ] No global configuration is destructively changed.
- [ ] CLI, handshake, and native TUI results are reported separately.

## Exit boundary

This order does not promise a Codex host fix. It produces reproducible evidence
and a bounded next decision under WO-005/TR-007.

## Safe execution evidence — 2026-08-02

The reversible fast-start CLI probe returned `FAST_OK` in **8.90s**. Native
interactive TUI timing and global-MCP attribution remain open.

## Bounded evidence — 2026-08-02

Native `codex` and the reversible fast-start TUI both reached the interactive
prompt, but MCP initialization was interrupted within the bounded window before
`lwa` completed. No global registrations changed.
