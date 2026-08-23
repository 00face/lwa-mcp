# WO-107 — Native binding cleanup and rollback

Scope all temporary Tab/Ctrl-I/Shift+Tab/Ctrl-C/Ctrl-Q bindings to the LWA
window and restore or remove only bindings created by LWA. Verify cleanup on
normal exit, Ctrl+Q, startup failure, and interrupted Codex startup.

## Gate

No stale binding, temporary pane, or temporary tmux server remains after the
harness or a failed launch.
