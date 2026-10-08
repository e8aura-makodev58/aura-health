# aura-health: what we are trying to achieve (current statement)

2026-10-08. Written by Claude from the repo, `HANDOVER.md`, `DECISIONS.md` §36–41 and
a look at the live demo. This is the current product statement; the framework
(`aura_health_framework_v1.0.md`) remains the detailed concept spec and the safety policy
(`aura_deterministic_safety_policy_state_machine_v1.2.md`) remains authoritative for
safety behaviour. Where this file and an older doc disagree, this file is newer.

## 1. One paragraph

AURA is a **longitudinal, wearable-first context layer for adults on stable antidepressant
maintenance treatment**. Wearable signals, check-ins, medication routine and life context are
tracked against each person's *own* reference. Deterministic engines decide what is true
and what is safe. An **AI agent** reads that record and turns months of data into a short,
sourced, human-readable assessment, answers questions about it, and helps prepare the
conversation with a clinician. The patient sees little by default; the clinician sees
the analysis. A demo-only **patient simulator** lets a viewer make a synthetic patient's
life happen (flu, travel, stress) and watch the whole system respond.

## 2. Who it is for and the problem

- **Problem.** Between appointments, GPs and polyclinics see almost nothing of how a stable
  patient is doing; patients forget, normalise slow change, or over-monitor themselves.
  Dashboards from wearables show raw numbers, not meaning, and add burden.
- **Clinician (primary user of the analysis).** Needs to understand, in a few minutes,
  what changed, when, what the patient said about it, and how complete the evidence is.
- **Patient.** Should think about their mental health *less* when things are going well, be
  able to look at their own data whenever they want (entitled to it), mention anything at
  any time, and get a short note to bring to the appointment.
- **Sponsor.** The problem-statement sponsor owns clinical and regulatory judgment.
  We are a technical proposal: clinical choices are exposed as sponsor-editable configuration
  (DECISIONS §41). No clinical validation is claimed.

## 3. How it works: who decides, who explains

```text
wearable / manual input ─▶ safety gate ─▶ longitudinal engines ─▶ stored decisions
(synthetic or typed)       (deterministic     (baseline, drift,       and evidence
                            + raise-only AI)   context, trust)               │
                                                                             ▼
                                   aura-agent (read-only tools, claim verification)
                                   brief · record Q&A · assessment · visit pack
                                                                             │
                                 clinician workspace  ◀──────────────────────┴──▶ patient view
```

| Layer | Role | Status |
|---|---|---|
| Safety state machine | Decides tiers/resources; the AI may raise concern, never lower it | built; AI detector approved, not built |
| Longitudinal engines | Personal baseline, drift, trust, anchors, held-for-review | built; signal registry added |
| aura-agent | Explains, investigates, drafts; no write tools | built (v1); readability rework approved |
| Patient simulator | Generates synthetic telemetry/feedback for demos; not product | planned, approved |
| Disclaimer page | One place for all demo/limits wording | planned, approved |

Principle: **engines decide what is true and safe; the agent decides what is worth saying,
to whom, and finds the evidence for it.**

## 4. Journeys (ranked)

1. **Clinician reviews between appointments** (the centre of the product): opens one
   patient, reads an assessment ("sleep timing drifted later from 23 Feb; activity fell;
   check-ins turned Rough this week; no context recorded"), checks the charts and sources,
   asks follow-up questions in plain language.
2. **Ordinary day for the patient:** nothing required; optionally look at "my full data" or
   a month-at-a-glance recap.
3. **AURA asks one question** when there is a reason and it is approved; the answer becomes
   context linked to the affected signals.
4. **Patient raises something** (structured taps now; free text behind the safety gate).
5. **Before the appointment:** the patient reviews and removes items from a short visit
   note. It stays "Not sent" until a persisted approval flow exists.

## 5. Principles and boundaries

- Personal reference over population norms; slow change must not become the new normal.
- Missing data is missing, not bad. No scores, risk labels or streaks.
- Silence is not hiding: everything not surfaced stays inspectable by the patient.
- Safety resources are pinned UI, never generated. No LLM in the highest-urgency, degraded
  or offline safety states. Held text never reaches the agent.
- The agent cannot write, diagnose, predict, advise treatment, or clear a signal.
- Telemetry shown is synthetic; manual input is always allowed.
- Clinical thresholds, signals, resources and wording are configuration for the sponsor.

## 6. State of the build (as of this file)

Built and live at https://aura-health.makodev58.com (DeepSeek `deepseek-flash`, synthetic
only): safety, longitudinal and application engines; six synthetic cases A–F; patient and
clinician views with a toggle; four aligned evidence charts; read-only agent with five
skills; protected provider settings; Cloudflare HTTPS hosting. In progress (Codex): signal
registry (committed), readable-assessment rework, Disclaimer page, model line in settings,
structured input and import, layered safety gate, simulator.

## 7. Honest assessment: why it does not impress yet

Based on the live clinician and patient pages (screenshots, 1280 px). Not seen: the agent
output (it needs a click and a model call), and the phone layout.

1. **The AI is the product but not visible.** The clinician page opens with a rule-based
   "What changed" list, and the agent sits in a collapsed card with a "Draft a brief"
   button. Nothing intelligent happens on arrival. The strongest idea is hidden.
2. **The demo is a replay, not a living system.** Case B is a fixed snapshot. The viewer
   cannot cause anything, so there is no cause and effect to be impressed by. The
   simulator and live input fix this more than any visual change.
3. **No narrative synthesis.** Four equal charts and a list of lines; the story (later
   sleep + falling activity + a week of Rough check-ins, same weeks) is never stated or
   drawn across the charts. A GP has to assemble it.
4. **Engineering vocabulary and fine print everywhere.** "Stored rolling-window data
   availability: 100% · 14 samples. Not chart-period coverage or a health score.", "Policy
   records, not a clinical risk assessment", "anchored reference", "Source-local sleep
   clock". Fifteen collapsed "+" sections. It reads like an audit tool.
5. **The patient screen is nearly empty.** A circle, "No question from AURA right now",
   and four links. It is calm, but it shows no benefit and no intelligence.
6. **The product's virtue is absence.** Quiet, restraint and safety are real strengths but
   are hard to see. A demo must show visible value first, then the restraint.
7. **Built engine-first.** The UI mirrors internal concepts (anchor, rolling, held, trust)
   instead of a clinician's question: "what changed and does it matter?"
8. **No before/after.** Nothing shows what a GP sees *without* AURA versus *with* it.

## 8. What would change the impression (proposed, in order)

1. Open the clinician page with an **AI assessment already written** (generated on load or
   cached per checkpoint): a headline, three dated findings with sources, and "worth
   asking". Rules-only text becomes the fallback.
2. **Annotate the charts** with the assessment (shaded drift period, context markers,
   check-in strip aligned under the charts) so the story is visible, not listed.
3. **Make the demo live:** the patient simulator ("flu for 3 days"), manual and imported
   data, then re-run the assessment and watch it change.
4. **An "Ask this record" box** always visible, answering with sourced text.
5. **Cut the fine print** (Disclaimer page) and rename engine terms in plain language.
6. **Give the patient a visible benefit:** a short month recap in plain words and the
   one-tap visit note, shown by default.
7. **A 3-minute story** in the demo guide: patient has a quiet month, then life events;
   AURA notices, asks one question, the clinician gets a brief, the visit note is ready.
8. **A before/after panel** for judges: raw wearable export versus AURA's assessment.

## 9. How we will know it is working (informal, not clinical)

- A first-time viewer can say in one sentence what AURA does after 30 seconds.
- A clinician-like reviewer can state what changed, when, and the evidence, within 2
  minutes and without opening an accordion.
- The viewer can trigger an event (flu, travel) and see the assessment change within 30
  seconds.
- Every agent claim has a source; no diagnosis, prediction or treatment advice appears.
- Safety resources and the offline/degraded/held paths behave exactly as in the policy
  and tests (hold, never generate).
