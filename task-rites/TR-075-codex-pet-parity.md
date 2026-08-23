# TR-075 — Codex Pet Parity and Fallback Integrity

Status: complete

1. Capture a red-first fixture of the active Codex `tui.pet` value and the
   authoritative Stacky asset/protocol emitted by the installed Codex.
2. Define the pet asset identity/version and reject mismatched catalog assets.
3. Refactor `PetFrame` so identity, source, renderer, and fallback state are
   explicit and safe for accessible status output.
4. Remove generic ASCII-art substitution from the primary configured-pet path.
5. Implement native and web rendering of the authoritative asset with bounded
   byte/dimension/frame limits.
6. Add explicit unavailable-asset and unsupported-renderer states.
7. Test startup, `/pets`, reconnect, resize, multiple tabs, low-resource mode,
   and screen-reader status output.
8. Run visual parity smoke tests against standalone Codex, `lwa`, and `lwa-web`.

## Rite result

All steps are implemented. Codex’s configured `stacky` value resolves to the
Codex frame cache, the web/native renderers use the same PNG frame and SHA-256
identity, and the Kitty/Ghostty placement path was exercised. Opaque payload
redaction and missing-cache fallback are covered by regression tests.
