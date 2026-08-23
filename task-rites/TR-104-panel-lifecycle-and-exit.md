# TR-104 — Lifecycle and exit rite

1. Create a single cleanup owner for curses, PTY, tmux bindings, and panes.
2. Make cleanup idempotent and safe after partial startup.
3. Scope Tab, Shift+Tab, Ctrl+C, and Ctrl+Q bindings to the LWA window.
4. Verify no binding or child pane remains after normal, interrupt, error, or
   terminal-close exits.
5. Run launch/exit soak tests before visual acceptance.
