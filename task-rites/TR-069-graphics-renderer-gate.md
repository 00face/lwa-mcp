# TR-069 — Graphics Renderer Gate

1. Detect host graphics capabilities.
2. Select native, Sixel, browser-pending, or text-fallback mode per surface.
3. Preserve native capability variables only for native sessions.
4. Prevent web sessions from making unsupported graphics claims.
5. Test `/pets`, graphics capability metadata, fallback text, and secret redaction.
6. Keep browser image decoding as an explicit follow-up gate.
