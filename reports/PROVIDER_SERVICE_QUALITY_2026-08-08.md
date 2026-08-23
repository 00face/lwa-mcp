# Provider/Service Pipeline Quality Report

**Date:** 2026-08-08  
**Scope:** All 19 configured provider services  
**Method:** Ratings combine adapter/configuration evidence, routing safety,
offline adapter tests, live-quality evidence, and telemetry/quota evidence.
No provider completion or catalog refresh was performed for this report.

| Service | Billing | Rating | Confidence | Evidence / blocker |
|---|---|---:|---|---|
| Gemini | Free quota | 8.0/10 | Measured adapter | Native completion/discovery tests; no fresh quota proof |
| OpenRouter | Free quota | 7.5/10 | Provisional | OpenAI-compatible path; no provider-specific live quality |
| Groq | Free quota | 7.5/10 | Provisional | Compatible adapter and stale quota history; no fresh proof |
| Mistral | Free quota | 7.5/10 | Provisional | Compatible adapter and stale quota history; no fresh proof |
| Cerebras | Free quota | 7.5/10 | Provisional | Compatible adapter and stale quota history; no fresh proof |
| Puter | User pays | 7.5/10 | Measured adapter | Native discovery/completion tests; not eligible for near-zero quota claim |
| Cloudflare | Free quota | 7.0/10 | Provisional | Configured compatible adapter; live models unsupported |
| SiliconFlow | Free quota | 6.5/10 | Conditional | Prior authentication/health concern remains unresolved |
| Pollinations | Free quota | 7.0/10 | Provisional | Compatible adapter configuration; no dedicated live quality |
| Cohere | Free quota | 7.0/10 | Provisional | Compatible adapter configuration; no fresh quota proof |
| NVIDIA | Free quota | 7.0/10 | Provisional | Compatible adapter configuration; no fresh quota proof |
| Zai | Free quota | 7.0/10 | Conditional | Locked proof route, but no fresh authoritative Zai snapshot |
| Aion | Free quota | 7.0/10 | Provisional | Compatible adapter configuration; no fresh quota proof |
| OpenAI | Paid | 7.0/10 | Provisional | Media adapter/configuration path; excluded from free-quota proof |
| Venice | Paid | 6.5/10 | Provisional | Paid route; no near-zero quota eligibility |
| Replicate | Paid | 6.5/10 | Provisional | Media adapter path; paid and outside proof scope |
| Stability | Paid | 6.5/10 | Provisional | Media adapter path; paid and outside proof scope |
| Zenmux | Paid | 6.5/10 | Provisional | Compatible adapter configuration; paid and outside proof scope |
| Blackbox | Paid | 6.5/10 | Provisional | Compatible adapter configuration; paid and outside proof scope |

## Interpretation

- **Measured adapter:** provider-specific adapter behavior has offline tests;
  this does not prove live quality or quota efficiency.
- **Provisional:** configuration and generic routing/adapter contracts exist,
  but provider-specific live quality evidence is absent.
- **Conditional:** a known health, authentication, billing, or quota blocker
  prevents a stronger rating.
- Free-quota services are not automatically near-zero proven. They still need
  fresh authoritative quota, complete telemetry, and two approved runs.
- Paid and user-pays services may be operationally useful, but are excluded
  from the near-zero free-quota proof program.

**Configured-service mean:** `7.0/10`. This is a readiness rating, not a live
quality score or quota proof.

## Uplift Work Orders

The promotion path for every row is tracked by the paired work orders and
task rites below:

- [`WO-036`](../workorders/WO-036-provider-adapter-contract-hardening.md) and [`TR-036`](../task-rites/TR-036-provider-adapter-contract-hardening.md): common adapter, usage, error, timeout, and redaction contracts.
- [`WO-037`](../workorders/WO-037-provider-health-quota-evidence.md) and [`TR-037`](../task-rites/TR-037-provider-health-quota-evidence.md): fresh provider/account health, quota, and billing evidence.
- [`WO-038`](../workorders/WO-038-provider-golden-quality-matrix.md) and [`TR-038`](../task-rites/TR-038-provider-golden-quality-matrix.md): repeated provider-specific quality fixtures.
- [`WO-039`](../workorders/WO-039-bounded-provider-operations.md) and [`TR-039`](../task-rites/TR-039-bounded-provider-operations.md): bounded discovery and warm control-plane behavior.
- [`WO-040`](../workorders/WO-040-provider-ten-eleven-audit.md) and [`TR-040`](../task-rites/TR-040-provider-ten-eleven-audit.md): independent 10/10 and 11/10 promotion audit.

No current row is promoted to 10/10 or 11/10 by this planning run.
