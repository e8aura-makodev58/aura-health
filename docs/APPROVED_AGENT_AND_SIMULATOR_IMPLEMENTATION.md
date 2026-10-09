# Approved agent, intake and life simulator implementation

Implemented 2026-10-09 for DECISIONS §§39–41. Synthetic engineering demonstration;
Claude/user implementation review remains separate from implementation. Accepted
`aura_safety` and `aura_longitudinal` algorithms were not changed this session.

## Delivered features

| Capability | Implementation |
|---|---|
| Readable assessment | Five v2 skills; headline, source-linked claims, sections and approved questions. No lexical vocabulary whitelist. |
| Grounding | Exact finding signal/direction/since, numeric/date/category/citation/prohibited-claim checks, then a separate model entailment verifier. Unsupported claims are removed; required history restored as labelled extraction. Fully invalid drafts use extraction. |
| Investigation | Nine scoped read tools, batch calls, deterministic window comparison, weekday statistics and calendar gap summaries. |
| Free-form Q&A | Persisted safety-gated question before generation. Held content excluded; current unsafe/degraded/offline state blocks general generation. |
| Disclaimer | One `#disclaimer` page (`#about` compatible); Demo, AI/source, Offline extraction and Not sent chips; pinned safety unchanged. |
| Provider visibility | Public provider/model/status in gear before unlock; keys/settings remain protected. |
| Manual entry | Exact registry units/date; omitted fields stay missing; ordinary source-labelled events through production service. |
| CSV/JSON import | Model mapping proposal, editable preview, explicit confirmation, deterministic atomic batch. No automatic conversion/filling. |
| Context | Safety-gated explanation, proposed category/signal links, explicit confirmation through existing context/held logic. No automatic credibility or anchor change. |
| Safety gate | Demo-only curated D2 OR semantic D4 proposals. Accepted engine alone commits safety; semantic failure preserves stronger rules and holds input degraded. |
| Visit pack | Structured review plus optional removable agent draft, browser Print/Save PDF, Not sent. No automatic transmission or persisted sharing approval. |
| Life simulator | Model selects bounded life plan; seeded generator owns numbers. Guide-only controls, manual entry alongside, optional feedback and after-input assessment. |
| Trace/replay | Append-only workflow records, exact retries, stored seed/config/profile/plan, deterministic regeneration and committed-event hash check, zero replay writes. |

## Boundaries

```text
Patient text/question → curated + semantic proposals → aura_safety
  → assessed input only if current policy permits → read tools → checked draft
  → separate verifier → race check → persisted agent run → UI

Demo request → life director → strict LifePlan → seeded generator
  → observable events ONLY → PatientEventService → accepted engines/persistence

Manual/import/confirmed context → PatientEventService → accepted engines/persistence
```

No agent write, shell, sharing, network-search or clinical-policy tool exists.
Analysis reads an immutable patient/source/metric-scoped projection; it does not
create drift or interruption policy. Vendor strict mode is not assumed: local
argument validation remains authoritative. Rejected reads return no facts.
Model-facing event references are opaque; UI citations retain real source links.
Historic held input does not block an otherwise permitted whole-record brief,
but its content never enters the model. Ordinary non-demo APIs do not acquire
a live detector/agent implicitly.

The verifier receives both prose and structured engine finding/analysis fields.
It is a second model call, **not an independent clinical reviewer**.
It can err; deterministic checks and source inspection remain necessary. No
synthetic, grounding or adversarial test proves clinical safety.

## Intake, storage and transactions

Model calls run outside DB transactions. Proposals do not ingest measurements.
Confirmations compare record/safety/registry fingerprints; stale proposals reject.
All batch events use existing `PatientEventService`/anchor commands under one
shared repository transaction. Any invalid later row rolls the entire batch back.
Safety failures commit held input and the accepted degraded state, not normal
agent content. If curated concern already exists, its upgrade precedes the
degraded overlay in the same atomic transaction/audit.

CSV/JSON: 1–60 consistent rows, at most 20 columns, ISO `YYYY-MM-DD`, UTC demo
interpretation, exact registry units (activity: steps), no guessed conversions.
Missing cells omitted. Sleep needs midpoint and duration because the accepted
entity requires start/end; midpoint is minutes since sleep-start-day midnight,
possibly above 1440 for overnight sleep. Manual, import, confirmed patient context
and simulator sources remain distinguishable.

Additive `workflow_runs`: PK `(patient_id, run_id)`, patient FK, kind/timestamp/typed
trace JSON, no-update/no-delete triggers. Kinds distinguish proposals,
confirmations, manual entry and simulator runs. This supplies the plan's
simulator-run interface in one shared workflow table, not another literal
`simulator_runs` table. `agent_runs` remains separate. Same run/options reuse
committed results; changed options conflict; stale state discards generated drafts.

## Simulator

Strict plan: 1–30 days/advance, ≤8 life events, ≤30 feedback entries, known enums,
one feedback/day. Seven events: FLU, TRAVEL, WORK_STRESS, ALCOHOL,
MISSED_MEDICATION, WEARABLE_OFF, EXERCISE. Model output contains no telemetry,
arbitrary self-harm prose, policy state or expected outcomes. Invalid/unavailable
planning uses honest `OFFLINE_KEYWORD_PLAN`.

Configured effects/ramps/noise/clamps/profile/durations and two-day recovery tail
are engineering fixtures, not measured physiology. Recent recovery carries across
separate advances. BP Mon/Thu/Sat, weight Mondays, SpO₂ omits Wednesdays,
thermometer during flu and short recovery checks. Wearable-off omits wearable
values; manual/cuff channels may remain. No interpolation/missing-to-zero.
Missed medication has **no modeled physiological effect**.

New enabled HRV/respiratory/skin channels receive 28 synthetic reference days and
explicit provisional/trust commands with `synthetic-fixture-review-v1`. Existing
four anchors remain unchanged. This is transparent fixture governance, not an
automatic rewrite from evaluated drift. Sparse-channel calendar coverage remains
governed by the accepted registry foundation.

Feedback off omits check-ins, routine and notes. Enabled note themes become fixed
patient-reported strings and use the same safety gate, never an allowlist bypass.
Hidden FLU/event labels never automatically apply context or clear a whole record.
Plans/truth stay in workflow traces; decision payloads contain observable events
only. Production event/safety/longitudinal code never receives expected outcomes
or useful-interruption windows. AW13 and existing DEMO16 cover isolation.

Replay regenerates numeric rows and verifies all committed observable-event
hashes, without model calls or writes. It does not claim deterministic detector
or model behavior, nor replace the existing domain-policy replay harness.

## Configuration and budgets

All defaults below are engineering parameters requiring sponsor review where relevant.

| Path / override | Purpose |
|---|---|
| `aura_longitudinal/signal_registry.json` / `AURA_SIGNAL_REGISTRY` | Accepted channels, engine/display flags and baseline/drift settings; unchanged this session. |
| `aura_detectors/engineering_policy.json` / `AURA_DETECTOR_POLICY` | Curated patterns and semantic proposals; unvalidated. |
| `aura_simulation/life_effects.json` / `AURA_LIFE_EFFECTS` | Synthetic effects/recovery/profile and 90-day/30-run persisted session budget. |
| `aura_agent/questions.json` / `AURA_AGENT_QUESTIONS` | Existing intent IDs and editable question wording. |
| `aura_app/context_guard.json` / `AURA_CONTEXT_GUARD` | Known risk terms that cannot be benign-cleared; not credibility validation. |
| `AURA_SAFETY_RESOURCES` | Version/date/resources through accepted registry; invalid live lookup keeps built-in fixture fallback. |
| `AURA_POLICY_QUESTION` | Question ID/goal/variants/review provenance through existing wording contract. |
| `aura_agent/engineering_config.json` | 8 steps, 24 calls total, 12/batch, 50s overall, 15s/request, 90k prompt characters. |

Docker passes override paths; operator mounts reviewed files inside container,
e.g. `/data`. This is not a public clinical settings editor or reviewer authorization.
Tool results ≤24k characters; draft ≤16 claims (600 characters, 24 citations),
≤3 approved questions; patient recap ≤2 claims. Provider budget remains shared
10/minute and 60/hour. Live failure/budget exhaustion uses labelled extraction;
safety evaluation failure remains fail-closed rather than ordinary fallback.

## Usage

In full data, expand **Record or import measurements**. CSV/JSON → propose mapping
→ inspect/edit → confirm import. **Add a contextual explanation** similarly
proposes then confirms explicit signal links. Record Q&A supports a free question.
Gear exposes provider/model before unlock; Demo opens Disclaimer.

In **Demo guide**, select a quick event or describe life events, choose seed and
feedback, then Advance 1/3/7 days. Inspect/save trace and verify replay. Optional
AI refresh follows explicit commits, never page load or view toggle. Review's
**Print / save visit pack** creates a local browser PDF; Not sent.

Routes: `POST /patients/{id}/workflows/{action}` (UUID run_id/data; manual,
import-proposal, import-confirm, context-proposal, context-confirm, advance);
`GET /patients/{id}/workflow-runs/{run_id}`;
`GET /patients/{id}/simulator-runs/{run_id}/replay`. Existing agent route additionally
accepts record_qa `question`, mutually exclusive with canned `query_id`.

```sh
.venv/bin/python -m unittest discover -s tests -q
.venv/bin/python -m unittest tests.test_agent tests.test_approved_workflows -q
.venv/bin/python tests/browser/run.py --hosted --suite workflows.cjs agent.cjs settings.cjs dual_view.cjs
# Explicit authorized paid synthetic smoke; never reads keys:
.venv/bin/python scripts/live_agent_smoke.py --confirm-live-synthetic-checks \
  --base https://aura-health.makodev58.com --output /tmp/aura-live-agent-sweep.json
```

AW1–AW27 cover verifier, scoped/batched reads, safety precedence/OR/failure,
intake idempotency/atomic rollback, units/stale proposals, context/held/anchors,
seed/sparse cadence/no drug physiology/gaps, strict plans/isolation/demo boundary,
append-only reload, fallback, polarity, JSON contract, feedback/budgets and
cross-advance recovery, structured verifier evidence and claim-level rejection
without loss of required findings and no empty recap from an unread record.
Final automated/live results are recorded in HANDOVER.

Final automated suite: **238 PASS** (332.120 s). Hosted browser workflows 5 PASS,
agent 5 PASS, dual view 12 PASS and settings PASS at 320/390/1280. Public A–F
status/evidence/timeline/review and cross-session isolation/exact manual retry PASS,
no paid calls in that probe. Accepted domain files/dependencies unchanged.

2026-10-09 live DeepSeek sweep: clinician brief and record Q&A retained checked
model claims after per-claim rejection; visit draft and free-question response used
extraction after schema/finding rejection. Import mapping was model-proposed and
life director returned a validated three-day flu plan; replay matched all 37
committed events and three generated days, zero writes. Every skill retry reused
the exact committed draft. Earlier in this session a patient recap returned two
verified claims; a later empty/unread recap exposed a gap now blocked by AW27.
Question ranking exercised the model but quiet-state output remained empty.
These mixed results are not advertised as five reliable generated clinical answers.

Limits: detector false positives/negatives and verifier quality; context credibility;
clinical parameters/content/resources; governed REESTABLISHING exit; reviewer
authorization; production auth/sharing; cross-worker paid-call deduplication;
history replay cost; hosted session lifecycle/durable offline storage. No real
wearables, psychotherapy, diagnosis, relapse prediction, clinician transmission
or CodeBuddy. Later asynchronous §§42–43 directions are separate, not silently
treated as implementation authorization here.
