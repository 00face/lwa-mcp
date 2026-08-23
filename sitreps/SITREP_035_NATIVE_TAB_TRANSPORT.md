# SITREP 035 — Native Tab transport failure and remediation

## Evidence

The historical working trace was:

```text
tab_received:string native=True surface=lwa
request_codex pane=%65
```

Recent native traces stop after startup `request_lwa`; no `tab_received` is
recorded. Therefore the controller is not the failing layer. The current
conditional tmux binding has never had a real two-pane integration test.

## Decision

Execute WO-105, WO-106, and WO-107 in order. The transport harness must pass
before any further focus-controller or visual changes are accepted.

## Accessibility impact

Keyboard users currently lose the primary prompt-switch operation. The fix
restores a visible, deterministic keyboard path and preserves mouse-free
operation across native and embedded modes.

## Implementation checkpoint

WO-105 and WO-107 are implemented. Native bindings now use exact pane IDs and
the root table is source-aware: Codex forwards Tab/BTab to LWA, while LWA
selects Codex directly. C-c is isolated so only Codex capture is handled by
tmux; LWA receives C-c through its own copy handler.

A private tmux server accepted and displayed the production bindings. The
remaining acceptance gate is a real interactive Ghostty run confirming that
the forwarded Tab produces `tab_received native=True` in the current LWA
process. WO-106 remains open until that live input event is observed.

## Directionality correction

The first explicit-binding implementation correctly handled LWA→Codex but
left Codex→LWA dependent on hidden-pane key delivery. That branch now selects
the LWA pane first and then sends Tab/BTab, synchronizing tmux focus with the
LWA controller state. Focused launch/frame tests pass (52 tests), and a
private tmux server accepts the corrected chained binding.
