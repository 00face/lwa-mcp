# WO-082–086 Terminal Compatibility Evidence

Date: 2026-08-22
Environment: Linux Mint host, Python 3.12 virtual environment

## Automated evidence

- Focused launcher, bridge, Codex frame, and terminal-frame tests: **57 passed**.
- Full repository suite from the repository root: **247 passed, 3 skipped**.
- Ruff checks for the changed launcher, bridge, session, launch, and tests:
  **passed**.
- Python compilation for `src/lwa_mcp`: **passed**.
- No provider execution, paid request, or credential value was used.

## Adapter matrix

| Terminal | Mode in implementation | Evidence | Notes |
|---|---|---|---|
| Ghostty | tmux-backed split when tmux is available; window when forced/unavailable | bootstrap test | Linux Ghostty uses tmux because its reliable CLI automation is new-window oriented. |
| Kitty | split when `KITTY_LISTEN_ON` is present; otherwise window | command-construction test | Uses guarded Kitty remote-control split. |
| WezTerm | split when `WEZTERM_PANE` is present; otherwise window | registered adapter | Not discoverable on current `PATH`; uses CLI split-pane path when available. |
| Alacritty | window | fake-launcher test | Real desktop inspection remains operator work. |
| Tabby | window | fake-launcher test | Real desktop inspection remains operator work. |
| Wave | window | registered adapter | Not discoverable on current `PATH`. |
| GNOME Terminal | window | fake-launcher test | Real desktop inspection remains operator work. |
| Konsole | window | fake-launcher test | Real desktop inspection remains operator work. |
| Terminator | window | fake-launcher test | Real desktop inspection remains operator work. |
| Guake | window | fake-launcher test | Real desktop inspection remains operator work. |
| LXTerminal | window | adapter test | Installed and discoverable on the current host. |
| Cool Retro Term | window | adapter test | Installed and discoverable on the current host. |
| Terminus | window | adapter test | Installed and discoverable on the current host. |
| tmux | split inside active tmux; otherwise window adapter | adapter test | Split requires `TMUX`; no split is claimed outside tmux. |
| Yakuake | window | adapter test | Installed and discoverable on the current host. |
| sakura | window | adapter test | Installed and discoverable on the current host. |
| lilyterm | window | adapter test | Installed and discoverable on the current host. |
| XFCE Terminal | window | adapter test | Installed and discoverable on the current host. |
| ratty | window | adapter test | Installed and discoverable on the current host. |
| tilda | window | adapter test | Installed and discoverable on the current host. |
| Rio | window | registered adapter | Not discoverable on current `PATH`. |
| Black Box | window | registered adapter | Not discoverable on current `PATH`. |
| Ptyxis | window | registered adapter | Not discoverable on current `PATH`. |

## Security and accessibility evidence

- Bridge socket parent directory is mode `0700`; socket is mode `0600`.
- Bridge events expose readable text/status and capability state, not raw
  credentials or graphics payloads.
- LWA/Codex ownership and keyboard/pane isolation remain covered by existing
  frame tests.
- An unavailable adapter fails visibly; no current-terminal untouched-Codex
  fallback is introduced.

## Lifecycle hardening

- A bridge now self-terminates after 30 seconds without an LWA attachment.
- Failed native-frame attachment removes the temporary socket and terminates
  the failed launcher child.
- Normal frame shutdown continues to use the bridge close command, allowing
  the Codex child and terminal bridge to exit cleanly.

## Open operator gate

A human desktop run is still required for each installed graphical terminal to
confirm window placement, focus return, mouse selection, screen-reader output,
and visual graphics behavior. This is an evidence gate, not a reason to claim
an untested terminal as complete.
