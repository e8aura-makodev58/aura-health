# Plain-language spec: no technical data terms for patients or clinicians (for Codex)

2026-10-11. Claude. **User direction (2026-10-11):** the tone in `PATIENT_VOICE_SPEC.md` is
accepted. No technical data terminology anywhere in the patient view, and the same for the
clinician view: they are patients and doctors, not data scientists, analysts or engineers.
This extends `PATIENT_VOICE_SPEC.md` to every default-visible surface. Part of WP4/WP5.

## 1. Rule
Everything a patient or a clinician sees by default is written in ordinary or everyday
clinical language. Technical vocabulary is allowed only (a) in an explicit, collapsed
**"Technical details"** fold that is closed by default, (b) in the Disclaimer page and
repo docs, or (c) in the demo guide's collapsed **"Developer tools"** fold. Doctors may see
clinical terms they use daily (resting heart rate, sleep duration, blood pressure, check-in)
and plain dates and units (12 Mar, 8.8 beats/min, about 3 hours). They do not see data-science
or system words.

## 2. Terms to remove from default view, and what to say instead
Seen on the live site (2026-10-10/11) unless noted.
| Now | Instead |
|---|---|
| Stored rolling mean (chart legend) | Recent trend |
| Your own reference / Governed personal reference | Your usual (chart line), no extra caption |
| Data observed | (remove) |
| Recent data: 100% · 14 samples | Data for 14 of the last 14 days |
| Research tier / Display only · recorded measurements | Newer measure (hover: "less established than the others"), or Readings only |
| Finding dates · same chart window | When things changed |
| Source extraction / Summary from the record chip | Remove the line; keep the single chip |
| AURA assessment / READ-ONLY RECORD ASSISTANT | Summary |
| PERSONAL LONGITUDINAL CONTEXT | (remove; the page title is enough) |
| Inspect assistant steps | Move into Technical details |
| Compared with your usual … | Fine, keep |
| Sleep midpoint / Sleep timing (clinician) | Sleep time / bedtime |
| anchored reference, rolling, deviation, drift, baseline, trend magnitude | your usual, recent, change, since |
| Transient / persistent | Recent change / ongoing |
| Trust state, provisional, re-establishing, sensing state | (remove; say "still learning your usual" only if needed) |
| held for review | Waiting for your clinician to look |
| committed events, checkpoint, fingerprint, trace, idempotent | (remove) |
| Medication routine · not verified ingestion | Medication: patient-reported |
| Synthetic case B · 35 · UTC · fixture-only; no treatment instruction | Demo patient · 35 (the Demo tag already covers the rest) |
| Chart dates: Last 8 weeks | Fine, keep |
| Source IDs, fact IDs, ISO dates (2026-03-11) | Sources: "Your check-ins, 20 Feb – 11 Mar"; dates as 11 Mar |
| median, spread, robust, coverage, samples, metric, channel, signal | (never shown) |
Demo guide: "Random seed", "Verify deterministic replay", "Save trace", "Inspect last
simulator run" move into Developer tools. The story buttons and event buttons stay.

## 3. Clinician register (plain, not chatty)
Short, factual, dated. Example headline: "Sleeping later and less active than usual since late
February; check-ins Rough for about three weeks." Cards keep rounded values and units. The
"Why?" popover gives a short plain explanation plus a "Technical details" fold for exact
values and source IDs. Clinicians still get sources: as readable labels ("Check-in, 11 Mar").

## 4. Implementation
1. **One list.** `aura_agent/plain_terms.json`: banned terms and optional replacements. The
   same list feeds (a) the headline/synthesis validator (extending the current
   `anchored|rolling|deviation|midpoint|extraction` rule), (b) template unit tests, (c) the
   browser lint below.
2. **Rename UI strings** per section 2 in `aura_ui/index.html`, `evidence.js`, `agent.js`,
   `features.js`, `app.js`. Chart legends and captions included.
3. **Technical details fold:** a reusable collapsed block marked `data-technical`, used in
   cards' "Why?", the assistant steps and the evidence area. Closed by default, remembers
   nothing.
4. **Server-side wording:** fact text and templates the UI shows verbatim use friendly
   phrases (engine descriptions stay internal; they feed the technical fold only).
5. **Agent prompts:** all five roles get the "no technical terms" rule; examples file
   (`PATIENT_VOICE_SPEC.md` §4) gets a clinician set in the section 3 style.

## 5. Acceptance
- **Browser lint test** `tests/browser/plain_language.cjs`: for cases A–F and after each
  simulator event, in patient and clinician views at 1280 and 390 px, read the visible text
  (excluding `data-technical` and Developer tools) and assert zero banned terms, no ISO
  dates and no source IDs. Failing output prints the term and its element.
- Unit tests for templates and for validator rejection of banned terms in model headlines.
- Existing tests that assert old wording are updated, not deleted.
- **User sign-off:** the user looks at both views and the five voice samples; any term the
  user still finds technical is added to the list and fixed.

## 6. Scope and risks
- Wording and layout only; no engine, safety, schema or validator-strength change (the term
  ban only adds a rejection).
- Over-simplifying can hide what a doctor needs: keep exact values one tap away and keep
  sources. Do not hide measurement quality; say it plainly ("data for 9 of the last 14 days").
- Evidence tier matters to doctors, so keep a plain marker for newer, less established
  measures instead of removing it.
