# M5 bounded communication

`PatientCommunicationService` reads a committed event, its safety assessment/reference,
the current safety state, and the existing longitudinal decision. It never invokes a
detector, writes safety state, moves an anchor, or recomputes drift.

## Public flow

1. Ingest through the existing event API (all relevant inputs remain safety-gated).
2. `POST /patients/{patient_id}/events/{event_id}/communication` with `{}` to request
   wording of the already committed decision. The body accepts only `purpose` (`AUTO`
   or patient-initiated `EXPLAIN_OBSERVATION`) and restrictive `client_offline`.
3. Read an evaluated gate reference and the *current* state. Held/unexamined input is
   blocked. STAY_QUIET returns an empty message; a voluntary observation explanation
   does not change the communication decision or create a notification.
4. Pass minimal immutable facts, approved intent, bounded context, and a finite set
   of authorized wording candidates to the optional provider.
5. Validate exact candidate content, fact IDs, question intent, CTA, output schema,
   length, and prohibited claims. A failed result is replaced once with fixed text.
6. Recheck committed state after the model call; discard stale output. Persist the
   result, generation metadata, timeline reference, and application audit atomically.

The model selects between approved wording alternatives. M5 deliberately does not
validate arbitrary open-ended prose with keyword heuristics. Exact candidate
grounding prevents unsupported facts/intent changes; regex checks are additional
defense, not a claim of comprehensive semantic or clinical validation. Exact
server-supplied reviewed policy questions may contain clinical vocabulary; they
must still match their authorized candidate and metadata without additions. Their
content approval remains a governance responsibility, not a model decision. The model
does not return state or actions. Optional free paraphrasing/review-summary wording
is deferred.

## Permissions and content review

T0 supports patient-chosen support, approved micro-check-ins/clarifications, and
voluntary descriptive explanations. T1 can phrase only server-supplied
`ApprovedPolicyQuestion` variants with policy version/review reference; none are
configured by default. T2 uses constrained support candidates without raw patient
context. T3/T4, degradation, and offline fail-closed use static responses without
model calls. Outstanding recheck/dropout workflow stays on static follow-up content.
The original output policy and clinical configuration remain authoritative.

All current wording is labelled `DEVELOPMENT_FIXTURE_REQUIRES_REVIEW`. Generic safety
system-status text and the existing unverified resource fixture are **not** reviewed
crisis guidance. This milestone supplies no crisis numbers, clinical instruments,
detector, or model-based safety assessment. Resources are a separate native/pinned
response field and never enter generation. Their age does not hide them.

## Optional provider

The default is `DisabledProvider`, which produces deterministic fallback. An explicit
model gateway can implement the neutral JSON POST contract in `prompts.py`.

**Patient API privacy stance:** ordinary patient API/demo factory entry points use
`DisabledProvider`, even if gateway environment variables exist. Live patient-model
use is deferred until an explicit informed consent workflow is reviewed. The domain
communication service still supports an explicitly injected provider for synthetic
developer evaluation; this is not a consent-approved patient deployment. Its standalone
environment adapter reads `AURA_COMMUNICATION_ENDPOINT`, `AURA_COMMUNICATION_MODEL`,
and private `AURA_COMMUNICATION_TOKEN`; these no longer automatically enable the
patient API. The fixture-restricted hosted service now has opt-in native vendor
settings; see [operator settings](../docs/SYSTEM_SETTINGS.md). This does not enable
real-data patient model use. No actual vendor call is asserted tested.

The gateway receives `contract_version`, `instructions`, `request`, `output_schema`,
and `model`; it returns exactly `candidate_id`, `message`, `acknowledged_facts`,
`question_intent`, and `cta_type`. This is a provider-neutral contract, not a claim
of compatibility with a vendor's native API. HTTPS is required except loopback
development HTTP. Redirects and environment proxies are disabled; responses have
size and timeout limits. No live vendor/model is configured or asserted tested.

Patient free text cannot be posted to this generation route. It must reference an
already persisted input with a completed safety gate. The default public API still
holds free text because its safety resolver is unconfigured; setting a model URL
does not make unexamined input safe. Developer fixtures explicitly inject resolved
proposals; no real detector is implemented.

## Persistence, retries, races, and privacy

`communication_outputs` is append-oriented and keyed by event/current state,
latest event, purpose, provider identifier, reviewed question, and actual config
fingerprints. Repeated calls in unchanged conditions return the committed output
without another provider call/audit/timeline row. Fresh safety state prevents cached
normal output overriding newer evidence. Resources are resolved independently.

The model call holds no database transaction. A second transaction rechecks all
relevant state and commits output/audit/timeline. If new evidence arrived, the old
generated response is discarded and a deterministic current-state fallback is used.
In a simultaneous identical request race, both calls may consume model work, but
only one output/audit commits; the other returns it. Avoiding duplicate remote work
across workers is future outbox/claim work. No model failure rolls back an already
committed patient event or changes domain state. A failure in the output transaction
rolls back only output/audit/timeline and returns a sanitized application error.

Store model/prompt/config/content/policy versions, fact references, validator status,
fallback reason, timing, and safety/resource links. Do not duplicate raw patient text,
prompts, rejected output, HTTP error bodies, credentials, or hidden scenario truth in
generation audit. A generated message itself is stored for replay/inspection.

## Engineering configuration and evaluation

`engineering_config.json`: response length 420 characters, context 600 characters,
at most 2 facts, provider timeout 5 seconds, response body 16,384 bytes. These are
inspectable engineering limits, not clinical thresholds. Bump prompt/content/config
versions when contracts or catalogs change. Clinical content/questions require review.

```sh
.venv/bin/python -m unittest discover -s tests -p test_milestone5.py -v
.venv/bin/python -m aura_communication.evaluation --save /tmp/aura-m5-evaluation.json
.venv/bin/python -m aura_communication.evaluation --behavior disabled
.venv/bin/python -m aura_communication.evaluation --fixture prompt_injection --behavior invalid
```

Nine synthetic prompt fixtures exercise the application boundary with fixed resolved
proposals. Accepted Cases B/E additionally test real descriptive drift/re-establishment
through the production domains. These tests evaluate containment, not detector
accuracy, model determinism, or clinical efficacy. Fixture generation is clearly
distinguished from optional live-model generation.
