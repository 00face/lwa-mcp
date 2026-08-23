# TR-112 — Predictable LWA cursor

1. Capture native and embedded key traces with privacy-safe focus diagnostics.
2. Reproduce cursor drift after Tab, Alt arrows, mouse focus, paste, newline,
   resize, and scroll.
3. Define one cursor-owner invariant and test it before implementation.
4. Refactor cursor placement and active-editor routing around that invariant.
5. Run terminal-frame tests and a Ghostty/tmux operator trace.

