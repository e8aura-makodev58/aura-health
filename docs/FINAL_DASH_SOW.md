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
1. **L1 is descriptive only.** New or non-legacy channels get server-computed window
   comparisons shown as "recent change" cards. The longitudinal engine's drift decisions,
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

### WP2 — The flu shows up in the assessment (L1)
Tasks:
1. In `RecordTools` (or a sibling module used by it) compute, for every channel with
   `display: true`, a **recent-window comparison**: median of the last `recent_days`
   covered days versus the median of the previous `baseline_days` covered days, the
   difference in the channel's unit, and the difference as a multiple of the person's
   robust spread (reuse `robust_spread` and the existing coverage thresholds). Defaults in
   `engineering_config.json`: recent 7, baseline 28, `moved_multiple` 2.0, minimum covered
   days 4 (daily/nightly); intermittent channels need ≥2 readings in each window.
2. Emit a fact for each channel that moved: text with rounded values, a `finding`
   `{signal, direction, since}` (since = start of the recent window) and
   `kind: "recent_window"` so the UI can tell it from an engine finding. Mark these
   required for the brief so the model cannot omit them. Channels below the minimum
   readings produce "N readings, not enough to compare" in the popover, never a card.
3. UI: card chip "Recent change" (no severity colour); same card layout as I9; chart
   callout for channels with a chart. Tier note ("Research tier") only in the popover.
4. The existing `compare_windows` tool stays; this is server-side, not model-dependent.
Acceptance:
- After "Simulate: flu 3 days" and refresh, the clinician assessment shows cards for at
  least resting heart rate (higher), HRV (lower) and one temperature channel (higher)
  within 30 s of the committed events, with sources.
- A quiet month (no events) produces no spurious recent-change cards across 20 seeds.
- Intermittent BP/thermometer with two readings do not produce a "moved" card.
- Tests: unit (windows, coverage, spread, intermittent minimums), isolation (no engine
  state or safety output changes; engine tables and decisions byte-identical before and
  after), and a browser test of the flu flow.
- No diagnosis or illness wording is generated; "flu" appears only if a patient-recorded
  context says so.

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
- The recent-window rule may flag normal variation; keep the multiple conservative and
  report false-positive rates from the 20-seed quiet test.
- Server-generated claims could hide model failure: the evidence doc must report how
  many viewers would see model-written text versus server extraction.
- Sparse channels need explicit "not enough readings" handling to avoid empty charts.
