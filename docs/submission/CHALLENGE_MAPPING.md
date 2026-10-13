# Challenge fit — Healthcare track, Challenge Statement 2

Status 2026-10-13, Claude. Source: the hackathon brief (Healthcare Track, contributed by
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
| Tracks daily medication | Medication-routine records: Acknowledged / Missed / Not sure; shown to patient and clinician; "This records your routine. It does not change your treatment." | Built |
| Two-minute mood and sleep check each evening | One-tap check-in (Good / Okay / Rough) plus sleep and activity from the wearable, so the patient does less than two minutes of reporting | Built (lower burden by design) |
| Preventive prompts when a downward trend appears (walk, support contact, therapy session) | AURA notices recorded changes and may ask one gentle approved question. It does not prescribe activities in the prototype | Deliberately different (see below); sponsor-approved gentle prompts on the roadmap |
| Nudges quarterly medication reviews | Not built | Roadmap |
| Flags early warning signs of relapse the user can choose to share with their clinician | Shows descriptive changes against the person's own usual ("sleep time later than your usual since late February") that the patient can bring to an appointment. Nothing is sent automatically ("Not sent") | Built as description; relapse prediction deliberately excluded |

## "What the solution should solve" — features

| Feature (brief) | AURA Health | Status |
|---|---|---|
| Medication understanding | Not built. Intended: plain-language explanation from approved sources, with "please check with your pharmacist" when unsure | Roadmap |
| Medication management | Routine records and their history | Partial (no reminders yet) |
| Adherence support | Missed and acknowledged routine entries are visible to patient and clinician and available to the record assistant | Partial (barriers not yet explored) |
| Health tracking | Core of the product: wearable sleep timing/duration, activity, resting heart rate, HRV, breathing rate, skin temperature; a governed personal baseline plus a recent rolling reference; missing data stays missing | Built |
| Preventive health | Not built | Roadmap |
| Healthcare preparation | "Prepare for my appointment" (patient chooses items, marked Not sent), approved "worth asking" questions, clinician brief, and the record assistant that investigates questions with cited answers | Built |

## "The solution should be" — qualities

| Quality (brief) | How AURA Health shows it |
|---|---|
| Empowering | The patient decides what to bring to an appointment; explanations they add are kept with the change |
| Personalised | Every comparison is against the person's own baseline, not population norms; context only affects the signals it relates to |
| Longitudinal | Two references (governed personal baseline and recent rolling pattern) separate a short illness from a slow, persistent shift |
| Safe | A deterministic safety state machine takes priority over all ordinary wording; safety resources are pinned and never AI-written |
| Practical | Quiet by default; one-tap check-ins; a warm, short recap instead of charts on the patient home |
| Strictly bounded — never crosses into medication advice | Automatic checks reject medication instructions, dosing, diagnosis, relapse or risk language before any AI text is shown |
| Honest about uncertainty | Missing data is labelled as missing; an AI answer that fails its checks is replaced by labelled related facts with the reason shown |

## Why AURA does not predict relapse or give advice

The scenario mentions flagging "early warning signs of relapse" and suggesting activities. AURA
deliberately stops at **describing what changed and when**, because a prototype that predicts
relapse or recommends actions to someone on antidepressant treatment would make clinical claims
that need clinical validation and sponsor governance. Instead, AURA makes the change visible,
lets the patient add context, and helps both sides arrive at the appointment with the same
picture. Clinical prompts can be added later under the sponsor's review.

## Required "Solution should include"

| Item | Where |
|---|---|
| Demo walkthrough | Live site https://aura-health.makodev58.com and the demo video |
| Architecture diagram, trust boundaries, key trade-offs | Deck `assets/aura-health-deck.pptx`; source `ARCHITECTURE_DOCUMENT.md` |
| Source code | https://github.com/e8aura-makodev58/aura-health |
