# SITREP 008 — Official Media Pipeline

**Date:** 2026-07-25  
**Status:** Official image/video pipeline integrated and offline-validated;
operator live media requests remain pending.

## Implemented

- Added official OpenAI media adapter using `OPENAI_API_KEY`.
- Added `gpt-image-1` image generation with local file persistence.
- Added asynchronous `sora-2` video jobs with polling and MP4 download.
- Added `generate_video` MCP tool with normal preflight and paid consent gates.
- Kept Bingart disabled because it is an unofficial cookie-based, image-only
  adapter.

## Verification

- Dependency-backed suite: **38 passed**.
- Ruff, compilation, and wheel build: PASS.
- No live image or video request was made.

## Operator boundary

Use the existing `OPENAI_API_KEY` setup. Media generation is paid API usage;
the local cap and `paid_only` approval policy remain active. OpenAI’s official
video API is asynchronous and supports `sora-2` jobs; generated files are
written under the Lwa state `generated` directory.
