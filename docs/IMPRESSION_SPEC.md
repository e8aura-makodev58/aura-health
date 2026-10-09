# Impression spec: making the AI visible (for Codex)

2026-10-09. Claude (planner). User agreed (2026-10-09) with the diagnosis and the ranked fixes
in `docs/PRODUCT_VISION.md` §7–§8. This turns them into buildable items. It reorders nothing
already approved: it sits on top of the readable-assessment rework, Disclaimer page, input
and simulator work in `HANDOVER.md`. Safety rules are unchanged (no LLM in IMMEDIATE,
degraded or offline modes; held text never reaches the agent; the agent never writes).

## I1. Assessment on arrival (clinician page)
- On opening a patient, the top card is the agent assessment, not a button. Shape (from
  review §4C): headline (≤20 words), up to 3 dated findings with numbers, "Context
  recorded", "Data gaps", "Worth asking".
- Generate on first open and cache per state fingerprint (reuse existing idempotent run
  IDs). Show the rule-based text immediately and swap in the AI text when ready; chip
  "AI-written · sources" vs "Offline extraction". Guard-blocked states show the static
  safety status instead.
- Done when: opening Case B shows a headline and ≥2 dated findings without any click, in
  <5 s with a live model, and the offline path shows the same structure.

## I2. Story drawn on the charts
- Each finding carries `signal`, `since`, `until?`. Render a shaded span on that chart and
  a numbered marker linking finding ↔ span. Context events become markers on all four
  charts; the check-in strip sits directly under the charts on the shared time axis.
- Done when: a viewer can point at the highlighted weeks that match the headline.

## I3. Living demo
- Demo guide gets buttons: "Simulate: flu 3 days / travel / work stress / missed meds"
  (patient simulator plan). After each, the assessment regenerates and the changed lines are
  highlighted. Manual input stays available at all times.
- Done when: pressing "flu" changes the assessment (temperature/RHR/activity) in ≤30 s.

## I4. Ask this record, always visible
- A single input under the assessment with 3 suggested questions. Answers cite sources.
  Until the free-text gate exists, allow the approved question menu plus clinician-style
  record queries on resolved data only; do not accept raw patient free text.

## I5. Plain language and less fine print
- Rename in UI strings only: "anchored reference" → "your usual", "source-local sleep
  clock" → "sleep time", "rolling-window availability" → "recent data". Drop explanatory
  fine print; keep the pinned safety panel, Demo tag, AI chip, state chips.
- Collapse the ~15 "+" sections to at most 3 (Evidence, Context, Details).

## I6. Patient benefit by default
- Patient home shows "Your month at a glance" (one or two plain sentences plus four
  mini-charts of own history) and a one-tap visit note ("Not sent" chip). Hide the card
  only when the agent returns nothing noteworthy. Full data stays one tap away.

## I7. Three-minute guided story
- Demo guide runs a scripted path: quiet month, trigger an event, AURA asks one question,
  the clinician view shows the assessment, the visit note is ready. Each step is a button
  and ≤1 sentence of text.

## I8. Before/after panel
- Side by side on the clinician page (toggle, hidden by default): left a raw wearable
  table/export for the same period; right the AURA assessment. Static copy, no claims
  about outcomes.

## Order
I1 → I2 → I5 → I3 → I4 → I6 → I7 → I8. I1+I2+I5 alone should change the first impression;
I3 needs the simulator.

## Review criteria (Claude checks each)
First-time viewer can state what AURA does in one sentence after 30 s; assessment visible
without a click; every claim sourced; no diagnosis, prediction or treatment wording;
guard-blocked and offline states still correct; browser tests updated.
