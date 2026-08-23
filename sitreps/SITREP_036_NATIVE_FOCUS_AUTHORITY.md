# SITREP 036 — Native focus authority

## Finding

The previous native binding was asymmetric. LWA→Codex used direct pane
selection, while Codex→LWA selected LWA and injected a synthetic Tab into the
LWA curses process. The latter depended on tmux keyboard translation and could
leave the visible pane and logical focus out of sync.

## Decision

Native mode now treats the active tmux pane as authoritative. Every supported
Tab form directly selects the opposite pane. No hidden process receives a
synthetic navigation key.

## Remaining operator gate

Automated tests validate command construction and safety. A real Ghostty/tmux
run remains necessary to verify terminal-specific key normalization and mouse
focus, because those behaviors cannot be proven by reducer tests alone.

