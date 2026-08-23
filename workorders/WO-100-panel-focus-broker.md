# WO-100 — Focus broker and key ownership

Create a `FocusBroker` that owns LWA/Codex focus transitions for embedded and
native modes. Terminal adapters report whether they consumed Tab, Shift+Tab,
mouse focus, Ctrl+C, or Ctrl+Q. The controller must not infer focus from the
last key or tmux's last-pane history.

Acceptance: a focus trace records requested target, actual target, source,
input sequence, and result for every transition; failed handoffs retry once
and surface a recoverable status.
