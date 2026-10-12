# Patient recap refinement — 2026-10-11

The original checkpoint below is historical. The newer patient voice implementation
uses DECISIONS §46 and `PATIENT_VOICE_SPEC.md`: up to 35 words total, at most
25 per sentence, with clinician wording kept concise and quantitatively exact.
User voice acceptance is still required; implementation is not design sign-off.

## Warm voice follow-up

Versioned, placeholder-only examples guide Aura-Agent's phrasing. Friendly source
fields supply human dates, source labels and deterministic rounded quantities;
original measurements and provenance remain inspectable. Patient fallback wording
uses the same supported fields. Check-in-only records describe attributed answers,
and data gaps describe only the affected signal, without generalizing missingness.

“Sleep time” is used rather than “bedtime”: the measured midpoint does not establish
when someone went to bed. An absent alert does not establish that everything else
is unchanged. Neither assertion was copied from the illustrative voice examples.
Optional next steps remain existing interface controls, not model-authored advice.

Patient Why panels use “What we looked at”, “What we saw” and “Where it comes from”.
Technical identifiers are secondary closed disclosures. Clinician comparisons retain
exact values, units, reading counts and source dates. Safety wording is not rewritten.
One shared term catalogue drives prompts, validation and visible-text browser checks.

Prompt/cache versions: `aura-agent-v8` / `arrival-v9`. No safety/longitudinal
algorithm, threshold, database schema, dependency, provider or quota change.

The unchanged 24 KB tool limit measures fields actually sent to the model rather
than duplicate UI disclosures. Exact sparse temperature readings are regression
tested so friendly source fields do not crowd out clinician evidence. Two earlier
v7 synthetic live attempts fell back at MODEL_STEP (`ProviderUnavailable`); those
are failures, not evidence of validated generation. The final cache version prevents
reusing those runs after the payload correction.

Follow-up verification (2026-10-12): **274 Python tests PASS**, 350.871 seconds;
**52 Chromium checkpoints PASS** across final targeted suite runs, including
A–F/seven simulated life events, phone/laptop wording, exact sparse readings,
source-panel refresh, safety/offline/session isolation and local operator workflows.
Registry checks use the development-only server; workflow checks use the hosted
synthetic server. Screenshots of home/Why/clinician data were inspected. Final
public HTTPS phone/laptop/source check PASS without model calls. No user voice
sign-off or 20-run/p95 acceptance is inferred from these checks.

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
