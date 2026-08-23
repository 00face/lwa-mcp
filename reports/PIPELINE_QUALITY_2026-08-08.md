# Canonical Pipeline Quality Report

**Date:** 2026-08-08  
**Scope:** All 12 `TaskKind` pipelines  
**Rating rule:** Offline benchmark coverage earns measured confidence; contract/test-only coverage is provisional. Global telemetry is currently invalid, so no pipeline receives a live-proof rating.

| Pipeline | Rating | Confidence | Evidence |
|---|---:|---|---|
| `quick_response` | 7.5/10 | Provisional | Contract and lifecycle path covered; no golden case |
| `query` | 8.5/10 | Measured offline | Golden case, schema/literal retention, lifecycle tests |
| `conversation_compression` | 7.5/10 | Provisional | Contract and lifecycle path covered; no golden case |
| `token_optimization` | 7.5/10 | Provisional | Contract and lifecycle path covered; no golden case |
| `document_editing` | 8.5/10 | Measured offline | Golden case and required-literal preservation |
| `sitrep` | 8.5/10 | Measured offline | Golden case and structured quality checks |
| `planning` | 7.5/10 | Provisional | Contract and lifecycle path covered; no golden case |
| `consensus` | 8.5/10 | Measured offline | Golden case, free-route policy, synthesis path |
| `verification` | 8.5/10 | Measured offline | Golden case and repreflight failure coverage |
| `coding_aux` | 8.5/10 | Measured offline | Golden case and lifecycle/regression coverage |
| `image_generation` | 7.0/10 | Provisional | Capability/metadata contract; no golden media run |
| `video_generation` | 7.0/10 | Provisional | Capability/metadata contract; no golden media run |

## Rating Interpretation

- **Measured offline:** the pipeline is represented in the seven-case mock
  benchmark; this proves schema/constraint behavior, not provider quality.
- **Provisional:** contract and lifecycle behavior are tested, but a dedicated
  golden quality fixture is missing.
- All ratings are reduced by the global telemetry gate: current records are
  not eligible for live quota proof.
- The simple mean is **7.9/10**; it is not a release score because six
  pipelines lack direct golden fixtures and live attribution is invalid.

## Next Coverage

Add golden fixtures for `quick_response`, compression, token optimization,
planning, image, and video before using this report as a comparative quality
baseline. Recompute after WO-032 through WO-035 promote.
