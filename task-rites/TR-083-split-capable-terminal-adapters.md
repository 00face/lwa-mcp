# TR-083 — Split-Capable Terminal Adapters Rite

Status: partial

Execute after TR-082.

1. Implement fake-CLI fixtures for Ghostty, Kitty, and WezTerm.
2. Test command construction, working directory, environment filtering, and
   pane identity handshakes.
3. Exercise Codex bridge attach, resize, input routing, output routing, close,
   and reconnect for each adapter.
4. Verify slash-command menus and modals stay below the Codex prompt inside
   the Codex pane stacking/ownership boundary.
5. Verify keyboard focus, Tab traversal, screen-reader status, mouse
   selection, clipboard behavior, and low-resource mode.
6. Record which adapters were verified as `split`; mark the rest `window`.

Result: Kitty remote-control and WezTerm split command paths pass automated
coverage. Ghostty is classified as a safe second-window path until a verified
control surface is available; visual desktop inspection remains open.
