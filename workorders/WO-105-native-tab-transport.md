# WO-105 — Native Tab transport contract

## Problem

The last working trace contained `tab_received native=True`; current native
launches often stop at startup `request_lwa`. The failure is before the LWA
focus broker, in Ghostty/tmux key transport.

## Objective

Replace the conditional pane-history handshake with explicit, inspectable
bindings for the authoritative LWA and Codex pane IDs. Tab from LWA must
select Codex; Tab from Codex must deliver one Tab byte to LWA.

## Gates

- no `select-pane -l` or inferred last-pane behavior;
- bindings target exact pane IDs;
- Tab, Ctrl-I, and Shift+Tab are covered;
- every handoff emits a transport trace before the controller trace;
- an unavailable binding fails visibly and leaves the current prompt usable.
