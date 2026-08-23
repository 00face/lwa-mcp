# WO-061-065 — Prompt Interaction, Selection, Accessibility, and Verification

## Objective

Complete multiline prompt navigation, output selection/copying, accessible transcript interaction, golden PTY fixtures, and low-resource checks.

## Acceptance

- Prompt viewport follows the cursor through all lines.
- Native output can be selected and copied with a host clipboard helper.
- Web transcript can be copied and downloaded.
- Formatting fixtures cover redraws and long lines.
- Low-resource mode avoids shader and redraw overload.

## Status

Native prompt navigation and selection are implemented. Web transcript controls and wrapping are implemented. Golden fixture and performance-matrix tests remain next.
