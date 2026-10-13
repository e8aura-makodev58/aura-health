# Challenge fit — Healthcare track, Challenge Statement 2

Status 2026-10-13, companion reconciliation by Codex against integrated `f37af0c`. Source: the hackathon brief (Healthcare Track, contributed by
NTU Lee Kong Chian School of Medicine). The brief asks each team to choose ONE case study
and to state it at the beginning of the presentation.

**Chosen case study: Challenge Statement 2 — "AI Healthier Every Day: Intelligent Support
for Long-Term Self-Care", Scenario 1 — "Mental Health Maintenance for Working Adults on
Antidepressants".**

Problem statement (brief): *How might we build an AI-powered health companion that helps
people understand and manage their medications, stay on track with their care, and take
greater ownership of their long-term health?*

Status key: **Built** = in the live demo · **Partial** = part of it is built · **Roadmap** =
intended final-product work, not in the demo · **Deliberately different** = a safety design
choice, explained.

## Scenario 1, element by element

| Scenario element (brief) | AURA Health | Status |
|---|---|---|
| Patient on a stable SSRI dose | Intended use: adults on stable, clinician-managed antidepressant maintenance | Built (scope) |
| Tracks daily medication | Today's dose: Taken / Not yet / Skipped. Taken and Skipped record patient reports; Not yet records nothing. Optional missed-dose reasons and seven-day counts appear in review preparation | Built (once-daily synthetic regimen) |
| Two-minute mood and sleep check each evening | One-tap check-in (Good / Okay / Rough) plus sleep and activity from the wearable, so the patient does less than two minutes of reporting | Built (lower burden by design) |
| Preventive prompts when a downward trend appears (walk, support contact, therapy session) | "A small idea for today" offers curated, optional choices linked to recorded changes; includes movement, wind-down and support-contact options. No generated treatment instructions | Built (development content awaiting sponsor review) |
| Nudges quarterly medication reviews | "Coming up" displays the stored next medication-review date and estimated refill date; synthetic regimen has a three-month review cadence | Partial (displayed dates, not push notifications or booking) |
| Flags early warning signs of relapse the user can choose to share with their clinician | Shows descriptive changes against the person's own usual ("sleep time later than your usual since late February") that the patient can bring to an appointment. Nothing is sent automatically ("Not sent") | Built as description; relapse prediction deliberately excluded |

## "What the solution should solve" — features

| Feature (brief) | AURA Health | Status |
|---|---|---|
| Medication understanding | Curated purpose/how-to-take/missed-dose/side-effects/alcohol topics for Sertraline, Escitalopram and Fluoxetine; prescribed schedule is displayed, not inferred. Unknown medicine/topic abstains. Typed questions pass safety first; optional model classification selects a topic, never writes an answer | Built (development content needs pharmacist review) |
| Medication management | Today's dose, patient-reported history, seven-day taken/missed counts and estimated refill date | Partial (no push reminders, refill ordering or multi-dose regimen support) |
| Adherence support | Skipped dose can record Forgot / Side effects / Ran out / Felt better / Other, or no reason. Retained reasons create Not-shared clinician-review items; unknown/unrecorded days are not missed doses | Built for recording barriers; follow-up workflow remains future work |
| Health tracking | Core of the product: wearable sleep timing/duration, activity, resting heart rate, HRV, breathing rate, skin temperature; a governed personal baseline plus a recent rolling reference; missing data stays missing | Built |
| Preventive health | Stored medication-review/refill dates and optional curated lifestyle/support suggestions | Partial (no screening/vaccination scheduling or proactive notification service) |
| Healthcare preparation | "Prepare for my appointment" (patient chooses items, marked Not sent), approved "worth asking" questions, clinician brief, and the record assistant that investigates questions with cited answers | Built |

## "The solution should be" — qualities

| Quality (brief) | How AURA Health shows it |
|---|---|
| Empowering | The patient decides what to bring to an appointment; explanations they add are kept with the change |
| Personalised | Every comparison is against the person's own baseline, not population norms; context only affects the signals it relates to |
| Longitudinal | Two references (governed personal baseline and recent rolling pattern) separate a short illness from a slow, persistent shift |
| Safe | A deterministic safety state machine takes priority over all ordinary wording; safety resources are pinned and never AI-written |
| Practical | Quiet by default; one-tap check-ins; a warm, short recap instead of charts on the patient home |
| Strictly bounded — never crosses into medication advice | Record-agent checks reject treatment instructions. Medication answers are curated, with fixed redirects for treatment-change requests; the model can select only an approved topic ID |
| Honest about uncertainty | Missing data is labelled as missing; an AI answer that fails its checks is replaced by labelled related facts with the reason shown |

## Why AURA does not predict relapse or change treatment

The scenario mentions "early warning signs of relapse". AURA instead **describes what
changed and when** without predicting relapse. Optional curated everyday suggestions
are now built, but are not treatment recommendations or clinically validated prevention.
Medication content, suggestion wording and clinical parameters still need sponsor review.
The patient can add context and prepare information for a clinician; nothing is
automatically sent, prescribed or scheduled.

## Required "Solution should include"

| Item | Where |
|---|---|
| Demo walkthrough | Live site https://aura-health.makodev58.com and the demo video |
| Architecture diagram, trust boundaries, key trade-offs | Deck `assets/aura-health-deck.pptx`; source `ARCHITECTURE_DOCUMENT.md` |
| Source code | https://github.com/e8aura-makodev58/aura-health |
