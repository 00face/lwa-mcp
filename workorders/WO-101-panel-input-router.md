# WO-101 — Panel input router

Normalize terminal input into semantic events before dispatch:

`FocusNext`, `FocusPrevious`, `SubmitLwa`, `SubmitCodex`, `Copy`, `Exit`,
`ScrollUp`, `ScrollDown`, `Paste`, `PetCommand`, and `PrintableText`.

Acceptance: raw Tab, Ctrl-I, Shift+Tab, mouse clicks, and terminal-specific
escape sequences map to the same semantic event; Ctrl+C never becomes an
interrupt in LWA-owned mode; Ctrl+Q is the only combined-surface exit.
