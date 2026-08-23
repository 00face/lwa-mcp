# WO-044 - Provider-Specific Probe Fixture Matrix

**Status:** Queued
**Priority:** P0
**Parent:** WO-041, WO-042
**Task rite:** [TR-044](../task-rites/TR-044-provider-probe-fixture-matrix.md)

## Objective

Prove the zero-payload accessibility contract for all 19 configured services
using deterministic provider-specific fixtures, without live completions.

## Service Scope

Gemini, OpenAI, OpenRouter, Groq, Mistral, Cloudflare, SiliconFlow, Venice,
Pollinations, Cohere, Replicate, Stability, NVIDIA, Zai, Aion, Zenmux,
Cerebras, Blackbox, and Puter.

## Promotion Gate

Each service has fixtures for configured, missing credential, disabled,
metadata success, authentication failure, rate limit, timeout, malformed
response, redaction, and unsupported probe endpoint behavior. Every fixture
asserts no task prompt or `RouteRequest` is sent.

Paid and user-pays services must be labeled by billing class; a reachable
metadata endpoint is not quota proof. SiliconFlow and Zai retain explicit
health/quota blocker evidence rather than being promoted by nominal fixtures.

## Rollback

Quarantine only the failing provider fixture or route. Never weaken the common
no-payload contract or substitute another provider's evidence.

## Evidence

The matrix must report 19/19 services, adapter family, probe endpoint policy,
fixture result, redaction result, and network-call count.
