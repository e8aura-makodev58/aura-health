# Milestone 4 review packet

## 1. TEST RESULTS

Last full run: `.venv/bin/python -m unittest discover -s tests -q` — **69 tests passed** (A1–A20, two additional application checks, and 47 accepted earlier tests). All A-tests below are in `tests/test_milestone4.py`.

| Property | Result | Test name / file | What was proven |
|---|---|---|---|
| A1 | PASS | `test_a1_api_controllers_have_no_domain_decision_logic` — `tests/test_milestone4.py` | API routes contain no safety/longitudinal engine imports or drift calculations. |
| A2 | PASS | `test_a2_duplicate_idempotency_prevents_domain_processing` — `tests/test_milestone4.py` | A changed event ID with the same patient/idempotency key returns the stored result without another timeline entry or gate call. |
| A3 | PASS | `test_a3_observation_cannot_mutate_anchor` — `tests/test_milestone4.py` | A later activity observation leaves all anchored centers unchanged. |
| A4 | PASS | `test_a4_named_command_reanchors_through_governed_path` — `tests/test_milestone4.py` | Generic event ingestion rejects an anchor command; the named command path can reanchor a fixture from 100 to 200. |
| A5 | PASS | `test_a5_longitudinal_output_persists_in_timeline` — `tests/test_milestone4.py` | Case B's persistent/rolling-anchor drift is stored as typed timeline data. |
| A6 | PASS | `test_a6_explanation_creates_held_state` — `tests/test_milestone4.py` | Case D reloads two `EXPLAINED_HELD_FOR_REVIEW` records. |
| A7 | PASS | `test_a7_review_snapshot_includes_held` — `tests/test_milestone4.py` | The snapshot includes both held drifts and both review items. |
| A8 | PASS | `test_a8_review_snapshot_never_implies_sharing` — `tests/test_milestone4.py` | Snapshot and review items say `NOT_SHARED`, with `automatically_sent=false`. |
| A9 | PASS | `test_a9_safety_precedence_over_quiet` — `tests/test_milestone4.py` | Case F returns `SAFETY_REVIEW_REQUIRED` when the safety engine enters `CLARIFY`. |
| A10 | PASS | `test_a10_application_does_not_assign_safety_tiers` — `tests/test_milestone4.py` | The service calls `SafetyEngine.apply` and contains no application assignment of CLARIFY/ELEVATED/URGENT/IMMEDIATE. |
| A11 | PASS | `test_a11_free_text_reaches_gate_before_conversation` — `tests/test_milestone4.py` | A recording gate is invoked before the neutral-text placeholder permits normal conversation. |
| A12 | PASS | `test_a12_transaction_rolls_back_partial_event` — `tests/test_milestone4.py` | An invalid explanation leaves neither its event row nor a new timeline entry after the transaction fails. |
| A13 | PASS | `test_a13_sensing_and_trust_survive_reload` — `tests/test_milestone4.py` | A new service instance reloads Case E as `OBSERVED + REESTABLISHING` for every signal. |
| A14 | PASS | `test_a14_safety_episode_reference_survives_reload` — `tests/test_milestone4.py` | A new service instance reloads Case F's `CLARIFY` safety state and stored safety references. |
| A15 | PASS | `test_a15_cases_a_to_e_retain_accepted_behavior` — `tests/test_milestone4.py` | Application-path A–E interruption counts remain 0/6/6/1/0, with Case D review items and Case E re-establishing trust. |
| A16 | PASS | `test_a16_case_f_safety_handoff` — `tests/test_milestone4.py` | Case F persists an `OPEN` safety episode and returns the safety-review decision. |
| A17 | PASS | `test_a17_timeline_order_is_deterministic` — `tests/test_milestone4.py` | Repeated reads match and entries sort by occurrence time, then insertion ID. |
| A18 | PASS | `test_a18_review_snapshot_is_deterministic` — `tests/test_milestone4.py` | Identical persisted state produces an identical structured snapshot. |
| A19 | PASS | `test_a19_no_endpoint_exposes_diagnostic_or_risk_score` — `tests/test_milestone4.py` | Status, snapshot, and timeline responses contain none of the prohibited diagnostic/probability/psychiatric-score fields. |
| A20 | PASS | `test_a20_api_restart_preserves_development_state` — `tests/test_milestone4.py` | Separately constructed API instances return the same persisted status from one SQLite file. |

Additional passing tests exercise HTTP creation/ingestion with fail-closed free text and held-input release after safety-gate recovery. The TestClient emitted a dependency deprecation warning; it did not affect results.

## 2. ARCHITECTURE

| Boundary | Implementation | Responsibility |
|---|---|---|
| API | `aura_app/api.py` | Validate transport schemas, call service, return responses/errors. |
| Application | `models.py`, `service.py` | Event envelope/entities, consent/idempotency checks, domain orchestration, precedence, review/status projection. |
| Longitudinal adapter | `aura_app/longitudinal.py` → accepted `aura_longitudinal` | Rebuild working state from stored inputs; call baseline, drift, context, held-registry, and communication APIs. |
| Safety adapter | `aura_app/safety.py`, `service.py` → accepted `aura_safety` | Accept resolved fixture proposals, invoke the deterministic engine, apply fail-closed output/resource planning. No detector is implemented. |
| Persistence | `repositories.py`, `persistence.py` | Repository protocols, SQLite unit of work, typed tables, ordered event replay. |
| Audit | `audit`, `safety_audit`, `safety_references` tables | Link application action/correlation to safety state and policy audit without copying free text into audit rows. |
| Fixture runner | `aura_app/simulator.py` | Feed synthetic A–F events through the **same** application service. |

Implemented flow: **patient event → API → service → atomic raw/normalized persistence → safety gate first for safety-relevant input → longitudinal projector if not held → safety-precedence communication result → output/timeline/audit persistence → API response**. Wearable-only events skip the safety gate; relevant text and structured input cannot reach conversational handling first. The projector invokes the production longitudinal modules; it contains no separate drift or communication rule. Controllers contain **no longitudinal or safety decision logic**.

## 3. DATABASE SCHEMA

SQLite is a development adapter. `app_events` stores the event envelope/payload and committed response; normalized and typed tables make the timeline queryable. “Patient FK” below means a declared foreign key; where only an ID is stored, that is stated.

| Table | Purpose | Primary key | Linkage / important FK | Write pattern |
|---|---|---|---|---|
| `patients` | Profile and onboarding | `patient_id` | Root patient record | Mutable schema, create-only API today |
| `treatment_context` | Medication/schedule/review context | `patient_id` | Patient FK | Mutable schema, create-only API |
| `consents` | Layered consent | `(patient_id, consent_type)` | Patient FK | Upsert-capable |
| `wearable_sources` | Source connection/last-seen metadata | `(patient_id, source_id)` | Patient FK | Mutable `last_seen` |
| `app_events` | Original typed envelope, payload, stored result, idempotency | `event_id` | Patient FK; unique `(patient_id,idempotency_key)` | Append event; result updated on completion/recovery |
| `observations` | Normalized signal/source/day/value/coverage | `(event_id,signal,source,metric)` | Event FK; patient ID stored | Append |
| `checkins` | Structured Good/Okay/Rough input | `event_id` | Event FK; patient ID stored | Append |
| `medication_events` | Routine status and scheduled time | `event_id` | Event FK; patient ID stored | Append |
| `contexts` | Category, window, linked signals | `event_id` | Event FK; patient ID stored | Append |
| `context_explanations` | Patient explanation and association/status | `event_id` | Event FK; patient ID stored | Insert, then status update |
| `baselines` | Current anchor, trust, sensing, rolling statistics | `(patient_id,signal,source,metric)` | Patient FK | Upsert current projection; anchor changes only via commands |
| `held_drifts` | Explained/reopened drift and direction | `(patient_id,signal,source,metric,direction)` | Patient FK | Upsert current held state |
| `review_items` | Patient-visible clinician-preparation items | `item_id` | Patient FK; unique `(patient_id,source_ref)` | Insert-if-absent today; status/share fields reserved |
| `safety_states` | Current deterministic safety state | `patient_id` | Patient FK | Upsert current state |
| `safety_references` | Per-input episode/state/sequence provenance | `event_id` | Event FK; patient ID stored | Upsert on held-input recovery |
| `archived_safety_episodes` | Immutable finalized episode snapshot | `(patient_id,episode_id)` | Archiving-event FK | Insert-if-absent |
| `timeline` | Typed raw, gap, drift, attenuation, decision, held, review, safety entries | `entry_id` | Event FK; patient ID stored | Append-oriented; ordered by `(occurred_at,entry_id)` |
| `audit` | Application action, domains, correlation, result | `audit_id` | Patient/event IDs are logical references; no declared FK | Append |
| `safety_audit` | Versioned safety attempts, before/after state and detector proposals | `attempt_id` | Event FK; patient ID stored | Append, including recovery attempts |

There is no separate idempotency table: the unique key and saved `result_json` in `app_events` form the idempotency record. Anchor command history is in `app_events`/`timeline`; current anchor is in `baselines`. Drift observations are typed `LONGITUDINAL_DRIFT` timeline entries, not a single opaque patient blob.

## 4. TRANSACTION STRATEGY

`SQLiteRepositoryFactory.transaction()` opens `BEGIN IMMEDIATE`; `PatientEventService._process()` keeps validation, duplicate lookup, normalized writes, safety result, longitudinal projection, review-item creation, timeline, saved response, and audit inside that transaction. Success commits once; an exception rolls back **all** writes from that ingestion attempt. SQLite serializes writers globally for this development implementation.

- **Domain or policy exception:** No partial raw event survives. A12's missing-context explanation reaches event insertion, fails in longitudinal association, then leaves no event or new timeline row. A thrown safety-policy/resource failure returns `SAFETY_UNAVAILABLE` (503) and rolls back the attempted event; it is not reported as success.
- **Deterministic fail-closed result:** A detector timeout/error is itself a valid safety outcome. The transaction commits the raw/normalized input, degraded safety state, safety reference/audit, `INPUT_HELD_FOR_SAFETY` timeline marker, and a `SAFETY_REVIEW_REQUIRED` response. It does **not** commit longitudinal drift/review effects for that input. On a later resolved safety input, held inputs are safety-evaluated first and released atomically; the recovery test verifies this path.
- **Retry:** The `(patient_id,idempotency_key)` lookup occurs before normalization or either domain call. A committed key returns its saved result with `idempotent_replay=true`; a rolled-back key has no record and can be retried as a new attempt.

## 5. API ENDPOINTS

| Method | Route | Purpose | Main response |
|---|---|---|---|
| GET | `/health` | Prototype health check | Health object |
| POST | `/patients` | Create profile, treatment, consent/source fixtures | Patient object |
| GET | `/patients/{patient_id}` | Read profile | Patient object |
| POST | `/patients/{patient_id}/events` | Ingest supported non-anchor envelope | `ApplicationResult` |
| GET | `/patients/{patient_id}/timeline` | Ordered typed records | Timeline array |
| GET | `/patients/{patient_id}/status` | Current sensing/trust/drift/held/safety state | Status object |
| POST | `/patients/{patient_id}/context-explanations` | Submit linked explanation | `ApplicationResult` |
| GET | `/patients/{patient_id}/review-snapshot` | Prepare structured, unshared data | `ClinicianReviewSnapshot`-shaped object |
| POST | `/patients/{patient_id}/anchors/provisional` | Named provisional-anchor command | `ApplicationResult` |
| POST | `/patients/{patient_id}/anchors/trust` | Named trust command | `ApplicationResult` |
| POST | `/patients/{patient_id}/anchors/reanchor` | Named clinical-review reanchor command | `ApplicationResult` |

Generic `/events` rejects `ANCHOR_COMMAND`; there is no generic anchor PATCH. No endpoint exposes relapse probability, depression diagnosis, or psychiatric risk percentage.

## 6. EVENT PROCESSING

| Event family | Application routing | Domain recipient |
|---|---|---|
| `WEARABLE_OBSERVATION` | Check wearable consent; normalize covered sleep/activity/HR points; update source last-seen; project sensing/rolling/drift. | `aura_longitudinal` only. |
| `PATIENT_CHECKIN` | Safety gate; then structured check-in trend and communication if evaluated. | `aura_safety`, then `aura_longitudinal`. |
| `MEDICATION_EVENT` | Safety gate; store scheduled/status event; feed routine-disruption evidence. | Both. |
| `CONTEXT_EVENT` | Store explicit category/window/affected signals; gate if it contains explanation text; apply signal-scoped context. | Longitudinal; safety when text is present. |
| `CONTEXT_EXPLANATION` | Gate text; require existing benign-context reference and explicit signal subset; invoke held registry; create review items. | Safety first, then longitudinal held logic. |
| `STRUCTURED_ASSESSMENT_RESPONSE` | Gate resolved structured input; forward explicit `changed` indicator as longitudinal evidence. No production PHQ workflow. | Both. |
| `PATIENT_FREE_TEXT` | Gate before conversational placeholder; persist result; no generation. | Safety; longitudinal replay adds no free-text interpretation. |
| `ANCHOR_COMMAND` | Accept only named command service/routes; replay explicit reference window/reviewer field. | `aura_longitudinal.BaselineManager`. |
| `REVIEW_COMMAND` | `PREPARE_REVIEW` requests a review communication; `ADD_QUESTION` is stored for snapshot and safety-gated if it contains question text. | Longitudinal; safety for text. |

No real detector, PHQ scoring, or treatment recommendation is implemented.

## 7. SAFETY INTEGRATION

`ResolvedSafetyGate.resolve()` supplies already-resolved D1–D6 proposals (the simulator uses `FixtureSafetyGate`). The service constructs an intake event and `DETECTORS_COMPLETE`/timeout/error event, then calls the accepted `SafetyEngine.apply()` against the persisted `SafetyState` under SQLite's single-writer transaction. The service does **not** assign T1–T4. A higher/degraded safety state changes the application decision to `SAFETY_REVIEW_REQUIRED` even if ordinary longitudinal communication was `STAY_QUIET`.

`PATIENT_FREE_TEXT` passes this gate before returning either `NORMAL_CONVERSATION_ALLOWED` (fixture-resolved T0 only) or `SAFETY_HANDOFF_OR_HELD`. Without a configured resolver, the public development API fails closed and holds the input. State, episode/sequence references, linked safety audit, and archived-episode snapshots are database records and survive reload. Reviewed-resource planning uses the accepted resource boundary; the fallback is explicitly unverified fixture data. **No LLM or generated conversational output is involved.**

## 8. CLINICIAN REVIEW SNAPSHOT

`PatientEventService.review_snapshot()` deterministically returns:

| Field | Source/content |
|---|---|
| `review_period` | First/last persisted event timestamps. |
| `sensing_coverage`, `baseline_status` | Current per-signal rolling coverage, trust, anchor version. |
| `meaningful_longitudinal_changes` | Grouped non-stable drift timeline records with first/last seen, count, latest description. |
| `patient_checkin_trend`, `medication_routine_events` | Typed timeline records, excluding safety-held inputs. |
| `active_context` | Current projected context associations. |
| `explained_held_for_review`, `unresolved_items` | Held-drift rows and patient-visible, unshared review items. |
| `safety_episode_references` | Persisted safety references, including episode/sequence/provenance fields; filtering issue noted in §13. |
| `patient_selected_questions` | Explicit `REVIEW_COMMAND / ADD_QUESTION` entries, if supplied. |
| `share_status`, `automatically_sent` | Always `NOT_SHARED`, `false` in this milestone. |

This is structured data, not LLM prose. Nothing is sent to a clinician. Patient approval and sharing are future workflows.

## 9. CASES A–F

Seed **7** was run with `.venv/bin/python -m aura_app.simulator --case ALL --seed 7 --db-dir /tmp/aura-m4-review-full`. The fixture runner supplies only observations, check-ins, contexts/explanation events, explicit anchor commands, and resolved safety proposals to the service; hidden `truth` labels stay in the simulator. Each case persisted four signal anchors at version 1. “Interruptions” count evaluated **days**, while a day may have multiple event-level decisions. All snapshots remained `NOT_SHARED`.

| Case | Input and application path | Final persisted state / communication | Timeline / snapshot result | Verdict |
|---|---|---|---|---|
| A — physical illness | Illness context plus higher HR, shorter sleep, lower activity and Good check-ins → API-equivalent envelopes → safety fixture T0 → longitudinal context. | Four `OBSERVED + TRUSTED`; final `STAY_QUIET`; **0** interrupted days. | 1,089 timeline entries; 124 scoped attenuation records; snapshot has 3 descriptive change groups, 0 held/review items. | PASS |
| B — slow drift | Gradually later sleep, lower activity, Good→Okay→Rough → anchored/rolling projection. | Four `OBSERVED + TRUSTED`; final `STAY_QUIET` after **6** interrupted days (2 targeted, 4 micro event decisions). | 958 timeline entries including persistent/divergent drift; 4 snapshot change groups, 0 review items. | PASS |
| C — illness + independent change | Illness-linked physiology plus unrelated later sleep/activity and worse check-ins → both safety gate and signal-scoped context. | Four `OBSERVED + TRUSTED`; final `STAY_QUIET` after **6** interrupted days. | 1,058 timeline entries, 93 attenuation records; 6 snapshot change groups and no held items. | PASS |
| D — explained benign drift | Long work-schedule shift, explicit benign context, linked patient explanation → production held registry. | Four `OBSERVED + TRUSTED`; final `STAY_QUIET`; **1** interrupted day; two `EXPLAINED_HELD_FOR_REVIEW` records, anchor version still 1. | 1,139 timeline entries, one held event and 2 review-item entries; snapshot retains 2 unshared review items. | PASS |
| E — wearable gap/return | Observed weeks, absent days 28–54, return day 55; Good check-ins continue. | Four `OBSERVED + REESTABLISHING`; final `STAY_QUIET`; **0** interrupted days. | 804 timeline entries including 4 `SENSING_GAP` and 4 `SENSING_RETURN`; snapshot has 0 change/review items. | PASS |
| F — safety handoff | Case-A-like ordinary longitudinal history, then fixture-resolved D2 concern in patient free text → `aura_safety`. | Ordinary four `OBSERVED + TRUSTED` signals remain; safety becomes `OPEN / CLARIFY`, episode `episode-F-7-69-safety-text`, sequence 1; final `SAFETY_REVIEW_REQUIRED`. | 1,096 timeline entries including safety boundary; structured snapshot retains safety references, no automatic sharing or LLM. | PASS |

Case F specifically demonstrates **ordinary longitudinal state + safety-relevant patient input → deterministic safety boundary → safety decision overrides ordinary communication → state/reference/audit persisted → no LLM**.

## 10. IDEMPOTENCY

A2 submits a Good check-in under key `duplicate-key`, then retries with a different event ID but the same patient/key. The first and retry decisions are both `STAY_QUIET`; the retry reports `idempotent_replay=true`, the timeline length is unchanged, and the retry's empty fixture gate is never needed.

A supplementary read-only diagnostic retried Case D's `D-7-30-explanation` key, whose first result created **two** review items. Before and after retry, `(observations, review_items, safety_audit, timeline)` counts were identically **(280, 2, 72, 1,139)**; the retry returned the prior `STAY_QUIET` result with `idempotent_replay=true`. Thus neither normalized observations nor safety/domain processing nor review items were duplicated.

## 11. RESTART / PERSISTENCE

The A20 test constructs new API instances against one SQLite file. A separate manual check ran the simulator writer process for E and F into `/tmp/aura-m4-review-restart`, let it exit, then reopened both files from a fresh Python process. E reloaded four `OBSERVED + REESTABLISHING` signals and its **804** timeline entries. F reloaded patient `synthetic-F-7`, the `CLARIFY` episode reference, four `OBSERVED + TRUSTED` signals, **1,096** timeline entries, and safety references in the review snapshot. Uvicorn was also started, stopped, and restarted against F's same DB; `/patients/synthetic-F-7/status` returned the same episode, mode, signals, and `SAFETY_REVIEW_REQUIRED` after restart.

Persisted: original envelopes, normalized inputs, results, baselines/trust/sensing, held/review state, current/archived safety state, safety references/audit, application audit, timeline. In-memory only: per-request replay/projector objects, fixture resolver proposal map, and resource-registry live lookup; projector state is reconstructed from persisted events. This is not a production scheduler or protected offline-client store.

## 12. ASSUMPTIONS

- **SQLite is development-only**; repository protocols provide a replaceable boundary, not a production migration/operations plan.
- **Synthetic safety proposals** are fixture-resolved inputs; no detector reliability or clinical tier mapping is claimed. The default API resolver fails closed.
- **Context signals are explicitly linked** by input; neither credibility nor affected signals are inferred from free text.
- **Anchor-review references are fixtures**, not authenticated clinicians. Named commands prevent incidental anchor movement, but reviewer identity is not verified.
- **Hidden scenario labels stay out of production decisions.** `aura_app.simulator` uses the case letter to generate events and trigger Case D's explicit explanation; it does not pass the generator's `truth`, onset labels, useful-interruption windows, or evaluation outcomes to `PatientEventService` or either engine. Case letters appear only inside opaque synthetic patient/event IDs; application code does not branch on them. No simulator/evaluation ground truth enters production application logic.

## 13. OPEN ISSUES

- A governed, evidence-based exit from `REESTABLISHING` is still undefined; only explicit trust/reanchor commands exist.
- Longitudinal windows, drift/persistence, burden rules, anchor sufficiency, and safety tier/timing/content parameters remain engineering defaults requiring clinical review.
- Benign/risk category, explanation credibility, and signal association are manually supplied; governance for accepting them is unresolved.
- Safety wording and the current unverified fixture resource bundle require qualified review and verified local resources.
- `reviewed_by` is caller-supplied: reviewer authorization and production authentication do not exist. Sharing approval/authorization also remains future work.
- Production database migrations, scaling, durable scheduler/outbox, protected offline-client storage, and cloud operations are not implemented.
- **Newly observed integration issue:** `safety_episode_references` in the review snapshot currently includes routine T0 safety-gate records with null episode IDs (Case F has 72 safety references but one concern episode). Before any clinician-sharing workflow, references need patient-approval policy and filtering to actual shareable episode references; no code was changed for this packet.

## 14. VERDICT

**Milestone 4's engineering stop condition is met:** orchestration, replaceable repository contracts, development persistence, minimum API, explicit safety/longitudinal boundaries, deterministic review snapshot, A–F runs, and A1–A20 are present and passing. The §13 issues constrain clinical use and clinician sharing; this remains a synthetic prototype. No Milestone 5 work or code change was made for this review packet.
