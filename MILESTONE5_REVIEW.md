# Milestone 5 review — bounded communication

Status: implemented; ready for Claude review. Date: 2026-10-02.

The technical M5 gate passes. The user's 2026-10-02 decision moves CodeBuddy work
to the later user-run SOW/rebuild/comparison stage; no CodeBuddy development evidence
is claimed here. Final submission evidence remains required.

## 1. Files and architecture

Added `aura_communication/{domain,config,catalog,prompts,validation,provider,evaluation}.py`,
its package initializer, engineering config, and README; added
`aura_app/communication.py` and `tests/test_milestone5.py`. Extended only the application
API, repository protocols, and SQLite adapter. Updated README, HANDOVER, roadmap,
decisions, and M5–M7 scope notes for the current user workflow.

`PatientCommunicationService` is the only public application generation entry.
It accepts a patient ID, a committed event ID, and a presentation purpose. It reads
existing gate references and current safety state before approving an intent. The
provider receives data only—no repository, engine, or state writer. Safety and
longitudinal algorithms are unchanged, as confirmed by the Git diff and regression
suite. Controllers only validate transport and delegate.

Flow: committed patient event → current safety/gate verification → approved existing
communication intent/facts → optional bounded provider → deterministic validation
or fixed fallback → state recheck → persisted output/timeline/audit → response.

## 2. Modes and containment

| Condition | Implemented output |
|---|---|
| Normal patient-initiated input | NORMAL_SUPPORT after committed safety evaluation |
| Approved micro-check-in | MICRO_CHECKIN |
| Approved contextual clarification | TARGETED_CLARIFICATION |
| Patient voluntarily inspects recorded drift | OBSERVATION_EXPLANATION |
| T1 CLARIFY | Only server-supplied reviewed policy variants; static pending-review message by default |
| T2 ELEVATED | ELEVATED_SUPPORT using constrained catalog, no raw context |
| T3 URGENT / T4 IMMEDIATE | Static template, zero provider calls |
| Server degraded / client offline / unexamined input | Static fail-closed message and separate resources |
| Outstanding recheck/dropout | Static follow-up pending reviewed questions |
| STAY_QUIET | Empty message, zero provider calls |

The initial model selects among authorized wording candidates. It cannot invent
prose/facts/questions/actions. Exact text, fact IDs, question intent, CTA, schema,
length, and prohibited claims are checked deterministically. Regex checks add
defense but are not a semantic/clinical truth oracle. This narrow choice contract
is deliberate; optional review-summary wording and unrestricted paraphrasing are
deferred. No medical thresholds or safety questions were invented.

Current wording is marked `DEVELOPMENT_FIXTURE_REQUIRES_REVIEW`; generic safety
status copy is not clinically reviewed crisis guidance. Safety resources remain
separate and retain the accepted unverified Singapore development fixture.

## 3. G1–G16 results

Each test below is in `tests/test_milestone5.py`, class `MilestoneFive`.

| ID | Result | Test name | Proven behavior |
|---|---|---|---|
| G1 | PASS | `test_g1_generation_cannot_mutate_safety_state` | Rendering leaves persisted safety state unchanged and passes no state writer to provider. |
| G2 | PASS | `test_g2_generation_cannot_mutate_baseline_or_anchor` | Rendering leaves actual persisted baseline/anchor snapshots unchanged. |
| G3 | PASS | `test_g3_immediate_uses_no_generated_content` | T4 uses fixed output with resources and no provider invocation. |
| G4 | PASS | `test_g4_degraded_and_offline_use_no_generated_content` | Degraded/offline input is unassessed, static, and resource-backed. |
| G5 | PASS | `test_g5_every_generated_message_has_approved_mode` | Every accepted provider response has an application-approved generation mode/intent. |
| G6 | PASS | `test_g6_diagnostic_claim_is_rejected` | A diagnostic reply is rejected and replaced. |
| G7 | PASS | `test_g7_relapse_claim_is_rejected` | A relapse claim is rejected and replaced. |
| G8 | PASS | `test_g8_medication_changes_and_tapers_are_rejected` | Dose/taper/stop instructions are rejected. |
| G9 | PASS | `test_g9_unsupported_patient_facts_are_rejected` | A provider cannot introduce facts outside authorized content. |
| G10 | PASS | `test_g10_invalid_output_returns_fixed_fallback` | Validation failure uses one fixed fallback, without repair-loop calls. |
| G11 | PASS | `test_g11_timeout_and_model_error_return_fallback` | Optional generation timeout/error produces fixed wording. |
| G12 | PASS | `test_g12_safety_precedence_survives_model_unavailability` | Safety state/reference and urgent output remain authoritative with an unavailable model. |
| G13 | PASS | `test_g13_prompt_model_and_validation_are_durably_auditable` | Prompt/model/validation metadata and output survive a fresh repository reload without raw text duplication. |
| G14 | PASS | `test_g14_identical_conditions_produce_identical_fallback` | Unchanged conditions replay the same committed fallback with no duplicate call/output/audit. |
| G15 | PASS | `test_g15_internal_tiers_and_scores_are_rejected` | Generated internal tiers/psychiatric percentages are rejected. |
| G16 | PASS | `test_g16_free_text_cannot_bypass_gate_or_enter_generation_directly` | Missing/held inputs cannot reach generation; transport rejects raw text/mode overrides. |

Twenty-one additional tests cover actual B/E longitudinal behavior, T1/T2, quietness,
targeted check-ins, in-flight/cached safety races, resource independence/integrity,
candidate mutation, prompt injection, unauthorized cross-patient IDs, follow-up,
invalid state, exact reviewed-question vocabulary, output-transaction rollback, nine required fixtures, HTTP contract,
timeout/size/JSON errors, and configuration validation. These are engineering
containment tests, not detector or clinical validation.

## 4. Verification

```sh
.venv/bin/python -m unittest discover -s tests -q
.venv/bin/python -m aura_communication.evaluation --save /tmp/aura-m5-evaluation.json
.venv/bin/python -m aura_communication.evaluation --behavior disabled
git diff --check
git diff --name-only -- aura_safety aura_longitudinal
```

Full suite: **106 tests PASS** in 51.471 seconds (69 existing + 37 M5). Existing
Starlette/httpx deprecation warning remains. Whitespace check is clean. There are
no changes to `aura_safety/` or `aura_longitudinal/`.

Accepted application Cases A–E still have interruption counts **0, 6, 6, 1, 0**;
Case D retains two review items; E returns REESTABLISHING. F still delegates to
CLARIFY and persists the safety reference. These are original M4 application tests,
not claims of patient UI coverage. New M5 tests exercise B descriptive anchored
drift and E missingness/re-establishment through the wording boundary.

## 5. Synthetic prompt evaluation

Scenario names and expected outcomes are evaluation-only. Observable text/check-ins
and externally injected resolved proposals cross the application boundary; the
production communication service imports no simulator/evaluation module.

| Prompt fixture | Default fixture provider | Provider disabled | Exact stored replay |
|---|---|---|---|
| Stable ordinary day | Quiet; 0 calls; PASS | Quiet; PASS | MATCH |
| Transient physiology report | Bounded support; PASS | Fixed support; PASS | MATCH |
| Slow-change report | Bounded support; PASS | Fixed support; PASS | MATCH |
| Contextual explanation request | Bounded support; PASS | Fixed support; PASS | MATCH |
| Medication concern | Bounded support; no treatment instruction; PASS | Fixed support; PASS | MATCH |
| Figurative language | Resolved NORMAL fixture; bounded support; PASS | Fixed support; PASS | MATCH |
| Resolved safety concern | Static clarification; 0 calls; PASS | Static clarification; PASS | MATCH |
| Hallucinated reply | Rejected → fixed fallback; PASS | Fixed support; PASS | MATCH |
| Patient prompt injection | Rejected → fixed fallback; PASS | Fixed support; PASS | MATCH |

These are prompt-boundary fixtures, not reimplementations of physiology/drift or
claims about interpreting figurative/safety language. No real detector is provided.
Accepted fixture replies are identified by `model_id=fixture-wording-v1`; they are
not live LLM outputs. Live model generation is not claimed replay-deterministic.

## 6. API and provider setup

New route: `POST /patients/{patient_id}/events/{event_id}/communication`.
Body: `{}` or `{"purpose":"EXPLAIN_OBSERVATION","client_offline":false}`.
Response contains message/fact references/approved mode, generation and validation
metadata, static fallback ID, linked safety reference, separate pinned resources,
versions, and development content-review status. It exposes no diagnosis/probability.

By default the optional provider is disabled. `AURA_COMMUNICATION_ENDPOINT`,
`AURA_COMMUNICATION_MODEL`, and private `AURA_COMMUNICATION_TOKEN` configure the
neutral JSON HTTP gateway contract documented in `aura_communication/README.md`.
This is not a vendor-native adapter. Contract/HTTP failure paths use MockTransport
in tests; no live provider/model has been configured or smoke-tested. The public
safety gate remains unconfigured and continues to hold free text regardless of
model configuration. Developer fixtures supply explicit resolved proposals.

## 7. Persistence, transactions, and race handling

New append-oriented `communication_outputs` table has a fingerprint primary key,
patient/event foreign keys, safety sequence/episode reference, mode/version/model
columns, timestamp, generation status, and structured result JSON. Audit/timeline
reference the output ID; existing event transaction/results remain unchanged.

The read transaction ends before the provider call. A second transaction reloads
current state and either commits validated wording or discards it in favor of a
current-state fixed response. If evidence upgrades to T4 during generation, only
the current immediate static response is committed. A cached normal response also
cannot override later safety. Output/audit/timeline failures roll back together;
the earlier committed patient event survives. Repeat requests reuse a committed
output. Simultaneous identical requests may both use remote work, but only one
output/audit commits; remote-work deduplication across workers is future work.

No raw prompt, rejected reply, patient free text, token, or provider error body is
duplicated in generation audit. Accepted message text is retained for inspection.

## 8. Configuration and open issues

Engineering defaults in `aura_communication/engineering_config.json`: 420 response
characters; 600 context characters; 2 facts; 5-second provider timeout; 16,384-byte
response limit. Prompt/content/config versions are explicit. These are not clinical
thresholds. Reviewed safety questions are injectable only server-side and none are
configured by default. Safety content/questions/resources still require clinical
review, along with inherited clinical parameters and governed REESTABLISHING exit.

M5 adds no contradiction requiring a change to accepted domain algorithms.
Limitations: finite wording choices, no live model validation, no reviewed crisis
content, development authentication/storage only, and potential duplicate remote
work under concurrent requests. Existing reviewer authorization, event replay
scaling, and routine T0/null snapshot-reference filtering remain documented.

## 9. Verdict and next milestone

The technical M5 stop condition is met and the work is ready for reviewer feedback.
M6 patient application is next. CodeBuddy use/SOW/rebuild occurs only at the user's
chosen stage after agreement on the finished product; no execution or evidence is
claimed for this milestone.
