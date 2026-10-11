# Patient recap refinement — 2026-10-11

User direction: make the patient page understandable, not an analytical report;
let Aura-Agent choose wording within deterministic rules. See DECISIONS §45.

## Experience

- One home heading and a short, everyday-language recap. No default measurement
  grid, research abbreviations, repeated state badges or check-in counts.
- **See what changed** reveals the retained findings and reports. Exact sources,
  dates and methods remain inspectable; **See my full data** still opens analytics.
- **Why this summary?** explains whether the wording is AI-generated or a factual
  record fallback and shows its sources. Provenance is secondary, not concealed.
- Patient help, actual policy-approved questions, appointment preparation and pinned
  safety remain independent. No added reassurance, advice or inline disclaimers.
- Clinician analytics keep their existing detail and behavior.

## Wording boundary

Aura-Agent chooses a complete natural sentence and selects supporting delivered
facts. The existing bounded headline contract remains: at most 20 words, exact
citations, no generated policy/action fields. Patient-specific presentation checks
reject technical report language and non-conversational headings. The existing
claim checks and independent live-model entailment verifier still apply. These
checks are defense in depth, not proof of clinical validity.

Rejected/unavailable generation uses a plain factual template with honest provenance.
The short recap does not claim to cover every retained finding. Full evidence stays
available on demand. Presentation selection is not clinical ranking.

No safety or longitudinal algorithm, clinical threshold, database schema, dependency,
configured provider or model quota changes are part of this work. Prompt and arrival
cache versions change so older wording is not reused under the new contract.

## Verification

- Full Python suite: **266 PASS**, 358.197 seconds. Six new patient wording tests
  cover natural output/citations, jargon and prohibited copy, verifier rejection,
  ordinary research-channel labels, exact reference comparisons and check-in claims.
- Final coherent browser run: **42 PASS** across cards, final-dash/polish,
  impression, agent, charts, dual-view and hosted isolation/safety suites. A new
  fixture verifies actual generated wording, exact recap citations and separately
  retained unrelated evidence. Phone/laptop screenshots inspected.
- Deployed HTTPS preview/source/details/phone/laptop check PASS, no model calls.
- Fresh live synthetic patient samples: B and B + three-day flu **2/2 validated**;
  total HTTP 3.588 and 3.773 seconds. Existing call budgets/35-second spacing
  preserved, no retry-until-pass. Sanitized results:
  `docs/evidence/patient-recap-live-smoke.json`.

The 20-run live wording/p95 acceptance and final UX review remain separate open
gates; this refinement does not imply M7 acceptance or clinical validation.
