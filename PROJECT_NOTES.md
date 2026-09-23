# Health track brainstorm checkpoint

## Agreed direction

- Brainstorm a project for the healthcare track in the local hackathon brief.
- Ground proposals in the brief's actual health challenge statements and example scenarios.
- Prefer AI that supports home care using objective measurements and trends, with less reliance on subjective symptom conversations.
- Avoid presenting the project as a diagnostic tool.
- Avoid both false reassurance and escalation for every isolated or noisy reading.
- We are still choosing an idea; no implementation has been selected.

## Brief requirements

The healthcare track offers two case studies. Each team selects one:

1. **AI Grandma Knows Best:** self-triage and care navigation. Examples: fever in a child aged 6–36 months; adult COVID-19 symptoms. The brief asks for conversational assessment, care navigation, warning-sign detection, abstention when uncertain, self-management support, dynamic reassessment, and personalization.
2. **AI Healthier Every Day:** long-term care. Examples: antidepressant maintenance, type 2 diabetes self-care, and hypertension management. The brief asks for medication understanding and adherence support, health tracking, preventive care, and preparation for healthcare visits. It explicitly says the solution should not cross from explanation into medication advice.

The examples are illustrative; alternative approaches that address the chosen challenge are encouraged. The submission requires a demo, architecture diagram, source code, and proof of CodeBuddy or WorkBuddy use.

## Ideas discussed

- **CareLoop:** basic hypertension tracking and reminders. Rejected as too simple and low-variance.
- **Living Triage:** longitudinal symptom navigation. Interesting, but relies heavily on subjective reports and consequential care-level decisions; not the favored direction.
- **Glucose Pattern Coach:** analyze glucose or CGM, meals, and activity to explain recurring patterns and prepare clinician questions. Fits the brief's type 2 diabetes example, but market research showed that existing products already provide much of this.
- **Heart Failure Home Monitor:** use daily weight, blood pressure, and heart rate against a pre-existing care plan. Objective and dynamic, but it is an alternative to the brief's named scenarios.
- **BP Evidence Coach:** assess measurement quality and repeated BP trends against a clinician-set target. More substantial than reminders, but may still feel too narrow.

## Reference leads checked

- [Singapore ACE hypertension guideline](https://www.ace-hta.gov.sg/healthcare-professionals/acg/hypertension---tailoring-the-management-plan-to-optimise-blood-pressure-control-acg/) supports home BP monitoring and trend review.
- [HealthHub heart failure weight and BP monitoring](https://www.healthhub.sg/health-conditions/heart-failure-monitoring-weight-and-blood-pressure) gives home measurement methods and a care-team contact trigger.
- [ADA CGM and time in range](https://diabetes.org/about-diabetes/devices-technology/cgm-time-in-range) explains glucose trend review and individualized targets.
- [PhysioNet CGMacros](https://www.physionet.org/content/cgmacros/1.0.0/) is an open demo dataset with CGM, meals, and activity from 45 participants, including 14 with type 2 diabetes. It is small and short-duration.

## Design principle to carry forward

Use graded responses based on signal quality, persistence, and the person's existing care plan. Treat isolated noisy measurements differently from sustained patterns. Keep any urgent triggers explicit and source-backed. Do not suggest independent medication changes.

## Emerging concept: home care plan companion

The clinician defines the care plan. AI translates its instructions into patient-friendly steps, schedules, and measurable checks, then uses home data to show whether the plan is being carried out and whether the patient's measurements are changing. It identifies unclear instructions for clinician clarification instead of inventing an interpretation.

Patient-facing feedback should explain the relevant plan instruction and the observed evidence. Clinician-facing feedback should distinguish a missed measurement, a patient-reported missed action, an uncertain observation, and a confirmed plan-defined threshold. A physiological reading alone does not prove medication adherence.

Notification timing should be part of the clinician-approved plan: immediate for specified high-priority conditions, otherwise a concise routine summary. Patient consent and visibility into what is shared are part of the design.

## Guardrails and fallback (emerging requirement)

- AI may draft structured instructions from clinician documents and explain approved instructions, but a clinician must confirm any extracted monitoring schedule, target, threshold, or escalation action before it becomes active.
- Each active rule should preserve the exact source passage, author/approver, effective date, units, time window, and action. A deterministic evaluator should apply the approved rules to validated readings.
- Distinguish measured, patient-reported, missing, conflicting, and technically unavailable data. Never infer medication adherence from physiological readings alone.
- If an instruction is ambiguous, contradictory, superseded, or unsupported by the available data, mark only that decision as unresolved; ask for clarification or route it to the responsible clinician. Continue unaffected parts of the plan.
- If a monitoring or messaging service fails, show that monitoring is unavailable and use the clinician-approved fallback contact instructions. Do not imply a care team is watching a dashboard continuously unless that service exists.
- Test extraction and judgment with boundary values, unit mismatches, poor OCR, conflicting plan versions, missing readings, sensor anomalies, and after-hours/no-acknowledgement cases.

Singapore's [MOH AIHGle 2.0 overview](https://www.moh.gov.sg/others/health-regulation/emerging-regulatory-policy-issues/) emphasizes clinician accountability, transparency, and risk assessment. The project's guardrails should be presented as concrete design choices, not as proof of clinical suitability.

## Market check (19 September 2026)

- Basic glucose/BP tracking, trends, pattern reports, alerts, reminders, and sharing are already offered by Dexcom Clarity, Abbott Libre, and Omron Connect. A standalone tracker or generic pattern coach is unlikely to be differentiated.
- More promising project territory: connect objective home readings to a *clinician-authored, patient-specific care plan*; distinguish unreliable readings from persistent changes; provide the smallest appropriate next step; and create an evidence-backed handoff to the care team.
- A remote-monitoring study identified high alert volume and alert fatigue as real workflow problems. This supports making alert usefulness measurable, rather than merely adding more alerts.
- Treat this as a potential gap to validate, not a claim that no existing product addresses it.

Sources: [Dexcom Clarity](https://www.dexcom.com/en-us/clarity), [Abbott Libre reports](https://www.freestyle.abbott/us-en/libre-living/spotting-glucose-trends.html), [Omron Connect](https://omronhealthcare.com/omron-connect-app), [remote-monitoring alert study](https://pmc.ncbi.nlm.nih.gov/articles/PMC12206671/).
