# aura-agent — read-only investigation and synthesis

Implemented 2026-10-08 following the user's 2026-10-07 instruction to build Claude's
agent proposal. Engineering prototype; synthetic data only. Reviewer: Claude.

## Why this is an agent

Unlike M5's finite wording selection, the live model chooses read tools in a
bounded loop, follows their results and drafts a source-linked answer. It can
combine retained longitudinal observations, recorded context, check-ins and
gaps into a short brief or investigate a selected record question. No fixed
template is claimed to perform equivalent semantic synthesis.

Five server-owned skills live in `aura_agent/skills/*/SKILL.md`:

- `clinician_brief`: what changed and when, retaining engine findings.
- `record_qa`: investigate an approved record question across sources.
- `patient_insight`: optional short recap, at most two claims.
- `visit_prep`: removable appointment-note draft, **Not sent**.
- `question_ranker`: propose an order within an approved question set only.

## Trust boundary

Application request → accepted safety output permissions + stricter agent
guard → immutable read projection → model/tool loop → deterministic structural,
factual-vocabulary, citation, numeric and claim checks → race check → persisted
draft/trace → UI.

The guard allows ordinary record investigation only in valid NORMAL state,
with no unassessed/deferred input or outstanding recheck/dropout. CLARIFY,
ELEVATED, URGENT and IMMEDIATE stay with the existing safety/wording pathway.
This conservative agent subset does not change what the safety machine permits.
Offline, degraded, invalid and held-input paths make zero agent provider calls.

Tools are `get_status`, `get_series`, `get_context`, `get_decisions`,
`get_review_snapshot`, `get_gaps`. All are fixed, patient-scoped reads. The
runtime has no repository, write, shell, browsing, sharing or clinical-decision
tool. Tools expose committed facts, not newly computed statistics. Window is
1–180 days (default 56; patient recap 30); measurements are explicitly limited
to eight recent observations per signal. Retained engine findings expose their
kind, first/last recorded dates and stored deviations/trend values separately
(display formatting to three decimals only). Missing measurements are not filled.

Only completed safety-gated context explanations may enter as quoted data.
Other patient notes, aliases, medication names, scenario names and hidden truth
are excluded. Model-facing source references are opaque hashes so demo event
prefixes do not reveal evaluation cases; UI citations retain original event IDs.
Arbitrary Q&A text is not accepted: selected record-question IDs remain the
demo contract until real safety detectors exist.

## Model vs fallback

Hosted synthetic workspaces use the existing protected provider configuration,
fixed vendor endpoints, server-side keys and shared 10/minute, 60/hour budget.
The ordinary API has no live agent enabled. OpenAI GPT-6 Luna uses native Chat
Completions function calling with `reasoning_effort=none`, no parallel tool
calls and `store=false`; other configured vendors use the compatible transport
and fall back if their chosen model does not support it. No new dependencies.
References: [OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling),
[GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna).

Externalized in `aura_agent/engineering_config.json`: 8 model steps, 50-second elapsed budget, 90,000-character
prompt cap, 24,000-character tool-result cap, existing 5-second vendor request
timeout for M5 wording, separate 15-second agent request timeout/16-KiB response cap,
2,048 completion tokens per agent step; at most
16 claims, 600 characters each, 24 citations per claim and three approved
questions. These are engineering limits, not clinical thresholds.

Every claim needs delivered fact IDs. Unknown citations, new numbers/ISO dates,
unsupported signal/category/vocabulary, prohibited claims and omitted retained
brief/visit findings reject the generated draft. The model may combine/reorder
facts; it cannot determine new drift, context credibility or communication
permissions. Three brief groups are preferred, but retaining evidence takes
precedence over the preferred sentence count.

These checks **do not prove natural-language entailment or clinical correctness**.
Polarity, subtle unsupported inference and paraphrase quality still require
review and broader evaluation. Conservative checks may reject legitimate
paraphrases. A draft is never an independently verified clinical conclusion.

Offline scripted execution traverses the same tools and supplies extraction,
not an AI answer. Live failure/timeout/invalid output also produces inspectable
extraction. The UI explicitly labels it **Offline rule-based extraction — no
AI-generated draft**. Pinned safety resources stay outside every draft.

## Persistence, retries and races

One additive `agent_runs` table, primary key `(patient_id, run_id)`, patient FK,
with no-update/no-delete triggers. Each row stores skill, request/state hashes,
provider/prompt/config versions, bounded tool call/fact-reference trace, prompt
hashes, resulting claims/sources, fallback reason, timestamp and safety reference.
Prompts are reconstructable from the versioned skill/schema/query and referenced
facts; full repeated prompts and raw provider errors are not logged. Application
validation diagnostics retain only a bounded alphabetic unsupported-word list,
not the complete rejected draft. Legitimate discourse words can be reviewed
without admitting new factual entities or clinical claims. Application
audit links the run; observation/timeline/anchor/safety records are not mutated.

No transaction stays open during a model call. Safety state, committed event IDs,
baselines/held items, resolved references and provider revision are checked before
retrieval, before generation and at commit. A changed record discards the draft.
Same run ID/options return the committed result without another call; different
options conflict; stale cached content is not re-rendered as current output.
The local service lock coalesces calls within one workspace. Cross-worker paid-call
deduplication and production auth/retention are not claimed.

## API and UI

`POST /patients/{id}/agent/{skill}`:

```json
{"run_id":"12345678-1234-4234-8234-123456789012","query_id":null,"window_days":56,"client_offline":false}
```

Run IDs must have canonical UUID form; they are not another free-text intake.
For `record_qa`, select `sleep_change`, `recorded_context`, `wearable_gaps` or
`routine`. No free-text, model name, tool or patient override is accepted.
`GET /patients/{id}/agent-runs/{run_id}` reloads the historical run/trace.
These development/demo routes are not authenticated clinical access.

Clinician workspace: **Draft a brief**, selected-question investigation,
optional approved-question order, per-claim **Show sources**, inspectable steps.
Patient: optional collapsed monthly recap with four existing-reference mini
charts; **Explain my month**. Review: **Help prepare my note** with per-line
removal from the temporary preview. Nothing is sent or stored as approval.
UI discards output if the selected patient/revision/connectivity changes.

## Verification commands

```sh
.venv/bin/python -m unittest discover -s tests -p test_agent.py -v
.venv/bin/python -m unittest discover -s tests -q
.venv/bin/python -m aura_agent.evaluation --db /tmp/aura-agent-evaluation.sqlite3 --save /tmp/aura-agent-evaluation.json
# Optional Playwright setup described in aura_ui/README.md
.venv/bin/python tests/browser/run.py --hosted --suite agent.cjs
```

AG1–AG20 cover tool scoping, actual multi-step mocked function calling, zero
domain writes, mode/offline/held guards, citations/numeric/claim checks, retained
findings, honest fallback, budgets, race discard, durable append-only trace,
retries, injection/hidden-truth isolation, all five skills and native transport.
Live smoke is recorded in HANDOVER only after observing actual validated output.

2026-10-08 live synthetic smoke: GPT-6 Luna clinician brief **PASS** (six tool
reads, three cited findings, 11,705 ms); record Q&A **PASS** (six tool reads in
a different model-selected order, two cited sentences, 11,869 ms). Both retry
results exactly reused the committed draft. Earlier conservative vocabulary
rejections and one short-timeout failure used extraction successfully; only
grammatical/discourse vocabulary and the separate agent request timeout changed.
The other three roles have mocked/offline coverage, not a claimed live sweep.

## Deliberate limits

No real detectors, open-ended patient chat, institutional authorization, real
wearables, production deployment claims or automatic sharing. Question ranking
is a proposed list, not wired to authorize new interruptions. REESTABLISHING
exit, context governance and clinical wording/resource review remain open.
The agent operates on bounded facts, not a complete clinical chart or a claim
of exhaustive review. Additional synthetic data and CodeBuddy remain deferred.
