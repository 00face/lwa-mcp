# WO-091 — Native Pet Animation Protocol and Acceptance Gate

Status: Open — investigation required before further implementation

## Objective

Make the configured Codex pet animate reliably in the native LWA split while
preventing cursor coupling, blinking, protocol acknowledgements, prompt
corruption, pane resizing, or accidental input delivery.

## Scope

- Ghostty 1.3.1 through tmux native split.
- Kitty-compatible image protocol only when the host advertises support.
- Authoritative Codex pet cache frames, including `dewey` and future names.
- Native Codex pane placement at bottom-right.
- LWA fallback rendering on hosts where native animation is unavailable.

## Non-goals

- Recreating Codex pet assets.
- Treating a static screenshot as animation success.
- Sending graphics escape sequences through Codex prompt input.
- Changing Codex configuration or pet selection as part of the test.

## Required evidence gates

1. **Asset gate:** enumerate cached frames, verify at least three distinct
   frame hashes, and confirm the configured pet name.
2. **Protocol gate:** capture the exact outbound sequence and prove it uses
   either terminal-owned animation (`a=f`/`a=a`) or preloaded frame placement
   (`a=t`/`a=p`) consistently. No mixed protocol is accepted.
3. **Host gate:** verify Ghostty/tmux passthrough, pane geometry, and graphics
   capability independently of LWA curses rendering.
4. **Input-isolation gate:** confirm no graphics response, base64 content,
   frame metadata, or hash-like protocol text reaches either prompt.
5. **Temporal gate:** observe at least three frame changes over five seconds
   at a fixed pane coordinate while the Codex cursor is idle and while it is
   moving.
6. **Fallback gate:** verify a non-graphics host receives readable pet text
   and remains fully usable.

## Acceptance criteria

- The pet visibly changes frames without disappearing between frames.
- The pet remains pinned to the Codex pane’s bottom-right corner.
- Codex prompt text, cursor, slash menus, and mouse selection remain intact.
- No tmux status bar or graphics protocol text is emitted into the UI.
- Failure of native animation produces one clear diagnostic and a stable
  fallback; it does not trigger repeated speculative retries.

## Stop condition

Do not change the compositor again until the protocol, host, and input-isolation
gates identify which layer failed. If Ghostty/tmux cannot pass the protocol
gate, record native animation as unsupported for that host and use the approved
fallback or a separately owned overlay surface.
