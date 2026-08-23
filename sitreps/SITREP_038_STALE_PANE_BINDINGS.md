# SITREP 038 — Stale pane bindings

The visible Tab/Shift+Tab text was a native footer regression: the renderer
still advertised the embedded-mode controls. More importantly, a fatal exit
could bypass the old cleanup path, leaving root tmux bindings behind for the
next launch.

Native startup now clears the legacy navigation keys before installing only
Alt+Left and Alt+Right. Embedded mode continues to advertise and use Tab-based
focus switching.

