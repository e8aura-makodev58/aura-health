# AURA Health — Canonical Decisions

Status date: 2026-09-23.

These are settled cross-cutting decisions. Reopen one only for a concrete contradiction, safety issue, implementation failure, or explicit new user decision.

## 1. Document precedence

Explicit current user decisions recorded here or in root `HANDOVER.md` supersede older plans. This file governs cross-cutting decisions. For safety, the accepted implementation and M1/M2 corrections govern, then `aura_deterministic_safety_policy_state_machine_v1.2.md`. The accepted corrections include CLOSED + degraded and immutable post-CLOSED handling. `aura_health_framework_v1.0.md` governs intended use. Milestone specs govern scope, but accepted code/tests/review packets win over reconstructions of completed work. `MILESTONE3_REVIEW.md` and `MILESTONE4_REVIEW.md` are acceptance evidence. Superseded documents are background only. Where ambiguity remains, do not invent clinical policy; request a decision.

## 2. Product identity

Official project name: **aura-health** (user decision, 2026-09-23); this is the submission title. "AURA Health" and "AURA" in prose and code refer to the same product. Care Plan Bridge is dropped and superseded.

## 3. Intended use

AURA is a research-informed prototype for adults aged 25–60 on stable clinician-managed antidepressant maintenance treatment. It organizes patient reports, medication routines, consented wearable data, and personal longitudinal patterns, helping prepare information for clinician discussion. It does not diagnose depression, predict relapse, prescribe or modify treatment, determine suicide risk, provide psychotherapy or emergency monitoring, or replace a clinician. Its value is longitudinal intelligence without unvalidated medical authority.

## 4. Initial MVP exclusions

The hackathon MVP does not center on treatment initiation, dose changes, switching, tapering, discontinuation, shift-worker baseline modeling, ages 18–24, autonomous clinician notification, emergency monitoring, or phone-behavior digital phenotyping. These are possible future research areas.

## 5. Wearable-first, not wearable-dependent

Wearables are contextual sensors, not truth about mental state. AURA remains meaningful without them. Missing data is never automatically deterioration, health, or zero.

## 6. Sensing and baseline trust are separate

Sensing is `OBSERVED` or `UNOBSERVED`; trust is `PROVISIONAL`, `TRUSTED`, or `REESTABLISHING`. The dimensions are orthogonal: having data is different from trusting a historical reference.

## 7. Anchored + rolling baseline

The anchored baseline is a governed historical reference; the rolling baseline is a recent adaptive reference. Compare current-vs-rolling and rolling-vs-anchor. Rolling-only references can absorb slow persistent drift.

## 8. Reference truth is governed

> The reference truth is governed; it is not automatically rewritten by the same stream it is evaluating.

Incoming observations, alert dismissal, benign explanation, and held-for-review never move the anchor. Explicit governed commands are required.

## 9. Explained, Held for Review

`EXPLAINED_HELD_FOR_REVIEW` retains anchor, drift, and explanation; suppresses repetitive interruption; remains inspectable and reviewable; and may reopen on new evidence. Context does not rewrite history.

## 10. Context is signal-scoped

Benign context attenuates only plausibly linked signals. Physical illness may explain heart-rate change, but cannot erase worsening check-ins, medication disruption, unrelated drift, or safety evidence. Risk context cannot explain deterioration away.

## 11. Observation and communication are separate

Observation asks what changed; communication asks whether interruption is useful. `STAY_QUIET` is a successful outcome.

## 12. Psychological burden is a product safety variable

No visible relapse probabilities, psychiatric risk percentages, streak guilt, gamified adherence, or alarm dashboard. Stable patients should have fewer interruptions.

## 13. Patient-initiated interaction remains available

AURA may initiate after meaningful change, but patients may initiate at any time. Patient-reported distress outranks absence of passive anomalies.

## 14. Safety policy is deterministic

The safety engine owns state, not an LLM. Detectors propose; rules decide. A model cannot lower stronger state itself.

> Signals propose. Rules dispose. The LLM phrases.

## 15. FAIL_CLOSED is an overlay

It is not T5. Degradation is orthogonal to live mode, episode status, and peak; CLOSED may be degraded.

## 16. CLOSED episodes are immutable

New safety evidence never rewrites a CLOSED episode. New T1–T4 evidence creates a linked new episode.

## 17. High-tier de-escalation is explicit and CAS-protected

Downgrades require a named transition, current sequence, and external configuration. Current T3/T4 target defaults are provisional engineering values awaiting clinical review.

## 18. Three computational roles remain separate

Deterministic engines own policy/state; Product AI only phrases permitted messages; the Simulation Data Agent operates only in development/evaluation. Never merge these roles.

## 19. Product AI boundary

The LLM cannot own T1–T4, lower safety state, move anchors, diagnose, declare relapse, determine suicide risk, change medication, create taper instructions, override communication policy, generate T4 emergency policy, or run where fail-closed/offline policy prohibits it. Safety-critical validation and fallback are deterministic.

## 20. Safety outranks ordinary communication

Safety policy overrides `STAY_QUIET`. Application code routes decisions but cannot assign safety tiers.

## 21. Free text is safety-gated first

Patient free text must pass the safety boundary before general conversational generation.

## 22. Clinician persona

The primary demo clinician is a time-limited Singapore primary-care GP/polyclinic-style reviewer; AURA prepares concise information and does not assume psychiatry is always first destination.

## 23. Clinician review is patient-controlled

A deterministic snapshot may be prepared, not automatically transmitted. Approval/sharing is separate future work.

## 24. Medication support is bounded

AURA may support routines, capture adherence context, discuss tolerability factually, and prepare prescriber questions. It does not change dose, recommend stopping, produce individualized taper schedules, or replace clinician medication advice.

## 25. Engineering thresholds are not clinical thresholds

Current windows, spreads, cooldowns, gaps, and comparator values are labelled engineering defaults. Synthetic tuning is not clinical validation.

## 26. Synthetic evidence is not clinical efficacy

Cases A–F and comparators validate engineering behavior, not sensitivity, specificity, treatment benefit, relapse prevention, clinical safety, or real-world effectiveness.

## 27. Simulation truth is evaluation-only

Scenario ID, onset, latent truth, useful-interruption windows, and expected outcomes never enter production decisions. M7 must explicitly test this boundary.

## 28. Simulation Data Agent role

The future agent may translate scenario ideas into structured specifications, vary populations, generate adversarial combinations, and find coverage gaps. A fixed-seed deterministic generator produces numeric data. The agent cannot manipulate product decisions.

## 29. Development persistence

SQLite is development/demo infrastructure. Repository boundaries permit later production storage migration; SQLite is not a production architecture claim.

## 30. No production authentication claim

The API lacks production authentication; caller-supplied reviewer identity is not sufficient deployed authorization.

## 31. Wearable/cloud integrations are stretch goals

Garmin, Apple Health, production cloud, and external health-system integrations are optional and must not displace the core demo.

## 32. CodeBuddy/WorkBuddy evidence is mandatory

The brief requires the project to be built on CodeBuddy and/or WorkBuddy, and requires **at least 3 screenshots or a screen recording of CodeBuddy/WorkBuddy chat logs** during development. Without proof, the project is not scored. Beginning M5, do genuine implementation in CodeBuddy and/or WorkBuddy and capture evidence as it happens. Store it under `docs/evidence/` with date, milestone, and task. Don't defer proof collection to M8; M5–M8 gates confirm evidence.

## 33. Demo story

Not “look at our mental-health chatbot,” but how AURA stays quiet, asks small questions, preserves historical truth, and hands safety to deterministic policy. Cases A–F demonstrate physical illness, slow drift, illness plus independent change, explained persistent change, wearable gap, and safety handoff.
