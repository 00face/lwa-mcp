# WO-085 — Cross-Terminal Session, Focus, and Cleanup Handshake

Status: partial — bridge protocol, orphan timeout, failed-launch cleanup, permissions, and focused routing pass; desktop focus/visual gates remain operator-owned
Priority: P0
Dependencies: WO-083, WO-084
Task rite: [TR-085](../task-rites/TR-085-cross-terminal-session-handshake.md)

## Objective

Make the two launch conventions behave as one LWA session regardless of host
terminal. Focus, input ownership, accessible text, graphics, pets, modals,
resize, cancellation, and cleanup must remain deterministic.

## Acceptance

- LWA prompt input never leaks into Codex prompt input before explicit
  finalization and send.
- Codex slash-command autocomplete/follow-up/modal content remains in the
  Codex surface and is selectable/copyable.
- Tab and mouse focus changes are visible; every action has a keyboard path.
- Screen readers receive pane/window identity, progress, errors, and readable
  transcript text, but not raw ANSI, graphics payloads, prompts, or secrets.
- Pets and optional graphics are capability-gated; their absence never blocks
  text interaction.
- Ctrl-C, Alt-Enter, Escape, terminal close, bridge EOF, and LWA shutdown
  restore the original terminal and remove temporary sockets/processes.

## Rollback

Turn off optional graphics/pets and retain the verified text bridge, or disable
the affected adapter while keeping the dashboard available.
