# Clinician Q&A: cited deterministic check-in calculations

Implemented on the Codex branch from main `eac0334`, 2026-10-14. Claude owns merge/deploy.

## What changed

Record Q&A can call `summarize_checkins` to calculate descriptive proportions,
counts and missing-day coverage. The model chooses the category, window and
denominator; Python computes the result from the immutable approved evidence
snapshot. There is no question-string matching, arbitrary code execution, SQL,
clinical scoring, or safety/longitudinal engine change.

The existing analysis tools still handle wearable window comparisons, weekday
patterns and gaps. Two check-in calls can compare periods side by side; percentage
point differences and general-purpose arithmetic are not implemented in this change.

## Calculation contract

- Category: Good, Okay or Rough.
- Inclusive date window: explicit ISO dates or `last_days` (1–56), ending at the
  record's latest patient-local date. Historical demo records do not use today's
  server date. The existing bounded evidence horizon also applies.
- Daily selection: latest timestamp among non-held check-ins in the patient's
  timezone; equal timestamps use the later position in committed timeline order.
- Default denominator: days with check-ins. Optional explicit calendar-day
  denominator counts days recorded as the category, without assigning a state to
  missing days. No recorded-day denominator yields an unavailable percentage.
- Exact decimal arithmetic; percentages rounded half-up to one decimal place.
- Result contains counts by category, numerator, denominator and its meaning,
  dates, timezone, recorded/missing/calendar days, operation version, rounding,
  display sentence and underlying event references. Model references are opaque
  hashes; synthetic scenario names in source event IDs stay outside model input.

Example with complete coverage:

> From 2026-02-10 through 2026-03-11: 66.7% (20 of 30 days with check-ins) were recorded as Rough. Check-ins covered 30 of 30 days; 0 days had no check-in. Missing days remain unknown.

With five unrecorded days and the same twenty Rough days, the recorded-day
percentage is 80.0%, with coverage 25/30 and five unknown days explicitly shown.

## Harness and validation

Prompt version `aura-agent-v12` directs Q&A to plan the relevant read/calculation,
use tools rather than model arithmetic, answer the requested quantity and cite
the resulting derived fact. It encourages relevant reads rather than a full
record sweep for every question.

Percentage claims currently use the exact server-produced display sentence.
Only that sentence, cited from a delivered check-in calculation in RECORD_QA,
receives the narrow percentage exception. Other roles, arbitrary percentages,
psychiatric risk language and unsupported numbers retain existing checks. This
deliberately preserves denominator/coverage rather than permitting arbitrary
model paraphrases of calculations. Headlines retain their existing restrictions.

The existing independent verifier receives the complete analysis metadata. The
normal application safety approval/race checks and call budgets remain in place.
If a retrieved calculation is omitted, one repair is permitted; another omission
falls back with `CALCULATION_ANSWER_INCOMPLETE`. This is a narrow completion check,
not a claim that every free-form question is semantically guaranteed answered.

The investigation trail reports the calculation and missing-day coverage. A
provider failure still uses existing related-fact extraction; it does not invent
analysis parameters or claim that a calculation ran when it did not.

## Verification and review

Full Python suite: 355 PASS / 492.432 seconds. Final focused suite: 10 PASS
after the completion-check refinement; calculation trail smoke and diff check
passed. Existing Starlette/httpx deprecation warning remains. The first full
attempt found empty-tool-call compatibility and outdated prompt-version test
expectations; both were corrected before the passing rerun.

`tests/test_checkin_analysis.py`: ten focused tests cover complete/partial/empty
coverage, held input, local-day duplicates and ties, explicit/relative windows,
invalid inputs, source aliases, deterministic replay, scoped percentage claims,
mock multi-step generation and independent verification, one bounded repair,
and provider-failure fallback.

No paid live-model calls or deployment are part of this implementation. Before
demo acceptance, rehearse the clinician's original 30-day question and a
two-period comparison on the merged deployed record; capture the actual outcome
and latency, including any fallback. Scripted tests do not prove live-model
reliability or clinical validity.
