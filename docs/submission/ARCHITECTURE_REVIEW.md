# Architecture PDF review — 2026-10-14

**Verdict: the high-level architecture matches the implementation. Two guarantees
needed narrower wording; several flows and demo boundaries needed clearer labels.**
The revised PDF and native diagram slides now describe the inspected code.

Reviewed the user's five-page `aura-health-architecture.pdf`, including connector
directions and visible wording, against immutable `origin/main`
`90e31ea6d7b797264bfc31fa0ae16229b76e164c`. The document's diagram instructions
were treated as review material, not authority to change product behavior.
This is a code/documentation audit, not a fresh live-deployment or clinical review.

## Corrections made

| Location | Original wording / depiction | Implementation evidence and correction |
|---|---|---|
| PDF p3, time limit | “Limits per answer … 90 seconds” | `aura_agent/engineering_config.json` sets 8 steps, 24 model-selected tool calls, 90 s and a 30-s provider timeout. `runtime.run` checks elapsed time before/after loop model calls and after verification; it does not cancel an in-flight call at 90 s. Request processing, fallback extraction and persistence are additional work. Changed to **loop budgets**, with the between-call check, provider timeout and separate verifier stated explicitly. This is not a 90-s response-time guarantee. |
| PDF p4, pinned resources | “Never waits for an AI model” | `aura_safety.output.output_plan` and resource lookup/rendering use no model. However, `aura_detectors.layered.LayeredSafetyGate.resolve` can synchronously call the semantic model before committing a new safety assessment. `aura_ui/app.js:loadPatient` also awaits `/communication` before rendering; that service can generate permitted wording, e.g. T2. Replaced the latency promise with **Resource rendering uses no model**, and disclosed model-assisted assessment and fail-closed failure. |
| PDF p4, fixed-output path | “T4 / offline: fixed text, no AI” | `output_plan` prohibits generated wording for T4, offline and degraded states. This concerns output permission; it does not prohibit all later detector model calls on new input. Label now reads **T4 / offline / degraded: fixed wording**. The app's T3 wording subset is also static, although the domain permits validated T3 generation. |
| PDF p4, resource fallback | “Old bundle stays visible” | `ResourceRegistry.resolve` uses its configured built-in fallback on live lookup failure; it does not retain an arbitrary previously successful live bundle. The browser uses its own matching built-in fixture when offline. Changed to **built-in fallback; stale/unverified: visible + notice**. No verified crisis contacts are supplied in the current fixture. |
| PDF p2, simulation connector | Observable events enter the application container, near the longitudinal box | This was a compressed container-level arrow, not an implemented bypass. Labelled it **Observable events via app ingestion**: the driver/workflow submits ordinary events to `PatientEventService.process/process_batch`, including consent, idempotency, relevant safety handling and atomic persistence. Hidden scenario truth stays outside product decisions. |
| PDF p2, application/AI connector | One-way arrow labelled “reads” | `AgentService` sends a permitted request/snapshot to the runtime and receives results/trace; `RecordTools` reads a prepared immutable snapshot. Updated to **request / result**, with both directions. No model SQL or write access is implied. |
| PDF p2, companion inventory | Medication, dose and coming-up cards; optional suggestions absent | `CompanionService.get` includes deterministic optional curated suggestions. Added them, plus explicit SQLite/audit and idempotency labels. Displayed dates are not push reminders or booked appointments; routine records are patient reports. |
| PDF p2–3, demo and guard scope | Production authorization and provider revision omitted | Added **demo roles, no clinical authentication; visit preview Not sent**. Step 1 is **Guard the request**, not patient/clinician approval. Step 5 explicitly includes provider revision: the agent fingerprint contains record/state/config and `provider.model_id`, which includes the settings revision. |
| PDF p3, failure handling | “Failure shows source-based related facts” | `runtime.run` can return related factual extraction after draft/provider failure, but an unmatched question may have no related facts. `AgentService` suppresses ordinary output when state becomes blocked or changes; cached stale responses are empty. Added **when available**, and distinguished blocked/stale suppression. |
| Architecture source §9, §14 | 50-s budget, 15-s timeout; DeepSeek presented as current | Updated source to the checked-in 90/30 settings and operator-selected provider/model/reasoning. Historical provider runs remain separately dated; no live model configuration was inferred from source code. |

## Boundaries confirmed

| Claim | Concrete source |
|---|---|
| One FastAPI/Python application, repository interfaces, SQLite and linked audit | `aura_app/api.py`, `service.py`, `repositories.py`, `persistence.py`; `compose.yaml` |
| Authoritative deterministic T0–T4 policy, detector evidence proposals and degraded fail-closed behavior | `aura_safety/domain.py`, `engine.py`, `output.py`; `aura_app/service.py:_safety_boundary`; `aura_detectors/layered.py` |
| Separate governed personal anchor and adaptive rolling reference | `aura_app/longitudinal.py`; `aura_longitudinal/baseline.py` and its explicit anchor commands |
| Read-only agent tools scoped by patient and permitted date window | `aura_agent/tools.py:RecordTools`; `aura_agent/roles.py`; agent has no write handle |
| Deterministic schema/citation/number checks, separate verification for eligible live drafts | `aura_agent/grounding.py`, `runtime.py`, `tasks.py`; verifier can use the same provider/model |
| Fresh-state checks before generation, before persistence and at Q&A display | `aura_app/agent.py:_approval/_execute`; Q&A click handler in `aura_ui/agent.js` |
| Patient typed Q&A is safety-assessed testimony; clinician questions remain attributed to the run | `AgentService._execute`; caller-declared actor is a synthetic-demo boundary, not authentication |
| Medication answers are fixed curated text; optional model only selects a topic | `aura_app/medication_ask.py`; `aura_agent/medication.py`, `medication_info.json` |
| Medication retry identity now includes the exact question hash | `MedicationAskService.ask`; regression `test_med4b_reused_run_id_with_new_text_is_assessed_again` |
| Companion projection is read-only; safety suppresses medication/suggestions | `aura_app/companion.py`; `aura_ui/companion.js` |
| Arrival recap uses an immediate deterministic preview, cache and guarded generation | `aura_app/assessment.py`; automatic summaries have constrained wording/fact selection, unlike Q&A investigation |
| Policy resources are separate from generated prose; patient navigation cannot dismiss them | `aura_safety/resources.py`, `output.py`; `aura_ui/app.js:renderResources/showSafety/goPage` |
| Clinician view is a read of the synthetic record; no alerts, automatic sharing or saved approval workflow | `aura_ui/app.js`, `aura_app/service.py:review_snapshot`, agent `share_status=NOT_SENT`; deployment/session code |

## Delivered and validation

- Corrected five-page PDF: `assets/aura-health-architecture-reviewed.pdf`.
  Original cover/closing pages preserved; the attachment was not overwritten.
- Canonical eighteen-slide deck: `assets/aura-health-deck.pptx`, diagrams on
  slides 11–13 updated as editable shapes with attached connectors. Other slide
  XML is preserved. The required architecture upload remains this one deck.
- Shared source: `../presentation/deck/native_diagrams.py`; regenerated diagram
  PNGs and deck frames. Historical SVGs are explicitly labelled historical.
- Reproducible exporter: `../presentation/deck/reconcile_architecture.py`.
  It draws the shared native shapes/text with ReportLab, embeds Nunito, checks
  text bounds, and preserves the supplied PDF's bookends. PDF/PNG appearance was
  inspected; this is not a PowerPoint or LibreOffice rendering verification.
- Full implementation regression: `.venv/bin/python -m unittest discover -s tests -q`
  — **334 tests PASS /459.063 seconds**. Existing Starlette/httpx deprecation
  warning. The restricted runner stalled and was terminated; the completed run
  used unrestricted local test access. No tests were added for these documentation changes.
- Artifact checks passed: eighteen slides, only11–13 slide XML changed, eighteen
  attached connectors referencing existing boxes, five PDF pages with readable
  text and pixel-identical original bookends, six matching1920×1080 PNGs.
- A mock-clock probe confirmed the deadline interpretation: a call started at
  89 s and returned at119 s; the runtime then emitted `MODEL_TIMEOUT` with119,000 ms
  elapsed and no generated output. No real delay or external model was involved.

No runtime, domain configuration, clinical threshold, provider setting or quota
was changed. No paid model calls, source-publication change, merge, deployment,
video rebuild or submission was performed. The video owner should refresh any
embedded architecture frames before publishing a final cut.

## Claude validation and fixes — 2026-10-14

Spot-checked the corrections against code (runtime between-call deadline checks, `LayeredSafetyGate`
model call, `ResourceRegistry` built-in fallback, `output_plan` offline/degraded no-generation,
separate `verify` task, settings revision in `provider.model_id`): all confirmed. Rendered the deck
with LibreOffice and fixed three presentation issues, then re-ran `reconcile_architecture.py`:
- `reconcile_architecture.py` read `shape.line.color`, which in python-pptx turns a no-outline box
  into a solid outline in the saved deck; it now reads `shape.line.fill.type` instead (boxes are
  outline-free again; only the dashed group frames have outlines).
- Slide 11: "Patient companion" text shortened so it fits even with a wider substitute font
  ("Recap, dose + reasons / Medication, dates / Optional small ideas").
- Slide 11: "Observable events via app ingestion" moved off the connector, beside the arrow.
Checked: 18 slides, 18 connectors glued to existing boxes, audit notes on slides 11–13, cover
unchanged, 5-page PDF. Video voice-over section E reworded to "loop budgets" and "safety resources
are shown without any AI model".
