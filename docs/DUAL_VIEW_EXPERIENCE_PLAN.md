# AURA — two views, one longitudinal record

2026-10-07. **Planning only; for Claude review, then user agreement.**
The user requests a very simple, intuitive, visual patient experience and an
analytical clinician dashboard, switched by a demo toggle. This supersedes the
earlier exclusion of clinician-dashboard work **for this proposed demo scope**;
it does not authorize production clinical access or new medical policy.

## 1. Product agreement before implementation

Patient benefit: **less to keep track of between appointments, an easy way to
mention something, and a clear note to bring to the clinician.**

Clinician benefit: **understand what changed, when, what the patient reported,
and how complete the evidence is—without reading months of records.**

These are two presentations of the same persisted selected synthetic patient,
not two independent products. Detailed analysis belongs primarily in the clinician
workspace; it remains optionally inspectable by the patient. Neither view diagnoses,
predicts relapse, recommends treatment, determines suicide risk or implies monitoring
by a human. Visual simplicity is not permission to hide mandatory safety content.

## 2. Demo shell and trust boundaries

```text
Synthetic demo · no real information     [Patient | Clinician]   [Demo guide] [⚙]
                 same selected patient / checkpoint
                      ↓                 ↓
              minimal patient      analytical workspace
                      ↓                 ↓
                 existing application read/write boundaries
                      ↓
              accepted longitudinal / safety engines
```

- Patient is the default view. The switch changes presentation only: no events,
  permissions, anchor changes, sharing or safety downgrades occur on toggle.
- Clinician view says **Synthetic clinician demonstration — not a shared patient
  record**. All current snapshots remain `NOT_SHARED`. A demo viewer can inspect
  synthetic records, not obtain clinical authorization by selecting a role.
- Real clinician access later requires identity, authorization and an explicit
  patient-approved/versioned sharing workflow. There is no automatic transmission.
- Scenario labels, narration, reset and simulated time stay in Demo guide. Hidden
  truth/useful-interruption windows never enter production decision inputs.
- The existing gear stays protected by its separate admin unlock. Clinician mode
  does not unlock keys or permit paid connection tests.
- Keep one concise synthetic notice outside the patient frame; detailed limitations,
  configured provider and actual generated/fallback provenance remain accessible.
  Do not imply that an institution-hosted private model already exists.

## 3. Patient: one current moment, not a dashboard

```text
┌──────────────────────────────────┐
│ AURA                             │
│                                  │
│ No question from AURA right now.  │
│          [quiet visual motif]    │
│                                  │
│ [ I want to mention something ] │
│                                  │
│ Prepare for my appointment     › │
│ My recorded information        › │
└──────────────────────────────────┘
```

Proposed visuals are functional: a small static open circle for “no question”, a
labelled question bubble when an approved answer is requested, and a document icon
for appointment preparation. No changing smiley, mood-colored orb or gauge suggests
that AURA has assessed mental health. The same text meaning remains available to
screen readers; icons supplement it rather than require interpretation. Within
optional recorded information, a simple dated sequence can show “You recorded…”
events without turning them into a score or a daily task.

The motif carries no health classification. No daily checklist, metrics, streaks,
permanent check-in/routine cards or three competing analytical tabs. An ordinary
day requires no visit; quiet means no current question, not that the person is safe
or healthy. Medication recording is an optional action inside recorded information,
or the current moment when explicitly chosen—not a treatment instruction.

When the server supplies a communication intent, replace the quiet area with one
short approved question, relevant answer controls and optional “Why this question?”.
Do not manufacture a question because a drift exists; Case B's final quiet cooldown
can coexist with retained change. “Not now” requires a defined ordinary deferral
contract and cannot dismiss safety, erase evidence or change a reference. Until that
contract is approved, defer control is an explicit implementation gap.

Four shortest journeys:

| Moment | Visible action | Honest endpoint |
|---|---|---|
| Ordinary day | None required; optional routine record. | No task, or “Record saved.” |
| AURA has a question | One focused answer; reason optional. | Answer saved; engine decides what remains active. No unconditional promise of silence. |
| Patient initiates | Choose a supported concern/record; fixture examples live in the demo guide. | Assessed/stored/held states distinguished. No arbitrary chat promise or inferred safety from a concern chip. |
| Appointment | Short deterministic factual preview, then optional evidence. | Clearly **Not sent**. Current selection is temporary; no “Saved/approved” promise until a persisted workflow exists. |

Good/Okay/Rough and acknowledged/missed/unknown can reuse accepted fixture paths.
Side effects, stopping treatment and arbitrary concerns are not currently resolved
paths. Do not map them to benign check-ins; plan them separately or omit unsupported
actions. All text retains the universal safety gate. Benign context affects only
explicitly linked signals; work stress is not a benign clearing answer.

Portrait first: short copy, labelled icons, large touch targets, no reliance on
color, generous but economical whitespace. Persistent concern access survives
secondary screens. Mandatory safety output/resources remain independently accessible
across views and offline; short screens may scroll rather than truncate policy text.

## 4. Clinician: analytical, focused, not a psychiatric risk dashboard

Start with **one selected synthetic patient**, not a population ranking or alert
queue. Optimize laptop for a time-limited GP review; phone fallback stacks sections.

```text
Selected patient · treatment context · actual record dates · coverage/trust limits
┌───────────────────────────────┬─────────────────────────────────┐
│ What changed / when           │ Patient's questions + context   │
│ Concise descriptive findings │ Held / unresolved review items  │
├───────────────────────────────┴─────────────────────────────────┤
│ Shared date axis: sleep timing + duration                       │
│                  activity; resting HR                          │
│ Actual observations · stored rolling · anchored reference       │
│ Gaps explicit; context bands scoped to their associated signals │
├─────────────────────────────────────────────────────────────────┤
│ Good / Okay / Rough entries · medication routine records        │
│ Safety episode references / status / incomplete follow-up       │
│ Evidence drawer: dates, sources, coverage, reference governance  │
└─────────────────────────────────────────────────────────────────┘
```

Analysis means better inspection, not more speculative inference:

- Four small-multiple charts with units and comparable time axes; no combined
  mental-health score. Sleep midpoint uses consistent source units/timezone and
  explicit overnight wrapping—not an invented clinical threshold.
- Raw observed points and production rolling values are distinct. Show anchor
  version/reference dates; historical anchor changes must use stored command/result
  provenance, not extend today's anchor backward as if always authoritative.
- Missing/insufficient periods remain gaps, never interpolated zero/normal. A point
  returning after a gap does not imply restored trust. `REESTABLISHING` remains
  labelled; no new exit rule is proposed.
- Drift/context/held annotations come from stored engine outputs. Show retained
  drift alongside its explanation and any reopening reason. Illness shading on HR
  must not visually clear independent check-ins or unrelated sleep timing.
- Check-ins are categorical patient reports, not a numeric depression trend.
  Routine acknowledgements are self-report, not verified ingestion/adherence.
- Safety is a separate policy-status/episode section with sequence, provenance,
  lifecycle, degradation/incomplete follow-up and timestamps. Never a risk percentage,
  inferred diagnosis, or automatically resolved status. Keep policy resources
  independent; clarify that no clinician/emergency service was notified.
- No dose editor, anchor command, “dismiss safety” or automatic messaging in the
  first dashboard. Reviewer authorization is not solved by caller-supplied identity.
- Selecting a finding reveals its exact source records and reference window.
  Historical findings and current communication are distinguished. Clinician-facing
  detail stays descriptive even if optional bounded wording is enabled.

## 5. Reuse, projections and genuinely new workflows

Evidence inspected: `aura_app/{api,service,patient_view,longitudinal,persistence,demo}.py`,
`MILESTONE3_REVIEW.md`, `MILESTONE4_REVIEW.md`, `MILESTONE6_REVIEW.md`, the framework,
and the prior reassessment/storyboard/UX documents. Existing mechanics are reusable;
the rejected information hierarchy is not a usability constraint.

| Capability | Existing source | Planned treatment / gap |
|---|---|---|
| Patient identity/treatment | `GET /patients/{id}` | Reuse; distinguish recorded regimen from instructions. |
| Current drift/held/sensing/trust/anchor/rolling | `GET /patients/{id}/status` | Render committed state, never recalculate it. |
| Source observations, context, decisions, anchor events | `GET /patients/{id}/timeline` | Reuse typed records; no hidden scenario inputs. |
| Latest event, context association, routine, disclosure | `GET /patients/{id}/view` | Reuse read-only presentation links. |
| Factual review data/questions | `GET /patients/{id}/review-snapshot` | Reuse; period currently covers complete history, coverage is current rolling coverage—not automatically whole-period coverage. |
| Bounded question wording | Existing event communication endpoint | Reuse permitted modes/validation/fallback, not open conversation. |
| Check-in/routine/explanation | Existing event/explanation commands | Preserve idempotency, explicit association and authoritative engine decisions. |
| Full historical rolling/anchor series | Persisted event `result_json`; current status only shows latest | New **read-only projection** may expose ordered committed per-event baselines. Do not smooth/recompute them in JS; no engine/schema change presumed. |
| Safety provenance detail | Persisted safety references/current state; snapshot is abbreviated | New bounded read-only projection if timeline/status are insufficient; omit routine null references without deleting history. |
| Date filtering / chart evidence contract | Current endpoints lack a dedicated chart contract | Define application read projection with units/source IDs and nulls; initially use actual full-record period. No new statistical/clinical rules. |
| Approved selected appointment note | Not persisted; temporary preview only | **New persisted workflow**, not part of initial read-only dashboard. Needs selection/version/audit and explicit user approval; cannot be simulated as an existing permission. |
| Ordinary deferral / extra concern categories | Not complete today | Separate application contracts/approved synthetic fixtures if subsequently authorized; never frontend safety classification. |

Frontend may format dates/coordinates and arrange records. It may not derive drift,
rolling statistics, sensing/trust transitions, safety tiers, context credibility or
new urgency rankings. If saved historical output is unavailable, show unavailable
or a labelled current summary—not a fabricated historical line. No new data required.

## 6. Cases A–F: toggle reveals the reason, not another patient's story

For each case, select an existing checkpoint in Demo guide once. Toggle keeps the
same `patient_id`, persisted event state and timestamp. Current before/after checkpoints
are distinct seeded records: label that explicitly; do not pretend fast-forward
mutated one record unless implemented through accepted observable-event replay.

| Case | Patient moment | Clinician evidence on that same selection |
|---|---|---|
| A | Quiet; optional explanation of illness-related changes. | Temporary physiology changes, scoped illness context, stable reported check-ins; changes retained without a mental-health conclusion. |
| B | Quiet at final cooldown, or existing approved prompt at its actual event. | Rolling adapts; anchor divergence and later sleep/lower activity plus categorical check-ins remain visible. |
| C | Existing focused clarification. | Illness-linked attenuation and independent sleep/check-in evidence coexist; no whole-state clearance. |
| D | Explanation confirmation/quiet held state. | Unchanged reference, retained drift/explanation, two review items; repeat prompts suppressed for the same held drift. |
| E | Data unavailable, then data returned with reference uncertainty. | Explicit gap, absent values, retained old anchor and `REESTABLISHING`; no deterioration inference. |
| F | Authoritative safety interaction, not ordinary conversation. | Linked safety policy state/episode/provenance and incomplete/held status where present; static/fallback output, no safety decided by an LLM. |

## 7. Proposed stages and acceptance gate

No implementation begins until Claude reviews this plan and the user agrees.

1. Agree on two static walkthroughs: quiet patient → one question → appointment;
   GP opens the same record → understands change/context/gaps → inspects provenance.
2. Define the smallest read-only chart/evidence contract using saved outputs. Agree
   what is unavailable. Avoid extending accepted domain algorithms.
3. Build the demo shell/toggle, minimal patient hierarchy and clinician read workspace.
   Reuse current safe writes/settings. Keep approval/sharing explicitly unimplemented.
4. Run A–F, policy/reload/offline/browser checks and human comprehension review.
   Additional synthetic data, detectors, real wearable APIs and production auth remain
   separate; no CodeBuddy run without the user's instruction.

Engineering acceptance: unchanged accepted domain gates; same-patient toggle performs
no writes and preserves active safety; charts reproduce stored values/gaps/versions;
context and held evidence remain inspectable; no hidden truth, scores or unapproved
sharing; admin remains separately protected; keyboard/44px targets/non-color labels;
320/390 portrait and 1280 laptop usable, clinician phone fallback and short-screen
safety verified. Preserve all current containment/idempotency tests.

Human acceptance, **not yet proven**: the user can understand the quiet screen without
explanation; a small external review (proposed five non-team viewers) can identify
whether action is needed and what AURA does; a clinician-like reviewer can explain
the change/context/coverage and locate its source without coaching. Judge walkthrough
should make A–F intelligible without opening engineering tables. Mechanical test
success alone does not establish patient usability or clinical efficacy.

## 8. Questions for Claude

1. Does this audience split finally make the patient benefit apparent, or is even
   this home too much? Which single patient journey should the initial demo emphasize?
2. Is the GP overview + four aligned signals + context/check-in/routine timeline the
   smallest useful analytical workspace? What can be secondary without losing meaning?
3. Agree to an initially **read-only synthetic clinician workspace**, keeping persisted
   patient approval/sharing as an explicitly separate workflow? If approval preview
   is essential now, identify the exact new scope before coding.
4. Are the reuse/gap boundaries accurate, particularly historical rolling series,
   categorical self-report, explanation association and safety provenance?
5. Which patient wording or analytical display could still imply diagnosis, constant
   monitoring, verified adherence, automatic context clearing or authorization?

Open limitations remain: clinical parameter/content/resource review, context
credibility/association governance, post-gap trust approval, real safety detectors,
production identity/access and deployment readiness. They are not resolved by a
better dashboard or the demo role switch.
