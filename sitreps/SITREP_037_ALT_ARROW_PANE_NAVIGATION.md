# SITREP 037 — Alt-arrow pane navigation

The native focus transport now uses explicit directional commands rather than
a toggle key. This avoids ambiguity about the current logical focus and leaves
Tab available for prompt editing and Codex autocomplete.

The bindings select panes directly and do not inject bytes into the destination
process. Legacy Tab bindings are still removed during cleanup so an older LWA
launch cannot retain them.

