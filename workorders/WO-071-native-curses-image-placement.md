# WO-071 — Native Curses Image Placement

Status: complete

## Objective

Place supported Codex image frames inside the native LWA curses layout without corrupting text, prompts, mouse selection, resizing, or terminal restoration.

## Scope

- Define an image region owned by the Codex Feed.
- Detect whether the host supports Kitty graphics or Sixel placement.
- Position images relative to the current frame geometry.
- Preserve the ASCII/text fallback when placement is unavailable.
- Clear and redraw image regions safely during resize and exit.

## Safety and performance

- Never write arbitrary graphics escape payloads directly into the curses screen.
- Enforce image byte, dimension, frame-count, and redraw-rate limits.
- Do not block PTY reads while placing or clearing an image.
- Restore the host terminal exactly on normal exit, interrupt, crash, and resize failure.

## Acceptance

- A supported image appears in the Codex Feed image region on a verified Kitty/Ghostty host.
- Text remains readable around the image.
- Prompt editing and mouse selection remain functional.
- Unsupported hosts receive a clear text fallback.
- Terminal state is restored after exit.

Evidence: bounded native placement is implemented in `terminal_frame.py`, gated
to Kitty/Ghostty hosts, with a text-only fallback and focused regression coverage.
