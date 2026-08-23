# TR-102 — Renderer boundary rite

1. Make layout calculation independent of terminal writes.
2. Give pet placement a dedicated compositor effect with stable image IDs.
3. Apply cursor visibility/position once per frame after all effects.
4. Never place graphics while the prompt input transaction is being handled.
5. Test rapid animation, pet switching, resize, and modal states together.
