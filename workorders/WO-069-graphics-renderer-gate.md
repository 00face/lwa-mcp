# WO-069 — Graphics Renderer Gate

## Objective

Choose an honest graphics path per LWA surface and prevent Codex from receiving a graphics capability claim that the surface cannot render.

## Renderer policy

- Native Ghostty/Kitty: preserve host graphics capability and allow the child Codex process to use the host protocol.
- Native Sixel: preserve Sixel capability when detected.
- Native plain curses: use text fallback.
- Web canvas: use a browser-image renderer only after the decoder gate is implemented; otherwise advertise a browser gate pending and keep text fallback.

## Acceptance

- `/pets` no longer fails solely because LWA stripped valid native graphics capability.
- Web sessions do not falsely claim native Kitty/Ghostty graphics support.
- Capability diagnostics clearly identify the selected renderer and fallback.
- Graphics escape payloads never leak credentials or corrupt the text transcript.
- Unsupported graphics remain readable through a safe placeholder.
