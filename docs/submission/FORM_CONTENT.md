# Form copy — review before submission

Status: DRAFT. Copy only field contents, not headings/instructions. Pending links
must be replaced with actual approved viewer-accessible URLs before submission.

## Project Title

AURA Health

## Short Blurb

Personal health patterns, clearer conversations between appointments.

Word count: **7** (do not paste this count into the form).

## Project Description

### Project Overview: Target Scenarios, Users, and Value Proposition

**Healthcare track (NTU Lee Kong Chian School of Medicine), Challenge Statement 2
"AI Healthier Every Day", Scenario 1: Mental Health Maintenance for Working Adults
on Antidepressants.**

AURA Health is a calm, wearable-first companion that keeps the context between
clinician appointments. Our scenario is adults aged 25–60 on stable,
clinician-managed antidepressant maintenance treatment. Patients receive a simple, calm view of their recent
records, medication information, today's dose and upcoming review/refill dates;
clinicians can inspect personal patterns, context and source-linked
answers without starting from an undifferentiated dashboard.

The differentiator is a bounded record-investigation agent, not an unrestricted
chatbot. A clinician can ask whether activity changed before sleep timing,
compare recent periods, or examine weekday patterns. AURA-Agent chooses tools
and date windows, reads the results and drafts cited answers. Its investigation
trail makes those actions inspectable. A short patient recap offers everyday
wording, with measurements and sources available on demand.

### Real World Scenario Insights: Pain Points, Audience, and Core Problem

The design starts from a practical workflow problem: how can patients and
clinicians reconstruct what changed between visits, without making patients
continually assess themselves? Raw wearable readings, check-ins, medication
routine records and explanations can be difficult to relate chronologically.
A temporary illness may explain some physiological changes, while a gradually
adapting baseline may obscure a longer-running shift.

These pain points informed our product framework and synthetic scenarios; they
are design hypotheses, not claims from a completed patient study.

Against the challenge, AURA's strongest fit is health tracking over time, healthcare
preparation and being strictly bounded: it describes what changed and when against
the person's own baseline, helps the patient prepare for an appointment, and its
checks reject generated medication advice. The patient companion now provides curated
medication explanations, dose records with optional missed-dose reasons, stored
review/refill dates and optional everyday suggestions. Displayed dates are not push
reminders, and the prototype does not book appointments or order refills.
The scenario mentions flagging early signs of relapse. AURA deliberately stops at
describing changes the patient can choose to bring to their clinician, because
relapse prediction and treatment prescriptions require validation and sponsor
governance. Curated lifestyle choices remain optional, not prescribed care. AURA combines
wearable-style information with what the patient reports, treats missing data
as missing, and keeps a governed personal reference alongside a recent rolling
reference. An explanation can reduce repeated interruption without erasing
the observation or rewriting the reference.

### Comprehensive Solution Design: Business, Architecture, and Prompts

The patient experience is deliberately lightweight. The clinician experience
offers deeper analytics and question-directed investigation. Review information
can be prepared and inspected; it is not automatically transmitted.

Four patient-home cards connect daily self-care to that record: My medication,
Today's dose, Coming up, and A small idea for today. A read-only companion service
projects the prescribed schedule, latest dose report and seven-day routine counts,
estimated refill and configured medication-review dates, and optional curated
suggestions. Missing or unknown dose reports never become missed doses. Skipped-dose
reasons remain visible in appointment preparation. Medication answers come from a
small curated catalogue explicitly awaiting pharmacist review; unknown medicines
or topics abstain. Typed medication questions enter the safety boundary first;
an optional model may classify the question to a topic ID, but never generate
medication instructions. Safety blocks suppress ordinary companion content.

Python/FastAPI application services orchestrate two independent deterministic
engines: longitudinal baselines/context/communication and safety policy. They
persist events, decisions and audit records through repository interfaces using
SQLite for development/demo storage. The responsive web interface displays the
committed results rather than calculating policy itself.

Five versioned AURA-Agent skills support clinician briefing, record Q&A, patient
recap, visit preparation and approved-question ranking. Prompts define each
skill's goal, permitted evidence, read-only tools, output schema and language
constraints. For Q&A, the model chooses retrieval and descriptive-analysis tools
and their windows, then uses returned facts to compose cited claims. Deterministic
checks enforce source references, numbers, dates and structured findings; a
separate verifier model call checks support. Rejected or unavailable drafts use
labelled related facts instead. The model cannot change anchors, treatment or
safety state, and generation remains subject to current safety/online guards.

A separate demo life director translates requests such as a three-day flu into
structured synthetic plans. A seeded generator produces numerical observations;
hidden scenario truth is kept outside product decision inputs. The live model
is used only with synthetic data in this demonstration. Institutional on-premises
or private-cloud model hosting is an intended future deployment direction.

### Business Value: Engineering Evidence and Intended Impact

The intended value is less patient reporting burden and a clearer, evidence-linked
starting point for clinician conversations. We have not measured consultation
time savings, patient outcomes or financial return, and do not claim them.

Defined impact for a pilot (metrics we would measure with the sponsor; targets to be
agreed, not results): (1) patient effort — reporting actions per week and share of
weeks with no prompt at all; (2) clinician preparation — minutes to answer "what
changed and when" before a visit, against usual chart review; (3) appointment
readiness — share of visits with a patient-prepared note; (4) answer quality — share
of AI answers passing source checks, and clinician-rated usefulness; (5) safety —
every safety-relevant input reaches the deterministic safety path first.

The current Codex candidate passed **330 Python tests** on 13 October 2026
(`68372f3`; branch regression evidence, not final release certification).
Engineering evaluation covers six synthetic scenarios: physical illness, slow
drift, illness plus independent change, an explained persistent shift, a wearable
gap/return, and safety handoff. Automated regression tests cover deterministic
policy, longitudinal invariants, application transactions, source grounding,
tool isolation and patient/clinician presentation.

In a historical live DeepSeek headline trial on synthetic Case B, 19 of 20 clinician
headlines and 19 of 20 patient headlines passed the configured checks; two used
fallback. This measures that prompt version and fixture, not current Q&A reliability
or clinical effectiveness. The recorded HTTP preview p95 was 332–496 ms and generated
headline response p95 was 4.24–4.46 seconds, not screen-paint measurements.

Future product work includes consented real wearables, institutional identity and
privacy controls, durable patient-approved sharing, and governed follow-up
workflows. Clinical suitability and parameter/content review belong with the
sponsor. AURA does not diagnose depression, predict relapse, determine suicide
risk, prescribe or change treatment, provide psychotherapy, or operate as an
emergency monitoring service. The demo uses synthetic data and engineering
parameters and does not claim clinical validation.

## Project Web Link

https://aura-health.makodev58.com

## Demo Video Link

PENDING — record/upload the 5–8-minute video and replace this line with its URL.

## Source Code

https://github.com/e8aura-makodev58/aura-health

## Social Media Post Link — optional bonus

Leave blank unless the user authorizes and publishes a post. Required hashtags:
#WorkBuddy #CodeBuddy #Miora #TencentCloudHackathon

## File upload mapping — not form prose

- Cover Image: `assets/aura-cover.jpg` (1672×941, ~0.42 MB; the PNG original is 1.8 MB, over the stated 1 MB limit) — awaiting approval.
- Conversation History: `assets/development-history.pdf` — CodeBuddy transcript from the user's export plus 8 genuine screenshots; awaiting review.
- Architecture Diagram PPT: `assets/aura-health-deck.pptx` — 18 slides; slides 11–13 native diagrams with glued connectors; awaiting approval.
