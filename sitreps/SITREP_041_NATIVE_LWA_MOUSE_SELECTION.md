# SITREP 041 — Native LWA mouse selection

## Evidence

The native LWA path parses SGR mouse sequences into
`(__LWA_MOUSE__, button, x, y, action)` events. Selection starts and finishes
only when the decoded button is zero. Drag-motion button codes are therefore
not used to update the selection focus while the pointer moves.

The selection is also cleared immediately after copy on release, removing the
visual evidence of what was selected. Coordinate mapping is performed against
wrapped feed rows and a local scroll offset, but this behavior lacks complete
characterization coverage.

tmux has mouse reporting enabled, so the operator-visible behavior depends on
whether tmux passes the event to curses or owns it in copy mode. This must be
diagnosed rather than inferred from a successful single click.

## Decision

WO-116 will make selection state explicit, support motion events, preserve
feedback, and test prompt/feed boundaries independently. Keyboard copy remains
available as an accessible fallback.

## Validation gate

Automated tests can prove decoding, state transitions, coordinate mapping, and
copy content. Only a real Ghostty/tmux drag can prove terminal mouse ownership,
so that remains an operator-owned gate.

