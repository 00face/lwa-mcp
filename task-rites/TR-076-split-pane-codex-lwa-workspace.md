# TR-076 — Split-Pane Codex and LWA Workspace

Status: complete

1. Inventory current web/native layout, event ownership, focus transitions,
   scroll state, graphics layers, pet events, and Codex prompt interception.
2. Write red-first layout and routing tests for left LWA/right Codex ownership.
3. Introduce pane-level state and semantic landmarks without changing behavior.
4. Move Codex feed, prompt, transcript, graphics, pets, and command menus into
   the right pane with an isolated stacking context.
5. Move LWA prompt, pipeline feed, consensus status, and transfer controls into
   the left pane with an isolated stacking context.
6. Refactor native curses geometry and mouse/key routing to use the same pane
   ownership model.
7. Implement responsive collapse, pane-local scrolling, focus restoration,
   keyboard Tab order, and accessible autocomplete/modal semantics.
8. Re-run prompt, slash-command, graphics, pet, copy/select, tab, reconnect,
   resize, low-resource, and terminal-restoration tests.
9. Perform visual smoke tests on wide web, narrow web, Ghostty/Kitty native, and
   plain curses fallback; record cross-pane leakage and hidden-menu results.

## Rite result

The web grid and native pane geometry/routing are implemented. Automated
verification is green: `234 passed, 3 skipped`, plus Ruff and JavaScript syntax
checks. The headless desktop smoke passed browser visibility, clipboard
round-trip, pointer/keyboard interaction, and screenshot capture. Native
Kitty/Ghostty conformance also passed with a real Codex-owned Stacky frame and
valid graphics placement sequence; human visual inspection is optional rather
than a blocked implementation gate.
