# WO-104 — Panel lifecycle and exit contract

Centralize startup, native split creation, tmux binding installation, session
close, signal handling, and cleanup. Bindings must be scoped to the LWA-owned
window and removed on every exit path.

Acceptance: Ctrl+Q exits both panes; Ctrl+C copies without freezing input;
startup failures leave no stale bindings or panes; repeated launch/exit cycles
do not accumulate tmux bindings.
