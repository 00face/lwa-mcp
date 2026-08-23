# SITREP 016 — Interactive TUI and Global MCP Startup

**Date:** 2026-08-02  
**Status:** Planned; separate open concern under WO-005/TR-007  
**Related work order:** [WO-018](../workorders/WO-018-interactive-tui-startup.md)

## Situation

Bounded CLI startup is measured and passing, but native interactive TUI/global
MCP behavior remains open. The TUI has attempted unrelated MCP initialization
and previously reported failures before a provider response.

## Rite

Use reversible profiles to measure native TUI phases and attribute failures.
Keep dashboard opt-in separate from Lwa stdio startup. Do not claim native TUI
acceptance from CLI evidence.

## Boundary

No global registrations are deleted or rewritten. If the host prevents a clean
interactive measurement, record that limitation and the exact next experiment.

## Safe execution evidence — 2026-08-02

- Reversible `codex-fast-start.sh exec --ephemeral` returned `FAST_OK`.
- Measured elapsed time: **8.90s**.
- This is bounded CLI evidence only; no native interactive TUI session was
  claimed or used to close WO-018.
