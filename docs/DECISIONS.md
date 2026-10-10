# AURA Health — Canonical Decisions

Status date: 2026-10-08.

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

## 31. Live hosted demo is required; other integrations are stretch goals

A publicly reachable **live demo** is in scope and required (user decision, 2026-09-24; the brief gives bonus points for a live link). It is demo hosting, not production infrastructure:
- synthetic data only
- deterministic reset to the fixed demo dataset
- no real patient data or accounts
- deterministic fallbacks if the model service is unavailable
- the prototype/limitations notice visible on the page

Hosting (user decision, 2026-09-24): the primary live demo runs on the project's own server, exposed via Cloudflare. A Tencent Cloud mirror will be decided near the deadline, so keep the deployment portable. Garmin, Apple Health, production cloud architecture, and external health-system integrations remain optional and must not displace the core demo.

## 32. CodeBuddy/WorkBuddy evidence is mandatory

The brief requires the project to be built on CodeBuddy and/or WorkBuddy, and requires **at least 3 screenshots or a screen recording of CodeBuddy/WorkBuddy chat logs** during development. Without proof, the project is not scored. Store actual evidence under `docs/evidence/` with date, milestone, and task; never fabricate retrospective evidence.

**Current user decision, 2026-10-02:** the user decides when/how CodeBuddy is used. Agents must not run it automatically. First complete and review our product, then prepare a detailed SOW for the user to trigger an independent CodeBuddy rebuild from scratch. Capture evidence during that actual rebuild. This supersedes the older instruction to run CodeBuddy during each M5–M7 milestone; it does not waive the final submission evidence requirement. Compare the completed applications, reuse useful reviewed improvements, and submit the stronger implementation (our version if preferred). See §35.

## 33. Demo story

Not “look at our mental-health chatbot,” but how AURA stays quiet, asks small questions, preserves historical truth, and hands safety to deterministic policy. Cases A–F demonstrate physical illness, slow drift, illness plus independent change, explained persistent change, wearable gap, and safety handoff.

## 34. Implementation ownership

User decision, 2026-10-02: Codex has implementation authority over the project; Claude Sonnet 5.5 acts as reviewer. Use root `HANDOVER.md` for coordination and leave each milestone reviewable with test evidence. Accepted product/safety boundaries still govern.

## 35. Product-first implementation and independent rebuild

User decision, 2026-10-02: build a functioning application and iterate until the user and reviewers agree it is a strong product. Only then translate the agreed product into a detailed SOW for a manually triggered CodeBuddy implementation from scratch. Preserve intended use, interfaces, governance, tests, demo behavior, and trust boundaries in that SOW. Keep the rebuild isolated from the existing implementation; compare the completed applications and adopt useful features after review/regression checks. Final implementation choice is based on product quality; using our version remains allowed. No SOW/rebuild is initiated by the M5 implementation task.

## 36. Live synthetic model and patient UX revision

User decision, 2026-10-07: use a live model with synthetic demo data; do not treat
“no live model” as a permanent product principle. Future institutional use is intended
to connect to an institution-managed on-premises/private-cloud model, not a claimed
implemented or validated clinical deployment. Deterministic state/policy/validation
boundaries remain authoritative. Provider choice/configuration and a verified live
call are still needed; do not declare it enabled prematurely.

A dedicated UI/UX agent should contemplate a purpose-led redesign, optimized for
phone portrait and usable on laptop. Additional synthetic-data work is deferred until
these changes are addressed. See `docs/PATIENT_UX_REDESIGN.md` (proposal) and
`docs/SYNTHETIC_LIVE_MODEL.md` (integration plan/current limitations).

## 37. Separate patient and clinician experiences — planning decision

User decision, 2026-10-07: the patient experience must be as simple, intuitive and
visual as possible; analytical information belongs in a separate clinician dashboard.
The synthetic demo should have a Patient / Clinician view toggle. Delegate a plan
to a sub-agent for Claude review before implementation.

This explicitly adds clinician-dashboard planning despite older milestone exclusions.
It does not authorize a production clinician portal, real-patient disclosure,
automatic sharing, reviewer authorization, clinical scoring or treatment decisions.
The demo toggle is presentation, not an access-control or consent mechanism. Accepted
safety/longitudinal engines and synthetic-only live-model boundary remain unchanged.
Patient inspection of retained information must remain available on request.

User direction relayed in Claude's 2026-10-07 review: the clinician view is the main
product workspace; patient analytics are on demand, not default, and patients are
entitled to inspect their data. The revised proposal uses one shared read-only
evidence projection, a patient **See my full data** entry, and an explicit disclosure
that the demo shows the full synthetic record while real clinician access would
require patient approval. This is not a completed approval/access-control workflow.

The dual-view direction is user-requested; the detailed design/implementation plan
has Claude's support after required revisions. User approved implementation with
"Proceed" on 2026-10-07. The synthetic dual-view scope is implemented; product/UX
acceptance and Claude implementation review are still outstanding. No production
sharing or new domain policy was authorized.

## 38. Read-only aura-agent and skills

User decision, 2026-10-07 (implementation continued 2026-10-08): implement aura-agent using Claude's handover proposal;
the project needs genuine AI-agent tasks beyond deterministic fallback wording.
This approves bounded record investigation/synthesis, the five proposed skills
and additive append-only agent trace storage, not new clinical scope.

“Signals propose. Rules dispose. The LLM phrases” remains the safety rule.
Outside safety decisions, the agent may investigate read-only evidence and
draft source-linked summaries/questions. It never disposes: no safety, anchor,
drift, treatment, credibility, interruption or sharing authority. Accepted
safety/longitudinal algorithms stay unchanged. A stricter initial NORMAL-only
agent guard leaves higher modes with the accepted safety interaction.

Live generation remains hosted synthetic-only through protected provider settings.
Offline extraction is explicitly not AI. Record questions are selected templates;
unassessed text cannot bypass safety. Source-linked drafting is not clinically
validated reasoning. Details: `docs/AURA_AGENT_IMPLEMENTATION.md`.

## 39. Agent readability, input, disclaimers and model visibility

User decision, 2026-10-08 ("I approve all"), on Claude's `docs/CLAUDE_AGENT_REVIEW_AND_PROPOSALS.md`:

1. Replace the lexical vocabulary whitelist with claim-level verification (structured
   fields checked against stored engine values, an independent verifier pass, and the
   existing numeric/date/signal/category/citation/prohibited-claim checks).
   Parametrized read tools and server-side descriptive analysis tools are approved.
2. Disclaimers leave the app and are summarized on one demo Disclaimer page. Kept in
   the app: pinned safety panel/resources, a small Demo tag, a brief "AI-written ·
   sources" chip, and functional state chips (e.g. Not sent, Offline extraction).
3. Structured data entry, wearable-export import and free-form record questions are
   approved. Free text is approved **only** behind a layered safety gate: curated
   risk rules plus a raise-only LLM detector (no model may lower concern); timeout or
   invalid output holds the text; held text never reaches the agent. Demo-only and
   unvalidated until adversarially tested; no clinical validation claim.
4. DeepSeek (`deepseek-flash`) is the active provider. Provider and model are shown in
   the settings dialog **without** admin unlock (the public status endpoint already
   returns them; keys and settings stay protected).
5. A demo-only patient-simulator agent is approved (see §40).

## 40. Patient simulator agent (demo only, not product)

User decision, 2026-10-08: build an aura-health patient-simulator agent that generates
synthetic telemetry (heart rate, blood pressure, sleep, temperature, etc.) and in-
character patient feedback, with injectable abnormal life events (e.g. 3-day flu with
raised temperature). It is not part of the product. Users can always enter data
manually. All telemetry remains synthetic. Plan: `docs/PATIENT_SIMULATOR_AGENT_PLAN.md`.

## 41. Project posture: technical proposal for the sponsor

User statement, 2026-10-08: the user is a developer; the sponsor of the problem statement
wants technical ideas and solutions and will own clinical and regulatory assessment,
including which signals and thresholds may be used. Consequences: (1) the user may
authorize engine changes, including new signals; (2) clinical choices are exposed as
sponsor-editable configuration (signal registry with evidence tier and enable flags,
thresholds, safety resources, question and wording catalogues) rather than hard-coded;
(3) the demo must be realistic about what wearables measure (continuous vs intermittent
channels); (4) the Disclaimer page states that this is a technical demonstration whose
clinical and regulatory suitability is for the sponsor to assess; (5) no clinical
validation is claimed; (6) the pinned safety panel and resources stay as a matter of
responsible design. This supersedes the earlier "do not add engine signals" caution
in the simulator plan.

Implementation, 2026-10-09: §39–41 input, verifier/read-tool, Disclaimer, provider
visibility and life-simulator paths are built; see
`docs/APPROVED_AGENT_AND_SIMULATOR_IMPLEMENTATION.md` for contracts/limits.
The earlier `docs/SIGNAL_REGISTRY_IMPLEMENTATION.md` is the foundation checkpoint.
Existing four-channel defaults and accepted domain algorithms remain unchanged.
New-channel coverage/floor safeguards, signal enablement and synthetic effects
are engineering settings, not sponsor clinical approval. Implementation is not
Claude/user acceptance, clinical validation or M7 acceptance.

## 42. Antidepressant maintenance is the focus; architecture stays open to other conditions (2026-10-09)

User direction: the product focus is adults on stable antidepressant maintenance
treatment. The high-level architecture should not preclude other medical conditions in
the future, which also keeps the work viable if this scenario proves unsuitable. This is
an architectural constraint, not a change of scope or a promise of other conditions.
Consequences: (1) keep condition-specific content (signals, drift thresholds, safety tiers
and resources, question and wording catalogues, prohibited-claim lists) in sponsor-editable
configuration, as §41 already directs; (2) avoid hard-coding depression assumptions into
the generic core (personal baseline, drift, trust, held-for-review, read-only agent,
claim verification) when it costs little; (3) the safety state machine is mental-health
specific, and another condition would need its own policy; (4) do not build or test
for other conditions now.

Addendum, 2026-10-09 (user): patients often manage several conditions at once, and a tool
that tracks only one has limited utility. Treat the person's whole record as the unit.
This is a design consideration for the architecture, not an approved feature: no
multi-condition scope, signals or safety policy are built or claimed now.

## 43. Patient is a full participant; default recap is text, not charts (2026-10-09)

User direction: "clinician first" refers to the depth of analytics, not to a lesser
patient experience, because without the patient there is no data. The patient home screen
shows a short recap written by aura-agent in layperson language, without charts. Charts
and full analytics remain available on demand. This supersedes the "four mini-charts"
in `docs/AURA_AGENT_PLAN.md` §7 and the chart wording in earlier patient-home plans.
Quiet still means no alarms, scores, daily tasks or guilt, not an absence of value.
Safety panel and resources are unchanged.

## 44. Factual wording without repeated inline disclaimers (2026-10-09)

User direction: stop appending remarks such as "not a conclusion about mental health"
or "not an assessment of your health" to ordinary findings and reports. Product scope
belongs in the Disclaimer and, for future deployment, clearly explained/acknowledged
onboarding. That onboarding is not implemented or claimed here. Routine cards,
explanations and summaries should state supported facts in neutral language without
implying diagnosis, prediction or advice. Exact sources, AI provenance, operational
states (missing/offline/held/Not sent) and the pinned safety panel remain. Claim
validation and safety policy are unchanged; removal of repetition is not a relaxation
of factual or clinical boundaries.
