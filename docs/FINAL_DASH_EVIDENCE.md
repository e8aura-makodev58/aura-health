# Final-dash evidence

Historical WP0 report, 2026-10-10. Scope: `FINAL_DASH_SOW.md`, **WP0 only**. User authorized following
Claude's instructions. This is the first work-package gate, not design lock or
M7 acceptance. No production behavior, validator, engine, schema, dependency,
provider setting or deployment was changed.

## Baseline

`.venv/bin/python -m unittest discover -s tests -q`: **248 PASS**, 354.515 s.
Existing Starlette/httpx deprecation warning remains.
`tests/live/assessment_pass.py` compiles; live measurements exercised its HTTP
path. Browser suites were not rerun: no browser code changed.

## Live measurement method

```sh
.venv/bin/python tests/live/assessment_pass.py \
  --confirm-live-synthetic-checks --runs 1
.venv/bin/python tests/live/assessment_pass.py \
  --confirm-live-synthetic-checks --runs 1 \
  --output docs/evidence/final-dash-baseline-measured.json
```

Hosted HTTPS, DeepSeek `deepseek-flash`, synthetic-only settings. One fresh
generation per role per scenario in each exploratory pass: eight generations
total, **not the later 20-run reliability gate**. Fresh UUIDs avoid cache hits;
requests are separated by at least 35 seconds without increasing provider
budgets. Each pass uses its own isolated synthetic workspace, Case B, followed
by a confirmed three-day flu advance (seed 42, notes disabled). The director's
resolved plan is used, not assumed deterministic. No keys, cookies, model prose,
patient free text or raw provider errors are stored.

Raw numerical evidence and reason codes:

- `evidence/final-dash-baseline.json`: first pilot.
- `evidence/final-dash-baseline-measured.json`: repeat with presentation-eligible
  card count and independent-verifier rejection count.

`preview_ms` times the immediate assessment GET. `model_elapsed_ms` is the
server agent runtime (tools/model/verification), not model-only inference.
`total_ms` includes GET + POST/network. Card count mirrors the current renderer's
eligibility and first-three/first-two limits; it is **not a browser DOM count**.
Distinct finding channels and claim counts are also saved, because a claim may
combine several findings and a raw prose row is not a finding card. A fallback
headline is not model-written; `headline_present` alone never establishes that.

### Pilot results

| Scenario | Role | Immediate ms | Runtime ms | Total ms | Outcome | Rejection code | Claims / finding channels |
|---|---|---:|---:|---:|---|---|---:|
| B | clinician | 538 | 6916 | 8037 | partial | semantic claim rejection; exact count not captured in pilot | 8 / 2 |
| B | patient | 335 | 2080 | 2693 | fallback | FABRICATED_NUMBER_OR_DATE | 2 / 2 |
| B + flu | clinician | 365 | 6562 | 7265 | fallback | FABRICATED_NUMBER_OR_DATE | 8 / 6 |
| B + flu | patient | 387 | 3695 | 4375 | validated | none | 2 / 6 |

Pilot full-fallback rejection histogram: `FABRICATED_NUMBER_OR_DATE: 2`.
Partial verification is reported separately, not relabelled full success.

### Repeat results with card eligibility

| Scenario | Role | Immediate ms | Runtime ms | Total ms | Outcome | Headline retained | Eligible cards | Verifier rejected items |
|---|---|---:|---:|---:|---|---|---:|---:|
| B | clinician | 209 | 5150 | 5609 | partial | yes | 2 | 1 |
| B | patient | 328 | 3069 | 3644 | partial | no | 3 | 1 |
| B + flu | clinician | 309 | 6584 | 7188 | partial | no | 3 | 2 |
| B + flu | patient | 744 | 3881 | 5027 | partial | no | 3 | 1 |

Repeat full-fallback rejection histogram: none; **five semantic-verifier items
were rejected across four partial drafts**. Across both passes: one complete
validated draft, five partial drafts, two full fallbacks. Only three of eight
results retained a nonempty model-written headline (fallback headlines are
excluded). Current patient UI hides even a retained headline; checked prose also
does not necessarily appear when a deterministic card replaces the claim.
This explains why `generation_used=true` is not sufficient evidence of visible
AI-written wording. No p95 or 18/20 claim is made from this small sample.

## Diagnosis A: flu visibility

**Claude's hypothesis of absent engine findings was not reproduced.** The
committed post-flu evidence contains `TRANSIENT_DEVIATION` for all four channels:

| Channel | Trust / sensing | Covered days in rolling window | Latest minus rolling median | Engine threshold magnitude |
|---|---|---:|---:|---:|
| Resting heart rate | TRUSTED / OBSERVED | 14 / 14 | +8.193 beats/min | 6.1935 |
| HRV | TRUSTED / OBSERVED | 14 / 14 | −13.572 ms | 4.45175 |
| Respiratory rate | TRUSTED / OBSERVED | 14 / 14 | +1.9885 breaths/min | 1.401 |
| Skin temperature | TRUSTED / OBSERVED | 14 / 14 | +0.6385 °C deviation | 0.2 |

Actual code: `aura_longitudinal/drift.py:assess_drift`,
`aura_longitudinal/baseline.py:BaselineManager.rolling`, registry defaults and
`aura_app/workflows.py:advance`. The 14-day window is sufficient (minimum five
points, calendar coverage 0.5, point coverage/quality 0.5). Scale is the maximum
of anchored robust spread, 5% of anchored center and configured absolute floor;
the deviation multiplier is 2.0. New research-channel references are explicitly
created/trusted by synthetic fixture commands. Three altered days do not meet
the persistent fraction 0.6; short-window transient comparisons nevertheless
detect them. No clinical interpretation is implied.

The **presentation bottleneck** is `aura_ui/agent.js:render`: only the first three
clinician claims are offered to the card renderer; fallback emits retained
findings in existing signal order, including two historical sleep kinds. Sleep
and activity occupy those slots before heart rate or research channels. Only the
first finding of a combined claim becomes a shaped card. Therefore “six cited
channels” does not imply six visible cards. WP1's exact-channel/latest selection
must happen before the display cap, with earlier spans retained in Sources.

### WP2 seven-day median limitation

Read-only evaluation of the specified recent-seven/prior-28 rule, same committed
post-flu evidence (not a new production algorithm):

| Channel | Recent / prior covered days | Median difference | Prior robust spread | Absolute difference / spread |
|---|---:|---:|---:|---:|
| Resting heart rate | 7 / 28 | +0.125 | 0.7413 | 0.169 |
| HRV | 7 / 24 | −1.547 | 1.4203308 | 1.089 |
| Respiratory rate | 7 / 24 | +0.177 | 0.1089711 | 1.624 |
| Skin temperature | 7 / 24 | +0.0905 | 0.0429954 | 2.105 |

Four preceding ordinary days dominate the seven-day median despite three changed
days. It cannot supply the requested heart-rate and HRV cards at a 2.0 multiple
on this fixture. Skin's result depends on whether the existing 0.1 absolute
spread floor is applied (then 0.905, below 2.0). This floor handling needs an
explicit implementation decision; no threshold was changed during WP0.
Thermometer has three recent readings and zero prior readings; BP has two recent
and zero prior readings. Neither has a comparison reference. Missing readings
are never inserted or interpolated.

**No engine expansion is needed.** WP1 can expose the existing transient engine
findings; WP2 can retain its specified descriptive medians without promising they
detect every three-day event. If acceptance instead requires these to be
*recent-window* cards specifically, the SOW needs a window-rule decision rather
than quiet threshold tuning. Ground truth/event labels must not select windows.

## Diagnosis B: live draft rejection

The pilot's two full fallbacks carry the deterministic numeric/date mismatch
code, not an unexplained disconnected-model state. The current prompt requires
model-authored prose, exact numeric strings/dates, exact finding metadata and
complete retained history in a small number of claims. It then performs a
separate semantic verifier pass. That combination creates avoidable rewriting
failure even though the UI ultimately draws its cards from stored findings.
The pilot clinician draft also had unsupported content removed by the semantic
verifier. This is expected containment, not a reason to relax checks.

WP1's prescribed direction is appropriate: deterministic retained claims for
cards, model-written headline/approved bounded wording, unchanged claim and
semantic checks, and honest generation labels. Server claims must not be counted
as successful model-authored content. Omitted-history, numeric and semantic
rejection paths remain required. The raw provider-error path is intentionally
redacted; this pilot did not justify inferring a provider-specific cause.

## Gate and next work

WP0 diagnoses are documented. WP1–WP6 remain **unimplemented in this turn**.
Per SOW “stop at each gate”, hand off this baseline before WP1. The next package
is reliable bounded AI wording and one latest card per exact signal/source/metric;
then descriptive window facts, followed by Claude's WP2 review. Design is not
locked; no M8 or CodeBuddy work began.

## WP1–WP2 implementation and review handoff — 2026-10-11

Claude's `da36b42` amendment governs WP2: expose existing committed engine
findings, not a new 7-versus-28-day detector. Accepted engines, configuration
thresholds, schema, dependencies and safety precedence are unchanged.

### Changes

- Clinician/patient generation now requests only a cited, bounded headline and
  approved question IDs. The server supplies retained claims. Existing numeric,
  citation, prohibited-claim, retained-history and patient-burden checks remain;
  the independent semantic verifier checks the headline against exactly its
  cited facts. Model failure or rejection retains the immediate record summary.
- UI selects the latest exact signal/source/metric finding, preserving older
  spans in Why. Date-descending channel cards replace the old claim cap:
  clinician six by default plus More changes; patient two plus See all.
  Transient engine findings say Recent change, not persistent drift.
- Display-only channels show latest/count/date range and inspectable recorded
  min/max over configurable `recent_readings_days=7` (engineering default,
  constrained 1–30). No interpolation, baseline, direction or alert is added.
  Deferred/low-quality observations are excluded. Raw source IDs remain in UI
  evidence but are stripped/aliased before model tools, preserving fixture
  isolation. AI provenance labels require visible validated generated wording;
  otherwise the label is Summary from the record.
- Versions: `aura-agent-v5`, `agent-engineering-v3`, `arrival-v5`. Other agent
  roles and legacy explicit draft contracts remain unchanged.

### Verification

FD1–FD4 cover server/model separation, retained evidence, prohibited and
fabricated wording, semantic rejection and sparse facts/isolation.
Final full regression: **252 PASS**, 361.490 s. Existing Starlette/httpx warning
remains. Final three new browser checks rerun PASS after all edits.
AG10 now asserts the approved record-summary disclosure and absence of the AI
label, rather than the obsolete literal Offline rule-based wording.

Browser checks: final dash 3, impression 5, agent 5, story charts 3, dual view
12 and hosted 7 PASS (35 total); standalone finding cards 3 PASS. Covers A–F
channel uniqueness, actual flu's six channels, three thermometer readings,
patient overflow, phone/laptop layout and safety/offline clearing.
HTTPS preview screenshots exist at `/tmp/aura-final-dash-https/`: clinician
and patient at 1280/390 pixels. That check blocked assistant POSTs; it exercised
one synthetic director call, not headline reliability. Clinician 390-pixel
screenshot inspected: all six findings and sparse readings visible, no overflow.

Twenty quiet seeds produced **0/20** with transient RHR/HRV/respiratory/skin
findings (`evidence/final-dash-quiet.json`). This is the explicitly stable
synthetic profile with a 28-day governed reference and 30 observed days, not
a population false-positive estimate or clinical validation.

Commands:

```sh
.venv/bin/python -m unittest discover -s tests -q
.venv/bin/python tests/live/quiet_channels.py --output docs/evidence/final-dash-quiet.json
NODE_PATH=/home/makodev58/aura-math/node_modules LD_LIBRARY_PATH=/home/makodev58/rendertest/libs/usr/lib/x86_64-linux-gnu \
  .venv/bin/python tests/browser/run.py --hosted \
  --suite final_dash.cjs impression.cjs agent.cjs story_charts.cjs dual_view.cjs milestone7.cjs \
  --artifacts /tmp/aura-final-dash-browser
.venv/bin/python tests/live/assessment_pass.py --confirm-live-synthetic-checks --runs 1 \
  --output docs/evidence/final-dash-wp1-wp2-live.json
.venv/bin/python tests/live/assessment_pass.py --confirm-live-synthetic-checks --runs 1 \
  --output docs/evidence/final-dash-wp1-wp2-v5-live.json
NODE_PATH=/home/makodev58/aura-math/node_modules LD_LIBRARY_PATH=/home/makodev58/rendertest/libs/usr/lib/x86_64-linux-gnu \
  node tests/live/final_dash_browser.cjs --confirm-live-synthetic-checks
```

### Live smoke, not the reliability gate

Fresh synthetic HTTPS runs, DeepSeek/deepseek-flash, seed 42, three-day flu,
feedback disabled. Provider budgets unchanged; 35-second measurement interval.
The first v4 pass validated clinician wording but rejected both patient
headlines with HEADLINE_BUDGET. These failures remain in
`evidence/final-dash-wp1-wp2-live.json`. Prompt revision v5 asks for 8–12 words
with absolute 20-word maximum; the validator was not changed.

| v5 scenario / role | Preview ms | Total ms | Agent runtime ms | Validated headline |
|---|---:|---:|---:|---|
| B / clinician | 170 | 2591 | 2195 | Yes |
| B / patient | 293 | 2640 | 2138 | Yes |
| B + flu / clinician | 366 | 3674 | 2990 | Yes |
| B + flu / patient | 497 | 2868 | 2038 | Yes |

Saved in `evidence/final-dash-wp1-wp2-v5-live.json`. These are one sample per
role/scenario, **not** 18/20 success or p95 acceptance evidence. Runtime includes
tools and semantic verification, not just model inference. Card counts in JSON
are eligibility estimates; DOM assertions are separate browser checks. One
initial request encountered a startup 502 before any model call; it was repeated
after health became ready, not retried until generation passed.

### Deployment and remaining gate

Rebuilt Docker app, preserving volume/provider settings and the user-managed
Cloudflare container. Deployed on `0.0.0.0:8017`, public
`https://aura-health.makodev58.com`. Health and synthetic-only live provider status
verified. Latest image: `874cdc963406cff9ceffdbabbf889b02f05055b0a3ba25ace6f5a565fa258c80`.

**WP1 quantitative 20-run/p95 gate remains pending. Claude WP2 review is next.**
WP3–WP6 have not been implemented in this slice. Do not claim design lock,
M7 acceptance, new clinical detection, or CodeBuddy evidence.

## WP3–WP5 review follow-ups — 2026-10-11

Claude reviewed WP1–WP2 in `19d3cea`: PASS with follow-ups. User requested
continuation and delegated model selection (Luna for lightweight work,
6.1-Sol medium for heavier work). Implemented within the approved SOW.

### Presentation, not policy

- Added a deterministic cited co-occurrence sentence for the clinician. Uses
  latest exact-channel finding spans and gap-broken, non-held check-in runs;
  common intersection must be at least `co_occurrence_days=3` (engineering
  default). Relevant recorded gap dates exclude the channel from that interval.
  At least two distinct cited facts are required, and the unchanged claim
  validator checks numbers/categories/finding metadata. Causal wording and
  headline jargon remain prohibited. Neutral labels cover the real registry,
  including Skin temperature rather than Skin-temperature deviation.
- **Deliberate bounded choice:** synthesis uses the validated deterministic
  template only. The model still writes the separately checked headline; optional
  model synthesis wording is not implemented. This avoids adding a second live
  generation failure path. Server synthesis is not counted as AI-written output.
- Clinician check-ins show count of distinct non-held recorded calendar days,
  denominator/window, and latest consecutive run. Missing days break a run.
  Latest eligible answer wins within a day; a held answer is never counted.
  Counts are patient reports, not scores. Raw event IDs stay in UI citations,
  not model-facing nested metadata.
- Worth asking uses approved IDs only: missing associated context selects
  context; a recorded scoped gap selects recording; otherwise visit. At most two
  copy chips. A historical scoped gap is not asserted to be active missingness.
  These inspection questions do not replace the communication/safety engines or
  create automatic patient interruptions.
- Patient cards use onset recency, surfacing recent physiology before older
  sleep/activity spans when last-seen dates tie. Plain deterministic recap is
  visible on fallback; validated generated headline remains available. No large
  six-channel clinician synthesis on patient home. Check-ins are plain words,
  without a steady chip. Skin units use °C; HRV/skin have distinct icons.
- Patient heading changes to Your recent days when findings exist. Appointment
  entry is a one-tap card with actual snapshot item count and Not sent. Approval
  is still temporary, not persisted or transmitted. Help and safety unchanged.
- Nonfinding prose is muted Also recorded with rounded display values and
  everyday dates; exact source values/dates remain in Sources. Core four charts
  appear first; other sourced findings are Also moved. Remaining or sparse
  (<3 actual readings) charts are collapsed under Other measurements. Source
  links reveal their groups. Evidence/Context/Details show item counts.
- Mobile demo guide is bounded overlay instead of pushing the patient page
  down. Story step 3 now honestly says Slow-change checkpoint: it selects the
  existing B checkpoint rather than promising a policy question.

New external presentation parameters: `co_occurrence_days=3`, `checkin_days=7`;
existing `recent_readings_days=7` unchanged. All engineering defaults. Versions
`agent-engineering-v4` and `arrival-v6`; headline prompt remains `aura-agent-v5`.
Accepted safety/longitudinal engines, thresholds, decision tables, DB schema,
dependencies and provider budgets are unchanged.

### Noisier quiet measurement (review follow-up)

```sh
.venv/bin/python tests/live/quiet_channels.py --noise-multiplier 3 \
  --output docs/evidence/final-dash-quiet-noisy.json
```

Original profile: **0/20** seeds with transients. Three-times-noise profile:
**8/20** seeds, with **24 HRV** and **9 skin-temperature** transient channel-days;
RHR and respiratory rate: zero. The same increased noise is used for the
28-day reference and 30 observed days; no life event is inserted. The generator's
fixed skin-deviation noise is scaled only in this evaluation harness. This is
an explicit synthetic stress profile, not a patient population distribution,
notification count, false-positive rate or clinical validation. **No retuning**
was done. Noise sensitivity remains a sponsor/reviewer limitation to assess.

### Regression scope and remaining work

FD5–FD10 cover exact overlap, gap exclusion, missing/held check-ins, context/gap
question selection, hidden source-ID isolation, all shown channels versus chained
overlap, and labels from the actual signal registry. Two live-report math tests
prove a smoke sample cannot pass the 20-run gate and p95 grouping is per role and
scenario. Timing summaries explicitly remain HTTP proxies, not DOM paint timing.
New `final_dash_polish.cjs` exercises sparse/chart grouping, patient phone/laptop
and all five real story actions. Earlier literal steady-chip and always-visible
sparse-chart assertions were updated to the approved UI behavior, preserving
source inspection, missing-report absence and reveal-on-link checks.

Final verification/deployment results are recorded in HANDOVER.md. An initial
preflight ran while the config/class was being edited and read mismatched old
code/new JSON; it is not a valid baseline result. Only stable final runs count.

**WP6 full HTTPS event walkthrough and the WP1 20-run/p95 gate remain pending.**
The larger live run consumes shared hourly budgets (native read/generate/verify
calls all count); do not raise limits, clear quota state, or retry-until-pass.
Four earlier v5 smoke results do not establish reliability after these changes.
Claude's final review, design lock and M7 acceptance remain open. No M8/CodeBuddy.

### Final WP3–WP5 verification and deployment

Full **260 PASS**, 415.785 s. Final coherent browser run: **41 PASS**, no page
errors (polish 3/final dash 3/impression 5/agent 5/charts 3/dual view 12/hosted
7/cards 3). Actual Case B synthesis cites sleep, activity and check-ins; actual
flu synthesis includes HRV. Patient first card is a recent change, with a recap
and no clinician preparation question chips. Sparse links reveal their group;
all five guide actions work. Final screenshots:
`/tmp/aura-final-dash-polish-final/`. HTTPS flu preview both roles at 1280/390
also PASS; assistant calls blocked, one real synthetic director call. Phone
patient screenshot inspected. Final tiny icon/duplicate-heading/question-chip
polish was then tested in the coherent local browser pass and redeployed.

```sh
NODE_PATH=/home/makodev58/aura-math/node_modules LD_LIBRARY_PATH=/home/makodev58/rendertest/libs/usr/lib/x86_64-linux-gnu \
  .venv/bin/python tests/browser/run.py --hosted \
  --suite final_dash_polish.cjs final_dash.cjs impression.cjs agent.cjs \
  story_charts.cjs dual_view.cjs milestone7.cjs cards.cjs \
  --artifacts /tmp/aura-final-dash-polish-final
.venv/bin/python tests/live/assessment_pass.py --confirm-live-synthetic-checks --runs 1 \
  --output docs/evidence/final-dash-wp3-wp5-live.json
```

Live DeepSeek/deepseek-flash, synthetic seed 42, feedback disabled, same prompt
v5 / configuration v4. Fresh calls, no generation retry, unchanged quotas:

| Scenario / role | Preview ms | Total ms | Agent runtime ms | Headline outcome |
|---|---:|---:|---:|---|
| B / clinician | 212 | 3565 | 2500 | Validated |
| B / patient | 419 | 2863 | 2159 | Fallback: HEADLINE_JARGON |
| B + flu / clinician | 407 | 3230 | 2415 | Fallback: HEADLINE_BUDGET |
| B + flu / patient | 566 | 4354 | 3068 | Validated |

**2/4 smoke results, not a reliability estimate or acceptance gate.** The
report's four per-role/scenario sample gates explicitly say INCOMPLETE. The
old all-success smoke cannot be generalized. Immediate deterministic recap
and synthesis remain available on both rejection paths. No validator relaxed.

Final Docker image: `a58781bec0736c91774169793d8e8309b7d152b8c38b2d2e026fd8abf8a97bfd`.
Bind `0.0.0.0:8017`; provider settings, volume and user-managed tunnel preserved.
HTTPS health/provider status verified. **WP6/full reliability review still next.**
