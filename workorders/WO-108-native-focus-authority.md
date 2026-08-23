# WO-108 — Native focus authority

## Objective

Make Tab and Shift+Tab switch between the LWA and Codex panes in both
directions without relying on synthetic input delivery.

## Acceptance criteria

- Tab, Ctrl+I, and Shift+Tab select the opposite pane from either source pane.
- No binding sends Tab or Shift+Tab into a hidden destination pane.
- Native focus is defined by the active tmux pane; embedded focus remains
  controlled by the curses focus broker.
- A failed focus effect cannot terminate the frame or corrupt the prompt.
- Unit tests assert direct pane selection and reject synthetic forwarding.
- The full test suite and lint checks pass.

## Accessibility gate

Keyboard focus must be deterministic, reversible, and visible. The operator
must never need to press a key twice because the first key was delivered to a
hidden surface.

