# Final-dash evidence

2026-10-10. Scope: `FINAL_DASH_SOW.md`, **WP0 only**. User authorized following
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
