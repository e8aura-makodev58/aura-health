# Patient reliability follow-up — 2026-10-12

Claude reviewed and deployed v9 on 2026-10-12, then started the user-approved
fixed 80-assessment reliability trial at 08:01 UTC. The trial is active; no
completed v9 reliability gate is claimed.

At the 08:17 UTC saved checkpoint, 16/80 assessments were recorded: Case B
clinician 8/8 validated and patient 7/8, with one UNSUPPORTED_CATEGORY rejection.
Both groups are INCOMPLETE. These are interim counts, not final results.
The active output remains untracked until completion; log `/tmp/v9_run.log`.
Do not redeploy, run additional live calls or run heavy tests during this trial.

## Preserved v8 results

Claude stopped the trial at 53/80 assessments. Case B clinician passed at 18/20;
patient failed at 16/20. Patient rejections: one HEADLINE_BUDGET, two
VERIFIER_REJECTED, one MALFORMED_JSON. Clinician rejections: one verifier and one
malformed JSON. Flu clinician 7/7 and patient 5/6 remain incomplete. No provider
failure was recorded. See `evidence/deepseek-fixed-reliability.json`.

Rejected raw drafts were not saved, so the precise semantic causes cannot be
reconstructed. The changes below address contract inconsistencies, not proven
individual hallucination causes.

## Changes

- Consistent patient target: one or two sentences, ideally at most 28 words total
  and 18 per sentence. Hard validation remains 35 total / 25 per sentence.
- Shorter placeholder examples; preserve attribution and recent-vs-usual comparator.
- Explicit native-tool versus final-JSON protocol and exact field/array types.
- Verifier receives exact fact IDs, last-recorded date and allowlisted check-in
  count/window metadata. Real event IDs and scenario labels remain excluded.
- Verifier instructions clarify supplied human dates/aliases while still rejecting
  unsupported direction, comparator, causation, feelings and clinical conclusions.
- Prompt `aura-agent-v9`, examples `patient-voice-v2`, arrival cache `arrival-v10`.

No parser repairs, repeated generation, schema change, relaxed validator, provider
switch, quota change, or safety/longitudinal algorithm changes.

## Verification

Full suite: **290 PASS / 346.043 s**. Affected Chromium: **21 checkpoints PASS**
(plain-language2/final-dash3/cards4/agent5/hosted7). Four new prompt-contract tests
inspect actual runtime messages, exact verifier metadata without hidden IDs, and
strict rejection of empty/fenced/truncated/wrong-shape output. These are offline
contract tests, not measurements of live semantic reliability.

## HTTPS rehearsal before v9 deployment

Seven real quick-event buttons and five story steps passed on phone/laptop;
zero page errors. Evaluation substituted explicit three-day MODERATE, seed42,
notes-off plans at the advance transport, rather than calling the LLM director.
Agent headline calls were blocked; ordinary AUTO communication stayed real.
Read-only audit confirmed **one communication generation attempt/use per rehearsal**.
This was not a zero-model-call exercise. No keys, messages or IDs were printed
by that audit.

| Event | Committed entries | Clinician finding cards after corrected capture |
|---|---:|---:|
| Flu | 37 (includes explicit research-reference setup) | 6 |
| Travel | 3 | 6 |
| Work stress | 3 | 6 |
| Alcohol | 3 | 7 |
| Missed medication | 3 | 7 |
| Wearable off | 1 (three generated days) | 7 |
| Exercise | 3 | 7 |

No event became patient-reported context merely from its simulation label. Notes
were off, so the medication scenario did not add medication reports. The short
wearable interruption did not enter UNOBSERVED; that is an observed engine result,
not a claim that absent data is healthy. Long-gap/return behavior remains covered
by accepted Case E.

Two 20-load Chromium preview measurements are retained:

| Measurement | Preview DOM readiness p95 | Target | Result |
|---|---:|---:|---|
| First run, concurrent full Python tests | 2643.4 ms | 2000 ms | FAIL |
| Corrected snapshot run, after full suite finished | 1745.7 ms | 2000 ms | PASS |

The second run is diagnostic, not a replacement for the first. Both used fresh
documents, disabled HTTP cache and the same private workspace; timing begins at
navigation timeOrigin and ends after visibility plus two animation frames. Physical
screen paint and live generated-swap p95 are not established by this measurement.
First report had a role-switch card-count capture bug and story status overwrite;
its timing samples remain valid and unchanged. The corrected report captures
clinician state before counting cards.

Artifacts: `/tmp/aura-https-rehearsal/` and
`/tmp/aura-https-rehearsal-corrected/` (screenshots/metrics; both retained).
Runner: `tests/live/https_rehearsal.cjs`; updated response counters save only
deduplicated communication counts, not IDs or prose.

## Next gate

Allow the active fixed 20-per-role/scenario v9 trial to finish within unchanged
limits, then verify all 80 entries and version consistency before committing its
sanitized evidence. Preserve the failed v8 trial, count every rejection, and do
not reduce sample size or retry until pass. Matching live/fallback voice samples,
user sign-off, generated-swap paint timing, Claude review and design lock remain
pending. Codex's handover reconciliation ran only the lightweight prompt-example
budget test (1 PASS); the full 290-test result above predates deployment.
