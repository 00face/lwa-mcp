# TR-071 — Native Curses Image Placement

Status: complete

1. Define image-region geometry and lifecycle events.
2. Implement host capability and placement gates.
3. Add bounded asynchronous placement and cleanup.
4. Test resize, scroll, selection, interrupt, and exit restoration.
5. Perform a verified visual smoke test on Ghostty or Kitty.
6. Keep plain curses and screen-reader fallback gates explicit.

Verification: focused terminal/compositor tests pass; native placement is never
emitted for plain curses hosts.
