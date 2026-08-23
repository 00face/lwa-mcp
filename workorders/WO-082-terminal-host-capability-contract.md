# WO-082 — Terminal Host Capability Contract and Matrix

Status: complete — capability contract, override, redacted records, and matrix tests implemented
Priority: P0
Dependencies: WO-076, WO-051
Task rite: [TR-082](../task-rites/TR-082-terminal-host-capability-contract.md)

## Objective

Define one truthful host contract for the supported terminal list:
Ghostty, Alacritty, Kitty, WezTerm, Tabby, Wave, GNOME Terminal, Konsole,
Terminator, Guake, LXTerminal, Cool Retro Term, Terminus, Rio, Black Box,
Ptyxis, tmux, Yakuake, sakura, lilyterm, XFCE Terminal, ratty, tilda, and
xterm.

LWA has exactly two launch conventions:

1. A verified split-capable host places LWA and Codex in one terminal session.
2. A host without a verified split adapter opens Codex in a second terminal
   window while LWA remains in the current terminal.

There is no silent third fallback. If neither convention is available, LWA
must stop with an actionable diagnostic.

## Scope

- Detect the current host using environment signals and executable discovery.
- Represent capabilities explicitly: `split`, `window`, `graphics`,
  `clipboard`, `mouse`, `sixel`, `kitty_graphics`, and `accessible_text`.
- Keep detection side-effect free until the selected launch adapter is run.
- Record adapter name, terminal name, mode, command availability, and reason
  codes without recording prompts, tokens, or environment secrets.
- Allow an explicit `LWA_TERMINAL_ADAPTER` override for controlled testing.

## Acceptance

- Each named terminal resolves to either `split` or `window` when installed.
- An absent executable or failed capability probe is visible to the user.
- The selected mode is shown before launch and in debug output.
- No adapter claims split support without a successful launch handshake.
- Unit tests cover every terminal name, ambiguous environment, missing binary,
  override, and contradictory capability signal.

## Accessibility and safety gates

- Diagnostics are plain text, screen-reader readable, and bounded.
- Capability status never includes raw environment values or credentials.
- Keyboard-only users can select or cancel the launch mode.

## Rollback

Disable automatic host selection and require an explicit adapter override;
retain the existing dashboard launcher.
