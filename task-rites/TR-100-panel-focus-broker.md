# TR-100 — Focus broker rite

1. Identify LWA and Codex pane IDs at startup.
2. Expose `focus_lwa`, `focus_codex`, and `toggle_focus` only through the broker.
3. Confirm actual tmux focus after each command.
4. Treat Tab, Ctrl-I, Shift+Tab, and mouse pane clicks as broker requests.
5. Record requested/actual focus without prompt contents or secrets.
6. Test 100 alternating transitions and stale-copy-mode recovery.
