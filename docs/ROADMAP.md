# AURA Health — Project Roadmap

Status date: 2026-10-03.
Hackathon submission deadline: 2026-10-16.

This roadmap is the canonical implementation sequence for AURA Health. AURA is a wearable-first, patient-controlled longitudinal companion for working adults on stable clinician-managed antidepressant maintenance treatment.

The product is deliberately bounded. AURA does not diagnose depression, predict relapse, prescribe or modify treatment, provide psychotherapy, determine suicide risk, or operate as an emergency monitoring service.

Its core product principle is:

> Demonstrate clinical discipline without claiming clinical authority.

Its core AI/policy principle is:

> Signals propose. Rules dispose. The LLM phrases.

---

## System layers

AURA divides computation into three roles:

1. **Deterministic engines:** `aura_safety`, `aura_longitudinal`, and application orchestration/governance determine state, permitted actions, and whether communication is allowed.
2. **Product AI:** the M5 bounded language-model interface phrases approved interactions and explains already-determined observations using authorized wording choices. The default provider is disabled until explicitly configured. It never owns safety state, baseline state, medication decisions, or clinical conclusions.
3. **Simulation Data Agent:** a future development/evaluation tool may generate synthetic scenarios and adversarial cases. Hidden scenario truth must never enter production patient-facing decisions.

## Milestone status

| Milestone | Purpose | Status | Target |
|---|---|---|---|
| M1 | Deterministic safety core | COMPLETE | accepted |
| M2 | Safety properties + simulator | COMPLETE | accepted |
| M3 | Longitudinal context engine | COMPLETE | accepted |
| M4 | Application backend/orchestration | COMPLETE | accepted |
| M4.5 | Project canonicalization | COMPLETE | 2026-09-24 |
| M5 | AI communication layer | COMPLETE / REVIEWED | 2026-10-02 (original target 2026-09-30) |
| M6 | Patient application | IMPLEMENTED / REVIEW PENDING | 2026-10-03 (target 2026-10-07) |
| M7 | Demo + integration hardening | ACTIVE / local gates implemented; public link pending | by 2026-10-12 |
| M8 | Submission + final freeze | PLANNED | 2026-10-13 to 2026-10-15 |

Submission is due 2026-10-16; the goal is to be submission-ready one day early.

## M1 — Deterministic Safety Core

Create a deterministic safety controller before detectors, LLMs, UI, or wearable integration. Delivered safety state/events, validation, an explicit transition dispatch table, sequence/CAS downgrade protection, external policy configuration, and audit structure. The accepted M1 review also established CLOSED + degraded validity, immutable CLOSED episodes, and externally configured high-tier de-escalation defaults. Primary gate: P1–P3. See [M1 safety core](milestones/M1_SAFETY_CORE.md).

## M2 — Safety Simulation and Structural Properties

Complete P4–P18, deterministic simulation/replay, resource fallback and offline containment interfaces, and late-result handling. The M1 review corrections remain authoritative; they were not first decided in M2. See [M2 safety simulation](milestones/M2_SAFETY_SIMULATION.md).

## M3 — Longitudinal Context Engine

Implement AURA's differentiating descriptive question:

> What changed relative to this person, and is it worth interrupting them about?

Delivered anchored and rolling baselines, orthogonal sensing/trust state, drift/context/held-for-review logic, burden-aware communication, deterministic Cases A–E, and fixed-threshold/rolling-only comparators. Primary gate: L1–L14. See [M3 longitudinal engine](milestones/M3_LONGITUDINAL_ENGINE.md).

## M4 — Application Backend

Connect accepted domains without moving policy into API controllers. Delivered FastAPI, SQLite development persistence behind repository interfaces, idempotent and atomic event ingestion, patient timeline/status, deterministic review snapshot, safety-first integration, and Cases A–F through the application path. Primary gate: A1–A20. See [M4 application backend](milestones/M4_APPLICATION_BACKEND.md).

## M4.5 — Project Canonicalization

Remove conversational dependency from the development plan by delivering this roadmap, canonical decisions, M1–M8 specifications, an initial demo script, and an updated root `HANDOVER.md`. **No runtime implementation occurs in M4.5.**

## M5 — AI Communication Layer

Original target: 2026-09-30; implementation ready for review on 2026-10-02. Introduce generative AI only after deterministic product policy exists. Keep scope small: bounded communication modes, structured request/response contracts, deterministic claim validation and fallbacks, safety-mode containment, prohibited-claim tests, and version logging. CodeBuddy timing/evidence is now owned by the user's later SOW/rebuild workflow (2026-10-02 decision).

The LLM may phrase an approved micro-check-in or clarification, explain an already-computed descriptive change, and optionally word structured review data where policy permits. It may not assign/lower T1–T4, move an anchor, declare relapse, diagnose, determine suicide risk, change medication, give taper instructions, independently contact a clinician, generate T4 emergency policy, or operate when fail-closed/offline policy forbids it. See [M5 AI communication](milestones/M5_AI_COMMUNICATION_LAYER.md).

## M6 — Patient Application

Target: complete by 2026-10-07. M6 may begin alongside late M5 work once contracts stabilize because most views consume existing endpoints. Build a calm patient-facing application embodying **quiet when stable**, **context before conclusions**, and **patient-initiated help is always available**. Core experiences include home, Good/Okay/Rough check-in, medication routine, why-AURA-asked provenance, longitudinal observations, held-for-review, wearable-unavailable state, review preparation, bounded safety interaction, and patient control. Avoid a psychiatric risk dashboard. See [M6 patient application](milestones/M6_PATIENT_APPLICATION.md).

Implemented for review: no-build-step responsive UI, explicit synthetic A–F checkpoints,
server-provided provenance, local-only wording, memory-only idempotent offline retry,
and UI1–UI15 API/browser gates. See [M6 review](../MILESTONE6_REVIEW.md). No accepted
safety/longitudinal algorithm changed. Live-model consent is a prerequisite before
enabling a patient-facing external provider.

## M7 — Demo and Integration

Target: complete by 2026-10-12. Make the system coherent under demo conditions: end-to-end frontend/backend integration; Simulation Data Agent; visible Cases A–F and adversarial scenarios; explicit ground-truth isolation test; trust-boundary diagram; stable reset/replay dataset; failure-mode checks; refined script. CodeBuddy timing follows the user-controlled SOW/rebuild workflow. M7 also delivers the **live hosted demo** (required; user decision 2026-09-24): synthetic data, deterministic reset, public URL. Only after the core demo is stable may a real wearable connector or production-grade infrastructure be considered stretch work. Garmin and production cloud infrastructure are not required for success. See [M7 demo and integration](milestones/M7_DEMO_AND_INTEGRATION.md).

## M8 — Submission

Target: 2026-10-13 through 2026-10-15. Freeze, document, rehearse, and submit: final README, architecture diagram, walkthrough/recording, cleanup, submission text, CodeBuddy/WorkBuddy proof, claims/limitations review, reproducible instructions, final tests, and final commit/tag. No major new feature begins in M8. Submission should be ready by 2026-10-15. See [M8 submission](milestones/M8_SUBMISSION.md).

## Standing implementation priorities

When schedule pressure appears, preserve in order: (1) safety boundaries, (2) deterministic longitudinal behavior, (3) coherent patient experience, (4) reproducible demo, (5) submission completeness, then (6) optional integrations. Do not sacrifice the first four to add wearable brands, production cloud services, or extra AI features. The simple hosted demo is part of (4), not (6).

## After the hackathon

- **Singapore's four official languages for patients** (English, 中文, Bahasa Melayu, தமிழ்). The demo
  shows a header Language menu with English active and the other three marked as coming; design in
  [architecture document §15.1](submission/ARCHITECTURE_DOCUMENT.md): per-language safety validation first,
  reviewed interface translations, AI text checked in English then translated with a back-translation
  check, clinician side in English.

## Known non-blocking open issues

- Governed exit from `REESTABLISHING` is undefined.
- Context credibility/association and clinical thresholds require review.
- Safety resource/content requires review.
- Reviewer authorization and production authentication are absent.
- Development replay cost grows with event history.
- Routine T0/null safety references should be filtered from the clinician snapshot before sharing.

Resolve these only where needed for the hackathon demo or document them as limitations; they do not justify uncontrolled scope expansion.
