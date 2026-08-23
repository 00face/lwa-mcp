# TR-077 — Animated and Movable Codex Pet

Status: complete

1. Resolve the Codex frame sequence and stable identity.
2. Bound frames, payload size, animation rate, and inactive-tab work.
3. Render the pet at the reduced default size.
4. Add Shift+drag with pointer capture and viewport clamping.
5. Add keyboard movement and accessible position announcements.
6. Test reconnect, tab, resize, low-resource, and missing-cache behavior.

## Result

Steps 1–6 are implemented. Automated verification passed; the active Codex
installation supplied 12 Stacky frames for the animation path.
