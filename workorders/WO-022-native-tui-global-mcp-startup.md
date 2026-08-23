# WO-022 — Native TUI and Global MCP Startup Evidence

**Status:** partial; evidence captured, startup attribution remains open  
**Priority:** P1  
**Parent:** WO-018 / Rite 11

## Objective

Measure native interactive TUI and global MCP startup phases separately from
the successful bounded CLI probe.

## Scope

1. Use reversible or ephemeral profiles; do not delete or rewrite global
   registrations.
2. Measure process start, MCP initialization/handshake, TUI readiness, prompt
   acceptance, and first response independently.
3. Compare normal, fast-start, and auxiliary-MCP-disabled profiles.
4. Keep the Lwa dashboard opt-in and separate from stdio readiness.
5. Record a host-level blocker if a native interactive session cannot be
   observed safely.

## Acceptance

- [ ] Native TUI phase timings or a precise host-level blocker are recorded.
- [ ] Global MCP attribution distinguishes Lwa from unrelated servers.
- [ ] Existing plugin workflows remain available.
- [ ] CLI success is not reused as native-TUI acceptance.

## Exit boundary

This order produces evidence and a next decision; it does not promise a host
Codex fix.

## Bounded evidence — 2026-08-02

- Native `codex` TUI reached the interactive prompt and displayed MCP startup
  progress, but the bounded session reported MCP startup interrupted before
  `codex_apps` and `lwa` initialized.
- The reversible fast-start profile likewise reached the TUI but reported
  `codex-skill-switchboard`, `codex_apps`, and `lwa` not initialized within the
  bounded window.
- A second ephemeral profile reached the prompt after visibly progressing
  through `codex-skill-switchboard`, `codex_apps`, and `lwa` startup, without a
  startup-warning banner.
- Sessions were stopped with Ctrl-C; no global registrations were changed.
- CLI fast-start remains a separate successful probe and is not native-TUI
  acceptance.
