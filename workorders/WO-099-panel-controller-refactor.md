# WO-099 — LWA panel controller refactor

## Hypothesis

We believe separating panel state, input routing, focus ownership, rendering,
and tmux integration will make the LWA panel predictable; confidence requires
100 repeated prompt switches with zero lost keys, pane misfocuses, or crashes.

## Scope

Replace the current `_interactive` state-and-key monolith with explicit
`PanelController`, `PanelState`, and adapter boundaries. No feature work is
accepted until the state transition tests pass.

## Gates

- no prompt text is sent to the wrong pane;
- one authoritative focus owner exists at a time;
- native and embedded modes share the same logical transitions;
- renderer failures cannot terminate input handling;
- all transitions emit secret-free diagnostics.
