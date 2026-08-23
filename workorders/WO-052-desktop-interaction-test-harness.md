# WO-052 — Desktop Interaction Test Harness

**Status:** Partial — desktop harness execution is promoted; the installer,
prerequisite diagnostics, and regression coverage are green. A live
screen-reader interaction run remains operator-gated.
**Latest evidence:** [WO-052 evidence](../reports/WO-052-desktop-interaction-evidence.md)
**Parent:** WO-051
**Task rite:** [TR-052](../task-rites/TR-052-desktop-interaction-test-harness.md)

## Objective

Make the remaining WO-051 desktop tests reproducible instead of relying on an
unmanaged Xvfb display. Provide a low-resource, isolated test display with a
window manager, Firefox profile, clipboard fixture, screenshots, and explicit
skip/failure states.

## Contract

- The harness owns only its temporary X display, browser profile, window
  manager, and log directory.
- Browser interaction tests must exercise visible focus, clipboard paste, and
  pointer activation against the live `/codex` page.
- Missing host prerequisites must be reported as `skipped` with an install
  command, never silently counted as passed.
- Screen-reader testing remains an adapter gate; the harness must not claim
  assistive-technology conformance without an attached screen reader.
- Evidence contains paths, statuses, and redacted UI markers only.

## Required work

1. Add a user-runnable prerequisite installer and a non-mutating prerequisite
   check.
2. Add an Xvfb/Openbox/Firefox/xdotool/xclip smoke harness with bounded
   cleanup and isolated state.
3. Add regression tests for the harness contract and accessibility markers.
4. Run the harness where possible, record skipped prerequisites separately, and
   document the screen-reader adapter boundary.

## Acceptance

- `scripts/desktop-interaction-smoke.sh --check` emits an explicit JSON
  readiness result.
- `--run` either completes a desktop smoke flow or exits with a documented
  prerequisite status; it must not hang or leave child processes.
- The rite report distinguishes pass, skip, and fail for every gate.

## Rollback

Remove the optional harness and retain WO-051's headless, PTY, and static
accessibility checks. It must not alter the runtime LWA dashboard.
