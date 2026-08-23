# SITREP 024: LWA Token and Tool-Call Efficiency

**Date:** 2026-08-08  
**Scope:** LWA Plugin / Lwa MCP routing, handshake, prompts, tool calls, and quality-preserving usage reduction  
**Status:** Optimization audit complete; 10/10 promotion remains blocked by live evidence gaps.

## Executive Assessment

The current Lwa MCP design is strong on governed execution but is not yet instrumented tightly enough to prove a `<0.1% usage` target. That target must first define its denominator. `<0.1% of quota` is measurable; `<0.1% of a response` is usually not a useful requirement because a high-quality answer may legitimately require more than that.

### Current Rating

| Surface | Rating | Evidence | Main deduction |
|---|---:|---|---|
| Lwa MCP routing and safety | 9.0/10 | Locked lifecycle, explicit approval, single-use plans, no dynamic rerouting, prompt hashes, redaction, compact responses, and regression coverage | Historical `not_reported` records and no independent live benchmark signoff |
| LWA Plugin / host-facing workflow | 8.0/10 | Cached handshake tooling, warm-session entrypoint, workflow records, and compact transport | Live handshake times out; host-owned plugin overhead is not independently metered |
| Quality-preserving efficiency | 9.0/10 | Seven-case, two-run offline benchmark: 0.0-point quality delta, 21.94% byte reduction, 23.77% estimated-token reduction, zero duplicate calls | Benchmark is provider-free/mock and browser smoke cannot render in this environment |

**Combined operational rating: 8.5/10.** 10/10 is not awarded because release-level attribution and live host evidence are incomplete. 11/10 is not achieved because predictive result reuse and two independent live runs are unproven.

## Verified Evidence

- `src/lwa_mcp/service.py` locks the finalized prompt, token budget, consent state, provider, model, and route before work.
- `src/lwa_mcp/service.py` evaluates library suggestions once during single-route preflight; execution no longer recomputes or returns them.
- `src/lwa_mcp/server.py` exposes both canonical lifecycle tools (`prepare_task`, `approve_preflight`, `run_prepared_task`) and compatibility/convenience routes such as `route_task`, `smart_complete`, `answer_query`, and `verify_work`.
- `src/lwa_mcp/db.py` records input/output tokens, cost, latency, status, prompt hashes, preflight events, routes, quotas, and workflow patterns.
- `src/lwa_mcp/config.py` defaults `max_library_suggestions` to `5`.
- `scripts/check-mcp-handshake.py` performs initialization plus tool, resource, and prompt discovery. In this environment it timed out after 8 seconds.
- No `/handshake` directory exists in the repository. The current handshake implementation is under `scripts/check-mcp-handshake.py`.
- WO-024C now defaults MCP JSON transport to compact encoding while preserving standard/debug modes and payload fields.
- WO-024D adds a provider-free seven-case golden benchmark with two-run reproducibility, prompt hashes, fixture seeds, p50/p95 estimates, and explicit quota/redundant-call denominators.
- WO-024E audit result: Lwa MCP `9.0/10`, LWA Plugin workflow `8.0/10`, combined `8.5/10`; 10/10 and 11/10 remain gated.
- WO-025 improves the evidence layer with explicit telemetry health and bounded handshake failure metadata; combined operational score is now `8.7/10`, while live gates remain open.

## Near-Zero Live Quota Proof Orders

The following proof ladder is now recorded. No order treats missing usage or a
nominal quota as proof:

1. **WO-026:** capture complete live per-call attribution and reported usage.
2. **WO-027:** reconcile the authoritative provider/account quota denominator.
3. **WO-028:** repeat the golden quality benchmark through the approved live route.
4. **WO-029:** inject failures and prove fail-closed rollback behavior.
5. **WO-030:** independently recompute the final near-zero result and rating.

WO-026 implementation now persists explicit `call_id` values and provides a
redacted export/validator. The score moves from `8.7/10` to `8.8/10` for
evidence readiness, but live proof is still blocked because historical records
remain unreported/unattributed.

WO-027 adds fail-closed quota reconciliation. It can reproduce `0.0186%` for
`186` control-plane tokens against an authoritative 1M-token snapshot, but the
fixture is mock data; no live quota claim is made. Evidence-readiness score:
`8.9/10`.

WO-028 adds a two-run live-evidence validator. It rejects offline fixtures as
live proof and requires matching fixture hashes, complete reported telemetry,
valid quota, free billing, zero duplicate execution, and latency/token metrics.
Evidence-readiness score: `9.0/10`; live promotion is still pending.

WO-029 adds six executable safety/rollback fault gates. All pass offline,
including repreflight after provider failure, fail-closed stale/missing evidence,
zero duplicate execution, and standard-response rollback. Evidence-readiness
score: `9.1/10`; live fault injection remains pending.

WO-030 adds the final mechanical audit. Current results: quota, benchmark,
handshake, and safety gates pass; telemetry fails due to `38` unreported and
unattributed historical records. Therefore `10/10=false` and `11/10=false`.
Current evidence-readiness score remains `9.1/10`; no live proof claim is made.

WO-031 attempted prerequisite validation for a controlled live proof session.
The locked free route was `zai/glm-4.7-flash`, but telemetry remained invalid
and the available quota snapshots were stale and for other providers. The run
was aborted before completion. The diagnostic doctor also performed `1,720`
live catalog refreshes; because that discovery overhead is not near-zero, the
evidence-readiness score is revised to `8.9/10`.

## Blocker Remediation Orders

1. **WO-032:** repair/quarantine the `38` invalid telemetry records and reset
   the proof boundary.
2. **WO-033:** capture a fresh authoritative quota snapshot for locked Zai.
3. **WO-034:** bound catalog discovery; warm cache hits must make zero network
   calls and doctor must stop using unbounded forced refresh for proof setup.
4. **WO-035:** retry the two-session proof and run the final audit only after
   the first three orders promote.

WO-032 now has an explicit quarantine verifier. The active configured ledger
currently yields `2` quarantined records and `proof_valid=false`; this is
consistent with the earlier broader observation of `38` invalid calls and does
not constitute a clean proof session.

The reviewed guard is
[`catalog_refresh_guard.py`](../scripts/handshake/catalog_refresh_guard.py);
it never performs network calls and requires explicit provider scope.

WO-033 adds `scripts/verify_zai_quota.py` and a quality report for all 12
canonical pipelines. The report mean is `7.9/10`: six directly benchmarked
offline pipelines rate `8.5/10`, while unbenchmarked pipelines are provisional
at `7.0-7.5/10`. No fresh authoritative Zai snapshot exists, so quota proof
remains blocked.

Provider-service quality is tracked separately in
[`PROVIDER_SERVICE_QUALITY_2026-08-08.md`](../reports/PROVIDER_SERVICE_QUALITY_2026-08-08.md):
all 19 configured services are listed, including Gemini (`8.0/10` measured
adapter readiness), Puter (`7.5/10`, user-pays and excluded from quota proof),
Zai (`7.0/10`, quota-blocked), and SiliconFlow (`6.5/10`, health-conditional).
Configured-service readiness mean: `7.0/10`; no live provider quality claim is
made.
- `./.venv/bin/lwa-router telemetry` showed two recent SITREP executions: `376 tok` and `410 tok`, both marked `not reported`; the aggregate displayed `0 requests · 0 in / 0 out`.

## What “<0.1%” Should Mean

Adopt three separate service-level objectives instead of one ambiguous percentage:

1. **Quota SLO:** provider tokens used by Lwa overhead divided by the provider’s available quota. Target `<0.1%` for control-plane overhead per session, excluding the user’s actual answer generation.
2. **Call SLO:** redundant MCP/plugin calls divided by total calls. Target `<0.1%` redundant calls after warm-up, with zero duplicate execution calls.
3. **Quality SLO:** golden-task pass rate, factuality, required-field retention, and test pass rate must not regress by more than 1 percentage point.

Without these denominators, a claim of `<0.1% usage` is not defensible.

## Highest-Value Actions

### P0: Make usage measurable

- Add a `session_id`, `parent_call_id`, `tool_name`, `phase`, `input_tokens`, `output_tokens`, `cache_hit`, and `redundant_call` field to the telemetry path.
- Record tokens for preflight, provider execution, synthesis, and host/plugin display separately.
- Add a compact dashboard view with: tokens per successful answer, tool calls per answer, preflight-to-execution ratio, duplicate-call rate, cache-hit rate, p50/p95 latency, and quality score.
- Treat “not reported” as an explicit telemetry failure, not as zero usage.

### P0: Remove duplicate control-plane work

- Compute `suggest_library_tools` only when the caller marks the task as recurring or when the user explicitly requests discovery. Do not run it automatically in both `prepare_task` and `run_prepared_task`.
- Cache the provider/model catalog and MCP capability manifest by content hash with a bounded TTL. Do not refresh or rediscover unchanged metadata on every request.
- Use one canonical lifecycle path. Reserve `route_task`, `smart_complete`, and compatibility aliases for migration; do not let clients call multiple aliases for one task.
- Keep `prepare_task → approve_preflight → run_prepared_task` as three logical states, but allow the host adapter to batch the non-provider control messages into one compact envelope where the MCP client supports it. Preserve the approval boundary.

### P1: Reduce bytes without reducing answer quality

- Add a `response_detail=compact|standard|debug` mode. Default to compact for successful machine-readable calls; retain full detail for failures, audits, and explicit debug requests.
- Stop pretty-printing JSON in machine-to-machine MCP responses. Preserve the same fields and semantics; remove whitespace only.
- Replace repeated full manifests with a stable manifest hash plus a changed-fields delta. Send the full manifest only on cache miss.
- Keep prompt and system-doctrine text lossless. Compress transport representations, not requirements, literals, safety constraints, or user content.
- Set `max_output_tokens` from measured task-specific p99 output plus a fixed safety margin. Do not lower the quality tier merely to fit a budget.

### P1: Make handshakes cheap and reliable

Create a `scripts/handshake/` family with reviewed, non-provider scripts:

- `mcp-capabilities-once.py`: initialize once, persist a redacted capability manifest and hash, and reuse it until the server binary or protocol version changes.
- `mcp-handshake-smoke.py`: fail fast on missing required tools/resources/prompts and report elapsed time; do not perform provider calls.
- `mcp-session-warm.sh`: keep one MCP process alive for a bounded session instead of spawning a new process per tool call.
- `mcp-handshake-report.py`: emit compact JSON metrics for startup time, discovery count, cache hit/miss, and failure reason.

The existing `scripts/check-mcp-handshake.py` should remain the full diagnostic path, while the normal plugin path uses the cached smoke path. Review every script source before enabling execution, consistent with the project doctrine.

### P2: Reduce expensive multi-call workflows selectively

- Use one routed execution by default.
- Invoke consensus only for explicitly high-risk or disagreement-sensitive tasks. Consensus currently creates multiple voter routes plus a synthesis route, so it is a deliberate quality mode, not a low-usage default.
- Use verification as a postcondition gate for changed code and high-stakes output, not as an automatic second completion for every response.
- Promote stable repeated work to inspected prompt recipes through the library. A recipe should reduce repeated reasoning, not silently trigger extra calls.

## Quality Guardrails

Every optimization should run against a fixed golden set containing:

- short query, long document edit, coding change, verification task, SITREP, and failure/recovery cases;
- required literals and constraints;
- structured-output schema validation;
- factual or expected-answer checks where deterministic;
- regression tests for consent, redaction, preflight locking, and `repreflight_required` behavior.

Accept an optimization only when all of the following hold:

- quality score is within 1 percentage point of baseline;
- no required field or literal is lost;
- no additional provider execution is introduced;
- p95 latency and token usage improve or remain neutral;
- telemetry still attributes every call and token count.

## Recommended Target Ladder

Do not jump directly to `<0.1%`. Measure and ratchet:

1. **Baseline:** 100% attribution for every MCP and provider call; eliminate “not reported.”
2. **First reduction:** remove duplicate suggestions, manifests, and pretty-printing; target 30–60% less control-plane payload.
3. **Warm session:** cache capabilities/catalogs and reuse the MCP process; target 70–90% fewer startup/discovery bytes.
4. **Quality-gated floor:** target `<0.1%` redundant calls and `<0.1%` quota overhead only after the denominator and quality SLO are proven.

## Risks and Non-Goals

- Token compression cannot make a genuinely complex answer free without either caching a correct prior result or reducing content. The optimization target applies to overhead, not to necessary answer content.
- A smaller `max_output_tokens` value is not automatically an efficiency win if it causes truncation, retries, or verification failures.
- Caching provider catalogs and manifests requires invalidation on server version, configuration, protocol, or capability changes.
- Never bypass consent, prompt locking, redaction, single-use plan tokens, or the explicit provider execution boundary to save calls.

## Next Work Orders

- **WO-024A:** Add complete per-session/tool-call telemetry and treat unreported usage as an error state.
- **WO-024B:** Add cached MCP handshake and warm-session scripts under `scripts/handshake/`.
- **WO-024C:** Add compact response mode and remove duplicate library suggestion evaluation.
- **WO-024D:** Build a golden-task quality and token-efficiency benchmark.
- **WO-024E:** Re-rate LWA Plugin and MCP after two measured benchmark runs.

## Acceptance Criteria

- Every tool call and provider execution has an attributed session and token record.
- Normal warm-session operation performs no repeated capability discovery.
- No duplicate library suggestion computation occurs in one lifecycle.
- Compact responses preserve the standard semantic fields and auditability.
- Golden-set quality remains within the agreed 1-point regression bound.
- The final report can show whether `<0.1%` refers to quota overhead, redundant calls, or another explicitly defined denominator.

## Final Audit Gates

| Gate | Result | Evidence |
|---|---|---|
| Quality regression within one point | Pass | Offline golden benchmark delta `0.0` points |
| Duplicate provider execution | Pass | `0` in two benchmark runs |
| Compact transport reduction | Pass | `21.94%` bytes and `23.77%` estimated tokens |
| Redundant-call denominator | Pass | `0.0%` in benchmark |
| Quota denominator | Conditional | `0.0186%` only with declared 1M-token offline denominator |
| Complete live attribution | Blocked | Historical `not_reported` telemetry remains |
| Live MCP warm handshake | Blocked | Smoke path reports `mcp_handshake_timeout` |
| Browser smoke rendering | Blocked | Firefox exits without screenshot in sandbox |
| Predictive safe result reuse | Not implemented | Required for 11/10 stretch |

## Provider-Service Quality Uplift

The 19-service provider matrix currently averages `7.0/10` readiness. This is
separate from the combined Lwa MCP/LWA Plugin efficiency rating and does not
claim live quality or quota proof. The next PWO sequence is:

1. **WO-036/TR-036:** normalize all adapter contracts and deterministic failure fixtures.
2. **WO-037/TR-037:** obtain fresh provider/account-scoped quota or billing evidence.
3. **WO-038/TR-038:** run repeated provider-specific golden quality cases.
4. **WO-039/TR-039:** integrate bounded catalog/handshake caching and prevent unbounded discovery.
5. **WO-040/TR-040:** independently audit each service for 10/10, then 11/10 stretch criteria.

The existing blocker set remains explicit: 38 historical unreported and
unattributed calls, no fresh authoritative Zai quota snapshot, stale or
cross-provider snapshots, and the observed 1,720 live catalog refreshes.
