# WO-051 / TR-051 Evidence

**Recorded:** 2026-08-21  
**Result:** Partial promotion; protocol, capability, fallback, and live route
checks pass. Full desktop graphics/input coverage remains open.

## Redacted checks

- Shared terminal protocol fixtures preserve Unicode and remove ANSI/VT and
  OSC-8 control wrappers without leaking link targets into visible fallback
  text.
- Capability metadata reports the active host renderer honestly:
  `ghostty-host / Lwa fallback frame`, ANSI/VT, Unicode, OSC-8 support, Kitty
  and Sixel availability, and `text-placeholder` image fallback.
- `/api/codex/capabilities` returned HTTP 200 with only non-sensitive metadata.
- Live `/codex` returned HTTP 200 after restarting the updated dashboard.
- A headless Firefox screenshot loaded the live workspace successfully and
  visibly rendered Codex Feed, Codex Prompt, LWA Feed, pause control, and LWA
  Prompt surfaces. The test used an isolated browser profile.
- A real pseudo-terminal run of `lwa frame --codex /bin/echo` exited with code
  zero after Esc and left no LWA frame child process behind. This validates the
  dependency-light native fallback without launching a provider or real Codex
  task.
- A live WebSocket session now receives `attached`, `running`, and `terminal`
  events in order; the PTY process is reaped after the client disconnects.
  This closes the prior UI state gap where the initial running event could be
  emitted before browser attachment.
- The final live WebSocket handshake accepted resize and compact prompt
  messages, returned ordered `session`, `status`, `finalization`, `lwa`, and
  `terminal` events, then left `/api/codex/sessions` empty after close.
- The provider-free MCP handshake passed with protocol `2025-11-25`, 40 tools,
  3 resources, and 1 prompt.
- Installed package verification passed: Kitty `0.32.2-1ubuntu0.4` and
  libsixel-bin `1.10.3-3build1`; `kitty +kitten icat --help` exited zero.
- An isolated Xvfb Kitty window smoke run displayed the workspace screenshot
  through `kitty +kitten icat` and exited zero.
- `img2sixel` `1.10.3` encoded the workspace screenshot into a 548-byte Sixel
  stream. The LWA parser preserved both text boundaries and emitted one
  bounded graphics placeholder.
- With `TERM=xterm-kitty` and `KITTY_WINDOW_ID` set, Kitty capability detection
  returned true; with `COLORTERM=sixel`, Sixel detection returned true. ANSI
  color and OSC-8 wrappers reduced to readable text, while Kitty/Sixel control
  payloads reduced to bounded placeholders.
- Accessibility review corrected header toggle spacing, added visible input
  focus outlines, throttled screen-reader terminal announcements, and set
  explicit label/hint associations for controls and prompts. Static DOM checks
  confirm all form controls are labelled, the terminal canvas is keyboard
  reachable, and its live-region behavior is intentional. The headless render
  shows separated, keyboard-labelled controls.
- The web frame now reports WebGL/WebGPU availability, text image fallback,
  and provides a bounded pause/resume feed control.
- Verification: `15 passed` in the focused suite, JavaScript syntax check
  passed, compilation passed, and Ruff passed.
- Full suite excluding the unrelated host-sensitive credential fixture:
  `169 passed, 3 skipped`.
- Final rite regression set covering handshake scripts, Codex frame, native
  terminal frame, and terminal UI: `18 passed`; JavaScript syntax, Ruff, and
  record/link checks also passed.
- An attempted xdotool click/clipboard run in an isolated Xvfb display did not
  produce a visible Firefox window because that display had no window manager;
  it is recorded as unverified rather than a desktop interaction pass.
- Handoff handshake recorded in [WO-051 terminal handoff](WO-051-terminal-handoff-handshake.md):
  MCP, web route, WebSocket, native fallback, graphics fallback, and regression
  obligations are accepted; desktop interaction obligations remain explicitly
  open with reasons.
- Desktop interaction remediation is tracked in [WO-052 evidence](WO-052-desktop-interaction-evidence.md):
  a managed Xvfb/Openbox/Firefox/xdotool/xclip harness now exists, but this host
  lacks Openbox and passwordless sudo, so execution is correctly deferred.

## Outstanding rite checks

- Direct browser interaction with WebGL disabled, narrow viewport, long
  output, clipboard, focus, and screen-reader status beyond headless rendering.
- Real ANSI cursor movement and OSC-8 click behavior in a Linux Mint terminal.
- Native frame repeat with a non-Ghostty host is now closed: a real PTY with
  Ghostty variables removed selected `curses fallback frame`, exited zero, and
  left no Codex child. The remaining open items are desktop interaction gates.
