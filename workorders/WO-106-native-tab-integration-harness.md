# WO-106 — Two-pane native Tab integration harness

Create a disposable tmux server with LWA and a deterministic receiver pane.
Exercise both directions, assert the receiver gets exactly one semantic Tab,
and assert the active pane changes to the requested pane. The harness must
not use the real Codex process or user tmux server.

## Acceptance

Run 100 alternating handoffs with zero lost, duplicated, or misdirected keys;
capture binding definitions and active-pane IDs on failure; clean up the
temporary tmux server even after interruption.
