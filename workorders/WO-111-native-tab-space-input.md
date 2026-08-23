# WO-111 — Native Tab space input

## Objective

Prevent terminals that deliver Tab directly to curses from triggering pane
focus transitions in native mode.

## Acceptance criteria

- Native Tab inserts five spaces into the active prompt.
- Native Shift+Tab/BackTab also inserts five spaces if delivered to curses.
- Neither key changes the active surface or pane.
- Embedded mode behavior is unchanged.
- Focus and full-suite tests pass.

