# SITREP 042 — LWA selection and cursor diagnostic

## Situation

The LWA left pane currently has two independent interaction systems:

1. Curses owns the LWA prompt cursor and keyboard editor.
2. tmux/Ghostty/curses mouse reporting owns feed selection.

The operator reports that neither mouse selection nor Shift+Left/Right feels
usable, and that the left cursor blinks rapidly.

## Evidence

- The LWA process enables `curses.curs_set(1)` twice during startup.
- The render loop calls `screen.move()` and `screen.refresh()` repeatedly while
  the cursor is visible. Even with the steady-cursor escape sequence, terminal
  cursor state can be reasserted during every repaint.
- Native tmux mode enables mouse reporting, so tmux and curses can compete for
  drag ownership.
- SGR mouse events are decoded into press, motion, and release events, but the
  exact event stream is not currently logged.
- Prompt selection is a separate keyboard range in `PromptEditor`; feed
  selection is a separate line/coordinate range. Their visible and clipboard
  feedback paths are different.
- Existing logs prove focus transitions, but do not prove cursor visibility,
  mouse ownership, selection phase, or decoded Shift-arrow events.

## Primary hypotheses

### H1 — Cursor repaint contention

Repeated cursor movement and refresh calls are causing a visible blink or
cursor reinitialization. Signal: cursor blink rate changes when redraws are
coalesced or cursor visibility is disabled while Codex owns the native pane.

### H2 — Native pane ownership mismatch

The LWA process may still receive input while tmux has Codex active, or tmux may
retain copy mode. Signal: every input event records the active tmux pane, LWA
surface, and cursor owner consistently.

### H3 — Mouse ownership conflict

tmux copy mode may consume drags before curses receives them. Signal: a test
drag produces either a complete LWA press/motion/release trace or a clear tmux
copy-mode trace, never an ambiguous partial trace.

### H4 — Keyboard protocol mismatch

Ghostty may emit Shift-arrow sequences not covered by the decoder, or tmux may
translate them. Signal: raw sequence, normalized action, editor selection range,
and copy result agree for every supported encoding.

### H5 — Selection feedback mismatch

The selection may exist internally but be visually absent or immediately
overwritten by a redraw. Signal: selected character count, visible highlight,
and clipboard payload agree before and after release.

## Test matrix

Run each test in a fresh LWA session, recording only metadata and outcomes.

| ID | Input | Surface | Expected evidence |
|---|---|---|---|
| C01 | Type plain text | LWA prompt | Cursor moves one stable cell per character |
| C02 | Idle 30 seconds | LWA prompt | No rapid cursor blink or CPU spike |
| C03 | Type, resize, type | LWA prompt | Cursor remains in prompt bounds |
| C04 | Shift+Left one character | LWA prompt | One character highlighted |
| C05 | Shift+Left repeatedly | LWA prompt | Range grows predictably |
| C06 | Shift+Right after reversal | LWA prompt | Range contracts/reverses predictably |
| C07 | Ctrl+C after keyboard selection | LWA prompt | Clipboard equals selected text |
| C08 | Mouse press, hold, drag, release | LWA feed | Press/motion/release trace and highlight |
| C09 | Drag across wrapped line | LWA feed | Character mapping remains correct |
| C10 | Drag across multiple lines | LWA feed | Newlines and endpoints are correct |
| C11 | Select after scrolling | LWA feed | Scroll offset is applied exactly once |
| C12 | Click prompt after feed selection | LWA prompt | Focus changes, feed selection remains isolated |
| C13 | Alt+Left then type | Native | Input belongs to LWA only |
| C14 | Alt+Right then type | Native | Input belongs to Codex only |
| C15 | Mouse drag while Codex active | Native | No LWA selection mutation |
| C16 | tmux copy mode attempt | Native | Ownership is explicit and recoverable |
| C17 | Paste multiline text | LWA prompt | Selection/cursor remain bounded |
| C18 | Output flood plus pet animation | Native | Cursor and selection remain responsive |
| C19 | Low-resource mode | Native | No unbounded queues or retained lines |
| C20 | Ctrl+Q during selection | Native | Clean exit, no stuck cursor or tmux mode |

## Diagnostic fields to add

The next implementation should log metadata-only events:

```text
mouse_event action=press|motion|release button=<class> x=<n> y=<n>
selection surface=lwa phase=anchor|dragging|selected length=<n>
cursor owner=lwa|codex row=<n> column=<n> visible=true|false
key raw_class=escape_sequence normalized=shift-left|shift-right
tmux active_pane=<id> copy_mode=true|false
```

Never log prompt contents, selected text, credentials, environment values, or
provider payloads.

## Recommended order

1. Instrument cursor owner and mouse/keyboard event classes.
2. Test C01–C07 to isolate the prompt editor and cursor.
3. Test C08–C12 to isolate curses selection and coordinate mapping.
4. Test C13–C16 to isolate tmux ownership.
5. Test C17–C20 for stress, fallback, and shutdown behavior.
6. Only then change rendering or transport behavior.

## Conclusion

The current evidence is insufficient to blame one layer. The most likely
combination is cursor repaint contention plus missing ownership diagnostics,
with tmux mouse capture as a separate selection failure mode. The matrix above
will distinguish those causes without another blind key-binding change.

