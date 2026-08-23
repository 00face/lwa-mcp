# TR-115 — LWA prompt and response separation

1. Inventory every writer to `lwa_lines`, prompt editors, suggestions, modal
   rows, and scroll offsets.
2. Define region geometry and ownership contracts before changing rendering.
3. Add tests proving feed writes cannot mutate prompt text or cursor state.
4. Refactor rendering and scrolling into independent bounded regions.
5. Verify multiline paste, streaming responses, modals, resize, selection, and
   copy in both native and embedded modes.

