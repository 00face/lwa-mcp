# WO-075 — Codex Pet Parity and Fallback Integrity

Status: complete — Codex-owned Stacky asset discovered and verified

## Objective

Stop LWA from displaying an undesired ASCII substitute when Codex is configured
with the Stacky pet. Resolve and render the same active Codex pet identity and
asset, or clearly report that the Codex asset cannot be rendered.

## Hypothesis

We believe using the active Codex pet asset/protocol, instead of silently
substituting an LWA-authored ASCII sprite, will make LWA startup visually match
Codex; confidence requires the same pet identity and a one-to-one visual asset
check in native and web smoke tests.

## Scope

- Determine the effective Codex pet key and the authoritative asset source or
  graphics protocol for `tui.pet = "stacky"`.
- Remove the unconditional LWA ASCII-art substitute from the primary pet path.
- Add an explicit asset identity/version to pet events so the renderer can prove
  which pet it displayed.
- Render the authoritative Stacky asset independently in native and web modes
  when possible, while retaining Codex PTY graphics as a compatibility path.
- If the authoritative asset is unavailable, show a labeled “Codex pet asset
  unavailable” state rather than a visually misleading robot or ASCII pet.
- Keep `/pets` as a refresh action and preserve the configured pet across tabs,
  reconnects, and resize.

## Acceptance

- A configured Stacky pet never renders as an unlabeled generic ASCII robot.
- Native LWA and LWA-Web report the same pet key and asset identity.
- The startup render does not require the user to reconfigure or re-run `/pets`.
- Asset failure is visible, non-fatal, and accessible; no silent substitution.
- Accessible status exposes pet name, asset identity, and renderer state without
  exposing configuration contents or binary payloads.
- Tests cover configured, missing, unknown, mismatched, and unavailable assets.

## Validation signal

For each surface, record exactly one startup pet event with `name=stacky`, an
authoritative asset identifier, and no generic ASCII fallback. A visual smoke
test confirms the native and web images match the configured Codex pet.

## Execution evidence

- `PetFrame` now carries `source`, `asset_id`, and `authoritative` metadata.
- The configured-pet path no longer emits the built-in ASCII sprite when an
  authoritative asset directory is absent; it reports an accessible,
  non-fatal unavailable state instead.
- Bounded PNG loading is implemented for native and browser renderers, with
  name, size, signature, dimension, and pixel-count validation.
- `/pets` and startup use the same independent renderer path.
- Automated pet tests pass, including authoritative fixture, alias, missing,
  and fallback behavior.
- Long opaque base64-shaped payloads are now redacted from terminal/accessibility
  text surfaces so image or token blobs cannot masquerade as readable output.
- The local Codex cache now supplies the authoritative Stacky frame, so the
  unavailable state is reserved for installations that genuinely lack the
  Codex cache.
- Native conformance verified: the exact authoritative frame is placed through
  the Kitty/Ghostty graphics sequence with `a=T` and the same asset identity.
