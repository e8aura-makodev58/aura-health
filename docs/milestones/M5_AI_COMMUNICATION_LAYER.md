# M5 — AI Communication Layer

Status: PLANNED. Target: complete by 2026-09-30.

## Goal

Add a deliberately small bounded language-model component that makes deterministic AURA decisions understandable without giving generation ownership of safety, clinical, baseline, or communication policy. This is not an open-ended therapy chatbot.

> Signals propose. Rules dispose. The LLM phrases.

## Initial generation modes

- **NORMAL_SUPPORT:** patient-initiated T0-allowed bounded support/information.
- **MICRO_CHECKIN:** phrase an already-approved low-burden question.
- **TARGETED_CLARIFICATION:** phrase an approved question about an observed change/uncertainty.
- **OBSERVATION_EXPLANATION:** explain an already-computed descriptive observation without diagnosis.
- **REVIEW_SUMMARY_WORDING:** optional concise wording from deterministic structured snapshot; snapshot remains authoritative.

No LLM in T4, degraded/fail-closed, client-offline fail-closed, or other prohibited modes. T3 generation, if attempted, requires deterministic validation and fixed fallback; a static T3 response is acceptable for M5.

## Contract and validation

Structured request: mode, allowed intent, selected observation facts, approved question goal, relevant patient context, prohibited claims, safety constraints, length limit, and policy/prompt version. Do not send unnecessary history. Structured output: message, acknowledged fact references, question intent, optional CTA type, model/prompt version—never policy state.

Deterministically reject diagnosis, relapse or suicide-risk determination, medication change/taper advice, claims that passive signals prove mental deterioration, continuous-monitoring claims, contradictions of approved intent, unsupported patient facts, internal tier/risk-score language, and unapproved emergency instructions. Use approved fixed fallback on invalid output, model failure, or timeout; do not ask a model indefinitely to repair itself.

Audit generation mode, prompt/model versions, fact references where practical, validation result, fallback use, latency/error metadata, without unnecessary sensitive free text.

Sequence: patient input → safety gate → application/longitudinal decision → approved intent → permitted LLM phrasing → deterministic validation → output/fallback. Never route unrestricted patient input to a conversational model before safety.

## Suggested tests (future G-series)

- **G1–G2:** generation service cannot mutate safety or anchor/baseline state.
- **G3–G4:** T4, degraded, and offline-prohibited modes use no generated content.
- **G5:** each message is tied to approved mode.
- **G6–G9:** reject diagnostic, relapse, medication-change/taper, and unsupported-fact claims.
- **G10–G11:** invalid generation and optional-generation timeout use deterministic fallback.
- **G12:** safety precedence survives LLM unavailability.
- **G13–G14:** versions are auditable and identical fallback conditions produce identical output.
- **G15:** no internal tier appears as a patient-facing diagnostic score.
- **G16:** direct generation calls cannot bypass free-text safety gate.

Evaluation fixtures should cover stable days, transient physiology, slow change, context, medication concerns, ambiguous figurative and clearly safety-relevant language, hallucination, and prompt injection. Boundary enforcement is the goal, not clinical model validation.

## CodeBuddy/WorkBuddy and stop condition

Perform at least one meaningful M5 task with CodeBuddy and/or WorkBuddy as required by the hackathon. Capture contemporaneous evidence, task/tool/date/path. M5 stops when bounded modes, structured service, deterministic validator/fallback, prohibited-claim tests, safety containment, prompt/model audit, unchanged safety policy, and genuine evidence are in place.
