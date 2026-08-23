# WO-074 — Independent LWA Pet Renderer

Status: complete

## Hypothesis

We believe an LWA-owned pet catalog and renderer will make the configured Codex
pet visible consistently during native and web startup; we will have confidence
when a configured pet appears without a `/pets` command or Codex-generated image
escape sequence, and the same identity is exposed through an accessible text
label on both surfaces.

## Objective

Resolve the active pet configuration and render it independently in LWA, while
preserving Codex's own pet behavior when available and providing a deterministic
fallback when the asset or graphics capability is unavailable.

## Scope

- Read the effective `tui.pet` setting from the active Codex configuration with
  an explicit LWA override for testing and per-session selection.
- Define an LWA-owned pet catalog/asset contract that does not depend on Codex
  emitting startup graphics.
- Support bounded native rendering through Kitty/Ghostty, Sixel, or ANSI/text
  fallback according to detected host capability.
- Support bounded web rendering through the existing graphics layer with a
  stable asset URL/data contract and a text fallback.
- Render the configured pet during LWA startup after the surface is ready, and
  keep `/pets` as a refresh/reselect action rather than the only render path.
- Keep pet graphics outside accessible transcripts while exposing the pet name,
  renderer state, and fallback reason through accessible status text.

## Safety and performance gates

- Never execute, import, or trust arbitrary paths from `tui.pet` as code.
- Validate catalog names, asset MIME types, dimensions, byte size, and frame
  count before rendering.
- Do not expose Codex configuration contents, credentials, or raw graphics data
  in logs or screen-reader transcripts.
- Do not block PTY reads or provider startup while loading an asset; use a
  bounded local load and a deterministic placeholder on failure.
- Low-resource mode must prefer a small static/text asset and disable animation.
- Startup rendering must be idempotent and must not duplicate pets on reconnect,
  resize, tab switch, or repeated `/pets` commands.

## Acceptance criteria

- With `tui.pet = "stacky"`, `lwa` displays the LWA-owned Stacky pet on startup
  without waiting for Codex to emit an image sequence.
- `lwa-web` displays the same pet identity on startup in every new terminal tab.
- `/pets` refreshes the independent pet and reports the selected asset/renderer
  without leaking configuration or secrets.
- Native Kitty/Ghostty, Sixel, browser graphics, and plain text fallback paths
  are each deterministic and tested.
- Screen readers receive a concise status such as “Pet: stacky; renderer: ...”;
  they do not receive binary payloads, terminal escape sequences, or secrets.
- Missing, invalid, or unsupported pets produce a visible placeholder and a
  useful accessible status without crashing LWA or Codex.

## Validation signal

The startup smoke test records: configured pet name, selected renderer, render
event count, fallback state, and accessible status. Success means one startup
render per surface, no manual `/pets` command, and no graphics payload in the
accessible transcript.

Evidence: `pet_renderer.py` provides the bounded LWA-owned Stacky catalog,
config resolution, PNG frame generation, and text fallback. Native startup and
web-tab startup now render independently; `/pets` refreshes the independent
event path.
