# TR-089 — Native Split Visual Acceptance Rite

Status: partial — fresh Ghostty layout evidence recorded; remaining interaction checks are open

Execute after TR-087 and TR-088.

1. Start from a fresh Ghostty session with no stale `lwa-*` tmux sessions.
2. Capture the startup screen and verify the expected left/right layout.
3. Run a short LWA prompt, review the synthesized Codex prompt, and send it
   with Alt+Enter.
4. Exercise `/model`, `/permissions`, `/pets`, autocomplete, and a modal in
   the Codex pane.
5. Exercise Codex scrolling, mouse selection/copy, resize, and one Ctrl+C
   interrupt followed by clean exit.
6. Repeat the text-only fallback check in a non-graphics terminal.
7. Record screenshots and a gate table. Keep this rite open if any visual
   inspection is unavailable; automated tests alone cannot close it.
