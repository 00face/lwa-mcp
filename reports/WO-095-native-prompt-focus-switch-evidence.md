# WO-095 Native Prompt Focus Switch Evidence

Date: 2026-08-23
Status: Automated implementation complete; native visual gate open

## Finding

The controller received Tab after an initial ESC path, but `_read_key()` did
not return a literal Tab encountered while consuming that path. It fell
through to the ESC fallback. In addition, native split mode was trying to
toggle an invisible Codex prompt inside the LWA frame instead of transferring
focus to the real Codex tmux pane.

## Implementation

- `_read_key()` now returns `"\\t"` immediately when encountered in the escape
  reader.
- Integer curses Tab (`9`) and string Tab use the same focus transition.
- Native mode transfers focus to the actual Codex tmux pane; tmux's unprefixed
  Tab binding returns focus to the previous pane.
- Non-native mode keeps the local LWA/Codex focus transition.
- Focus switching clears stale suggestions and never writes to the Codex PTY.
- Cursor placement remains derived from the active surface after redraw.
- Added a single `_toggle_prompt_surface()` focus contract.

## Verification

```text
Ruff                                                     PASS
Focused focus/input suite                                48 passed
Full suite                                                265 passed, 3 skipped, 2 warnings
```

## Gate status

| Gate | Status | Evidence |
|---|---|---|
| Raw Tab parser | PASS | Regression test returns literal Tab from the ESC reader. |
| Local focus toggle | PASS | Unit test verifies LWA ↔ Codex transitions in non-native mode. |
| Native pane handshake | PASS by code path | Native Tab selects Codex; tmux `select-pane -l` returns to LWA. |
| PTY isolation | PASS by code path | Tab is consumed before any session write branch. |
| Cursor visual position | OPEN | Requires Ghostty/tmux operator observation. |
| Resize/mouse parity | OPEN | Requires native visual verification. |

## Operator closeout

Restart `lwa` in Ghostty, type distinct text into each prompt, and press Tab
five times. Focus should alternate between prompts, the cursor should appear
only in the active prompt, and no Tab or marker should reach Codex. Repeat once
after resizing the window.
