# Live-model integration — synthetic demo decision and plan

User decision: 2026-10-07. A live model should be used with **synthetic data only**.
Future real institutional use is intended to run an institution-managed on-prem model
or private-cloud solution. That direction is not an implemented/validated deployment
capability, privacy certification or medical-readiness claim.

## Current verified state

The accepted `PatientCommunicationService` already supports an injected provider,
bounded requests, deterministic validation/fallback, safety precedence, race checks,
audit and cached response reuse. `HTTPGenerationProvider` supports a provider-neutral
JSON gateway, not a vendor-native chat API. Model requests select an approved candidate;
this is not unrestricted paraphrasing or conversational therapy.

All current supplied API/demo entry points still force `DisabledProvider`. No live
model is configured, enabled or tested by this planning change. Existing copy is
accurate for today's runtime but must become configuration-aware during integration.
Provider/model/endpoint and credential provisioning need a user choice. Share config
names or a protected secret-file path, never credential values in chat/Git.

## Integration boundary

```text
named synthetic input → existing fixture safety gate → domain policy/communication
→ approved minimal synthetic wording contract → live provider
→ existing deterministic validation → validated output OR fixed fallback
```

Live selection belongs only in the fixture-restricted hosted/synthetic workspace.
The ordinary real-data/development API remains disabled by default; arbitrary public
free text and unknown patient profiles remain rejected/held, never implicitly safe.
Environment configuration must not accidentally enable generation for all patients.

The model cannot assign/lower safety tiers, change anchors, create clinical conclusions,
alter treatment, judge context credibility or decide communication outcomes. T3/T4,
degraded/offline and other prohibited modes remain static. Resources stay separate.
Keep the accepted finite-candidate contract initially; any future free paraphrasing or
new detector requires a separately reviewed boundary, not a vendor adapter shortcut.

## Provider work once configuration is selected

1. Use the existing neutral gateway if available; otherwise implement the selected
   provider's native transport behind `GenerationProvider`, using its official API.
2. Keep secrets server-side (protected file/secret mount); no key or internal endpoint
   in browser responses, prompts, audit/error bodies or Git.
3. Require explicit synthetic-only opt-in and fail safely on invalid/missing config.
4. Send only already-approved facts/context/wording options; no scenario hidden truth,
   unrelated history, repository access or write-capable object.
5. Keep bounded timeout/body size, no redirects, deterministic invalid/error fallback,
   state recheck after generation, existing version/model audit and idempotency.
6. Test mocked transport first, then a labelled synthetic live smoke test. Verify
   actual provider use and validator result; do not equate 'configured' with 'generated'.
7. Rebuild the hosted demo and verify phone/laptop flows, safety and model failure.

## Honest UI/documentation disclosure

When enabled/configured:

> Live AI wording · synthetic demo data only.

When a response used fixed content/fallback, disclose that path where useful; do not
label every response AI-generated. When no provider is enabled, say “Fixed wording”
or “Live model not configured,” rather than presenting “no live model” as a product
principle. Keep synthetic-data/prototype limitations separate from model availability.

Future-direction wording:

> For future institutional use, AURA is intended to connect to an institution-managed
> on-premises or private-cloud model, subject to clinical, privacy and security review.

No statement that institution-hosted deployment already exists or guarantees compliance.

## Required integration tests

- Only explicitly enabled synthetic workspace can call provider; ordinary API stays off.
- Unknown/free-form intake cannot reach generation; hidden simulation truth excluded.
- Provider gets approved minimal facts/intents, not product-policy authority.
- T3/T4/degraded/offline/STAY_QUIET and unassessed input preserve current containment.
- Invalid output/timeout/network failure uses the existing deterministic fallback.
- New evidence during generation rejects stale wording; audit/version/cache intact.
- Configuration and per-response disclosure accurately distinguish live/static/fallback.
- A live smoke test proves a real call; synthetic evaluation does not imply efficacy.

Additional synthetic data is deferred until live integration and UX are addressed.
