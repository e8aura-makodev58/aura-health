# aura-health patient simulator agent — plan

2026-10-08. Claude (planner/reviewer). **Plan for Codex to implement; approved in
direction by the user (DECISIONS §40), not yet in detail.** Demo-only: not part of the
product, not a clinical model, not evidence about patients.

## 1. Purpose

Let a demo viewer make a synthetic patient's life happen and watch AURA respond:
"the patient gets flu for 3 days, temperature rises" → telemetry changes → engines process
it → clinician brief/assessment explains it. Also supplies believable patient feedback
(check-ins, medication records, short notes). Users can still type data themselves at
any time; the simulator only supplies telemetry and optional simulated feedback.

## 2. Division of labour (same principle as aura-agent)

| Part | Who | Why |
|---|---|---|
| Choose life events, timing, severity, persona voice | **LLM "life director"** (DeepSeek via existing provider settings; offline template fallback) | Open-ended, creative, natural language |
| Turn events into numbers | **Deterministic seeded generator** with an effect table | Reproducible, bounded, plausible; LLM never writes measurements |
| Validate the plan | **Strict validator** (shape, ranges, budgets), like `validate_plan` | Same pattern as `aura_simulation/agent.py` |
| Ingest | **Existing event service** (idempotent keys, safety-first) | Simulator is just another source; no DB shortcuts |
| Decide safety, drift, trust, anchors | **Accepted engines, unchanged** | Simulator must not influence decisions except through observable events |

## 3. Telemetry channels (scope decision flagged)

The accepted longitudinal engine handles four signals only: sleep timing, sleep duration,
activity, resting heart rate (framework §6 primary signals). Adding signals to drift
detection is a clinical-configuration change nobody has authorized. Proposal:

- **Engine-fed (unchanged):** sleep midpoint, sleep duration, activity, resting HR.
- **Display-only telemetry (new, never feeds drift/trust/safety):** skin/body temperature
  (deviation from personal norm for wearables; absolute °C for manual thermometer),
  HRV, respiratory rate, SpO2, blood pressure (sparse, cuff-style: a few readings per week,
  not continuous), and optionally steps detail. Stored as observations, charted in the
  clinician and "full data" views, available to the agent as cited facts, clearly absent
  from decisions. Needs a new observation event type and projection; Codex to design,
  keeping accepted engine/schema behaviour otherwise unchanged.
- Realism note: consumer wearables do not measure blood pressure continuously; model BP as
  periodic readings.

## 4. Life-event catalogue (initial, illustrative effect sizes)

Effects are engineering values for plausible-looking demos, **not clinical parameters**;
document them in a config file and label them as such. Each event has start day, duration,
severity (mild/moderate/strong) and a recovery tail.

| Event | Typical duration | Effects |
|---|---|---|
| Flu / viral illness | 3–7 d | temp +0.8–1.5 °C; RHR +6–12 bpm; HRV down; resp rate and SpO2 slightly worse; sleep longer but fragmented; activity −40–70 %; check-ins Rough; med routine usually kept; context candidate: ILLNESS |
| Travel / jet lag | 3–6 d | sleep midpoint shifted 2–6 h then drifting back; duration irregular; activity up then down |
| Work deadline stress | 5–14 d | sleep shorter and later; RHR +2–4; HRV down; check-ins Okay/Rough |
| Alcohol night | 1 d | RHR +5 that night, HRV down, sleep fragmented |
| Missed medication run | 2–5 d | acknowledgement events missing/"missed"; no direct physiological effect modelled |
| Wearable off / battery | 1–10 d | gap (no values), then return |
| Exercise block | 7–21 d | activity up, RHR slowly down |

Every event can also be combined (flu during travel). Users may add events from buttons or
by describing them in words.

## 5. Life director (LLM)

Input: persona (age band, job, routine, medication regimen label from the existing
profile), the current date/day index, a short digest of the last events (observable data
only), and the user's request ("she catches flu on Thursday and still flies on Monday").
Output (strict JSON): `{events:[{type,start_day,duration_days,severity}], feedback:[{day,
checkin?,medication?,note_theme?}]}`. Validator: known types, bounded counts and windows
(e.g. ≤ 30 days per advance, ≤ 8 events), severity enum, no numeric telemetry, no free
text beyond a short note theme. Offline fallback: keyword template planner (flu, travel,
stress, alcohol, missed meds, battery) so the demo works with no model.

**Patient feedback text** (notes) is free text and therefore follows DECISIONS §39.3:
it goes through the same layered safety gate as user text, is quoted as data, and is never
a bypass. Safety scenarios stay on the existing curated fixtures (`SAFETY_CONCERN`,
`FIGURATIVE`, `GATE_TIMEOUT`); the director must not write self-harm content.

## 6. Generator

Seeded (`seed`, `patient_id`, day index) so a replay is exact. Baseline per channel from
the persona/profile, daily and weekly noise, event effects added with ramp-up/recovery
shapes, plausible clamps. Output as ordinary observation events with idempotency keys like
`sim:{run_id}:{day}:{channel}`, `source="SIMULATOR"` so provenance is visible, then ingested
through the normal service. No event may carry ground truth ("this is flu") except where the
simulated patient explicitly reports context through the normal explicit-association path.
Extend M7's hidden-truth isolation test to cover the new components.

## 7. Interaction and UI

- Lives in the **Demo guide** only, never in the patient or clinician view.
- Controls: "Advance 1 / 3 / 7 days", quick event buttons (Flu 3 days, Travel, Stressful
  week, Wearable off), a text box "Describe what happens", and "Simulated feedback: on/off".
- After advancing, show a one-line summary of what was simulated ("Flu, days 12–14,
  moderate") and a link to the clinician brief/assessment; optionally run the assessment
  automatically.
- Manual user inputs continue to work alongside; simulated and manual events are
  distinguishable in the timeline by source.
- Hosted: each browser has a private workspace clone, so simulation never affects others;
  rate-limit advances; a reset button already exists.

## 8. Audit and storage

Append-only `simulator_runs` trace (plan, validator result, provider/model, seed,
event ID range, fallback reason) mirroring `agent_runs`. Idempotent run IDs. Plan and
generated values reproducible from seed + plan.

## 9. Acceptance criteria

- With no model: all quick events and the keyword planner work end to end.
- With DeepSeek: a free-text request yields a validated plan or a labelled fallback.
- Flu example: temperature rises for the chosen days and returns; RHR/sleep/activity
  respond; the engines process the engine-fed channels unchanged; the assessment cites
  the temperature facts; display-only channels never change a decision (test).
- Same seed + plan → identical events (replay test).
- Simulator cannot write anything except via the event service; no hidden-truth leak
  (isolation test); director output never contains telemetry numbers.
- Simulated notes cannot bypass the safety gate; GATE_TIMEOUT holds them.
- Budgets enforced (days per advance, events per plan, runs per session).
- Simulator UI absent from the patient and clinician views; not mentioned in
  submission claims as product functionality.

## 10. Risks and open questions

- Adding display-only channels needs a new observation type and projection; confirm it
  does not touch accepted engine behaviour or the existing schema guarantees.
- Illustrative effect sizes must not be presented as physiology or clinical truth.
- A simulator that fills the record can make AURA look validated; keep the Disclaimer page
  explicit that results are on synthetic, simulator-generated data.
- Long simulated horizons interact with the known replay-per-event cost issue.
