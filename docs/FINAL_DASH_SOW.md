# Statement of work: final dash before design lock (for Codex)

2026-10-10. Author: Claude (planner/reviewer). **Authority:** the user asked Claude on
2026-10-10 to finalize this plan and SOW for Codex. Codex starts from this document; per the
HIL rule in `HANDOVER.md`, stop and ask the user only where this SOW conflicts with your
in-progress work or with a safety/policy document. Inputs: `docs/CLAUDE_FINAL_ASSESSMENT.md`
(what is wrong, seen on the live site), Codex's brainstorm in `HANDOVER.md`
(2026-10-10), `docs/IMPRESSION_SPEC.md` I1–I9, DECISIONS §39–§44.

## 1. Goal
After this work a first-time viewer sees, without clicking: an AI-written, sourced
assessment that **reflects what just happened** (including a simulated flu), shown as
scannable cards with one synthesis line; a patient home with a plain recap and a clear
next step; and an AI path that works reliably on the hosted demo. Then the design is
**locked**: after this SOW only fixes, no new features.

## 2. Decisions fixed by this SOW (do not reopen)
1. **L1 is presentation of existing engine output plus descriptive readings.** No new
   detection rule (amended after WP0). The longitudinal engine's drift decisions,
   anchors, trust, safety state machine and communication engine are **not changed**.
   Raising engine drift on new channels is out of scope.
2. The AI validators are **not weakened**. Fix the draft shape, prompts and fallback, not
   the rules (prohibited-claim, fact-citation, numbers/dates, signal/category, finding
   metadata match, verifier pass).
3. No new dependencies, no DB schema change, no new write tools, no unguarded hosted
   intake. Pinned safety panel and patient-initiated help ("I want to mention something")
   stay as prominent and reachable as today.
4. Keep §44 copy discipline: factual, neutral, no repeated inline caveats.
5. No cause language anywhere ("because", "due to", "led to"). Co-occurrence is stated as
   "recorded over the same period".
6. Condition-specific numbers (window lengths, multiples, minimum readings) live in
   `aura_agent/engineering_config.json`, not in code (DECISIONS §41/§42).

## 3. Work packages (do in this order; stop at each gate)

### WP0 — Baseline and diagnosis (no behaviour change)
- Run the existing suites; record counts and time.
- Add `tests/live/assessment_pass.py` (not in CI; needs the live key via env or the
  running hosted settings). It runs N generations of the clinician brief and patient
  insight on Case B and on Case B + "flu 3 days", and writes a table: run, role, model
  latency, outcome (validated model draft / partial / fallback), **rejection reason code**,
  card count. Store the output under `docs/evidence/` (text, no secrets).
- Diagnose and record in the evidence doc: (a) why the flu produced **no engine
  finding** for resting heart rate, HRV, respiratory rate or skin temperature although
  they are `enabled_in_engine` (thresholds, minimum days, trust state, transient window,
  coverage); (b) the histogram of rejection reasons for live drafts.
- **Gate:** both diagnoses written before WP1/WP2 code.

### WP1 — Reliable AI path and one card per channel (L2)
Tasks:
1. **Draft shape.** The cards already render from verified structured findings, so asking
   the model to rewrite every retained finding as prose only creates rejection risk
   (`OMITTED_RETAINED_FINDING`, `FABRICATED_NUMBER_OR_DATE`, `UNSUPPORTED_*`). Preferred
   design: the server emits deterministic claims for every retained and recent-window
   finding (same facts/metadata, rounded display); the model contributes only the headline,
   the synthesis sentence (WP3) and approved question ids, each validated exactly as today.
   If you choose another design, document why and keep validation unchanged.
2. Fix causes found in the WP0 histogram at prompt/skill/schema level. Fail closed.
3. **One latest card per exact channel** (signal + source + metric): clinician cards,
   patient cards, chart callouts and the finding-dates strip. When a channel has several
   findings (e.g. a transient deviation and a sustained drift), show the most recent
   `last_seen`; list earlier spans in the "Why?" popover. This removes the duplicate Sleep
   timing cards seen on 2026-10-10.
4. **Honest labels.** "AI-written · sources checked" only if model-written content
   (headline/synthesis/questions) passed validation and is shown. When only server
   extraction is shown, label it plainly ("Summary from the record", not an alarming
   "Offline extraction" when a live model is connected). Never show both.
5. **Arrival.** Show the rule-based version immediately and swap in validated AI content
   when ready; cache per state fingerprint (existing idempotency). No flicker or
   duplicate cards on swap.
Acceptance:
- On the hosted demo with the live model, ≥18 of 20 runs on Case B and ≥18 of 20 after
  "flu 3 days" yield a validated AI headline (no full fallback). Report the actual figure.
- p95 time to first visible assessment ≤2 s (rule-based) and AI swap p95 ≤8 s; report.
- No duplicate cards for one channel in any case A–F or after any simulator event.
- If the target is unreachable, stop and report the reasons table. Do not relax checks.

### WP2 — The flu shows up in the assessment (L1) — AMENDED 2026-10-10 after WP0
WP0 evidence (`docs/FINAL_DASH_EVIDENCE.md`) showed the engine **already** raises
`TRANSIENT_DEVIATION` findings for resting heart rate, HRV, respiratory rate and skin
temperature after the three-day flu (all TRUSTED/OBSERVED, 14/14 days). The cause of the
missing flu is presentation: the UI offers only the first three claims to the card
renderer and sleep/activity fill those slots. The seven-day-vs-28-day median rule I first
specified would **not** detect RHR (0.17× spread) or HRV (1.09×) on this fixture, so it is
dropped as the primary mechanism. Do not add a new detection rule and do not tune
thresholds to make the demo pass.
Tasks:
1. **Show every engine finding.** After WP1's one-latest-card-per-channel selection, apply
   the display cap to channels, not claims. Show up to six channel cards on the clinician
   view, ordered by `last_seen` descending (not by severity), with the rest under "More
   changes (n)". Every retained engine finding must appear somewhere visible or one tap
   away. Patient view keeps its two-item burden limit, ordered the same way, with "See all".
2. **Transient findings are labelled for what they are.** Card text for
   `TRANSIENT_DEVIATION` says "Recent change" (not "Later/Lower than usual since …" for a
   multi-week drift); sustained drift keeps "than usual since …". Use the finding kind
   already in the evidence; no new computation.
3. **Display-only channels** (SpO2, blood pressure, thermometer, weight; no engine
   baseline): show a descriptive "Recent readings" row/card: latest value, number of
   readings in the last 7 days and their range, with dates. No "moved", direction or
   threshold, because there is no reference. Missing readings are never filled in.
4. Optional, only if time remains and clearly labelled descriptive: keep the 7-day-vs-prior
   window facts as popover detail; do not promote them to cards.
Acceptance:
- After "Simulate: flu 3 days" and refresh, the clinician view shows cards for resting heart
  rate, HRV, respiratory rate and skin temperature (plus sleep and activity), each with
  sources, and a "Recent readings" item for the thermometer, within 30 s of the committed
  events. Patient view shows at least the two most recent channels with "See all".
- Quiet-month check: run 20 seeds with no events and report how many produce any
  transient card on the newly visible channels. This is a measurement of existing engine
  behaviour; if it is high, report it to the user and do not change thresholds.
- Engine, safety and decision tables are byte-identical before and after (isolation test).
- No illness/diagnosis wording; "flu" appears only if a patient-recorded context says so.
- Browser test for the flu flow at desktop and 390 px.

### WP3 — Synthesis, check-ins and varied "Worth asking" (L3)
Tasks:
1. **Deterministic co-occurrence.** Group findings (engine and recent-window) and
   check-in runs whose spans overlap ≥`co_occurrence_days` (default 3). The server
   produces the group (fact ids). The model may phrase one sentence; fallback template:
   "Sleep timing, activity and check-ins were recorded over the same period (since
   21 Feb)." The validator rejects cause language and requires ≥2 cited facts from
   the group.
2. **Check-ins card** for the clinician: count and run ("Rough on 7 of the last 7
   days, since 4 Mar"), patient-reported label, no scoring or colour judgement.
3. **"Worth asking"**: choose approved question ids by deterministic rules (context not
   recorded for a finding → context question; gaps recorded → recording question;
   otherwise visit question), show at most two; the model may reorder only. Render as
   tap-to-copy chips.
Acceptance: Case B shows one synthesis line citing sleep, activity and check-ins; the
question chips differ between Case B (no context), a case with context recorded and a
case with gaps; no cause wording; tests cover the validator rejection.

### WP4 — Patient home (L4, DECISIONS §43)
Tasks:
1. A one- or two-sentence plain recap above the cards (agent-written with a plain template
   fallback; same grounding rules; relative dates; no jargon). Hidden only if nothing
   noteworthy.
2. Replace the static "A little less to carry." headline when findings are shown with a
   neutral line (for example "Your recent days"). Keep the static line only when there is
   nothing to report.
3. Remove the "steady · reports" chip next to check-ins; show the check-ins card in plain
   words ("Check-ins this week: mostly Rough") with no chip.
4. One "Why? / Sources" control per card. Make "Prepare for my appointment" a card with a
   short preview ("N items ready · Not sent"). Do **not** reduce the prominence of "I want
   to mention something" or the pinned safety/resources.
5. Phone width checks at 390 px.
Acceptance: browser test at desktop and 390 px; recap present or intentionally hidden;
no ISO dates on the home screen; the visit note is reachable in one tap.

### WP5 — Tidy (L5)
1. Any claim without finding metadata renders as a muted "Also recorded" row with
   rounded values and relative dates; ISO dates and exact values only in popovers. The raw
   "7.9611 to 8.0647 hours" sentence must be gone.
2. Banned jargon in headlines and synthesis ("anchored", "rolling", "deviation",
   "midpoint", "extraction"): validator rejects, template fallback never uses them.
3. Charts: core four first; channels with a card form an "Also moved" group; everything
   else collapsed under "Other measurements (n)". No chart with fewer than three readings
   is shown by default.
4. Hide empty accordions (Evidence, Context, Details) or show a count chip.
5. Demo guide: confirm each three-minute-story button does what its label says; fix the
   ones that do not; keep the panel from pushing the page down on small screens.

### WP6 — Verification, evidence and handover
- Full test suite and affected browser tests green; new tests listed in the evidence doc.
- Re-run the WP0 live pass; write the before/after table.
- Walk, live over HTTPS, and screenshot: Case B clinician and patient at 1280 and 390,
  each simulator event (flu, travel, work stress, alcohol, missed medication, wearable
  off, exercise), and the five story steps. Record what did and did not change in the
  assessment per event.
- Deploy (`docker compose` per `HANDOVER.md`), confirm `/health` and `/system/status`.
- Write `docs/FINAL_DASH_EVIDENCE.md`; update `HANDOVER.md` (Current state, Next steps,
  Log), commit and push in small commits per work package.

## 4. Review gates
Claude reviews after WP2 (the demo moment) and after WP6, by a live pass like the one in
the assessment doc. Do not start WP3 before Claude/user have seen WP1–WP2 unless the user
says to continue. If the user is unavailable, continue and mark the review as pending.

## 5. Design lock (after WP6 and review)
Freeze: card layout, patient hierarchy, descriptive recent-change rule, label vocabulary.
After lock, accept only bug fixes, copy corrections and accessibility fixes; any new
feature needs a written user decision first.

## 6. Out of scope
Engine drift on new channels; new safety rules; multi-condition support; sponsor policy
editor UI; durable approval/sharing workflow; real authentication; M8 submission work;
CodeBuddy rebuild.

## 7. Risks
- Making all engine findings visible may expose more transient cards in quiet months than
  viewers expect; the 20-seed quiet check in WP2 measures this. Report; do not retune.
- Server-generated claims could hide model failure: the evidence doc must report how
  many viewers would see model-written text versus server extraction.
- Sparse channels need explicit "not enough readings" handling to avoid empty charts.
