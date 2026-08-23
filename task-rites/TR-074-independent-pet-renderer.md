# TR-074 — Independent LWA Pet Renderer

Status: complete

1. Write red-first tests for config resolution, explicit LWA override, unknown
   pets, and missing configuration.
2. Define a versioned LWA pet catalog with bounded asset metadata and a small
   static/text fallback for low-resource systems.
3. Implement a renderer-neutral `PetFrame`/render event contract separate from
   Codex PTY graphics events.
4. Implement native Kitty/Ghostty, Sixel, browser, and text fallback adapters;
   keep unsupported adapters honest and non-fatal.
5. Add startup lifecycle wiring so each native session and web tab performs one
   idempotent independent pet render after its surface is ready.
6. Make `/pets` refresh the independent renderer and expose only pet name,
   renderer, and safe fallback status to the feed/transcript layer.
7. Add accessibility checks for status naming, focus order, hidden binary data,
   and screen-reader output.
8. Run low-resource, resize, reconnect, multi-tab, malformed-asset, and missing-
   asset tests; then perform one visual native and one visual web smoke test.
9. Record the startup render count and fallback reason as the validation evidence
   for WO-074.

Verification: pet renderer, native frame, web workspace, accessibility, and
full regression tests pass; startup rendering is independent of Codex graphics
output.
