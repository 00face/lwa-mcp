# WO-052 Desktop Interaction Harness Evidence

**Recorded:** 2026-08-21  
**Status:** Desktop harness promoted; screen-reader interaction remains
operator-gated

## Checks

- Shell syntax validation passed for the installer and smoke harness.
- Harness regression tests passed: `17 passed` across desktop harness, Codex
  frame, native terminal frame, and terminal UI coverage.
- Full suite excluding the host-sensitive credential fixture passed: `172
  passed, 3 skipped`. The targeted Ruff check, shell syntax checks, and
  JavaScript syntax check passed. A repository-wide Ruff run still reports two
  pre-existing issues in `tests/test_installer.py` (unused `os` import and
  import ordering), outside this work order.
- `scripts/install-desktop-test-deps.sh --check` now returns `status=ready` for
  Xvfb, Openbox, Firefox, xdotool, xclip, Orca, AT-SPI, and ImageMagick.
- `scripts/desktop-interaction-smoke.sh --run` returned `status=passed`, with
  visible Firefox window discovery, X11 clipboard round-trip, pointer and
  keyboard actions, bounded cleanup, and screenshot evidence at
  `/tmp/lwa-desktop-interaction-465432.xwd`.
- The screenshot was converted to PNG and visually inspected; it shows the
  rendered Codex Feed, LWA Feed, LWA Prompt, and Send through LWA control.
- LWA-Web now exposes an expandable `Accessible text transcript` with a
  keyboard-focusable `role="log"` region. Canvas rendering remains visual,
  while the transcript carries bounded readable Codex text for screen readers.
- The main LWA dashboard notice is now a polite `role="status"` live region.
- Focused accessibility/runtime regression set: `17 passed`; live `/codex`
  serves the transcript marker and the dashboard serves the status marker.
- The dashboard route remains reachable; the prior live route and WebSocket
  checks remain valid from WO-051.

## Why execution is deferred

The desktop prerequisite installation completed on the host. Orca `46.1` and
the AT-SPI bus launcher are available. The installer command remains the
reproducible setup path:

```sh
scripts/install-desktop-test-deps.sh --install
scripts/desktop-interaction-smoke.sh --run
```

The first attempt was blocked by sudo, then the operator completed the install;
the final readiness check is green.

The smoke harness owns a temporary display/profile and retains only a root
window screenshot plus redacted status metadata. It reports missing
prerequisites as `skipped`, not `passed`.

## Assistive technology boundary

Orca `46.1` and AT-SPI are installed. The structural access gate is closed by
the transcript/status implementation and regression checks. A live announcement
quality run with Orca remains optional operator validation; it is not inferred
from browser rendering.
