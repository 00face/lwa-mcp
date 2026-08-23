# WO-084 — Second-Window Terminal Adapters

Status: complete — all seven named window adapters have argv-level coverage
Priority: P0
Dependency: WO-082
Task rite: [TR-084](../task-rites/TR-084-second-window-terminal-adapters.md)

## Objective

Provide explicit second-window launchers for terminals that do not have a
verified same-session split adapter: Alacritty, Tabby, Wave, GNOME Terminal,
Konsole, Terminator, and Guake. The same contract also remains available as
the compatibility path for Ghostty, Kitty, and WezTerm.

## Acceptance

- Each named launcher receives the selected working directory and the Codex
  bridge command without shell-string interpolation of user prompt text.
- LWA remains responsive in the current terminal while Codex runs in the new
  window.
- The bridge socket is authenticated by an unguessable per-session path,
  permissioned to the user, and removed after shutdown.
- Window launch failure gives a bounded, screen-reader-readable error and does
  not leave a stale “Codex connected” state.
- Tests cover command syntax, quoting, spaces in paths, missing binaries,
  desktop absence, child exit, and cleanup for all seven launchers.

## Terminal-specific policy

The adapter must not claim graphical features merely because the terminal
process launched. Graphics and clipboard capabilities are reported separately;
text and accessible transcript behavior remain mandatory.

## Rollback

Disable only the failing launcher and retain other verified adapters. Do not
silently run Codex in the LWA-owned terminal.
