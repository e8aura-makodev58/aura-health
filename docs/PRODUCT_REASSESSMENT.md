# Product reassessment — discussion with Claude

2026-10-07. **Implementation paused at the user's request.**
The user finds the current application unintuitive, its purpose unclear, and its
demands overwhelming for the intended patient. This is product feedback, not a
request for another styling pass. No new direction below is approved.

## What we are trying to achieve

The canonical framework describes a low-burden context layer around an existing,
clinician-managed antidepressant maintenance plan, for adults 25–60. It is not a
generic mental-health dashboard or therapy chatbot. Relevant framework sections:
2–3 (purpose), 5 (two interaction paths), 17 (adaptive engagement), 29–31 (burden,
communication versus observation), and 32 (patient-controlled review preparation).

Its central promise: **make the patient think about their mental health less when
things are going well**, remain available when they initiate a concern, ask the
smallest useful question when justified, and help preserve context for a review.
This does not imply continuous human monitoring, diagnosis or treatment changes.

## Where the implementation misses that promise

Evidence: `aura_ui/index.html`, `aura_ui/app.js`, current screenshots under
`/tmp/aura-redesign-browser-artifacts`, and the user's direct feedback.

- We mapped domain capabilities into Today/Patterns/Review screens before agreeing
  on a compelling patient journey. Patients are being asked to understand our system.
- A quiet-state card still sits alongside check-in, routine, data, Talk, and navigation
  choices. Fewer pixels and collapsed details do not by themselves remove decision burden.
- Reference trust, held observations and review categories are meaningful internally,
  but their default presentation does not clearly answer a patient's immediate need.
- Review has nine groups, checkbox selections and repeated observations; selection
  does not complete a sharing workflow. Technical transparency is not a finished task.
- “Talk to AURA” is prominent, but the hosted experience accepts only named fixtures.
  That is honest containment, not evidence of a useful patient-initiated interaction.
- Synthetic/operator controls and implementation limitations coexist with the patient
  experience. We need a clear distinction between demonstrating the system and using it.
- Tests prove routing, containment, persistence and layout mechanics—not comprehension,
  emotional burden, task usefulness or usability with intended patients.

These are implementation/product-fit concerns. They do not invalidate the accepted
safety or longitudinal engines, or authorize expanding the intended use.

## Journeys to agree before choosing screens

1. **An ordinary day:** Why would the patient open AURA? What, if anything, must they
   do? Can it legitimately require no visit and no mental-health administration?
2. **AURA has one question:** What specific uncertainty needs clarification? Can the
   patient answer or defer without navigating measurements or filling out a form?
3. **The patient brings a concern:** What useful, bounded task can we actually finish
   for them? Distinguish the intended experience from today's fixture-only capability.
4. **Before a clinician review:** What concise preparation helps the patient, and what
   remains optional inspection? Do not imply that preparation equals approval or sending.

For each journey, specify the patient's situation, immediate benefit, one primary
action if needed, shortest completion path, completion feedback, and what stays out
of the default view. Preserve inspectability and mandatory safety resources.

## Request for Claude — respond through root HANDOVER.md

Please challenge this assessment and provide a product recommendation, not code:

- State AURA's patient value in one plain-language sentence, without architecture terms.
- Rank the four journeys above and explain the default experience you recommend.
- Identify what should be absent from the default patient surface, optional to inspect,
  or reserved for operator/demo control. Do not conceal required safety output.
- Walk through an ordinary day, a prompted clarification and a patient-initiated concern.
  Name the benefit and endpoint of each interaction, not merely available features.
- Identify gaps that cannot be fixed by UI alone, especially fixture-only interaction
  and incomplete sharing. Do not suggest bypassing safety or inventing clinical policy.
- Propose a minimal storyboard and a few comprehension/burden acceptance criteria.
  Clearly separate your recommendation from settled policy and user-approved decisions.

## Gate before resuming

Codex and Claude deliberate through `HANDOVER.md`, then present a concise proposed
experience to the user. Obtain agreement on purpose and journeys before coding.
Use a storyboard/walkthrough first; do not launch another speculative implementation.
Mechanical tests remain necessary but must not be called patient-usability validation.

Keep accepted engines, synthetic-only live-model boundary and clinical exclusions.
No UI/code changes, new data, new detectors, LLM expansion or deployment changes in
this reassessment. No actual Claude response or joint agreement is claimed yet.
