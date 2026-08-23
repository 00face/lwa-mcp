# SITREP 021 — First-Response Timing and Durable MCP Attribution

**Date:** 2026-08-02  
**Status:** Partial; first-response probe is authorized but not yet executed  
**Related work order:** [WO-023](../workorders/WO-023-first-response-mcp-attribution.md)

**TUI design baseline:** [`/home/face/.codex/quirks/quirk_tui_plugin_design.md`]

## Evidence

- Direct native TUI reached the interactive prompt while MCP startup displayed
  `codex_apps` and `lwa` progress.
- An ephemeral comparison also reached the prompt after sequential MCP progress
  without a warning banner.
- A separate bounded run reported MCP startup interrupted before initialization
  completed.

## Boundary

No first-response prompt was submitted because that would invoke an external
model response. It requires an explicit operator-controlled response probe
switch. No global MCP registration was changed.

## Next decision

Execute one trivial, non-sensitive probe under the operator authorization
recorded on 2026-08-08, then close the rite if the probe yields durable timing
and attribution evidence without mutating global configuration.
