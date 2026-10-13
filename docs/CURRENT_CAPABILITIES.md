# AURA Health — Current capabilities and agent contribution

Status: 2026-10-13. Code inspected at `be3e795`. This is a capability audit,
not a new feature specification or clinical-validation claim.

User direction: stop feature development; limit subsequent implementation to
bug fixes and minor updates. Distinguish the demo now from intended final-product
capabilities. Missing capabilities are not necessarily rejected product ideas.

## What the application is today

A synthetic-data technical prototype for longitudinal context around stable,
clinician-managed antidepressant maintenance. It has a simple patient view and
a deeper clinician inspection view of the same synthetic record. The demo toggle
is not clinician authorization or patient-approved sharing.

Deterministic engines retain personal anchored and rolling references, describe
changes, apply signal-linked context, retain explained changes for review, govern
communication and control safety state. A bounded model/tool layer investigates
records and phrases supported observations. These are separate responsibilities.

## Where aura-agent does substantive work

| Component | Model contribution today | Agentic characterization |
|---|---|---|
| Record Q&A | Chooses retrieval/analysis tools, signal/source keys and bounded date windows; reads returned results; composes cited answers | Strongest product agent: question-directed, multi-step, read-only investigation |
| Clinician brief / patient recap | Retrieves evidence under required-read rules, selects cited facts and phrases a short headline | Constrained agent loop; predominantly grounded selection/summarization, not autonomous analysis policy |
| Visit preparation | Retrieves evidence and drafts cited review claims; required history remains represented | Bounded read-only drafting; not a scheduling, sending or sharing agent |
| Question ranker | Selects/orders questions from an approved catalogue; quiet-state questions can be suppressed by the server | Limited prioritization, not an autonomous follow-up workflow |
| Independent verifier | A separate model invocation checks each draft claim against supplied facts | Generator/checker pattern, not a separate multi-step agent; not necessarily a different model/provider |
| Simulation life director | Converts a request into a constrained synthetic scenario plan | Demo/evaluation planning; not a product care agent or numeric-data generator |
| Semantic safety detector | Proposes a concern category from text; deterministic policy resolves state | Classifier, not agentic care or suicide-risk determination |
| Import/context proposal | Suggests a structured mapping or context association for human confirmation | Extraction/proposal, not autonomous ingestion or contextual judgment |

The Q&A tool set is `get_status`, `get_series`, `get_context`, `get_decisions`,
`get_review_snapshot`, `get_gaps`, `compare_windows`, `day_of_week` and
`summarize_gaps`. The model can choose later calls after seeing earlier outputs.
Default execution limits are eight model-loop steps, 24 tool calls and 50 seconds;
the verifier is a separate call. Tools enforce the selected patient's record,
source/metric separation, coverage requirements and allowed calendar window.

The model chooses the investigation; deterministic tools compute the descriptive
statistics. This division does not make the investigation non-agentic. What is
not justified is attributing baseline governance, change detection or safety
policy to the model.

Evidence: [roles](../aura_agent/roles.py), [runtime](../aura_agent/runtime.py),
[tools](../aura_agent/tools.py), [record Q&A skill](../aura_agent/skills/record_qa/SKILL.md),
[application boundary](../aura_app/agent.py).

## What works today, and what remains future product work

| Area | Implemented now | Intended direction / remaining work |
|---|---|---|
| Personal patterns | Anchored plus rolling references; descriptive drift, coverage and signal-linked context | Sponsor-reviewed parameters and validation using appropriate real-world data |
| Patient interaction | Check-ins, routine records, explanations, optional full data, short recap and patient questions | Longitudinal conversational continuity and governed clarification/follow-up workflows |
| Clinician assistance | Charts, sourced Q&A, structured review snapshot and printable/temporary review preparation | Authorized clinician workspace; approved, durable follow-up drafts and review workflow |
| Wearable information | Synthetic daily/nightly and sparse channels; manual/confirmed synthetic import paths | Consented real-device integrations and institution-governed ingestion |
| Safety | Deterministic state machine, pinned fixture resources, synthetic layered rule/model proposals, fail-closed guards | Reviewed resources/content and validated detector/governance arrangements; no emergency-monitoring claim |
| Agent continuity/actions | Patient-record context and durable run traces/cache; no multi-turn conversation or model write tools | Governed memory and clinician/patient-approved actions, subject to permissions and audit |
| Sharing and identity | Demo session isolation; review output is not automatically sent | Real authentication, reviewer authorization, patient approval and controlled sharing |
| Model hosting | Configurable live providers on synthetic data | Institutional on-premises or private-cloud model deployment with privacy/security governance |

Future directions are not delivered capabilities or permission for autonomous
treatment, unsolicited clinician messaging or unrestricted access. Exact workflows
and authorization still need design and sponsor review. Other-condition support
is an architectural aspiration, not implemented or validated coverage.

## Limits that should not become future-feature promises

AURA does not diagnose depression, predict relapse, determine suicide risk,
prescribe/change treatment, give tapering instructions, provide psychotherapy,
replace clinicians or operate as an emergency monitoring service. Those are
standing intended-use boundaries, not items waiting to be switched on.

## Confirmed bugs and narrow follow-ups

1. **Clinician question misattribution — highest priority.** `AgentService._execute`
   stores every free-form record question as `PATIENT_FREE_TEXT`, source
   `synthetic_patient_ui`, before running Q&A. It therefore enters the patient's
   timeline/safety processing and can later be retrieved as an assessed patient
   note. The UI sends no author distinction. Clinician investigation text must not
   be treated as patient testimony. A fix needs an explicit trusted actor/purpose
   boundary; merely renaming the source or skipping every free-text safety gate
   would be insufficient. Genuine patient text must retain safety-first routing.
2. **Q&A fallback presentation.** Non-patient fallback uses fact text verbatim,
   unlike the special patient recap. Status facts still include single-word
   `OBSERVED`/`TRUSTED`; some findings/timestamps remain technical. Existing
   clinician transformations do not cover every shape. Fix display wording while
   retaining exact values, units, dates, comparator and citations.
3. **Malformed tool calls.** Runtime directly indexes tool-function arguments.
   Missing fields can terminate a run and trigger fallback. Inspect the offending
   trace before selecting a narrowly bounded protocol fix; analysis arguments
   must never be invented and numeric/semantic validation must not be relaxed.
4. **Visible investigation trail.** Tool names/fact counts already appear under
   Technical details. The trace also contains selected windows and verifier counts.
   A short human-readable trail could expose genuine agent work without revealing
   hidden chain-of-thought or pretending fallback is a completed investigation.
5. **Demo story.** The older `DEMO_SCRIPT.md` lacks an explicit Q&A investigation
   moment. The newer `SUBMISSION_DRAFT.md` already includes one in its video outline.
   Align the final walkthrough around a real Q&A question, tool windows, checked
   answer and sources. Do not preselect successful evidence and call it reliability.

The model has no write tools, but the application wrapper currently has the
question-ingestion side effect above. Thus "the entire Q&A path is read-only"
would be inaccurate until that bug is resolved.

## Evidence and uncertainty

- Committed v9 headline trial: Case B clinician19/20 and patient19/20 validated;
  flu groups not measured following the user's scope reduction. This does not
  establish Q&A reliability or v10 reliability.
- Current code uses prompt `aura-agent-v10`. Do not present historical v9 numbers
  as a new v10 test.
- Opus's three live Q&A attempts were supplied by the user: one completed partial
  answer, one number-check fallback and one malformed-call failure. These are
  reviewer-reported observations, not independently reproduced measurements here.
  The exact rejected number/rounding cause is not established by the report.
- Existing AW4 tests intentionally prove safety-first behavior for a patient-like
  question, but do not prove separation of clinician questions from patient reports.
  A green suite can therefore coexist with this integration bug.
- No additional paid calls, runtime changes or deployment were made for this audit.
- Existing automated suite rerun: **292 tests PASS / 351.175 seconds** using
  `.venv/bin/python -m unittest discover -s tests -q`. This is offline engineering
  regression evidence, not proof of live Q&A completion or clinical suitability.

Suggested submission characterization: **A bounded record-investigation agent
chooses tools and comparison windows, uses deterministic analysis and produces
source-linked answers checked by an independent verifier. Separate deterministic
engines govern longitudinal state and safety.**
