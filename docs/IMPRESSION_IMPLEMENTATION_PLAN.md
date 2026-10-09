# Visible assessment and patient recap — implementation plan

2026-10-09. Planning agent, delegated by Codex after the user's instruction to proceed.
Scope: `IMPRESSION_SPEC.md` I1–I8 and `DECISIONS.md` §§42–43. These are presentation,
read-only agent orchestration and demo changes; accepted safety/longitudinal algorithms
remain unchanged. Claude reviews the implementation. This plan does not declare acceptance.

## Design

The first clinician screen should answer **what changed, when, and what was reported**.
The first patient screen should answer **what AURA has noticed, in everyday words**.
Neither audience needs to request a draft to see value. Patient charts remain on demand.

Build order: arrival boundary → assessment/recap → linked charts → simplified disclosures
→ live-input refresh → visible questions → guided story → raw-record comparison.

## 1. Server-owned arrival boundary (I1, I6)

Add a small read-only presentation service (for example `aura_app/assessment.py`) and a
thin `GET /patients/{patient_id}/assessment/{role}` route for clinician brief and patient
insight. Return a guarded deterministic preview immediately, a state fingerprint, a
server-owned run ID, an optional exact cached agent result, and whether generation may be
requested. Accept a validated offline flag where needed. Do not make the GET call a model.

Reuse `AgentService._approval`, `RecordTools`, existing evidence preparation and the
existing `POST /patients/{id}/agent/{role}` execution path. Factor shared record preparation
if needed; do not create another safety or grounding implementation. Provider `model_id`
already contains the settings revision, so the existing signature captures provider/key
changes as well as safety, events, baselines, held records and configuration.

- Derive the automatic run ID from role, window, presentation version and server signature.
  Repeated opens/toggles use the same persisted `agent_runs` result, including failures.
- Read cache only after current approval; never return previously permitted claims over
  a blocked, changed or offline state. Preserve existing before/after generation race checks.
- Keep fallback construction outside agent DB append semantics: preview must not occupy
  the eventual generation run ID or create audit churn on every refresh.
- If a POST uses an obsolete automatic fingerprint, reject before the paid call where
  practical; otherwise the existing post-generation guard must still discard stale content.
- A single in-flight request per role/signature in the browser, plus existing service lock
  and persisted idempotency, prevents duplicate paid requests. No retry loop on provider error.
- Only request the currently visible audience's arrival role. QA and visit generation remain
  explicit. No model request for a hidden tab, disclaimer page, offline or blocked state.
- Browser request tickets include patient, role, fingerprint and offline state. Reset stale
  content immediately on record/offline change; do not leave old claims visible while checking.

Return presentation metadata derived from committed facts: ≤20-word display headline,
up to three primary dated findings with numeric companion facts where present, context,
gaps, and approved questions. Preserve **all** original checked claims, required finding
coverage, sources and traces in Evidence; the display cap must not weaken grounding.
Use static approved safety status for unsafe states, not an ordinary reassuring recap.

For immediate extraction, retrieve scoped tools deterministically without invoking a model.
Retain exact citation IDs/refs. A plain patient template should translate structured finding
direction/dates and committed deltas into short sentences (e.g. sleep later than your usual),
not perform global replacements on arbitrary model text. Update patient insight's prompt
to everyday language and ≤2 short sentences, preserving its existing claim checks and
no-task/no-diagnosis contract. Hide only when the committed record has nothing noteworthy;
do not invent a change or ask a question to populate a stable home.

## 2. Assessment-first UI and disclosure structure (I1, I4, I5, I6)

Edit `aura_ui/index.html`, `agent.js`, `app.js`, `features.js`, and `styles.css`:

- Promote `#agent-workspace` to the first clinician card; retain existing output IDs where
  sensible. Render extraction at once and replace with checked AI using identical structure.
  Chip truthfully distinguishes checked AI, mixed extraction, offline extraction and paused.
- Put the record question input and **three** existing canned-query chips directly below the
  assessment; Enter/click calls the existing safety-gated `record_qa` route. Answers remain
  sourced. The free-text gate now exists; do not regress to an unrestricted chat endpoint.
- Replace collapsed `#month-recap` and `#recap-charts` with an open text recap on patient home.
  No home SVG/charts. Keep one-tap full data and visit-note access with **Not sent** visible.
- Limit main clinician disclosure groups to **Evidence**, **Context**, **Details**. Collect
  source links, complete findings and source tables in Evidence rather than adding one
  accordion per finding/chart. Context holds explanations/retained items; Details holds
  timeline, references, safety history and trace. Input forms can use explicit buttons/dialogs
  instead of more nested accordions. Pinned active safety resources never become a disclosure.
- Use presentation labels "your usual", "sleep time", and "recent data". Keep exact internal
  state/source values inspectable in Details. Patient recap itself has no anchor/drift/baseline
  jargon. Move limitations copy to Disclaimer; preserve Demo, source and trust/sensing chips.
- Preserve existing IDs accessed unconditionally by app.js, notably `#hosted-notice`, or
  update those accesses safely. Do not hide controls through brittle CSS without changing
  their accessible semantics. Keep keyboard, reduced-motion and 320/390px overflow coverage.

## 3. Chart story from committed facts (I2)

In `evidence.js`, use the selected finding's exact `signal`/`since` and its linked stored
last-seen date as the display span end; no new detector or browser drift computation.
Add stable numbered finding anchors and matching SVG bands/markers. Finding clicks focus
the corresponding chart/span and chart marker links back to its narrative finding.

Keep source/metric distinction: two sources for a signal must not share an unqualified band.
Use claim fact IDs to resolve to evidence findings, not model prose or invented date parsing.
Preserve gaps and reference versions. All four primary charts have the same date axis;
place a categorical Good/Okay/Rough strip directly below using that axis (no connected trend).
Render context markers across charts for timing, but visually distinguish **linked** context
from unlinked event markers: only explicitly associated signals get attenuation/shading.
Additional registry channels remain inspectable without dominating the four-chart story.

## 4. Inputs visibly change the assessment (I3)

Reuse `WorkflowService.advance` and existing life director. Add direct guide actions for
flu 3 days, travel, work stress and missed medication (not buttons that merely fill a box).
Keep seed/feedback controls and manual intake. After commit, refresh the record and fetch a
new arrival result; remove/consolidate `features.js`'s old button-click auto-assessment
listener so one commit cannot trigger both an explicit random-ID and automatic cached run.

Compare new vs previous displayed claim/finding signatures (source-linked signal/date/text),
highlight changed/new lines briefly, respect reduced motion, and explain when no committed
finding changed. Do not claim an event caused a physiological finding simply because it
was simulated. Measurement intake remains atomic and existing sparse/recovery rules remain.

## 5. Guided story and raw comparison (I7, I8)

Guide buttons: quiet month → event → approved question → clinician assessment → visit note.
Each step has one narration sentence. Use the existing stable/checkpoint fixtures and real
advance/intake paths; disclose checkpoint selection, not a falsely continuous timeline.
Only display an "AURA asks" step when the production communication result actually permits
an interaction; otherwise say no question is needed, or explicitly select a labelled fixture
where one exists. Never manufacture a prompt authorization, clearance, booked visit or sharing.
The visit step should switch to patient review intentionally (current clinician navigation
forces `patterns`) and show an actual prepared **Not sent** preview.

Clinician comparison is opt-in and hidden initially: raw measurement table/export on the left,
current sourced AURA assessment on the right. Use exactly the same selected chart dates,
source rows and missingness. Responsive single-column on phones. No efficacy claims.

## Files likely involved

- `aura_app/assessment.py` (new) and small shared preparation/arrival additions in
  `aura_app/agent.py`; thin route in `aura_app/api.py` and hosted route/transport validation.
- `aura_agent/templates.py`, `skills/patient_insight/SKILL.md`, optionally presentation-only
  wording content; no clinical thresholds or accepted engine changes.
- `aura_ui/index.html`, `app.js`, `agent.js`, `evidence.js`, `features.js`, `styles.css`.
- `tests/test_impression.py` and `tests/browser/impression.cjs` (new); update old browser
  assertions only where §§43/I1 intentionally supersede them; implementation notes/runbook.

No new dependency, domain migration, authentication system, sharing workflow or other-condition
policy is required. Reuse `agent_runs` for durable cache/audit; avoid a new cache table.

## Verification

Add I1–I8 tests with separate guard/race/cache assertions:

1. Case B immediate preview has headline and ≥2 dated numerical findings; retrieval invokes
   no provider; repeated automatic run is exact cached result with one domain-neutral agent call.
2. Blocked/degraded/offline arrival returns static/paused output and no provider invocation;
   provider revision, new event or safety change invalidates old cache; in-flight stale result
   cannot replace current visible safety state.
3. Top display cap preserves all required history in underlying output/Evidence and citations.
4. Patient default has ≤2 plain sourced lines, no home charts, optional full data and Not sent;
   stable empty result remains quiet and blocked recap does not reassure.
5. Finding bands and numbered anchors match exact committed signal/source/dates; unrelated
   context never receives attenuation; chart gap/no-zero/reference-version tests remain green.
6. One committed input triggers one cached role refresh; changed lines marked; quick actions
   use existing workflow endpoint; manual/import/context paths remain present and atomic.
7. QA input/three suggestions visible and questions still hit the safety boundary before model;
   three main disclosure groups only; source/trace content remains inspectable.
8. Guided story uses production communication permission and real Not sent visit output;
   raw comparison is initially hidden and uses exactly the selected date window.

Existing `AG_UI3` optional recap/mini-chart assertions and `DV2` zero POST-on-toggle assertion
are deliberately superseded: require no **domain mutation**, no duplicate run for unchanged
role/signature, and no home charts instead. Range change still causes no generation/mutation.
Other accepted P/L/A/G/AW/UI/safety/isolation/idempotency tests should remain unchanged in meaning.

Run full unittest gate, updated hosted browser suites plus impression suite at 320/390/1280,
public no-paid-model smoke, and a bounded synthetic live arrival/event timing check. Main owns
HANDOVER update, deployment, commit and push; planning/coding agents do not.

## Targets and honest limits

No policy contradiction blocks implementation. **Live <5 s and flu <30 s are performance
targets, not facts yet.** The last live clinician brief took 5.759 s; model latency is external
and validation may fall back. The first advance may bootstrap 28 synthetic reference days and
run accepted event-history replay, exceeding 30 s. Surface immediate extraction/progress and
measure end-to-end timings; do not bypass validation, hide bootstrap duration, invent a trusted
reference, or rewrite accepted algorithms to satisfy a demo stopwatch. Cache hits should be
fast. A separate optimization proposal can follow if measurements miss targets.

Grounding/verifier checks remain engineering safeguards, not clinical verification. Required
reference trust exit, context credibility, sponsor content review and production authorization
remain known limitations; this UI work does not silently settle them.
