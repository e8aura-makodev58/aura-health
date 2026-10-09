# Assessment-first experience — I1–I8

Implemented 2026-10-09 after the user's explicit delegation approval. This is a
presentation and read-only orchestration change; accepted safety and longitudinal
algorithms are unchanged. Claude/user review remains required.

## Arrival and trust boundary

`GET /patients/{id}/assessment/{clinician_brief|patient_insight}` returns an immediate
grounded extraction, current fingerprint, server-owned `arrival-…` run ID, optional
persisted checked result and generation permission. It never invokes a provider or
appends a run. The browser renders it immediately, then requests the existing agent
POST once for the visible audience. Successful and fallback runs reuse `agent_runs`;
identical opens/toggles cannot launch a new paid run for the same signature. The signature
includes committed events, safety, references, baseline/held state, configuration,
registry, question catalog and provider/model revision. Stale automatic IDs reject
before generation. Existing before/after-generation checks remain authoritative.

Offline, degraded and unsafe states clear ordinary cached prose, full assessment,
visit draft, chart story links and comparison assessment. Pinned policy/resources remain
independent. Current application policy only permits these agent skills in NORMAL.
Free record questions retain the existing safety-first processing path; no unrestricted
conversation endpoint was added.

## Visible experience

- Clinician: assessment first; ≤20-word display headline, ≤3 primary findings, dated
  source-extracted numerical companions when needed, context, gaps and approved questions.
  Every required finding and original claim remains inspectable under **Evidence**.
- Patient: default ≤2 plain sourced recap lines, no home charts; full data and a
  **Not sent** visit preview are one tap away. No retained observation means no recap.
  Jargon-containing model recap uses an honestly labelled plain template, not arbitrary
  rewriting of model text.
  The recap comes immediately after the patient heading; when present it compacts the
  quiet-state card. Its template selects the latest retained finding per exact channel
  in existing signal/source order, avoiding duplicate sleep intervals without severity
  ranking or changing clinician history. Home hides technical trace/refresh controls;
  source access remains. Arrival cache version is `arrival-v3`.
- Three clinician disclosure groups: **Evidence**, **Context**, **Details**. Exact
  source/status/history records remain inspectable; manual intake has a separate button.
- Record Q&A and three existing suggested questions remain visible beneath the assessment.
- Chart spans resolve exact committed signal/source/metric and finding dates. Numbered
  links connect narrative and spans; global context timing is distinct from explicitly
  linked attenuation, and categorical check-ins share the chart time axis.
- Opt-in comparison uses exactly the selected dates and actual rows, with CSV export,
  unchanged missingness and matching sourced assessment; hidden by default.
- Guide quick actions commit real synthetic life events, then refresh the fingerprinted
  assessment and highlight changed lines. Manual/import/context paths remain available.
  The five-step story labels checkpoint switches, generates actual flu events at step 2,
  never invents permission to ask, and opens a genuine **Not sent** visit preview.

## Verification and limitations

`tests/test_impression.py` covers immediate numerical preview with zero provider calls,
durable exact cache, stale-ID rejection, provider revision, unsafe/offline clearing,
mid-read race, non-demo live containment, plain/quiet recap and retained evidence.
`tests/browser/impression.cjs` covers arrival/cache/three disclosures, visible questions,
mobile recap, offline clearing and guided visit. `story_charts.cjs` verifies exact
source/date links, scoped context, aligned check-ins and same-date comparison. Existing
agent/workflow/dual-view browser expectations were updated only where default recap and
automatic arrival intentionally supersede old optional/no-call behavior.

AW28 extends the existing bounded read-before-finalize contract to clinician briefs:
`get_series` is required, plus `get_review_snapshot` when held facts require it. A
premature blank draft must retrieve the evidence, or exhaust the unchanged step budget
and fall back. Claim validation is unchanged. Prompt version is `aura-agent-v3`.

The older hosted/patient browser text assertions were also aligned with the accepted
Disclaimer and safety-gated free-text paths: unknown synthetic text with no working
detector is committed as **held**, not passed to generation. Patient and registry suites
use separate fresh non-hosted databases, because registry intake deliberately adds channels.

## Reproduction

Final verification (2026-10-09): **248 Python tests PASS**, 365.544 seconds;
focused read/grounding gate **31 PASS**. Chromium impression 5, chart story 3,
agent 5, dual view 12, workflows 5, registry 3, patient/offline/retry 17 and
hosted 7 PASS; settings checked at 320/390/1280 pixels. Public A–F reads,
session isolation and exact manual retry passed without paid calls. Final
deployed HTTPS health returned OK.

Opt-in live synthetic checks used DeepSeek/deepseek-flash. Initial clinician /
patient extraction arrived in 257 / 440 ms; both drafts were rejected and
sourced extraction retained. A real three-day flu advance took 6.220 seconds,
with a validated plan and exact replay. After AW28, a final clinician attempt
took 5.049 seconds end-to-end (4.606 seconds model), but was still rejected;
cache/retry equality and offline clearing passed. These single-run engineering
measurements do **not** meet the validated-live-wording target or demonstrate
clinical efficacy. Live wording quality and reviewer/user acceptance remain open.

```sh
.venv/bin/python -m unittest discover -s tests -q

# Opt-in: paid calls, hosted synthetic record only; never reads API keys.
.venv/bin/python scripts/impression_smoke.py \
  --base https://aura-health.makodev58.com --confirm-live-synthetic-checks --flu
# Narrow one-role retry, still using a new private synthetic workspace.
.venv/bin/python scripts/impression_smoke.py \
  --base https://aura-health.makodev58.com --confirm-live-synthetic-checks \
  --roles clinician_brief --output /tmp/aura-impression-brief-check.json
```

The runner reports extraction latency, actual model outcome, exact persisted cache/retry,
offline containment, and optional real synthetic-event/replay timing. A fast rejected draft
does **not** count as meeting the live-generation latency target.

Live wording <5 seconds and first flu update <30 seconds are **targets**, not guaranteed
facts. Immediate extraction avoids an empty screen. The provider and verifier may be slow
or reject a draft; the first advance can prepare 28 days of explicit synthetic references
and accepted event-history replay grows with history. No algorithm shortcut or clinical
claim is used to meet a stopwatch. Current grounding/verifier checks are engineering
safeguards, not clinical validation. No new clinical thresholds, authentication, sharing,
wearable integration, other-condition policy, dependency or database table was added.
