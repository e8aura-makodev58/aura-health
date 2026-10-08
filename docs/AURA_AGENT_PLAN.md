# aura-agent — role, boundary and scaffold plan

2026-10-07. **Original planning by Claude. User approved implementation on
2026-10-07 by asking Codex to build aura-agent and its skills.** Live OpenAI
GPT-6 Luna connectivity was separately approved/verified before this work.
Implementation and scoped deviations: `docs/AURA_AGENT_IMPLEMENTATION.md`.
The historical proposal below is retained; no-key claims are superseded.

## 1. Why this is needed

User direction (2026-10-07): the application must be **agentic**, "that is the whole
point". The patient main page is now so simple that it offers no high-level insight.
Today the only model use is `aura_communication`: it *selects one of a finite set of
approved wordings*. That is phrasing, not agency. A reviewer reading the app today sees
a deterministic rules engine with a decorative LLM.

Framework line 464 says: *Signals propose. Rules dispose. The LLM phrases.* Making the
product agentic changes the third clause. **This is a framework-level decision for the
user** (proposed text: *"The agent synthesizes, investigates read-only and drafts; it
never disposes."*). Safety policy §35 already permits bounded generation in NORMAL,
CLARIFY (policy-defined questions only), ELEVATED, and validated URGENT; none in
IMMEDIATE, degraded or client-offline. The agent inherits those limits unchanged.

## 2. The dividing line: who decides, who proposes

| Question | Deterministic engines (unchanged) | aura-agent |
|---|---|---|
| Is this a safety event? What tier/state? | **Decides** | Never involved; never sees held/unassessed text |
| Did a signal drift? Is the baseline trusted? Move an anchor? | **Decides** | Reads the result only |
| Is context credible / does it clear a signal? | **Decides** (explicit association only) | May *ask* the patient a question; cannot judge |
| Interrupt the patient now? | **Decides** (communication engine) | May rank *approved* question intents; cannot create one |
| Share with a clinician? | Patient approval only | May *draft* the note; cannot send |
| **Make sense of months of multi-signal data in plain language** | Cannot | **Does** |
| **Choose what is worth a GP's 5 minutes** | Cannot (no judgment) | **Proposes**, with citations |
| **Answer "why did my sleep chart change?"** | Cannot | **Investigates** with read tools, cites sources |
| **Draft the appointment note / pre-visit brief** | Cannot | **Drafts**; human approves |
| **Notice what is missing or worth asking about** | Rule-based gaps only | **Proposes** questions from the approved intent set |

One sentence: **the engines decide what is true and what is safe; the agent decides
what is worth saying about it, to whom, and finds the evidence for it.**

## 3. Agent roles (each is a bounded task with a typed output)

All roles are read-only against the record and return structured claims, never state
changes. Patient-facing roles are available on demand or via the existing communication
trigger; none sends unprompted messages.

1. **Clinician brief** (primary, clinician view). Input: committed facts for a window.
   Output: ≤3 "what changed / when" findings, each with `fact_ids`, plus 1–3 "worth
   asking the patient about". This is the clinician workspace headline.
2. **Record Q&A** (clinician and patient, on demand). Multi-step tool use over read-only
   tools: "When did sleep timing start drifting?", "Was an illness recorded then?",
   "Show gaps in the last month". Answers cite sources; may answer "not in the record".
3. **Patient insight** (patient main page). A one-to-two-sentence, non-alarming
   "your month at a glance" built from the same facts (framework §31 allows a quiet
   monthly recap). Descriptive only; no scores; hidden when nothing noteworthy.
4. **Visit prep** (patient). Drafts the appointment note in sentences and proposes which
   items to include; the patient edits/removes. Stays **Not sent** until a persisted
   approval workflow exists (currently a documented gap).
5. **Question ranker** (existing communication path). Chooses among *authorized* question
   intents/candidates given history. Extends today's candidate selection; does not
   author new clinical questions.

Deliberately **not** agent roles: safety detection, safety wording in T3/T4, tier
decisions, anchor changes, adherence judgments, treatment suggestions, diagnosis,
relapse prediction, context-credibility rulings.

## 4. Architecture

```text
role request ─▶ ModeGuard (reads committed safety state; blocks IMMEDIATE/degraded/offline,
                           held input, T3/T4 → static path only)
            ─▶ AgentRuntime  (step / token / time budget; loop: model ⇄ tools)
                  ├─ Tool registry: read-only, patient-scoped, role-scoped
                  ├─ Provider (see §5): real LLM *or* scripted offline agent
                  └─ Trace recorder (every prompt, tool call, result, output)
            ─▶ GroundingValidator (every claim → fact_ids; numbers/dates must appear
                                   in cited facts; prohibited-claims check)
            ─▶ validated structured output  OR  deterministic template fallback
            ─▶ UI (disclosure: "drafted by AURA's assistant from your record", plus
                   "show sources")
```

Design rules:

- **Tools are the only way to data.** Initial set, all wrappers over existing read
  methods: `get_status`, `get_timeline_window`, `get_series(signal, window)` (reuses
  `aura_app/evidence.py`), `get_context`, `get_decisions`, `get_review_snapshot`,
  `get_gaps`. No write tools exist in the registry at all. A write would be a separate
  command the *user* confirms through the existing API, never an agent tool.
- **Patient text is data, not instructions.** Notes the patient wrote enter prompts only
  as quoted, delimited data after the safety gate, and only when the gate resolved them
  (never held input). Prompt-injection tests are mandatory.
- **Structured claims, not free prose.** The model returns `[{type, text, fact_ids}]`.
  The validator rejects any claim whose numbers/dates/signals are absent from the cited
  facts, any diagnosis/prediction/treatment/"normal range" language, and any claim without
  a citation. Failure → fixed deterministic text (today's Case-B-style template).
- **Hidden truth never enters.** Simulation ground truth and `useful-interruption`
  windows stay outside tool scope (extends M7's isolation test).
- **Full audit trace** per run in a new append-only table (`agent_runs`); the schema
  claim "DB schema unchanged" must be consciously relaxed for this table only.
- **Same deterministic answer with the model off.** Every role has a template fallback
  that produces the same *structure* from the same facts. The agent adds fluency,
  prioritization and investigation; the product never depends on it for safety.

## 5. Working without an API key (scaffold now, plug in later)

Add a `ScriptedAgentProvider` that implements the same tool-calling interface with a
fixed, inspectable plan per role (e.g., Clinician brief = call `get_status`, `get_series`
for each signal, `get_context`, then fill a template). It makes the whole pipeline —
tools, guard, validator, trace, UI — real and testable today, and the UI labels it
**"Offline rule-based assistant — no language model connected"**. When the operator saves
a key in the existing gear dialog, the live provider (existing OpenRouter/OpenAI/
DeepSeek/Tencent transports in `aura_communication/vendor.py`, extended with a
tool-calling method) replaces it with no change to tools, guard or validator. Do not
describe the scripted provider as AI in any UI or submission text.

## 6. Scaffold layout (spec for Codex)

```text
aura_agent/
  roles.py        # AgentRole enum + per-role task spec, output schema, allowed tools
  schemas.py      # Claim, Finding, BriefOutput, QAAnswer, VisitNoteDraft (strict)
  tools.py        # ToolSpec + registry; wrappers over existing read services only
  guard.py        # ModeGuard: safety-state/tier/held/offline gating (fail closed)
  grounding.py    # claim→fact validation, prohibited-language check, fallback choice
  runtime.py      # bounded loop, budgets, provider abstraction, trace hooks
  providers.py    # ScriptedAgentProvider; adapter to existing vendor transports
  templates.py    # deterministic fallbacks for every role
  evaluation.py   # fixtures: grounded/ungrounded/injection/forbidden-claim cases
aura_app/agent.py # service: assemble context, call runtime, persist trace, expose API
                  # POST /patients/{id}/agent/{role}  (read-only; role-checked)
tests/test_agent_*.py
```

UI additions (after the above passes): clinician brief headline + "Ask about this
record" box with source chips; patient "Your month at a glance" card (see §7); the
disclosure line and "show sources" on every agent output.

## 7. Patient main page: restore high-level insight (revises my earlier advice)

My earlier recommendation (HANDOVER, 2026-10-07) pushed the patient surface to near
nothing; the user is right that it now carries no insight. Revised default, still
consistent with framework §29/§31:

- Status line unchanged ("No question from AURA right now").
- **"Your month at a glance"**: four small own-reference mini-charts (sleep timing,
  sleep duration, activity, resting HR — dots/lines, no good/bad colour, no score) plus
  the agent's one or two sentences, e.g. "Your sleep has been later than usual since
  mid-September; you noted travel on 14 Sept." Tapping opens the full data view that
  already exists (patient entitlement).
- Shown as a recap, not a daily task: no required action, no streaks, can be collapsed
  and remembered as collapsed. Hidden entirely if there is nothing noteworthy.
- Safety panel and resources unchanged and independent.

## 8. Acceptance criteria (informal; not clinical validation)

- With no key, every role works end-to-end via the scripted provider and says so.
- No write tool exists; a test enumerates the registry and fails if one is added.
- Every agent claim has `fact_ids`; fabricated numbers/dates are rejected (test set).
- Held/unassessed input, T3/T4, degraded and offline produce **zero** provider calls.
- Prompt-injection notes ("ignore your rules…") cannot change tools, output schema or
  claims; covered by fixtures.
- Hidden-truth isolation test passes for the agent context.
- Agent outputs contain no diagnosis, prediction, treatment advice, "normal range",
  risk label or score (scan + fixtures).
- Same facts with model on vs off yield the same set of cited facts for the brief
  headline (model may reorder/phrase, not drop required findings: validator checks
  that all engine-flagged retained drifts appear).
- Disclosure and "show sources" present on every output; trace viewable by operator.

## 9. Open decisions for the user

1. **Approve the framework change** from "LLM phrases" to "agent synthesizes and
   investigates read-only, never disposes" (and record it as a DECISIONS entry).
2. Approve the five roles; cut any. Suggested priority: Clinician brief → Record Q&A →
   Patient insight → Visit prep → Question ranker.
3. Approve the new `agent_runs` trace table (only schema change).
4. Operator supplies a key/model later through the gear dialog; synthetic data only.

## 10. Risks and honest limits

- Without a real model the "agentic" behaviour is scripted; do not claim otherwise.
- Grounding validation cannot prove clinical correctness, only that claims match cited
  facts and avoid prohibited forms; clinical content/wording still needs human review.
- Open-ended Q&A on patient questions runs through the safety gate; free text remains
  fixture/held in the hosted demo until real detectors exist, so patient Q&A in the demo
  should accept chosen question templates plus the clinician-style record queries only on
  already-resolved data.
- Deadline 2026-10-16 (M8 window 13–15 Oct): build order should be runtime + tools +
  scripted provider + clinician brief first; the rest only if time remains.
