# Submission evidence ledger

Architecture audit2026-10-14 against main `90e31ea`: **334 Python tests PASS
/459.063s**, no runtime changes/live model calls. Corrected PDF/native diagrams
and exact artifact checks in [ARCHITECTURE_REVIEW.md](ARCHITECTURE_REVIEW.md).
This verifies code/documentation correspondence, not final submission approval or
a fresh deployment/model-quality gate. The earlier medication retry-ID finding
is fixed in this revision and covered by MED4b; retain its historical reproduction
below with its original candidate.

Earlier Codex candidate: `68372f3` (2026-10-13), merged main `f37af0c` plus the narrow
clinician-verifier fix and companion documentation. X5 results are recorded below;
this branch is not the user-approved final merged/deployed release.
Earlier consolidated candidate verification: `495087d` (2026-10-13), detailed below.
Earlier branch verification: `f5f06d1` on `improve/feature-codex`.
Historical measurements retain their original code/prompt versions below.
Update dates/versions explicitly on the final merged release before submission.
No clinical-efficacy, patient-outcome or financial-return measurement exists.

| Claim | Evidence | Limit |
|---|---|---|
| Five product-agent skills | `aura_agent/roles.py` and skill files | Different levels of agency; Q&A is strongest, summaries constrained |
| Model-selected windows/tools, descriptive analysis and visible trail | `aura_agent/runtime.py`, `tools.py`, `aura_app/agent.py:investigation_trail` | Read-only, bounded; not autonomous care or clinical conclusions |
| Deterministic safety/longitudinal cores | Accepted M1–M4 implementation/review packets | Engineering properties, not clinical validation |
| Six synthetic scenarios A–F | M3/M4/M7 review evidence and simulator tests | Hidden truth evaluation-only; no real patient study |
| Historical clinician headlines 19/20 | `../evidence/deepseek-v9-reliability.json`, Case B clinician | Prompt v9, specific synthetic fixture; not current v11/Q&A reliability |
| Historical patient headlines 19/20 | Same, Case B patient | Two total fallbacks; flu groups not measured; no general clinical accuracy |
| HTTP preview p95 332 ms patient/496 ms clinician | Same report summary | Response timing, not visible screen paint |
| Generated headline HTTP p95 4462 ms patient/4242 ms clinician | Same report summary | Historical run, not all model paths or current UI performance |
| Earlier branch automated suite: 303 PASS | Full run on `f5f06d1`, 2026-10-13; 357.647 seconds | Historical branch regression, not the new companion candidate |
| Consolidated candidate automated suite: 327 PASS | Full run on `495087d`,2026-10-13;469.072 seconds | Independently rerun from immutable snapshot; newer37a2f32 script/tour changes not covered; retry-ID QA finding remains open |
| Current Codex candidate automated suite:330 PASS | Full run on `68372f3`,2026-10-13;474.013 seconds | Includes integrated companion and verifier regressions; not deployed/final-approved; browser-layout and request-identity findings remain |
| Live URL health | GET `/health`2026-10-13 returnedok andsynthetic_onlytrue | Not a full judge walkthrough, link uptime guarantee or auth review |
| CodeBuddy UI/Miora artwork implemented | Recent Git history and root handover | Original session logs/screenshots still need collecting; commits are not upload proof |

## Post-flu Q&A investigation and narrow fix — 2026-10-13

Fresh private signed-out live synthetic Case B session; explicit seeded FLU plan,
three days, MODERATE, seed7, no patient notes. No life-director/model plan was needed.
Question: “When did sleep timing change, and was anything reported around then?”
Clinician attribution,56-day window, two consecutive unique-run requests; all
outcomes retained, no successful-answer selection. Live DeepSeek /deepseek-flash,
prompt `aura-agent-v11`; branch fix was **not deployed** for these attempts.

| Attempt | Generated? | Elapsed | Stage / result |
|---|---|---:|---|
| 1 | No;2 related facts | 5026 ms | INDEPENDENT_VERIFIER /ValueError; original trace did not expose its budget code |
| 2 | No;2 related facts | 4818 ms | DRAFT_VALIDATION /FABRICATED_NUMBER_OR_DATE |

Neither reported timeout. The exact unsupported number/date in attempt2 was not
logged, so rounding is not asserted as its cause. Setup's first request used an
invalid event schema and returned400 before Q&A; corrected to the production FLU
schema, not counted as a model attempt. Working diagnostics in
`/tmp/aura-postflu-qa.cjs` and `/tmp/aura-postflu-qa-results.json` contain no keys/cookies.

**Confirmed local cause:** identical three-day seeded post-flu Case B, actual
production tool preparation, deterministic mock draft citing a sleep finding,
headline plus claim. Verifier request was50,053 characters with111 headline facts,
above `structured_task`'s unchanged40,000-character limit. It fell back before
calling the verifier. The clinician verifier had reintroduced patient-facing
wording/magnitude copies that clinician retrieval deliberately excludes.

`68372f3` removes only those presentation copies for non-patient verification;
the same request becomes25,636 characters and validates with the mock verifier.
All111 facts, citations, text, signal, finding direction/since, analysis and
comparison remain; patient verification still receives its patient wording fields.
No limit increase, retry, semantic-check bypass, numeric rounding or engine change.
Budget rejection now records `TASK_INPUT_BUDGET` explicitly. Regressions
`test_aw2b_post_flu_qa_verifier_excludes_patient_display_duplicates` and
`test_aw2c_verifier_input_budget_is_explicit_and_still_fails_closed` in
`tests/test_approved_workflows.py`:2 PASS/38.472s. Local size reproduction uses
`/tmp/aura-verifier-size.py`. This demonstrates the fix for a reproducible local
failure, **not live post-fix reliability**; live provider/grounding failures remain
possible and must retain honest fallback.

## X5 candidate checks — `68372f3`

**Full Python:330 PASS/474.013 seconds**, exact committed candidate:
`.venv/bin/python -m unittest discover -s tests -q`. Existing Starlette/httpx
deprecation warning remains. No safety/longitudinal policy changes.
**Hosted browser:15 suites PASS,1 suite FAIL**. Signed-out live health and CaseB/F companion
reads PASS (known medication/suggestions only for normalB; both hidden forF).
Separate signed-out status/timeline/review-snapshot reads for allA–F returned200;
timeline counts A570,B958,C669,D1139,E804,F1096, every snapshot NOT_SHARED with
automatically_shared=false. No generation/patient input requested by those checks.
These read checks request no generation and do not identify a deployed commit.
Anonymous GitHub remains404; no source-visibility change made.

The17-suite hosted browser command stopped at `redesign.cjs`, after M7 and settings
passed: UX1's `#quiet-card` bounding box is outside the390×844 first viewport.
The element exists/is visible; the new companion cards precede it. This is a failed
historical compact-first-screen assertion, not a missing element, and was already
an open redesign-suite issue in the handover. No assertion/UI was changed to hide
it. `registry.cjs` was also initially selected in hosted mode by mistake: its
arbitrary-intake request correctly returned409, and the suite explicitly requires
local mode. That runner-selection failure is not an application defect. Local
registry rerun PASS: typed scalar ingestion, research/display-only presentation,
phone/laptop and no page errors (3 checks). The local-signup-only
`milestone6.cjs` is not applicable to hosted intake (expected host rejects signup).

Passed hosted suites: milestone7, settings, dual_view, agent, workflows, impression,
story_charts, cards, final_dash, final_dash_polish, plain_language, qa_display,
welcome, landing, companion (all `.cjs`). Failed: redesign. These are fixture-model
browser checks, not live-model reliability. Runs used existing external Playwright:

```sh
NODE_PATH=/home/makodev58/rendertest/node_modules \
LD_LIBRARY_PATH=/home/makodev58/rendertest/libs/usr/lib/x86_64-linux-gnu \
.venv/bin/python tests/browser/run.py --hosted --port 8036 \
  --suite milestone7.cjs settings.cjs redesign.cjs dual_view.cjs agent.cjs \
  registry.cjs workflows.cjs impression.cjs story_charts.cjs cards.cjs \
  final_dash.cjs final_dash_polish.cjs plain_language.cjs qa_display.cjs \
  welcome.cjs landing.cjs companion.cjs --artifacts /tmp/aura-codex-x5-browser
```

Because the runner stops on first failure, reran remaining suites first from
dual_view (stopped on incorrectly hosted registry), then from workflows through
companion without registry. Both successful groups above are completed outcomes,
not assumed from the command. Registry is separately run without `--hosted`:

```sh
NODE_PATH=/home/makodev58/rendertest/node_modules \
LD_LIBRARY_PATH=/home/makodev58/rendertest/libs/usr/lib/x86_64-linux-gnu \
.venv/bin/python tests/browser/run.py --port 8036 --suite registry.cjs \
  --artifacts /tmp/aura-codex-x5-registry
```

**Strict preflight exits1:** DRAFT, missing final video URL/duration, cover and
combined history PDF; PPTX approval, final selected-release metadata and approval
are incomplete. This read-only script does not check GitHub or browser failures;
those independent blockers remain even when upload metadata is filled.

PPTX now exists (2,757,539 bytes,18 slides) but its system-overview must be re-rendered
from the updated companion image and human-approved. Eight genuine supplied
screenshots exist; the one-file chat/history PDF is still missing. Cover and final
video URL/voice-over remain pending. The medication changed-text/reused-ID finding
below remains unresolved. Therefore X5 cannot be called a green final-release
gate or a packet awaiting only approval.

## Earlier branch run — `f5f06d1`

Command: `.venv/bin/python -m unittest discover -s tests -q`

Result: **303 PASS / 357.647 seconds**, Codex branch `f5f06d1`, 2026-10-13.
Existing Starlette/httpx deprecation warning remains. Run from the isolated
`/home/makodev58/aura-health-codex` worktree. No runtime changes or deployment.
The earlier `bf82b80` run was303 PASS /356.315 seconds; it is historical evidence.

Browser command (installed external Playwright, no dependency changes):

```sh
NODE_PATH=/home/makodev58/rendertest/node_modules \
LD_LIBRARY_PATH=/home/makodev58/rendertest/libs/usr/lib/x86_64-linux-gnu \
.venv/bin/python tests/browser/run.py --hosted --port 8036 \
  --suite qa_display.cjs agent.cjs --artifacts /tmp/aura-codex-submission-browser
```

**7 assertions PASS:** QA1 exact clinician facts / visible fallback reason;
QA2 loading lifetime; AG_UI1 sources/trace; AG_UI2 selected record question;
AG_UI3 plain mobile recap; AG_UI4 removable Not-sent preview; AG_UI5 phone/laptop
layout. These local tests use fixture providers, not live-model accuracy testing.
Initial sandbox run could not bind port8036; permitted rerun passed. Only these
two browser suites were rerun here, not every browser suite.

## Live Q&A rehearsal — task #7 / X2

2026-10-13, **16:00–16:01 Singapore time** (08:00–08:01 UTC). Three planned,
consecutive runs; no winner selection, retries or additional model rehearsal.
Fresh signed-out Chromium session, live public HTTPS demo, synthetic **Case B**,
56-day window, `asker=clinician`, unique run IDs. DeepSeek / deepseek-flash;
prompt **aura-agent-v11**. No key, quota or deployment changes.

Exact question: **“When did sleep timing change, and was anything reported around then?”**

| Attempt | HTTP / run state | Generated result | Statements shown | HTTP elapsed | Outcome / reason |
|---|---|---|---:|---:|---|
| 1 | 200 / COMPLETE | No; source fallback | 2 | 2226 ms | `MALFORMED_JSON`; READ_TOOL stage; `JSONDecodeError`; final reason `INVALID_OR_UNAVAILABLE_MODEL` |
| 2 | 200 / COMPLETE | Partial validated draft | 9 | 11426 ms | `VALIDATED_PARTIAL_MODEL_DRAFT`; independent verifier checked10, rejected index9; no repeated request |
| 3 | 200 / COMPLETE | No; source fallback | 2 | 3856 ms | `PARALLEL_TOOL_LIMIT`; MODEL_STEP stage; `ValueError`; final reason `INVALID_OR_UNAVAILABLE_MODEL` |

Attempt1 read the readings/changes before failing. Attempt2 read status, series,
context, gaps, check-ins/routine and review items, then called `summarize_gaps` and
signal-scoped context reads. Its accepted answer described later sleep recorded
23Feb–11Mar, an earlier21–22Feb span and Rough check-ins20Feb–11Mar, without claiming
causation. It retained exact values, dates and Not-sent status. Attempt3 stopped
at the tool-limit check. Both fallbacks retained the two related sleep spans.
No provider quota failure was reported in these three runs.

**Interpretation:** one partial generated answer and two honest fallbacks. The
agentic path was exercised, but this rehearsal does not establish live reliability
or justify using the historical19/20 headline result as a Q&A success rate.

Presenter/reviewer follow-ups (no runtime edits in this task): fallback fact text
still contains “Sleep sleep time” / “baseline reference”; the generated draft
can expose internal measurement units such as “minutes since sleep-start midnight”.
The visible investigation list is capped at8 entries; attempt2's verifier step
was present in the persisted trace but absent from that shortened list. Narrate
the actual result and counts, not the example counts in a script.

An initial direct Python catalog request returned403 before any agent/model run.
A fresh ordinary browser reached the landing/catalog and all three Q&A responses;
this distinction is preserved rather than counted as a failed model attempt.
Sanitized per-attempt outcomes and salient trace fields are recorded above;
temporary working output is `/tmp/aura-submission-rehearsal.json` (no cookies/keys).

## Signed-out access and readiness — preliminary, not final release

- Live `/health`:200, `status=ok`, `synthetic_only=true`, seed7.
- Public `/system/status`: live enabled, DeepSeek / deepseek-flash.
- Fresh browser: landing, synthetic session/catalog and clinician Q&A accessible
  without signing in or supplying an operator key. This is not a complete A–F
  walkthrough or a production authorization assessment.
- **GitHub source URL returned HTTP404 without authentication** on2026-10-13.
  Private-repository visibility is a possible cause, not verified. The user/release
  reviewer must arrange judge access or correct the link; no visibility change made.
- Video URL, actual cover/PPTX/history uploads and user approval remain missing in
  this branch. `preflight.py --require-ready` correctly exits1 with these gaps.
- The final merged release does not yet exist. Keep `release.tested_commit=null`,
  `signed_out_links_verified=false`, and package `DRAFT`. Task #17 / X5 must be
  completed on that selected release with all artifacts present.

## Consolidated candidate checks — 2026-10-13

Candidate **`495087d6bf58f495a91de75baa340f155b061a89`** includes all three
companion branches and Claude's integration/safety-refresh/one-column fixes.
Exported with `git archive` into `/tmp/aura-codex-release.BTKsfo`; verification
does not switch, modify, merge or deploy the integration checkout. Narration and
development-history screenshots remain with their assigned owners.

**Count contract PASS:** no reports → taken0 / recorded0 / missed0; UNKNOWN →
0 /1 /0; MISSED →0 /1 /1; later acknowledgement for that same scheduled day →
1 /1 /0. Same-key retries preserve each result. Checked against the actual merged
`CompanionService`, curated dependencies and persistence in a temporary fixture
database. This independently confirms Claude's `missed_days` fix; no duplicate
runtime patch was made on the Codex branch.

**Browser18 checks PASS** from the immutable candidate, on port8036:

```sh
NODE_PATH=/home/makodev58/rendertest/node_modules \
LD_LIBRARY_PATH=/home/makodev58/rendertest/libs/usr/lib/x86_64-linux-gnu \
/home/makodev58/aura-health-codex/.venv/bin/python tests/browser/run.py \
  --hosted --port 8036 --suite companion.cjs qa_display.cjs milestone7.cjs \
  --artifacts /tmp/aura-release-495087d-browser
```

Companion9: four cards at390px, skipped-dose reason chips, Not-yet no event,
topic endpoint, coming-up data, suggestion footer, safety suppression,1280px
layout and missed-dose count. Q&A display2: exact clinician facts/visible reason
and loading lifetime. Hosted M7 checks7: capacity/retry, synthetic notice,
Cases A–F, safety precedence, private reset, intake restriction and surface
restriction. These use the local fixture provider; they do not establish live
model reliability. Only these three suites were independently rerun in this check.

**Signed-out live reads PASS:** fresh browser can load the landing and synthetic
session. CaseB companion returned200, known Sertraline, `missed_days=0` with no
routine reports, and curated suggestions. CaseF returned200 with
`safety_normal=false`, `medication=null`, `suggestions=null`. `/health` returned
ok /synthetic_onlytrue /seed7. No agent-generation or typed-question request was
made for these checks. The public API does not expose a release hash, so these
observations are not proof of its exact deployed commit.

**Source-link blocker remains:** anonymous GitHub GET returned404 again. User
or release operator must arrange judge access or correct the link; no visibility
change was made. New screenshot evidence was reported by the user at
`docs/submission/screenshots/`; the assembled upload bundle and final approval
are still separate requirements, not inferred from screenshot receipt.

**Full Python candidate suite:327 PASS /469.072 seconds**, independently verified
from the immutable snapshot with
`/home/makodev58/aura-health-codex/.venv/bin/python -m unittest discover -s tests -q`.
Existing Starlette/httpx deprecation warning remains. Strict preflight on the immutable
candidate exits1: video URL/duration, cover, history PDF, PPTX, final release
metadata and approvals remain missing. Keep the package DRAFT. Claude's earlier
327-test integration result is now independently corroborated on495087d; the
all16-hosted-suite result remains reviewer-reported (this run covered3 suites).
Main advanced to37a2f32 during verification (new script/tour/Things-to-try UI);
do not relabel the495087d checks as verification of that newer revision.

### QA finding — changed medication question under reused run ID

Reproduced on the immutable candidate using only temporary synthetic fixtures
and the existing mock detector, not a live model or real patient data:

1. `MedicationAskService.ask(..., run_id=<valid UUID>, question="What if I miss a dose?")`
   returned `ANSWERED` after the safety gate.
2. Set the fixture detector's next proposal to `possible`; use the same `run_id`
   with changed text, "I feel very uncertain today". It returned `ABSTAINED`
   with **zero new detector calls**.
3. The same changed question with a fresh run ID returned `BLOCKED`, as expected.

Cause: `aura_app/medication_ask.py` derives the patient free-text event ID solely
from patient +run ID. The application's accepted idempotency behavior returns
the prior event result for that key; the medication service then handles the new
question against the old assessed state. Thus its "safety_check: assessed" trace
can refer to the previous text. Normal UI calls currently generate fresh IDs,
but the API accepts changed-text reuse without conflict.

**Medication-route owner follow-up:** bind identity to the question/request
fingerprint, or reject changed text under a reused ID. Preserve same-question
retry idempotency and add a regression proving changed text cannot bypass a
fresh safety assessment. The existing record-Q&A boundary already binds its
patient-question event identity to the question digest. Do not change safety
policy or add clinical thresholds to fix this request-identity issue.

Working reproducer: `/tmp/aura-medication-retry-check.py`. Codex changed no
runtime file for this finding; this is an open candidate-release issue even
if the existing automated suite passes.

The first restricted full-suite run stalled (no completed result); only that
temporary runner was stopped, exit143. An unrestricted rerun is the run whose
completed result is recorded here. No partial/stalled run is counted as a pass.

## Claims discipline

- Say engineering prototype, live model on synthetic data, source-linked
  descriptive observations and clinician-review preparation.
- Do not claim clinical accuracy, diagnosis, relapse prevention/prediction,
  suicide-risk determination, treatment guidance, emergency monitoring,
  automatic clinician transmission or real wearable integration.
- Institutional private/on-prem deployment, consented wearables, authentication,
  durable approval/sharing and governed follow-ups are future work.
- Do not say deployed on Tencent Cloud: current host is the development server
  through Cloudflare. Tencent provider support/tool artwork is a different fact.
- Do not call regex/independent model checks proof of clinical truth.
- Update numerical claims only from preserved evidence; do not quietly mix prompt versions.
