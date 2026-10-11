# Plain-language spec: no technical data terms for patients or clinicians (for Codex)

2026-10-11. Claude. **User direction (2026-10-11):** the tone in `PATIENT_VOICE_SPEC.md` is
accepted. No technical data terminology in the patient view; the clinician view loses internal
schema-style names and tags but **keeps its factual data** (clarified later the same day).
They are patients and doctors, not data scientists, analysts or engineers.
This extends `PATIENT_VOICE_SPEC.md` to every default-visible surface. Part of WP4/WP5.

## 1. Rule (revised 2026-10-11 after user clarification)
The user's clarification: **do not remove factual data from the clinician view.** The target
is schema-like names and tags, not information. Two audiences, two levels:

- **Patient:** everyday words only (per `PATIENT_VOICE_SPEC.md`); rounded values; relative
  dates. Exact values and sources are one tap away under "Why?".
- **Clinician:** all factual information stays visible: exact values with units, dates, how
  much data there is (for example "14 of 14 days", "3 readings"), when a usual is still being
  established, held-for-review status, medians/ranges for readings, check-in counts and
  runs, sources. What goes is **internal naming**: enum/code identifiers, record and fact
  IDs, system labels and tier tags. Clinical and statistical words a doctor would use
  (baseline, median, range, resting heart rate, check-in) are fine when they carry data.

"Technical details" fold (closed by default) is reserved for the genuinely internal:
assistant steps, raw event/source IDs, validator and version info. Developer tools in the
demo guide hold seed, replay and trace.

## 2. Remove or rename: internal names and tags only
Seen on the live site (2026-10-10/11) unless noted.
| Now (internal naming) | Instead |
|---|---|
| `SLEEP_MIDPOINT`, `TRANSIENT_DEVIATION`, `E3_RESEARCH` and any UPPER_SNAKE value | Plain label: "Sleep time", "Recent change", "Newer measure" |
| Source/fact/event IDs (demo-B-7-69-checkin, f12) | Readable source: "Check-in, 11 Mar"; raw ID only in Technical details |
| anchored reference / Governed personal reference | "Your usual" (patient) or "Baseline" (clinician), with the value |
| Stored rolling mean (legend) | Recent average |
| Data observed | (remove; adds nothing) |
| Research tier / Display only · recorded measurements | "Newer measure" or "Readings only" |
| Finding dates · same chart window | When things changed |
| Source extraction line; "AI draft from synthetic records…" | Remove (one chip remains) |
| READ-ONLY RECORD ASSISTANT / PERSONAL LONGITUDINAL CONTEXT | Summary / remove the kicker |
| Inspect assistant steps | Technical details |
| Synthetic case B · 35 · UTC · fixture-only; no treatment instruction | Demo patient · 35 (the Demo tag covers the rest); keep timezone only if it clarifies times |
| committed events, checkpoint, fingerprint, trace, idempotent, workspace | (remove from default view) |
| Medication routine · not verified ingestion | Medication: patient-reported (state kept) |
| Trust state / sensing state codes | State the fact in words: "Usual still being learned (9 days of data)", "Watch not worn since 8 Mar" |

**Kept for clinicians (do not remove):** "Recent data: 100% · 14 samples" may be reworded as
"Data for 14 of 14 days · 14 readings"; exact values, medians and ranges; check-in counts
("Rough on 20 days in a row, 20 Feb – 11 Mar"); held-for-review status; sources; the
exact numbers behind each card.

## 3. Registers
- **Clinician headline:** "Sleeping later and less active than usual since late February;
  check-ins Rough for about three weeks."
- **Clinician card:** rounded headline value, then the factual line with exact numbers and
  units visible: "Bedtime 3 h 32 min later than baseline (median 02:41 vs 23:09), 23 Feb – 11 Mar".
- **Patient:** per the voice spec; numbers rounded, no baseline/median words.

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
  simulator event, read the visible text (excluding `data-technical` and Developer tools).
  Patient view at 1280 and 390 px: zero jargon terms, no ISO dates, no source IDs. Clinician
  view: zero schema-like tokens (UPPER_SNAKE, `f\d+`, event/source IDs, tier tags) and zero
  system labels from the banned list; exact values, units and data-amount statements must
  still be present (assert they appear). Failing output prints the term and its element.
- Unit tests for templates and for validator rejection of banned terms in model headlines.
- Existing tests that assert old wording are updated, not deleted.
- **User sign-off:** the user looks at both views and the five voice samples; any term the
  user still finds technical is added to the list and fixed.

## 6. Scope and risks
- Wording and layout only; no engine, safety, schema or validator-strength change (the term
  ban only adds a rejection).
- Over-simplifying can hide what a doctor needs: keep exact values, data amounts and
  sources visible in the clinician view. Say measurement quality plainly ("data for 9 of the
  last 14 days").
- Evidence tier matters to doctors, so keep a plain marker for newer, less established
  measures instead of removing it.
