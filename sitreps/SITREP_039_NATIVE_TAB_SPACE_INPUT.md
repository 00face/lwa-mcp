# SITREP 039 — Native Tab space input

Even after tmux cleanup, terminal-specific key handling can deliver Tab to the
LWA curses process. Previously that path entered the focus broker and could
move logical focus or trigger a stale-pane failure.

Native mode now treats Tab and BackTab as prompt input and inserts five spaces.
Alt+Left and Alt+Right remain the only native pane-navigation controls.

