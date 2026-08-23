# TR-116 — Native LWA mouse selection

1. Add characterization tests for SGR press, motion, and release events.
2. Reproduce selection failures across short, wrapped, multiline, and scrolled
   LWA feed content.
3. Introduce a small selection state controller with anchor, focus, and stable
   completion states.
4. Handle left-button drag motion codes without confusing wheel events or
   prompt clicks.
5. Preserve selection highlight until the next selection or explicit copy
   completion, and add a keyboard copy fallback.
6. Verify source/display coordinate mapping and local scroll offsets.
7. Add tmux/curses diagnostics for mouse ownership and run the Ghostty operator
   gate.
8. Run focused tests, lint, and the full suite before closing the rite.

