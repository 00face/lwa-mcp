# WO-059/060 — Adaptive Native and Web Layout

## Objective

Ensure the Codex Feed receives flexible space while prompts, status, tabs, and accessibility controls remain usable across terminal and browser sizes.

## Acceptance

- Native layout retains usable prompt rows above the minimum terminal size.
- Web layout wraps controls and prompts on narrow screens.
- Output wraps rather than truncates at a fixed character count.
- Resize events update PTY geometry without freezing input.

## Status

Web wrapping and transcript controls implemented; native compact-layout and resize-matrix work remain open.
