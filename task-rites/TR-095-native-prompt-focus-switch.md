# TR-095 — Native Prompt Focus Switching Rite

Work order: `WO-095-native-prompt-focus-switch.md`

Status: Automated rites complete; native visual acceptance open

## Sequence

### 1. Input-path inspection

- Trace raw Tab from Ghostty through tmux and curses.
- Record whether it arrives as integer `9`, string `\t`, or a tmux pane event.
- Confirm which branch currently consumes it and whether any PTY write occurs.
- Record terminal cursor-save/restore sequences emitted during redraw.

### 2. Focus-state contract

- Define one controller-owned focus transition function.
- Make `active_surface` the sole source of truth for prompt focus.
- Define cursor placement from the active editor, pane geometry, and current
  prompt row.
- Separate focus switching from slash-command completion.

### 3. Native handshake

- Configure tmux so the LWA controller retains keyboard ownership while its
  pane is active.
- Ensure Codex receives input only after explicit Codex prompt submission or
  the documented Codex-send shortcut.
- Verify no focus or Tab bytes cross the LWA/Codex boundary.

### 4. Implementation

- Normalize all Tab representations into one local focus event.
- Consume the event before generic integer-key handling.
- Clear stale suggestions or preserve them without stealing focus, according to
  the focus contract.
- Redraw and position the cursor only after the new active surface is set.

### 5. Automated tests

- Test integer Tab and string Tab.
- Test repeated alternating switches.
- Test switches with empty prompts, multiline prompts, and slash suggestions.
- Assert no session write occurs for focus Tab.
- Test resize and redraw cursor coordinates.
- Test native tmux and non-tmux controller modes.

### 6. Operator verification

- Launch `lwa` in Ghostty with the native split.
- Type distinct markers into each prompt, such as `LWA-FOCUS` and
  `CODEX-FOCUS`.
- Press Tab five times and confirm focus alternates without moving either
  marker or sending text to Codex.
- Click each prompt, then repeat the Tab sequence.
- Resize the window and repeat.
- Confirm the cursor never appears in the old shared-frame location.

### 7. Closeout

- Record raw input-path evidence and PTY-write evidence.
- Record native visual evidence in a WO-095 report.
- Run the full test suite.
- Leave operator-only cursor/focus gates open until Ghostty/tmux observation
  confirms them.
