# WO-014: Cross-Project Provider Access and Pro-Route Readiness

Status: queued
Priority: P0

## Objective

Make provider access predictable across Codex projects and make ChatGPT/OpenAI
and Gemini Pro requests truthful, observable, and explicitly gated. A project
must use an approved provider without copying secrets into source, while a
request for a paid/pro route must never be reported as satisfied by a free
fallback.

## Evidence and boundary

- MSF has no dedicated Codex/Lwa log files in the inspected tree. Its README
  requires `GEMINI_API_KEY` in project `.env.local`, and `metadata.json`
  declares server-side Gemini capability.
- Lwa credential discovery is intentionally bounded to the current process,
  Codex `env_key` references, MCP environment maps, and fixed Codex/project
  `.env` locations. A key available to one project is not automatically
  available to every Codex project.
- Codex OAuth session material is not a reusable OpenAI or Gemini API key.
- OpenAI/ChatGPT and Gemini adapters exist, but live authentication, model
  availability, quota, and paid access remain operator-gated.
- Prior evidence records Gemini/ZenMux `403 access_denied`, OpenRouter `401
  User not found`, and a request completing on `free_quota` despite
  `allow_paid=true`. These are access or route-intent failures, not successful
  pro handoffs.

## Work packages

1. **Project-scope inventory:** expose a redacted diagnostic showing each
   recognized credential source, owning project/config path, provider, and
   configured/available state. Never print values or recursively scan a home
   directory.
2. **Safe cross-project configuration:** define an explicit shared Lwa
   credential namespace plus project-level aliases. Add an operator-approved,
   atomic migration path and document precedence, permissions, and revocation.
3. **Provider readiness:** add separate checks for OpenAI authentication,
   Google Gemini authentication, model listing, quota, and paid/pro
   entitlement. A configured key is not evidence that every model is usable.
4. **Strict route intent:** add a `require_billing_class` (or equivalent)
   intent for pro requests. If no paid route is available, return a structured
   blocked result before execution; do not silently downgrade to `free_quota`.
5. **Codex onboarding:** provide a per-project registration check identifying
   missing MCP environment mapping without copying secrets into the project.
6. **MSF contract:** change MSF guidance to use the governed Lwa credential
   path, or label direct Gemini `.env.local` use as project-local and separate.

## Acceptance checks

- [ ] Two separate Codex projects resolve the same approved provider through
  the documented shared namespace without duplicating key material.
- [ ] Project-local credentials remain isolated when shared access is disabled.
- [ ] Doctor output identifies source, provider, and state without secrets,
  prompt bodies, or OAuth tokens.
- [ ] OpenAI and Gemini checks distinguish missing key, invalid key, denied
  model, quota exhaustion, and paid entitlement absence.
- [ ] A request requiring `paid` cannot complete with `free` or `free_quota`.
- [ ] `allow_paid=true` remains permission, not proof that a paid route ran.
- [ ] Gemini Pro and ChatGPT/OpenAI success is claimed only after a fresh,
  provider-specific, operator-approved live check.
- [ ] Credential rotation and rollback preserve unrelated environment entries,
  use mode `0600`, and leave no secret in logs, ledgers, or manifests.

## Rollback and authorization

Credential migration, rotation, provider enablement, and paid live checks are
operator-authorized actions. Snapshot configuration metadata only, not secret
values. Roll back aliases/configuration atomically; never restore secrets into
source control or project logs.

## Exit criteria

Close only after the cross-project matrix, OpenAI/Gemini readiness matrix,
strict pro-route test, MSF integration check, and redaction/rotation tests all
have recorded evidence. Until then, status remains queued or partial.
