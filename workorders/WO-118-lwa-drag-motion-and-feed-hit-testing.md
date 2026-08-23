# WO-118 — LWA drag motion and feed hit testing

## Evidence

The latest trace shows native curses mouse press/release events, but no motion
events and no `selection` lifecycle event. LWA therefore receives the click,
but cannot maintain a drag selection. The curses mask currently requests all
button events without explicitly requesting `REPORT_MOUSE_POSITION`.

## Hypothesis

We believe explicitly enabling mouse-position reporting will deliver the
missing drag phase through the native Ghostty/tmux path; confidence requires a
press/motion/release trace and a non-empty selection length for a visible LWA
feed line.

## Acceptance criteria

- The native curses mouse mask includes `REPORT_MOUSE_POSITION` when available.
- A visible LWA feed drag emits press, motion, and release metadata.
- Feed hit testing uses the same viewport bounds as rendering.
- Clicks in blank space or the prompt remain non-selection focus actions.
- Keyboard selection remains available as a non-dragging alternative.
- No prompt contents or selected text enter diagnostics.

## Accessibility finding

Mouse dragging was the only practical feed-selection path, but its missing
motion phase made the task unavailable to mouse users. Keyboard copy remains
the required alternative for motor and assistive-technology users.

