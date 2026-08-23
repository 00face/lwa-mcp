# TR-090 — Native Pane Selection, Scroll, and Pet Visibility Rite

Status: partial

1. Start a fresh native Ghostty split and verify LWA mouse selection is bounded
   to the left pane.
2. Verify LWA PageUp/PageDown and wheel scrolling move only the LWA feed and
   move its scrollbar independently.
3. Verify Codex selection and scrolling remain native to the right pane.
4. Reload the configured Stack/Stacky pet and verify image visibility through
   tmux passthrough, then verify the ASCII fallback with graphics disabled.
5. Capture evidence for both panes and record any host-specific scrollbar
   behavior without claiming LWA ownership of native Codex UI.

