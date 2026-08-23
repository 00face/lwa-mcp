# WO-110 — Remove stale pane bindings

## Objective

Ensure old Tab/Shift+Tab pane bindings cannot survive a prior crash and
reappear in a new native LWA session.

## Acceptance criteria

- Native footer documents only Alt+Left and Alt+Right.
- Startup removes legacy Tab, Shift+Tab, and Ctrl+I pane bindings before
  installing Alt-arrow bindings.
- Embedded mode retains its own Tab/Shift+Tab focus behavior.
- Native Tab and Shift+Tab insert five spaces into the active prompt if the
  terminal delivers them to curses.
- A crashed prior launch cannot leave pane-navigation bindings active.
- Regression tests and the complete suite pass.
