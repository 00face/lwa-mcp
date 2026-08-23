# TR-103 — Scroll and selection rite

1. Model each pane's feed viewport independently.
2. Keep prompt cursor coordinates in logical lines, not screen rows.
3. Convert mouse coordinates through the active pane's wrapping map.
4. Exit copy mode before returning focus to a prompt.
5. Verify scroll, select, copy, Tab, and pet switch in alternating sequences.
