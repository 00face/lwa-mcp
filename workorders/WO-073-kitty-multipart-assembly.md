# WO-073 — Multi-part Kitty Image Assembly

Status: complete

## Objective

Assemble Kitty graphics transmitted across multiple control sequences into complete bounded image frames.

## Scope

- Track Kitty image identifiers and chunk ordering.
- Support continuation flags and final-chunk detection.
- Handle interleaved image IDs without mixing payloads.
- Expire incomplete assemblies by size, time, count, and session shutdown.
- Emit only complete validated frames to the compositor.

## Safety and performance

- Bound concurrent image assemblies per session.
- Bound total pending bytes and per-image bytes.
- Reject duplicate, out-of-order, malformed, and expired chunks safely.
- Never retain incomplete payloads after session close.

## Acceptance

- Single-part and multi-part Kitty fixtures produce equivalent frames.
- Interleaved image streams remain isolated.
- Incomplete assemblies expire deterministically.
- Oversized and malicious chunk streams cannot exhaust memory.
- Text output remains ordered while image assembly occurs asynchronously.

Evidence: image-ID keyed assembly, split-read buffering, interleaving isolation,
compression support, raw RGB/RGBA conversion, and pending-byte limits are
implemented in `image_compositor.py`.
