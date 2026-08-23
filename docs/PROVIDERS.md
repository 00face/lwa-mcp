# Provider Matrix

The endpoint configuration is stored in `config/router.example.yaml` and copied to `~/.config/lwa-mcp/router.yaml` on initialization.

Seed models and billing classes are fallback metadata only. They do not establish
current availability, entitlement, quota, balance, or price. Live catalog and
official account probes are authoritative when the provider exposes them.

Provider status distinguishes configuration from verification. An offline
`ready` row means a seed route is configured and eligible for preflight; it is
not a live reachability, quota, or billing claim. Use the zero-payload probe or
an explicit catalog refresh when live evidence is required.

The baseline adapter contract explicitly rejects streaming until an adapter has
an audited implementation. Text adapters provide model discovery where enabled;
quota/balance probes are optional and unsupported probes are reported as such.
Seed entries are always marked `source: seed`; live discovery is marked
`source: live` and may replace only the volatile catalog fields.

When callers provide `preferred_providers`, the list is an ordered preflight
priority: the router selects the best eligible model from the first listed
provider, then falls back to later entries or unlisted providers. It does not
override capability, reasoning-effort, credential, quota, or billing gates.

Catalog discovery is bounded by `catalog_page_limit` and
`catalog_model_limit` on each provider configuration so a large paginated
endpoint cannot monopolize the control plane.

| Provider | Adapter | Default billing class | Live model discovery | Notes |
|---|---|---:|---:|---|
| Google Gemini | native Gemini REST | free_quota | yes | Uses `GEMINI_API_KEY`, the `x-goog-api-key` header, and `models.list`; local request caps apply. |
| OpenAI / ChatGPT API | OpenAI-compatible | paid | yes | Uses `OPENAI_API_KEY`, Bearer authentication, a $5 local monthly cap, and the official `/v1/models` endpoint. |
| OpenAI media | native OpenAI media REST | paid | seeded | Uses `gpt-image-1` for images and asynchronous `sora-2` jobs for video; paid consent and local caps apply. |
| OpenRouter | OpenAI-compatible | free_quota | yes | Includes `openrouter/free`; catalog pricing is parsed when available. |
| Groq | OpenAI-compatible | free_quota | yes | Seeded for low-latency and large GPT-OSS routes. |
| Mistral | OpenAI-compatible | free_quota | yes | Trial/free allocation depends on account and current policy. |
| Cloudflare Workers AI | OpenAI-compatible | free_quota | no | Requires account ID and API token; seed uses a Workers AI model path. |
| SiliconFlow | OpenAI-compatible | free_quota | yes | Experimental and disabled by default after the last live model probe returned HTTP 401; re-enable only after credential verification. |
| Venice | OpenAI-compatible | paid | yes | Uses prepaid USD/crypto or DIEM allowance; official balance probe is configured. |
| Pollinations | OpenAI-compatible | free_quota | yes | Text adapter only in this baseline; live catalog is preferred. |
| Cohere | OpenAI-compatible compatibility API | free_quota | yes | Uses Cohere's compatibility endpoint. |
| Replicate | prediction adapter | paid | no | Supports seeded text or image models via `metadata.input_mapping`. |
| Stability AI | image adapter | paid | no | Saves generated files under the state directory. |
| NVIDIA Build/NIM | OpenAI-compatible | free_quota | yes | Uses the hosted NIM integration endpoint. |
| Z.AI | OpenAI-compatible | free_quota | yes | Uses the PaaS v4 base URL. |
| Aion Labs | OpenAI-compatible | free_quota | yes | Seed model should be checked with `doctor`. |
| ZenMux | OpenAI-compatible | paid | yes | Premium aggregation; local cap plus optional official management balance probe. |
| Cerebras | OpenAI-compatible | free_quota | yes | Strong high-speed reasoning route when available. |
| BLACKBOX AI | OpenAI-compatible | paid | no | Uses its documented public endpoint and model slug. |
| Puter | OpenAI-compatible | user_pays | yes | Supports user-authorized access; cost belongs to the Puter user. |

## Model lifecycle

The YAML seed list supplies intentional task scores. Live discovery adds current models and their context/pricing metadata. Exact seed matches retain their task scores. Unknown live models receive a neutral task score and therefore act as fallbacks rather than unexpectedly displacing tested seeds. If live discovery fails before a provider has any successful live evidence, its seed models are disabled for that process and the provider is labeled experimental. Configured-only providers without an error remain unverified, not disabled.

When a seeded model is rejected during execution, Lwa records the failure and returns `repreflight_required`. The client must stop Working and prepare a new route; Lwa does not select another provider inside the active execution phase. Promote newly verified models by adding explicit scores to the local YAML.

## Plan and credential metadata

Provider subscription fields (`subscription_plan`, `subscription_status`, and
`subscription_monthly_token_limit`) are operator-declared metadata. They are
shown in provider status and model-tier output; Lwa does not infer consumer
subscriptions from an API key. In particular, a ChatGPT subscription and an
OpenAI API billing account are separate services.

Model fields `free_plan_max_tokens` and `pro_plan_max_tokens` are also declared
quota metadata. The `lwa-router tiers` command ranks models by
`free_plan_max_tokens`, placing unknown limits after declared limits.

Providers can use a key pool and an independent billing/quota key:

```yaml
api_key_env: GEMINI_API_KEY
api_key_envs: [GEMINI_API_KEY_1, GEMINI_API_KEY_2]
billing_api_key_env: GEMINI_BILLING_API_KEY
```

Generation uses the first configured key in the pool. Quota and billing probes
prefer `billing_api_key_env` (then the existing `quota_key_env`). Only
environment-variable names appear in status output; secret values are never
serialized.

## Adding a model

```yaml
models:
  - provider: example
    model: provider/model-slug
    billing_class: free_quota
    context_length: 131072
    capabilities: [text, reasoning, tools]
    task_scores:
      quick_response: 90
      document_editing: 84
      sitrep: 82
      planning: 86
      consensus: 80
      conversation_compression: 88
      token_optimization: 89
      verification: 82
      coding_aux: 85
```

Use higher scores only after a reproducible test. Do not encode marketing claims as quality evidence.

## Image and video generation

Image-capable routing is capability-based. `gpt-image-1` uses the official
OpenAI media pipeline and saves image output locally, `sora-2` submits an
asynchronous video job and downloads the completed MP4, `black-forest-labs/flux-schnell`
is routed through Replicate, and `stable-image-core` is routed through Stability.
All of these use the normal paid-route preflight approval.

## Google Gemini setup

Create or manage a key in Google AI Studio, then run:

```bash
./.venv/bin/lwa-router keys
```

Select Google Gemini when prompted. The wizard stores `GEMINI_API_KEY` in the
protected `~/.local/state/lwa-mcp/lwa.env` file. Gemini model discovery uses the
official `models.list` endpoint; generation uses the official
`models/{model}:generateContent` endpoint and sends the key in the
`x-goog-api-key` header. No Gemini quota/balance endpoint is assumed by this
baseline, so local request caps remain the enforceable boundary.
