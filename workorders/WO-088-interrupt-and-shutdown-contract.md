# WO-088 — Interrupt and Shutdown Contract

Status: partial — deterministic repeated-interrupt and bridge traceback suppression gates pass; visual exit gate remains
Priority: P0
Dependencies: WO-087
Task rite: [TR-088](../task-rites/TR-088-interrupt-and-shutdown-contract.md)

## Objective

Make interruption and exit deterministic across LWA, native Codex, the bridge
fallback, tmux, and graphical terminals.

## Acceptance

- First Ctrl+C interrupts the active Codex turn without printing a traceback.
- A repeated Ctrl+C within the configured grace interval exits LWA cleanly.
- Esc exits LWA immediately.
- LWA restores terminal modes, cursor state, bracketed paste, and focus.
- Codex, bridge, controller, and pipeline tasks are terminated or awaited.
- Temporary sockets and stale pane registrations are removed.
- A bridge receiving SIGINT never prints an asyncio traceback into a user pane.
- Tests cover Ctrl+C during startup, consensus, Codex execution, pane close,
  and shutdown.

## Rollback

Retain the existing interrupt behavior behind a compatibility flag while the
new lifecycle handler is repaired. Never leave raw tracebacks in the visible
terminal surface.
