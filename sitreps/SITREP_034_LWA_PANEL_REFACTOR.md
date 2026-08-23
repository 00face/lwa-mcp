# SITREP 034 — LWA panel refactor readiness

## Evidence

The current panel implementation concentrates layout, key decoding, focus
handoff, tmux integration, scrolling, selection, pet compositing, and lifecycle
cleanup inside `terminal_frame._interactive`. This has produced repeated
regressions where:

- tmux consumes Tab before LWA can trace it;
- tmux copy mode leaves yellow overlays and blocks input;
- pet graphics alter focus/scroll perception;
- embedded and native modes implement different key paths;
- cleanup and global bindings outlive the intended panel session.

The historical working trace proves the desired native path: LWA receives Tab,
then emits `request_codex`. The current trace often stops before
`tab_received`, proving that focus ownership is outside the reducer and is
being decided by competing terminal layers.

## Decision

Proceed with WO-099 through WO-104 in order. The first milestone is behavioral
parity and traceability, not visual redesign. Pet animation, slash commands,
and styling remain downstream consumers of the stable panel state.

## Validation hypothesis

The refactor is successful when a scripted 100-cycle matrix of focus, typing,
scroll, selection, pet switch, copy, and exit operations produces no wrong-pane
input, no stale tmux mode, no lost focus transition, and no process crash.

## Open gate

Native Ghostty/tmux visual acceptance still requires operator verification,
because an automated test cannot fully prove OS-level pane focus and rendered
graphics placement.

## Implementation checkpoint

TR-099 through TR-104 are implemented as the first refactor slice:

- `panel_controller.py` owns pure state transitions and the single focus broker;
- `panel_input.py` normalizes global terminal actions;
- `panel_rendering.py` owns pane geometry and bounded scroll calculations;
- `panel_lifecycle.py` makes session cleanup idempotent;
- `terminal_frame.py` routes Tab, Shift+Tab, mouse prompt focus, pipeline focus,
  and transfer focus through the broker.

Validation: `PYTHONPATH=. pytest -q` → 274 passed, 3 skipped. The remaining
operator gate is a real Ghostty/tmux run confirming the trace sequence
`request_lwa → tab_received → request_codex` and the reverse handoff, with no
yellow tmux mode overlay or lost input.

Follow-up verification: the focused panel/focus suite now passes 35 tests,
including a 100-transition native focus soak and malformed escape-sequence
checks. Desktop readiness reports Openbox and the dashboard URL available;
Ghostty and tmux are installed. The live visual gate remains intentionally
open because it requires observing the actual terminal window and mouse focus.
