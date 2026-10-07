# AURA Health — Demo Script

Status: M7 local walkthrough; public URL pending. Allow about six minutes. All patients,
inputs and detector proposals are labelled synthetic; no clinical-efficacy claim.

## Operator preparation (before presenting)

Follow [deployment](DEPLOYMENT.md); open the loopback Docker demo or the verified
public URL once configured. Explore demo → Reset synthetic session → confirm. Seed 7
restores only this browser's workspace. Keep [trust-boundary diagram](ARCHITECTURE.md)
ready. No live model or external wearable API is needed. Select **Stable day** first.
Do not enter real information. If connectivity fails, show the local pinned fallback
and use the loopback demo; cold-start offline functionality is not implemented.

This is not “here is our mental-health chatbot.” The story is that AURA quietly follows context around stable treatment, notices meaningful personal change, asks only when useful, preserves historical truth, and hands safety to deterministic policy.

## Opening

AURA is a wearable-first longitudinal companion for adults on stable antidepressant maintenance treatment. It organizes personal patterns, medication routines, and clinician-review context without diagnosing or changing treatment. Show calm stable home: **when nothing meaningful changes, AURA can stay quiet.**

## Case A — physical illness

Explore demo → **A · Physical illness** → Patterns → Why AURA asked (if available).
Show signal-scoped context and preserved measurements (about 35 seconds).

Show elevated resting heart rate and temporary sleep/activity disruption with patient-reported illness. AURA sees change; illness attenuates relevant physiological interpretation; no depression conclusion. **Context before conclusions.**

## Case B — slow drift

Select **B · Slow change** → Patterns; compare anchored and recent references (45 seconds).

Show progressively later sleep, lower activity, less-positive self-report. The rolling baseline adapts but the governed anchor does not silently move; accumulated change remains descriptively visible. **Personal, longitudinal, resistant to adaptive normalization.**

## Case C — illness plus independent change

Select **C · Illness + independent change** → Today/Patterns; show the approved question
and unrelated evidence remaining active (35 seconds).

Illness attenuates linked physiology but does not clear independent subjective/longitudinal evidence. **One explanation does not clear the whole patient state.**

## Case D — explained benign persistent change

Select **D · Before explanation** → Patterns → Explain → use the prepared `new stable
work schedule` → Record. Show held records and unchanged reference. Select **D · Explained,
held for review** to show the later quiet checkpoint and retained Review items (60 seconds).

Patient explains a schedule change. Show `EXPLAINED_HELD_FOR_REVIEW`, unchanged anchor, fewer repeat notifications, and retained review item. **AURA learns context without rewriting reference truth.**

## Case E — wearable gap

Select **E · Wearable unavailable**, then **E · Wearable returned**. Patterns shows
UNOBSERVED versus OBSERVED + REESTABLISHING. Explicitly disclose that no governed
automatic exit from REESTABLISHING exists yet (35 seconds).

Show prolonged missing data without deterioration inference. On return, sensing resumes and baseline trust is REESTABLISHING. **No data is not bad data.**

## Case F — safety policy wins

Select Stable → Talk to AURA → labelled `fixture safety concern` → Record. Alternatively
select **F · Safety handoff**. Navigate Patterns/Review: safety panel remains pinned.
Resources are development fixtures, not verified crisis contacts (45 seconds).

Begin in ordinary longitudinal state. Enter an approved safety-relevant synthetic free-text fixture. Show safety boundary first, deterministic interaction control, normal conversation unable to override it, and no internal risk percentage. Avoid sensationalism. **Models may detect and explain; policy decides and constrains.**

## Clinician review preparation

Select D → Review; inspect held context and temporary selection preview (30 seconds).
Do not claim a clinician received anything. Review-question input has a named fixture;
arbitrary personal text is rejected by the hosted demo.

Show a patient-visible prepared snapshot with sensing coverage, changes, check-in trend, medication events, context, held items, and appropriate safety references. It is **prepared, not automatically transmitted**. Patient approval/sharing remains future work unless explicitly implemented and reviewed in M6/M7.

## Architecture and closing

Show the trust-boundary diagram: deterministic longitudinal/safety engines, bounded Product AI, and development-only Simulation Data Agent. **Signals propose. Rules dispose. The LLM phrases.**

Close: AURA aims to be quiet when stable, personal rather than generic, and honest about uncertainty. It does not replace treatment; it preserves context for a better-informed patient–clinician conversation.
