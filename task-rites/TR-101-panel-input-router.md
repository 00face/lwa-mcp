# TR-101 — Input router rite

1. Decode raw curses and tmux sequences into semantic events.
2. Handle Shift+Tab as `FocusPrevious` and Tab/Ctrl-I as `FocusNext`.
3. Keep Ctrl+C copy-only and Ctrl+Q exit-only by ownership mode.
4. Reject graphics acknowledgements and modal bytes as prompt input.
5. Add property tests for malformed, partial, and repeated escape sequences.
