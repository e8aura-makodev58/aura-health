# Submission draft (Claude, 2026-10-12)

**Superseded for submission preparation on 2026-10-13.** Canonical current form
copy, required uploads and agent instructions are in
[`docs/submission/README.md`](submission/README.md). This file is historical
background; do not copy its outdated optional-field or performance wording.

Draft text for the hackathon form. Reliability numbers come from `docs/evidence/deepseek-v9-reliability.json`. Nothing here claims clinical validity, diagnosis, prediction or treatment.
Requirements are in `docs/milestones/M8_SUBMISSION.md`.

## Title
aura-health

## Blurb (hard limit: under 10 words; pick one)
1. Your usual pattern, remembered. Changes, explained plainly. (8 words)
2. A calm health companion that notices what changed. (8 words)
3. Wearable context that tells doctors what changed. (7 words)

## Project description

### 1. Overview
AURA is a longitudinal, wearable-first context layer. It follows a person's own sleep,
activity, heart rate and check-ins against their personal usual, and an AI agent turns
months of data into a short, sourced, plain-language summary. The proof-of-concept scenario
is adults on stable antidepressant maintenance treatment, and the design is meant to extend to
other conditions and to people managing several. Two users: the **patient** sees a warm,
two-sentence recap and can open their full data whenever they want; the **clinician** sees
what changed, when, and the evidence, without dashboard-digging. A built-in synthetic
patient simulator lets a viewer make a flu, a trip or a stressful week happen and watch the
summary react.

### 2. Real-world insight
Between appointments, clinicians see almost nothing of a stable patient. Patients forget,
normalise slow change, or over-monitor themselves, and wearable dashboards show raw numbers
without meaning. Most mental-health apps need daily effort from people who may have the least
energy for it, and typical retention is very low. AURA asks for almost nothing: it
runs on the wearable the person already has, stays quiet when nothing changed, and explains
change in everyday words. Patients with more than one condition get a single joined-up
picture instead of one app per condition.

### 3. Solution design
- **Business architecture:** patient and clinician views of the same record. Silence is the
  default; the patient is never nagged and always has access to their own data.
- **Technical architecture:** deterministic engines decide what is true and what is safe
  (personal baseline and drift, trust, held-for-review, a safety state machine). The AI agent
  can only read, summarise and propose; it has no write tools and can never lower a safety
  concern. Safety resources are fixed, pinned interface content and are never generated.
  Trust-boundary diagram: `docs/ARCHITECTURE.md`.
- **How prompts drive the AI:** the agent calls read-only tools to fetch facts (each with an
  ID), then writes a bounded headline. Every sentence must cite those fact IDs; numbers,
  dates, signals and categories are checked against the cited facts; cause, diagnosis,
  prediction and treatment language is rejected; a second, independent verifier call checks
  that each claim is supported. If anything fails, a plain template built from the same
  facts is shown instead. Separate patient and clinician prompts set the voice: warm and
  plain for patients, factual and dated for clinicians, with sample remarks as style
  references only.
- **Patient simulator (demo only):** an AI "life director" plans events such as a three-day
  flu; a seeded generator produces the numbers, so the model never invents data. Wearable
  channels are realistic: continuous ones daily or nightly, blood pressure and thermometer
  readings only intermittently.

### 4. Quantified results (synthetic data only; engineering evidence, not clinical validation)
- Automated tests: **290 passing** (Python suite, 2026-10-12), plus 50+ browser checks across
  phone and laptop sizes.
- Reliability of the AI headline on the live model (DeepSeek, 20 runs per group): clinician
  **19 of 20**, patient **19 of 20** validated; the other two fell back to the template.
  No provider failures after the fix. (Case B; the flu groups were not measured.)
- Speed: summary text appears in about 0.3–0.5 s; the AI headline swaps in at about
  4.5 s (p95, HTTP timings, not visual paint).
- Seven simulated life events and six synthetic cases pass end to end on phone and laptop.

## Safety, limits and future work
Synthetic data only. Not a medical device, diagnosis, treatment advice or emergency service.
Thresholds are engineering defaults for a sponsor to set; no clinical validation is claimed;
authentication and sharing are not implemented. Future work: sponsor-editable clinical
configuration, other conditions (for example hypertension and diabetes alongside mental
health), real wearable import, patient-approved sharing with clinicians.

## Demo video outline (5–8 min)
1. (0:00) Problem in one sentence; show the clinician view opening on an AI summary.
2. (0:30) Patient view: the warm recap, "See what changed", the appointment note.
3. (1:15) Make it happen: "Simulate: flu 3 days" — the summary changes, with sources.
4. (2:15) Ask the record a question; show sources and the plain "Why" panel.
5. (3:00) Safety: pinned panel, AI cannot lower concern, held text never reaches the agent.
6. (3:45) How it is built: engines decide, the agent explains; trust-boundary diagram.
7. (4:45) Reflection: building with Codex, Claude and WorkBuddy; what worked, tips.
Before recording: reset the demo session, since it expires after an hour idle.

## Assets still to make
Cover image (16:9, about 380 x 216 px); WorkBuddy chat evidence (at least 3 screenshots or a
recording, genuine and contemporaneous); final project link (https://aura-health.makodev58.com).
