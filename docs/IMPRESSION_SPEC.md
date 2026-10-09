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

## I6. Patient recap by default (decided 2026-10-09, DECISIONS §43)
- Patient home shows a short, plain-language recap written by aura-agent: what has been
  steady, what has shifted, what the patient told us. **No charts on the home screen.**
  Aim for everyday words, short sentences and no jargon (no "baseline", "drift", "anchor");
  the patient_insight role's prompt and template target this reading level.
- Same grounding rules as every agent output (cited facts, exact numbers and dates, no
  diagnosis, prediction or treatment advice). Rule-based template fallback in the same
  plain style when no model is available or the guard blocks.
- Charts and full data stay one tap away ("See my data"), which preserves the patient's
  entitlement to analytics on demand. Also show the one-tap visit note ("Not sent" chip).
- Hide the recap only when the agent has nothing noteworthy to say.

## I7. Three-minute guided story
- Demo guide runs a scripted path: quiet month, trigger an event, AURA asks one question,
  the clinician view shows the assessment, the visit note is ready. Each step is a button
  and ≤1 sentence of text.

## I8. Before/after panel
- Side by side on the clinician page (toggle, hidden by default): left a raw wearable
  table/export for the same period; right the AURA assessment. Static copy, no claims
  about outcomes.

## I9. Findings as cards, less prose (user approved cards 2026-10-09)
Problem seen on the live page: raw numbers ("195.423 minutes"), each finding stated three
times, empty sections taking space, uniform sentences with no hierarchy, ISO dates on the
patient card. Keep the necessary text; layer it and give it shape.

**Clinician finding card** (one per finding, rendered from the structured claim fields
`signal`, `direction`, `magnitude`, `since`, `until`, `fact_ids`, not from prose):
```text
┌──────────────────────────────────────────────┐
│ ☾ Sleep timing              ● 1   ⌃ Why?     │
│ ↑ about 3 h later                            │  <- big, rounded, human units
│ ▕░░░░░░░▓▓▓▓▓▓▓▓▓▓▕  23 Feb → 11 Mar        │  <- thin span bar, shared axis
│ Later than usual for 3 weeks.   See on chart │  <- one line, no raw numbers
└──────────────────────────────────────────────┘
```
- "Why?" opens a popover: method line, exact values (`195.4 min`), "compared with your
  usual", and Sources. Nothing is deleted, only layered.
- The number marker links to the numbered span already drawn on the chart. Also show the
  one-liner as the chart's callout so the words sit next to the evidence.
- Signal icon and a neutral colour chip per category. No good/bad colour, no scores.
- Round to sensible units (minutes→hours, steps→"about 2,000 fewer a day"); exact value only
  in the popover. Relative dates ("since 23 Feb", "last 3 weeks").
- Arrange cards in a responsive grid (2 up on desktop, 1 up on phone) under the headline.
- Collapse empty sections ("Context", "Data gaps") into a single muted line, or hide.
- "Worth asking" becomes tap-to-copy chips. Record-question block collapses to one input
  with suggestion chips (drop the dropdown and extra buttons).
- Add a thin timeline strip above the charts showing the cards' spans on the shared axis.

**Patient card** (home, no charts; DECISIONS §43):
```text
┌──────────────────────────────────┐
│ ☾  Sleeping later than usual     │
│    since late February           │
│ ● shifted                        │
└──────────────────────────────────┘
```
- One short sentence per card with an icon and a "steady" / "shifted" chip (not a chart,
  no colours that imply good or bad). Include one "steady" card so the screen is not all
  changes. Replace "Recorded changes" and ISO dates with relative, everyday wording.
- Tap a card for the plain explanation and Sources; "See my data" still opens the charts.

**Constraints**
- Render deterministically from the verified structured fields; the agent's prose is
  limited to the headline, the one-liner and "worth asking". Offline extraction fills the
  same card fields.
- Keep the AI chip, Sources, state chips and pinned safety panel visible and small.
- Done when: a viewer can read the three findings in ten seconds without opening
  anything, and no raw 3-decimal numbers appear outside the popover.

## Order
I1 → I9 (cards, with I2) → I5 → I6 → I3 → I4 → I7 → I8. I1+I2+I5 alone should change the first impression;
I3 needs the simulator.

## Review criteria (Claude checks each)
First-time viewer can state what AURA does in one sentence after 30 s; assessment visible
without a click; every claim sourced; no diagnosis, prediction or treatment wording;
guard-blocked and offline states still correct; browser tests updated.
