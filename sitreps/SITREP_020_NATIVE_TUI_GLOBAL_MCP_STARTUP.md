# SITREP 020 — Native TUI and Global MCP Startup

**Date:** 2026-08-02  
**Status:** Partial; evidence captured, separate concern remains open  
**Related work order:** [WO-022](../workorders/WO-022-native-tui-global-mcp-startup.md)

## Situation

The reversible CLI probe succeeded, but that does not establish native
interactive TUI or global-MCP startup behavior.

## Boundary

Use ephemeral/reversible profiles only. Preserve global registrations and keep
the Lwa dashboard independent from stdio readiness.

## Acceptance

Record native phase timings and attribution, or document the exact host-level
blocker preventing measurement.

## Result — 2026-08-02

Native TUI reached the prompt, but bounded startup reported MCP initialization
interrupted before `lwa` and other MCP servers completed. No registrations were
changed. This is evidence of the startup concern, not closure of WO-005/TR-007.

A second ephemeral comparison reached the prompt while showing sequential
`codex-skill-switchboard`, `codex_apps`, and `lwa` startup progress, without a
startup-warning banner. First-response timing and durable attribution remain
open.
