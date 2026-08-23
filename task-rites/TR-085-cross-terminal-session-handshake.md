# TR-085 — Cross-Terminal Session, Focus, and Cleanup Handshake Rite

Status: partial

Execute after TR-083 and TR-084.

1. Run a fake bridge session for each adapter mode.
2. Exercise LWA draft → consensus → review → explicit Codex send.
3. Exercise Codex slash commands, follow-up menus, modal confirmation,
   multiline input, copy/select, scroll, and resize.
4. Exercise graphics-capable, graphics-ineligible, and low-resource profiles.
5. Interrupt every stage and assert terminal restoration, socket cleanup,
   process cleanup, focus restoration, and bounded diagnostics.
6. Run screen-reader/accessibility assertions against status and transcript
   surfaces; record human visual checks separately where required.

Result: bridge routing, close, resize, socket permissions, redacted status,
and full regression checks pass. Desktop focus, screen-reader, and visual
placement checks remain operator-owned.
