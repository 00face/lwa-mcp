# SITREP 017 — Puter Discovery Adapter Rite

**Date:** 2026-08-02  
**Status:** Complete; adapter implemented and verified  
**Related work order:** [WO-019](../workorders/WO-019-puter-discovery-adapter.md)

## Situation

The generic OpenAI-compatible Puter `/models` probe reports HTTP 404. Official
Puter documentation describes a native model-listing source, so adapter-specific
schema confirmation is required before implementation.

## Boundary

One bounded redacted request may establish the response shape. No endpoint,
credential, billing, or routing rewrite is authorized by this SITREP.

## Acceptance

Implement only a documented, fixture-tested parser; otherwise retain the
generic probe and record the blocker.

## Result — 2026-08-02

The bounded documented endpoint returned HTTP 200 with 538 models. `PuterAdapter`
now handles native discovery, while completion routing retains Puter's existing
OpenAI-compatible base URL. No secret was printed.
