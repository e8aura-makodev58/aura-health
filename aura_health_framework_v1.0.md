# AURA Health — Canonical Concept Framework v1.0

**Status:** Canonical concept, safety, research, and governance framework  
**Track:** Healthcare — NTU Lee Kong Chian School of Medicine  
**Challenge:** Challenge Statement 2 — *AI Healthier Every Day: Intelligent Support for Long-Term Self-Care*  
**Primary scenario:** Working adults on stable antidepressant maintenance treatment, with SSRIs as the initial demo case  
**MVP population:** Adults aged 25–60, on an established stable antidepressant regimen, with regular daytime schedules  
**Primary clinician persona:** GP / polyclinic doctor managing stable antidepressant maintenance  
**Purpose:** Define the product idea, intended use, safety boundaries, evidence hierarchy, patient-interaction model, longitudinal reasoning model, and prototype/research posture before system specification and implementation.

---

## 1. Intended Use

> **AURA is a research-informed prototype intended to support adults aged 25–60 who are on stable clinician-managed antidepressant maintenance treatment by organizing patient-reported and consented wearable information, supporting medication routines, identifying changes from personal longitudinal patterns for further assessment, and helping patients prepare information for discussion with their healthcare professional. AURA does not diagnose depression, predict relapse, prescribe or modify treatment, provide psychotherapy, or provide emergency monitoring.**

This intended-use statement governs the product framing, feature claims, safety boundaries, demo narrative, and future regulatory analysis.

---

## 2. Product Thesis

AURA is a **wearable-first, patient-controlled, longitudinal antidepressant-maintenance companion**.

It is designed around two realities:

1. When patients feel well, many will not actively use a health app.
2. Depression itself can also reduce engagement.

AURA therefore must not treat disengagement as either automatically benign or automatically pathological.

The system should remain low-burden when the patient is stable, but capable of noticing meaningful change and responding conservatively.

> **AURA should make the patient think about their mental health less when things are going well, not more.**

---

## 3. What AURA Is — and Is Not

AURA is not:
- a therapy chatbot,
- a diagnostic system,
- a prescribing system,
- a replacement for a clinician,
- an emergency monitoring service,
- or a generic wellness dashboard.

AURA is:

> **A longitudinal context layer around an existing treatment plan.**

Its role is to:
- support medication routines,
- maintain longitudinal context,
- identify meaningful change,
- ask the smallest useful question,
- reduce unnecessary interaction and psychological burden,
- identify when professional review may be useful,
- help the patient prepare for clinical review,
- and enter a deterministic safety pathway when warning signs are detected.

Core statement:

> **AURA does not manage the antidepressant. It manages the context around the patient’s treatment.**

---

## 4. MVP Scope

### In scope
- Adults aged 25–60
- Stable antidepressant maintenance treatment
- Primary demo case: SSRI maintenance
- Regular daytime schedule
- Patient-reported wellbeing
- Medication adherence / routine support
- Wearable-derived longitudinal signals
- Low-burden check-ins
- Structured assessments
- Patient-initiated distress conversations
- Clinician preparation and summaries
- Deterministic safety escalation
- Simulated longitudinal demo data
- Evidence labeling for research-grade concepts

### Out of scope for the MVP
- Ages 18–24
- Shift workers
- Antidepressant initiation
- Dose changes
- Switching
- Tapering
- Medication discontinuation plans
- Diagnosis
- Psychotherapy
- Emergency psychiatric care
- Autonomous clinician notification
- Autonomous treatment modification
- Phone-use behavior as an active MVP input

These exclusions are MVP boundaries, not claims that AURA can never support these populations or scenarios.

---

## 5. Two Ways AURA Can Enter a Conversation

### A. AURA-initiated interaction
A passive or longitudinal pattern gives AURA a reason to check in.

Examples:
- sleep timing has drifted,
- activity has fallen,
- medication acknowledgement becomes irregular,
- the patient’s usual response pattern changes,
- multiple weak signals begin moving together.

### B. Patient-initiated interaction
The patient opens AURA because something feels wrong.

Examples:
- “I feel terrible today.”
- “I haven’t slept properly for three nights.”
- “I feel anxious and I don’t know why.”
- “I missed my medication.”
- “I think the medication is causing something.”
- “I feel fine now, so I’m thinking of stopping.”
- “I don’t think I can handle work tomorrow.”
- statements involving hopelessness, self-harm, or suicidal thinking.

Core principle:

> **The wearable tells AURA when it may be useful to ask. The patient can always tell AURA when help is needed.**

Patient-reported distress takes precedence over the absence of passive anomalies.

---

## 6. Wearable-First, But Not Wearable-Dependent

Wearables are integral to the AURA concept, but AURA must remain functional without them.

### Primary MVP wearable signals
- **Sleep timing and regularity**
- **Activity**
- **Resting heart rate**

### Secondary / research-grade wearable signals
- HRV
- respiratory rate
- SpO₂
- other device-specific metrics

AURA should not reproduce a Garmin, Apple Health, Fitbit, or similar dashboard.

Its value is in combining passive context with subjective wellbeing, medication routine, life context, treatment context, structured assessments, and longitudinal history.

Wearable measurements are contextual observations, not diagnoses.

---

## 7. Evidence Tiers

To avoid confusion with Singapore medical-device risk classes, AURA uses **E1 / E2 / E3** evidence tiers.

### E1 — Clinical / safety evidence
Examples:
- direct patient statements,
- structured assessment responses,
- validated suicide-risk follow-up,
- medication and treatment information.

Permitted use:
- deterministic safety policy,
- clinician preparation,
- treatment-context reasoning.

### E2 — Evidence-supported longitudinal signals
Examples:
- sleep timing and regularity,
- activity trends,
- selected wearable measures.

Permitted use:
- longitudinal change detection,
- contextual questioning,
- burden-aware engagement.

### E3 — Research-grade signals
Examples:
- phone-use behavior,
- some HRV-derived patterns,
- other exploratory digital-phenotyping features.

Permitted use in future research:
- personalization,
- anomaly detection,
- interaction timing,
- deciding when a validated assessment may be warranted.

E3 signals are not permitted to independently diagnose deterioration, establish emergency risk, change treatment guidance, or reduce a safety state established by stronger evidence.

Core rule:

> **No passive digital feature is allowed to carry a clinical interpretation unless that interpretation has an explicitly documented evidence basis.**

---

## 8. Research-Grade Features and Future Validation

AURA may demonstrate hypotheses that require prospective clinical validation, provided they are clearly labeled.

Suggested maturity labels:
- **Technically demonstrated**
- **Research-informed**
- **Requires clinical validation**
- **Requires regulatory review before deployment**

AURA should not claim that exploratory digital signals are validated biomarkers.

For the hackathon, the goal is to demonstrate **technical potential plus safe boundaries**, not clinical deployment readiness.

---

## 9. Consent Model

Consent should be layered rather than bundled.

### Layer 1 — Core care data
Information needed for AURA to function for the patient.

### Layer 2 — Optional sensor data
Wearable access and future optional behavioral data.

### Layer 3 — Research & improvement participation
Optional permission for appropriately protected longitudinal data to contribute to future AURA research and validation.

A patient should be able to say:

> “Use my wearable data to help me, but do not use it for research.”

AURA must still function.

Consent should be explicit, understandable, revocable, data-source specific where practical, and separate from optional research participation.

---

## 10. Sensing State and Baseline Trust State

These are two independent dimensions and must not be conflated.

### Sensing State
- **Observed** — recent source coverage is adequate.
- **Unobserved** — source data is unavailable.

### Baseline Trust State
- **Provisional** — enough data exists to begin modeling, but the reference is not yet trusted.
- **Trusted** — the baseline has been accepted under the current governance rules.
- **Re-establishing** — data has resumed after a long gap or major context change and the previous baseline may no longer apply.

A patient can therefore be observed + provisional, observed + trusted, observed + re-establishing, or unobserved while retaining the last known trust state.

---

## 11. Missingness Is Context, Not a Diagnosis

Core rule:

> **Missing data is never evidence of deterioration on its own. A meaningful change in a patient’s usual missingness pattern may be a weak contextual signal.**

### Benign missingness
- watch charging,
- device not worn,
- switch to a mechanical watch,
- permissions revoked,
- device replacement.

### Potentially meaningful change
- patient normally answers low-frequency check-ins but stops,
- wearable use gradually falls while other signals drift,
- medication acknowledgement disappears while subjective distress rises.

A missingness change may justify one gentle check-in. It must never independently establish relapse.

---

## 12. Anchored + Rolling Baselines

A rolling baseline alone can absorb gradual deterioration.

AURA therefore maintains:
- an **anchored baseline** representing a known or accepted stable period,
- a **rolling baseline** representing recent behavior.

AURA compares:
- current values vs. rolling baseline,
- rolling baseline vs. anchored baseline.

This supports both short-term anomaly detection and slow-drift detection.

---

## 13. Anchor Governance

The evidence stream must not casually rewrite its own reference.

Rules:
- The first anchor is **provisional**.
- Patient dismissal of an alert can **never move the anchor**.
- A benign explanation can annotate or suppress a drift but does not move the anchor.
- The anchor normally moves at a planned clinical review when the patient is considered stable.
- A future secondary pathway may permit anchor movement after long persistence plus stable structured assessments, but only under explicit policy.
- Re-established baselines after a long sensing gap remain provisional until supported by additional context.

Core principle:

> **The reference truth is governed; it is not automatically rewritten by the same stream it is evaluating.**

---

## 14. Explained, Held for Review

A benign long-term lifestyle change may create persistent drift without representing deterioration.

Examples:
- new job schedule,
- new baby,
- relocation,
- sustained benign exercise change.

If AURA receives a credible benign explanation and no stronger evidence suggests deterioration, the relevant drift enters:

> **Explained, Held for Review**

Behavior:
- repeat notifications for that same drift are suppressed,
- the anchor does not move,
- the explanation is annotated,
- the item is queued for the next GP review,
- the patient can inspect the held item.

The hold can end early if new evidence appears, such as a worse subjective check-in, a new signal, medication-routine disruption, a meaningful PHQ change, or a safety warning sign.

This allows the benign long-term-change demo case to remain low-burden without weakening anchor governance.

---

## 15. Personal Early-Warning Plan

AURA should support a patient-specific **personal early-warning plan**.

Examples:
- “When I begin to struggle, I sleep later.”
- “I stop exercising.”
- “I withdraw socially.”
- “I stop responding.”
- “My medication timing becomes irregular.”

The plan may be patient-authored, clinician-informed, or jointly reviewed.

It may define which signals matter most, which changes justify a check-in, what the patient wants monitored, and what they are comfortable sharing.

The plan guides attention; it does not become a diagnostic rule.

---

## 16. Structured Clinical Check-ins

Low-burden check-ins may use:

> Good / Okay / Rough

These are intended to reduce daily burden.

AURA may also use validated structured instruments at appropriate intervals, potentially including:
- **PHQ-2**
- **PHQ-9**

These instruments are not the sole decision engine.

They provide longitudinal structure, clinician-familiar context, and a defined route into safety follow-up when necessary.

Any self-harm-related response must route into the deterministic safety pathway.

---

## 17. Adaptive Engagement

AURA should avoid:

> notification → open app → questionnaire → repeat forever

Instead:

> **passive observation → detect uncertainty/change → ask the smallest useful question → update context → stay quiet again**

Suggested interaction levels:
1. Passive
2. Micro-interaction
3. Targeted clarification
4. Bounded deeper conversation
5. Safety escalation / human handoff

Core principle:

> **The more stable the patient appears, the less AURA should ask of them.**

---

## 18. Adaptive Measurement Requests

AURA may identify an information gap and request the smallest additional measurement that could materially reduce uncertainty.

Examples:

> “If convenient, wearing your watch tonight could give us more sleep context.”

> “If you have a thermometer available, a temperature reading may help explain the recent change.”

> “I don’t have recent wearable data. Would you like to reconnect it?”

Internal reasoning:
- What do I know?
- What am I uncertain about?
- Would one additional measurement materially reduce that uncertainty?
- Is the burden appropriate?

Measurement requests remain optional.

---

## 19. Safety Detection Architecture

This is a settled design principle:

> **Once AURA detects a credible safety warning sign, deterministic safety policy takes control.**

Detection must not rely on a single model.

### OR-combined detectors
Possible detectors include:
- deterministic structured triggers,
- validated assessment items,
- curated risk-phrase rules,
- dedicated classifiers,
- semantic model detection,
- contextual pattern detection.

### Asymmetric escalation
- Any detector may raise concern.
- No model may lower concern.
- Only policy-defined structured follow-up may resolve the appropriate safety tier.

### Universal safety gate
Every free-text input passes through the safety gate, including:
- normal chat,
- check-in replies,
- medication notes,
- side-effect notes,
- context annotations,
- edits to clinician summaries.

Core principle:

> **Signals propose. Rules dispose. The LLM phrases.**

Or:

> **Models may detect and explain. Policy decides and constrains.**

---

## 20. Safety Gate Failure Must Fail Closed

If the safety-classification or policy service times out, throws an error, returns an invalid state, or otherwise cannot complete reliably, the message must **not** pass into ordinary conversational handling.

The system should:
- hold the message,
- show appropriate safety resources and a clear system-status explanation,
- log the failure,
- require the safety pathway to recover before normal conversation resumes.

Core rule:

> **A safety-system failure cannot silently downgrade into ordinary chat.**

---

## 21. Graded Safety Tiers

AURA should not equate every warning sign with immediate emergency escalation.

The policy should use graded tiers such as:
1. **Needs clarification**
2. **Elevated concern**
3. **Urgent human support**
4. **Immediate safety response**

Structured follow-up should distinguish passive thoughts, active ideation, plan, intent, preparatory behavior, and immediate danger.

Validated tools such as C-SSRS-type screening may inform the eventual policy design.

Exact mappings require qualified clinical review before any real deployment.

---

## 22. Safety-Mode Dropout

This is distinct from ordinary unreachability.

If a patient enters a high safety tier and stops responding mid-flow:
- crisis / emergency resources remain pinned on screen,
- AURA does not enter a repeated “Are you still there?” loop,
- one bounded re-contact may be attempted,
- the unresolved safety state is logged,
- terminal status is **Safety follow-up incomplete / unable to establish contact**,
- AURA does not imply that a clinician or emergency service was notified unless that actually occurred.

High-tier closure must not rely on a single negative answer.

For Tier 3 or Tier 4 cases, policy should require a later re-check before the state is considered fully resolved.

---

## 23. Ordinary Unreachability

For non-safety interactions, AURA may:
- send an initial low-burden check-in,
- send one bounded follow-up if concern persists,
- prepare a clinician summary if previously authorized,
- record that contact could not be established.

Terminal state:

> **Unable to establish contact.**

AURA must not imply that a clinician was notified, imply that someone is continuously monitoring the patient, automatically re-anchor, or conclude deterioration solely from silence.

Onboarding should state:

> **AURA is not an emergency monitoring service and cannot guarantee intervention if you become unreachable.**

---

## 24. Distress Mode

AURA is not a therapy chatbot, but it is safety-aware.

When the patient initiates a distress conversation:

> patient message → universal safety gate → bounded conversation or deterministic safety pathway

### Ordinary distress
AURA may acknowledge, ask focused questions, use longitudinal context, and support reasonable next steps.

### Treatment-related concern
AURA may provide bounded factual information, identify whether clinician review is appropriate, help prepare a question, and avoid treatment changes.

### Potential acute safety issue
AURA enters deterministic safety mode.

Core principle:

> **AURA should neither therapize ordinary distress nor normalize genuine warning signs.**

---

## 25. Treatment Tolerability

AURA should explicitly handle concerns such as:
- emotional blunting,
- sexual side effects,
- weight change,
- sleep effects,
- perceived medication intolerance,
- concern about long-term use.

AURA should record what the patient reports, establish timing and context, provide bounded factual information from authoritative sources, help prepare questions for the prescriber or pharmacist, and avoid turning the concern into an instruction to stop or change medication.

---

## 26. Medication Discontinuation Scenario

For:

> “I feel fine now. I think I’m going to stop.”

AURA should:
- acknowledge the reasoning,
- explain factually that stopping or changing antidepressant treatment should be discussed with the prescriber,
- mention that abrupt changes can cause discontinuation symptoms and may affect relapse risk,
- avoid taper schedules,
- avoid advising whether the patient personally should continue or stop,
- offer to prepare questions for the clinician,
- include the concern in the clinician summary if approved.

---

## 27. Non-Judgmental Adherence Support

Medication adherence should not be gamified.

Avoid:
- streaks,
- broken-streak warnings,
- achievement pressure,
- guilt-oriented language.

A missed dose is context, not moral failure.

Example:

Instead of:

> “You broke your 37-day streak.”

Prefer:

> “Yesterday’s dose wasn’t recorded. Was there something that made your usual routine harder?”

The goal is to understand barriers, not grade the patient.

---

## 28. Benign Confounders vs. Risk-Context Factors

### Benign / contextual confounders
Examples:
- acute physical illness,
- travel,
- unusually strenuous exercise.

These may explain a particular physiological change.

### Risk-context factors
Examples:
- work stress,
- major life events,
- persistent sleep loss,
- problematic alcohol use.

These do not explain mental-health concern away. They may increase attention.

Core invariant:

> **A contextual explanation may attenuate the interpretation of a particular signal; it never clears the whole patient state.**

Example:
- influenza may explain an RHR rise,
- but does not erase worsening mood or withdrawal.

---

## 29. Psychological Burden Is a Safety Variable

AURA itself can create harm through health anxiety, hypervigilance, guilt, obsessive checking, reassurance-seeking, or constant self-surveillance.

AURA should avoid:
- visible relapse-probability scores,
- noisy daily scoring,
- high/medium/low psychiatric-risk labels without clinical purpose,
- excessive notifications,
- guilt-inducing adherence messages,
- over-exposure of noisy physiological metrics.

Core principle:

> **AURA must consider the psychological cost of communicating an observation, not only the value of detecting it.**

---

## 30. Observation Layer vs. Communication Layer

AURA separates two decisions.

### Observation layer
What changed?

### Communication layer
Should this be surfaced now, and how?

AURA may detect an anomaly and choose not to interrupt the patient.

However:
- anything not actively notified remains inspectable by the patient,
- normal-path clinician sharing still requires patient visibility and approval.

Silence should mean:

> **Not worth interrupting right now.**

Not:

> **Hidden from the patient.**

---

## 31. Periodic Presence Without Burden

Too much silence may cause AURA to be forgotten or uninstalled.

AURA may maintain a low-cost periodic presence through:
- quiet monthly recap,
- pre-review preparation,
- low-frequency structured check-in,
- optional stable-status summary.

The goal is familiarity, not engagement for engagement’s sake.

---

## 32. Clinician Handoff

MVP clinician persona:

> **GP / polyclinic doctor managing stable antidepressant maintenance.**

AURA should prepare a concise patient-approved summary containing:
- meaningful changes,
- dates / time windows,
- wearable trends,
- structured assessment trends,
- patient-reported context,
- adherence changes,
- tolerability concerns,
- explained/held-for-review items,
- actions already tried,
- questions the patient wants to discuss.

The summary should be readable in a short clinical review.

Nothing should be sent in the normal pathway unless the patient has seen it, approved it, and chosen to share it.

---

## 33. Simulated Data for the Demo

The hackathon demo should use simulated longitudinal data rather than depend on live wearable integration.

The simulator should generate data from hidden latent states such as:
- stable mood,
- gradual deterioration,
- physical illness,
- work stress,
- travel,
- medication disruption,
- wearable absence,
- benign lifestyle change,
- overlapping illness + genuine deterioration.

Generated outputs may include:
- sleep timing,
- sleep regularity,
- activity,
- resting HR,
- medication events,
- mood check-ins,
- structured assessments,
- missingness patterns.

---

## 34. Demo Cases

### Case A — False alarm avoided
Physical illness causes higher RHR, worse sleep, and lower activity. A naive app alarms. AURA asks for context and avoids an inappropriate mental-health conclusion.

### Case B — Slow drift caught
Gradual multi-week deterioration shifts sleep timing, activity, subjective check-ins, and engagement behavior. A rolling-only baseline normalizes the drift. AURA detects divergence from the anchored stable baseline.

### Case C — Hard positive
Physical illness overlaps with real deterioration. AURA must not let illness explain everything away.

### Case D — Hard negative
A benign long-term lifestyle change creates persistent drift. AURA moves the drift to **Explained, Held for Review**, suppresses repeat notifications, keeps the anchor unchanged, and queues the context for GP review.

---

## 35. Evaluation Design

Evaluation should vary:
- drift rate,
- drift magnitude,
- noise,
- missingness,
- contextual events.

Measure:
- detection latency,
- false alarms,
- missed deterioration,
- unnecessary notification burden,
- appropriate escalation.

Appropriate escalation should be defined in simulator ground truth **before** running the comparison.

A naive comparator may use:
- single thresholds,
- rolling-only baseline,
- no contextual disambiguation.

The purpose is to demonstrate why AURA’s architecture is needed, not merely that it produces attractive graphs.

---

## 36. Adversarial Safety Validation

The safety detector should be tested against an adversarial corpus including:
- indirect suicidal language,
- euphemisms,
- misspellings,
- sarcasm,
- negation,
- quoted speech,
- metaphor,
- mixed intent,
- ambiguous context.

Evaluate:
- recall,
- false positives,
- robustness,
- detector disagreement,
- silent failure,
- fail-closed behavior.

The deterministic policy remains authoritative regardless of which detector triggered the case.

---

## 37. Regulatory and Clinical-Governance Posture

AURA should explicitly distinguish:

> **Prototype feasibility from deployment readiness.**

The project is a research-informed prototype.

It should not claim that the current hackathon system:
- is clinically validated,
- is approved for medical deployment,
- has an assigned HSA medical-device risk class,
- or satisfies every production regulatory requirement.

Regulatory classification depends on intended use, claims, implementation, and regulator interpretation.

Any future regulatory statement used in a pitch, report, or specification should be verified against current Singapore **primary sources**, including relevant HSA, MOH, PDPC, legislation, and professional guidance.

The previously generated Gemini regulatory report should be treated as a **research map only**, not as an authoritative source.

---

## 38. Regulatory Research Register

Before any regulatory claim is promoted into presentation material or product documentation:

1. Locate the current primary source.
2. Confirm the document is current and applicable.
3. Record the exact clause / section / table.
4. Distinguish statutory requirement from regulator guidance or best practice.
5. Record the practical consequence for AURA.
6. Mark unresolved interpretation questions for medical/regulatory review.

This register exists for disclosure and maturity, not to eliminate innovative prototype features prematurely.

---

## 39. Claims Vocabulary

Product wording is part of the intended-use boundary.

### Preferred / allowed prototype language
Examples:
- “identifies changes from your usual pattern”
- “supports antidepressant maintenance”
- “helps organize longitudinal health information”
- “supports medication routines”
- “helps prepare for clinician review”
- “provides context from consented wearable data”
- “uses safety-aware escalation rules”
- “research-informed prototype”
- “requires clinical validation before deployment”

### Avoid / prohibited without future evidence and review
Examples:
- “detects relapse”
- “predicts depression”
- “diagnoses deterioration”
- “determines suicide risk”
- “prevents relapse”
- “clinically monitors your depression”
- “knows when you are becoming depressed”
- “replaces your doctor”
- “manages your antidepressant”
- “provides emergency monitoring”

Core rule:

> **AURA describes observed change and supports assessment; it does not claim clinical truth that has not been validated.**

---

## 40. Research Roadmap

Two concepts remain valuable but are deliberately outside the MVP core.

### Optional phone-use behavior
Future research may evaluate coarse features such as nighttime use, screen-time change, routine timing, and unlock frequency.

These remain **E3 research-grade hypotheses** and should not appear in the main demo unless needed for a research slide.

### Learning Plane
A future governed research system may allow separately consented patient data to support offline validation, feature evaluation, model research, and future version improvement.

Research findings must not automatically change the patient-facing Care Plane.

This is a roadmap/governance concept, not a central hackathon product claim.

---

## 41. Product Maturity Model

### Level 1 — Idea
A technically and clinically plausible hypothesis.

### Level 2 — Prototype
The mechanism can be demonstrated technically.

### Level 3 — Research-grade
Supporting evidence exists, but not enough validation for the exact target population.

### Level 4 — Clinically validated
Prospective evidence supports the intended use.

### Level 5 — Deployment-ready
Clinical, regulatory, privacy, cybersecurity, operational, and governance requirements are satisfied.

AURA in this hackathon is expected to operate mainly around **Levels 2–3**.

---

## 42. Core Principles for the Pitch

1. **Quiet when stable.**
2. **Personal, not generic.**
3. **Context before conclusions.**
4. **Patient-initiated help is always available.**
5. **Models detect; policy governs safety.**
6. **Treatment stays with humans.**

---

## 43. Current Working Definition

> **AURA is a wearable-first, patient-controlled, longitudinal antidepressant-maintenance companion for working adults. It combines patient-reported context, medication routines, validated check-ins, and selected consented wearable signals to identify meaningful changes from personal longitudinal patterns while minimizing interaction burden. It remains available for patient-initiated distress, uses deterministic policy for safety escalation, and helps prepare concise clinician-ready summaries. AURA does not diagnose, predict relapse, prescribe, provide psychotherapy, or provide emergency monitoring.**

---

## 44. Framework Freeze and Next Artifact

Version 1.0 is the **canonical concept framework**.

Further framework changes should be driven by:
- medical reviewer feedback,
- verified regulatory findings,
- safety-policy testing,
- or implementation discoveries.

The next critical artifact should be the:

> **AURA Deterministic Safety Policy State Machine**

That specification should define:
- safety detector inputs,
- OR-combination rules,
- severity raising rules,
- graded safety states,
- allowed transitions,
- follow-up questions,
- fail-closed behavior,
- safety-mode dropout behavior,
- re-check requirements,
- terminal states,
- LLM permissions and prohibitions,
- logging requirements,
- and test cases.
