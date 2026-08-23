# WO-109 — Alt-arrow pane navigation

## Objective

Use only Alt+Left and Alt+Right for native LWA/Codex pane navigation.

## Acceptance criteria

- Alt+Left directly selects the LWA pane.
- Alt+Right directly selects the Codex pane.
- Tab, Ctrl+I, and Shift+Tab are not intercepted for native pane switching.
- No synthetic key is sent into either pane.
- Prompt Tab behavior remains available to the active prompt.
- Focus binding tests and the complete suite pass.

## Operator gate

Verify both directions in Ghostty/tmux, then verify that Tab remains usable in
the active LWA and Codex prompts.

