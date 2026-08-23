# WO-036 - Provider Adapter Contract Hardening

**Status:** Partial — explicit usage reporting, timeout normalization, malformed
JSON handling, redaction, and offline construction coverage are implemented;
the complete per-adapter fixture matrix remains.
**Priority:** P0
**Parent:** WO-033
**Task rite:** [TR-036](../task-rites/TR-036-provider-adapter-contract-hardening.md)

## Objective

Bring all 19 services to a uniform adapter contract for request mapping,
response parsing, usage extraction, error redaction, timeout, and cancellation.

## Service Scope

Gemini, OpenAI, OpenRouter, Groq, Mistral, Cloudflare, SiliconFlow, Venice,
Pollinations, Cohere, Replicate, Stability, NVIDIA, Zai, Aion, Zenmux,
Cerebras, Blackbox, and Puter.

## Promotion Gate

Each service has deterministic fixtures for success, malformed response,
timeout, auth failure, quota headers, and sensitive-data redaction. No adapter
may report unknown usage as zero.

## Rollback

Disable only the failing adapter/provider and preserve the last known-safe route.

## Evidence

- `18` focused provider/ledger tests pass.
- Full offline suite passes: `124 passed, 3 skipped`.
- All `19` configured provider adapters construct without credentials or network.
- No successful provider completion or paid route was used; the locked Zai
  route made one failed live request and returned HTTP 429 overload.
