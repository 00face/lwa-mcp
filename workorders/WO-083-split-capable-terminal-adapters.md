# WO-083 — Split-Capable Terminal Adapters

Status: partial — Kitty and WezTerm split paths are covered; Ghostty remains an explicit window adapter pending a verified control surface
Priority: P0
Dependency: WO-082
Task rite: [TR-083](../task-rites/TR-083-split-capable-terminal-adapters.md)

## Objective

Forge reliable same-session split adapters for Ghostty, Kitty, and WezTerm,
with LWA on the left and Codex on the right. The adapter must prove that the
Codex bridge is attached to the intended pane before LWA reports readiness.

## Scope

- Ghostty split creation and pane-target handshake where the installed
  version exposes a usable control surface.
- Kitty `launch --location=split`/remote-control path with an explicit socket
  or window target.
- WezTerm CLI split-pane path with pane identity capture.
- Stable working directory, inherited environment policy, terminal size,
  cleanup, focus return, and pane-close handling.
- Capability downgrade to `window` when a split command is unavailable or
  cannot prove pane ownership.

## Acceptance

- LWA and Codex appear in separate same-session panes with deterministic
  left/right ownership.
- Codex output, prompt, slash menus, graphics, pets, and modals remain in the
  Codex pane; LWA output remains in the LWA pane.
- Resize, close, reconnect, Ctrl-C, and normal exit do not orphan bridges.
- A failed split handshake downgrades to the approved second-window adapter
  and tells the operator which mode was selected.
- Tests use fake terminal CLIs and verify exact command construction without
  launching a real desktop terminal.

## Rollback

Disable the affected split adapter and use its second-window adapter.
