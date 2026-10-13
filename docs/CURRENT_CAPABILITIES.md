# AURA Health — Current capabilities and agent contribution

Status: 2026-10-13. Updated against integrated `f37af0c` (original audit `be3e795`). This is a capability audit,
not a new feature specification or clinical-validation claim.

The user reopened scope for the patient companion, now integrated and deployed.
Distinguish this synthetic demo from intended final-product capabilities. Missing
capabilities are not necessarily rejected product ideas. The earlier bugs-only
freeze is not a statement that the companion remains future work.

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
| Medication question classification | Deterministic topic matching or optional model selection of an approved topic ID after patient safety processing; answer always curated | Classification, not an agent-generated medication answer |
| Patient companion | Projects dose reports, reasons and dates; selects curated optional suggestions from committed changes | Deterministic application/content work, not autonomous agent actions |

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
| Medication understanding | Curated information for Sertraline, Escitalopram and Fluoxetine (purpose, how to take, missed dose, side effects, alcohol); stored prescription displayed; unknown medication/topic abstains | Pharmacist-reviewed content, broader catalogue and institutional content governance |
| Medication routine/barriers | Taken / Not yet / Skipped; optional categorical skipped-dose reason; latest-report seven-day counts and Not-shared review items | Push reminders, multiple medications/doses and governed barrier follow-up |
| Coming-up dates | Stored medication review and estimated refill dates | Notifications, booking and refill ordering; no booked appointment is inferred |
| Everyday suggestions | Optional curated choices selected from existing descriptive changes; hidden when safety blocks | Sponsor content review and evaluated usefulness; not treatment prescription or clinical prevention claims |
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

## Fixed findings and remaining narrow issues

- Clinician questions now have explicit attribution and do not enter patient
  testimony/safety processing. Patient-authored questions remain safety-first.
  Demo caller attribution is not production authorization.
- Q&A fallback selects related facts by whole-word topic, including routine and
  held items; unrelated questions produce no unrelated evidence. Visible trail
  includes actual reads/windows and the verification or fallback outcome.
- Clinician numbers/dates remain exact. Internal unit names are simplified, but
  raw stored precision can still be unwieldy; no rounding is accepted as a new fact.
- Missing zero-argument tool arguments can be normalized narrowly; malformed
  analysis arguments can still fail. No windows or statistics may be invented.
- Post-flu Q&A completion is not established by the historical headline trial.
  New diagnostics and any narrow fix are recorded in the submission evidence ledger.
- Reused medication-question run IDs with changed text have a separately reproduced
  safety-assessment identity gap; it remains an open review item, not a safe API
  behavior to rely on. Normal UI requests use fresh IDs.

The Q&A agent's tools are read-only. Patient question ingestion and run/audit
persistence are application side effects. The medication companion and curated
lookup are not additional autonomous agent skills.

## Evidence and uncertainty

- Committed v9 headline trial: Case B clinician19/20 and patient19/20 validated;
  flu groups not measured following the user's scope reduction. This does not
  establish Q&A reliability or current prompt reliability.
- Current prompt is `aura-agent-v11`. Do not present historical v9 numbers as a
  current Q&A gate.
- Opus's three live Q&A attempts were supplied by the user: one completed partial
  answer, one number-check fallback and one malformed-call failure. These are
  reviewer-reported observations, not independently reproduced measurements here.
  The exact rejected number/rounding cause is not established by the report.
- Companion candidate `495087d` passed327 Python tests and18 selected browser
  checks. That is historical candidate evidence, not certification of newer code.
  Latest release checks and bounded live diagnostics are in
  [EVIDENCE_LEDGER.md](submission/EVIDENCE_LEDGER.md). No deployment is performed
  by this documentation/QA task.

Suggested submission characterization: **A bounded record-investigation agent
chooses tools and comparison windows, uses deterministic analysis and produces
source-linked answers checked by an independent verifier. Separate deterministic
engines govern longitudinal state and safety.**
