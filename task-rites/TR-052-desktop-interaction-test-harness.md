# TR-052 — Desktop Interaction Test Harness Rite

**Purpose:** close the reproducibility gap for visible browser interaction
tests identified by WO-051.

**Current result:** Desktop and structural screen-reader access promotion
complete. The managed harness passes, Openbox and Orca/AT-SPI are installed,
and LWA-Web exposes a keyboard-focusable accessible transcript plus dashboard
status live region. A live screen-reader announcement quality run remains
optional operator validation because announcement preferences are user-specific.

## Entry

Use the project virtual environment and a loopback dashboard. The rite may
install only the explicitly listed desktop-test packages when the operator
chooses the installer; the check mode is read-only.

## Action

1. Run `scripts/install-desktop-test-deps.sh --check`.
2. Run `scripts/desktop-interaction-smoke.sh --check`.
3. If ready, run `scripts/desktop-interaction-smoke.sh --run`.
4. Capture only status, window discovery, focus, clipboard, screenshot, and
   cleanup results.
5. Mark the screen-reader gate `deferred` unless an operator supplies an
   attached screen reader and an adapter command.

## Check

- Xvfb has a bounded lifetime.
- Openbox manages a visible Firefox window.
- xdotool activates the page and reaches the LWA prompt.
- xclip provides and reads a sentinel clipboard value.
- The browser receives a paste and a pointer click without exposing prompt
  contents in the report.
- Temporary processes and profiles are cleaned up.

## Promote when

The harness completes on the Linux Mint host with all desktop gates passing,
and a separate screen-reader adapter run records actual announcements.

## Why gates may remain open

The browser harness can prove visible pointer, keyboard, and clipboard paths,
but it cannot prove screen-reader behavior by itself. Screen readers require a
host accessibility stack and an attached AT client. If those are absent, the
correct result is `deferred`, not a false pass. Likewise, a missing window
manager is an environment prerequisite failure, not evidence that the LWA
workspace is broken.

## Rollback

Stop the harness, remove only its temporary display/profile, and continue using
the WO-051 headless and native fallback checks.
