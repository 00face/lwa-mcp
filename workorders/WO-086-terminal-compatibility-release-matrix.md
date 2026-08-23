# WO-086 — Terminal Compatibility Release Matrix

Status: partial — automated matrix is recorded; installed-terminal visual and assistive-technology checks remain open
Priority: P1
Dependencies: WO-082, WO-083, WO-084, WO-085
Task rite: [TR-086](../task-rites/TR-086-terminal-compatibility-release-matrix.md)

## Objective

Produce the release gate for the ten dictated terminals and prevent an
unverified terminal from being presented as supported.

## Required evidence

For each of Ghostty, Alacritty, Kitty, WezTerm, Tabby, Wave, GNOME Terminal,
Konsole, Terminator, Guake, LXTerminal, Cool Retro Term, Terminus, Rio, Black
Box, Ptyxis, tmux, Yakuake, sakura, lilyterm, XFCE Terminal, ratty, tilda, and
xterm, record:

- selected mode: `split` or `window`;
- executable/version detection result;
- launch and bridge handshake;
- working-directory and prompt-routing result;
- resize, focus, scroll, copy/select, and cleanup result;
- accessible transcript/screen-reader result;
- graphics capability and text fallback result;
- low-resource result and known limitations.

## Release gates

- No terminal is marked supported without an adapter test and a launch
  handshake.
- A missing desktop/launcher is a visible blocked prerequisite, not a hidden
  fallback.
- Full automated tests pass, and operator visual checks are labeled as such.
- The README and installer report the same matrix as the runtime.

## Rollback

Ship only adapters that pass the matrix; leave the rest explicitly disabled
with a documented remediation path.
