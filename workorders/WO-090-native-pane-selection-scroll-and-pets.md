# WO-090 — Native Pane Selection, Scroll, and Pet Visibility

Status: partial — LWA pane-local selection/scroll isolation and tmux pet passthrough implemented; native Codex scrollbar remains host-owned
Priority: P0
Dependencies: WO-087, WO-089
Task rite: [TR-090](../task-rites/TR-090-native-pane-selection-scroll-and-pets.md)

## Objective

Keep mouse selection and scrolling bounded to the pane that owns them, and
make the configured pet visible in native split mode even when tmux graphics
passthrough is unavailable.

## Acceptance

- LWA mouse selection never enters or highlights the native Codex pane.
- LWA history has an independent scrollbar and PageUp/PageDown/mouse-wheel
  state.
- Codex retains native selection and scroll behavior in its own pane.
- Kitty graphics sent through tmux use the required passthrough wrapper.
- The configured pet is visible as an image when graphics pass through and as
  an ASCII fallback otherwise.
- Tests prove selection-region isolation, scrollbar state, graphics wrapping,
  and pet fallback behavior.

## Open boundary

Native Codex owns the right pane, so its scrollbar appearance is controlled by
Codex/the host terminal rather than LWA. A graphical scrollbar drawn by LWA
over that pane would violate native Codex ownership. The right-pane scroll
interaction remains native and is visually verified in TR-089/TR-090.

