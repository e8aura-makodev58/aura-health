# Critique: "Care Plan Bridge" product framework

> **Superseded (2026-09-23):** Care Plan Bridge was dropped. The project is **aura-health**; see [`aura_health_framework_v1.0.md`](aura_health_framework_v1.0.md). Kept for background only.

**Reviewer:** Claude (Opus 5) · **Date:** 19 September 2026
**Target:** [`PRODUCT_FRAMEWORK.md`](PRODUCT_FRAMEWORK.md) (concept draft, 19 Sept 2026), read against [`PROJECT_NOTES.md`](PROJECT_NOTES.md) and the text of [`AI_CAN_DO_IT_Hackathon_Singapore_2026_Brief.pdf`](AI_CAN_DO_IT_Hackathon_Singapore_2026_Brief.pdf).

Written in response to the copy-ready critique request in §19. I have tried to keep factual corrections separate from design opinions, and to flag anything I could not verify in this session.

---

## 0. Summary verdict

This is an unusually disciplined safety document and a weak product document. Its reasoning about evidence, provenance and failure is better than most production clinical software. But it is a **risk register wearing the costume of a product spec**: across 20 sections and ~340 lines it accumulates 18 explicitly open questions (8 in §18, 10 in §19) and resolves none of them, 27 days before the 16 October submission deadline.

Three problems are load-bearing, in descending order of severity:

1. **The brief asks for a patient-facing prototype. The framework designs a clinician-gated workflow** where nothing reaches the patient until a clinician approves it. This is not a tuning issue; it is the architecture.
2. **The framework's central safety claim is circular.** "AI is safe because a clinician approved every rule" — but the clinician approves AI-extracted candidates, the clinician in the demo is simulated, and nothing in the design counters automation bias. The control the entire architecture rests on is the one control that is never tested.
3. **The design minimises AI on purpose, and the rubric scores AI depth out of 10.** §19 Q8 notices this risk and the document then supplies no answer to it.

There is a good project in here. It needs someone to make about six decisions and delete about half the scope.

---

## 1. What the framework gets right

Stating this properly, because the rest of this document is negative and the good parts are genuinely good and genuinely rare.

- **§5.3 "Observation is not inference"** — "No BP uploaded" ≠ "BP was not measured"; "high glucose" ≠ "medicine was missed." Most real products collapse exactly this distinction. It is the single best idea in the document.
- **Three-valued logic where `unknown` cannot be coerced to false** (§10). Correct, and almost always got wrong.
- **Separating `generated` / `delivered` / `acknowledged`** (§9 `Notification`, §11). "Never show 'clinician notified' until delivery is confirmed" is the detail that would make a clinician judge sit up. Keep it in the demo; it is worth more than any chart.
- **Refusing to let a generic guideline override a patient-specific plan** (§4). Subtle, correct, and counterintuitive to most engineers.
- **§5.4 localised uncertainty** — one ambiguous instruction pauses one rule, not the plan. Right call, and it is what makes the clinician gate survivable at all.
- **Build sequence putting gold-standard expected outcomes *before* any AI** (§16). This is the correct order and most teams get it backwards.
- **Honest scoping of CGMacros and of the regulatory position** (§15, §4). The document does not oversell, anywhere.

On the rubric's **Responsible AI & Ethics** dimension, as written, this is probably a 9–10. That is one dimension out of ten.

---

## 2. The central misalignment: a two-sided product for a one-sided brief

The challenge statement says, verbatim:

> "Build a **patient-facing prototype** that brings together medication management, health monitoring and preventive care to provide personalised, practical support."

The framework's §7A makes the clinician the first actor and the gating actor: clinician uploads → AI drafts → validator checks → **clinician approves** → plan becomes active → patient finally sees something. §5.1 elevates this to the first product principle. §13 gives the clinician a full second application (review console + inbox + pre-visit summary generator).

Consequences the document does not address:

- **Cold start.** The patient-facing app is empty and inert until a clinician does unpaid setup work. There is no designed path for a patient who opens the app today.
- **The demo's first two minutes belong to the wrong user.** §17 spends steps 1 and (partly) 6 in the clinician console. On **Human-Centered Design** and **UX & Accessibility** (20 points combined), judges will be watching for the patient.
- **Two apps in 27 days.** See §8 below.
- **It contradicts the brief's "Empowering" quality** — "help patients take greater ownership of their health rather than simply issue reminders." Care Plan Bridge's stance toward the patient is structurally *"your clinician said X, and you may ask why."* The patient cannot set a goal, adjust anything meaningful, or act on their own data. The word "empower" does not appear in the framework; §12's best offer is "the app explains what it noticed and what it shared." That is transparency, not ownership. The framework mistakes *not being paternalistic* for *being empowering*; it achieves the first and not the second.

**This is fixable without abandoning the thesis.** Invert the entry point: the *patient* (or caregiver) uploads the discharge note or medication list they already have. AI structures it. The patient gets immediate value — plain-language explanation, a schedule, a question list — from *unapproved, clearly-labelled* content, because explanation of a document the patient already possesses is not a clinical decision. The clinician gate then applies only to the narrow set of things that genuinely need it: **thresholds, escalation triggers, and contact routes**. Everything else flows day one.

That change keeps every safety property in §5, keeps the clinician gate as the differentiator, satisfies "patient-facing prototype," and removes the cold start. I think it is the highest-value single edit to the document.

---

## 3. Scored against the actual rubric

The brief's Demo Day rubric is ten dimensions at 10 points each (preliminary track criteria are released after registration and may differ — **worth chasing**, since they govern whether you reach Demo Day at all). Predicted performance of the framework *as written*:

| Dimension | Predicted | Why |
|---|---|---|
| Responsible AI & Ethics | **9–10** | The document's whole centre of gravity. |
| Technical Execution | 7–8 | Strong design; heavy risk of being judged on an incomplete build. |
| Impact & Relevance | 6–7 | Real problem, but the value claim is hedged into invisibility. |
| Human-Centered Design | 5–6 | Designed clinician-first; patient is a recipient. |
| Feasibility | 5–6 | "Realistic and scalable beyond the hackathon" — the clinician-approval workflow is a genuine adoption barrier and the doc knows it (§18 rows 2–3). |
| UX & Accessibility | 5–6 | §12 is one paragraph of good intentions; no flows, no screens, no accessibility specifics beyond "large text." |
| **AI Interaction** | **4–5** | See below. |
| **Innovation & Creativity** | **4–5** | See below. |
| **Demo & Storytelling** | **4–5** | See below. |
| Overall Quality | 6–7 | |

### AI Interaction (10 pts) — "quality and depth of AI usage"

The framework's architecture is a deliberate campaign to *remove* AI from every consequential path. §8's trust boundaries: "extracted rules are drafts; only approved plan records enter the evaluator; **LLM output is display text, not an executable instruction**." §7.B.4: a **deterministic** evaluator does the actual work. §7.B.5: AI "cannot recalculate thresholds or select a new action."

Every one of those decisions is correct for safety. Together they mean a judge assessing *depth of AI usage* sees: **a document parser and a template renderer.** §19 Q8 asks "can we show enough AI depth through extraction, clarification, and explanation?" — and the document never answers its own question, nor does §16's MVP add anything that would.

The answer exists and should be written down: **the AI depth is in adversarial self-limitation, and it has to be made visible.** Concretely —

- **Ambiguity and conflict detection as the headline AI capability, not a validator footnote.** Detecting that "check sugars regularly" is unschedulable, that two documents disagree, that a threshold is missing its unit, that an instruction is internally contradictory — that is hard NLP over messy real text and it is the thing the product is actually *for*. Right now it is buried in §7A.3 as "a schema validator."
- **Show calibration.** Run extraction over the annotated corpus live, or pre-recorded, and display where the model said *"I cannot structure this"* versus where a human agreed it was unstructurable. A confusion matrix of *abstention* is a far more interesting AI artifact than a chatbot.
- **Show the injection defence working.** §10 lists prompt injection in an uploaded document. Actually put a malicious instruction in demo document #2 and show it being neutralised and surfaced for review. That is a memorable 20 seconds and scores on two dimensions at once.
- **Grounded explanation with refusal.** The brief explicitly wants "Honest about uncertainty — able to say *'I'm not able to identify that medication, please check with your pharmacist.'*" Demo the refusal, not just the explanation.

Reframe the pitch from "we use AI carefully" to **"we use AI for the part that is genuinely hard — understanding ambiguous clinical prose — and we refuse to use it for the part that is easy to fake."** Same architecture, +3 points.

### Innovation & Creativity (10 pts)

"Structured extraction → human approval → deterministic rule engine → typed events → routed notifications" describes clinical decision support systems going back decades. §2 is admirably honest that the differentiation is "proposed, not a claim that no competitor has it" — but honesty about weak novelty does not make it novel. The genuinely fresh ideas in the document are the *provenance and abstention* semantics (§5.3, §5.4, three-valued logic, generated/delivered/acknowledged). Lead with those. They are unusual and defensible.

### Demo & Storytelling (10 pts)

Count the arc of §17: of seven beats, **four are the system declining to act** (ambiguity → withheld; poor-quality reading → not evaluated; missing reading → asks a question; outage → shows fallback). Two more are administrative (plan setup, plan revision). One beat is the payoff.

Rigour is not narrative. A demo whose emotional shape is *"and correctly, nothing happened"* is a hard sell in 5–8 minutes. Restructure around a **single patient across time** with a visible stake, and make the refusals *tension* rather than *content*: the system withholds, withholds, withholds — and then the moment a clinician-approved condition is genuinely met, it fires with a complete evidence packet and the clinician acts in one click. The restraint earns the payoff instead of replacing it.

Also: the submission requires a **Short blurb, hard limit under 10 words**, and Project Description bullets including **"Business Value: quantifiable metrics or clearly defined impact."** The framework's §1 one-liner is 13 words, and §15 conscientiously refuses to claim outcomes. That refusal is intellectually right and will read as an empty field on the form. Resolve it by quantifying **process**, not outcome — see §10 below.

---

## 4. Answering §19 Q4: where AI still makes clinical decisions

The framework asks this about itself and does not answer. It should, because a skeptical clinician reviewer will find these in about ten minutes, and the document is far stronger if it names them first.

1. **Extraction is interpretation, and approval only ratifies it.** Deciding that *"check your BP twice a day if you're not feeling well"* becomes `schedule: BID, condition: symptomatic` is a clinical judgment. The clinician sees a plausible structured object next to the source text and clicks approve. The judgment was made by the model; the human supplied authority, not analysis.

2. **Deciding what counts as ambiguous is itself a clinical judgment — and it is unguarded.** §10's entire guardrail table is organised around *detected* failures. The dangerous case is the opposite: **confidently wrong extraction.** The model believes it understood, raises no flag, presents a clean candidate, and the reviewer agrees. There is no control for this anywhere in the document. Every safety property in §5 is downstream of a flag that was never raised.

3. **The quality gate can suppress an urgent reading before any rule sees it.** §7.B.3 validates "identity, units, device status, staleness, duplicates, expected timing, and any plan-specific technique requirements," and only §7.B.4 then evaluates rules. §5.5 promises "high-priority conditions are not delayed for statistical smoothing" — but smoothing is not the threat. **Exclusion is.** A genuinely alarming reading that arrives with a device warning, an odd timestamp, or a technique-requirement miss is dropped, and the patient receives "this reading cannot be compared with your plan yet" (§11, patient-only channel). That is the **most dangerous false-reassurance path in the whole design**, it is created by a safety mechanism, and neither §10's failure table nor §15.3's test matrix covers it.
   *Fix:* quality gating must be **asymmetric**. A reading that fails quality checks but would have crossed a plan-defined urgent threshold *had it been valid* is never silently dropped — it produces a distinct event type (`urgent_unverified`) with its own clinician-approved action, and the patient-facing wording must not read as reassurance.

4. **`unknown` has no defined behaviour for urgent rules.** §10 correctly forbids `unknown → false`. It never says what `unknown` *does* when the rule in question is the high-priority one. Read literally, the design routes it to a patient-only "please repeat." Same hazard as (3); needs an explicit answer in the rule schema: every high-priority rule must declare its `on_unknown` action.

5. **Deduplication decides that two events are "the same."** §11 folds repeat reports of an unresolved condition into one case. Whether today's reading is "the same" as yesterday's or a deterioration is a clinical judgment being made by grouping logic. Preserve and *display* each new observation inside the case, and let worsening break the dedup.

6. **Sustained silence is routed as low priority.** §4 rightly forbids treating missing data as evidence the patient is well. But §11's channel table sends "repeated missing measurements" to the **scheduled summary**. For a patient whose plan exists *because* they are at risk, extended silence is a signal, not an absence of one. Needs a clinician-approved **silence threshold** with its own escalation. The word "silence" does not appear in the document.

---

## 5. The clinician gate is untested, and the evaluation plan assumes clinicians you do not have

§7A concedes: "For a hackathon MVP, clinician review can use a simulated clinician account." Then §15.2 proposes to "measure whether reviewers can spot injected errors, undefined units, contradictory schedules, and wrong routes before activation," §15.5 proposes a patient usability study, §15.6 a clinician workload comparison, and §18 proposes clinician interviews, role mapping in a pilot service, and pharmacist testing of medication explanations.

**If the clinician is simulated, the safety guarantee is simulated.** And §15.2/§15.5/§15.6/§18 all require human subjects that the project has no stated plan, budget or time to recruit in 27 days. The evaluation section is currently aspirational in a way that the rest of the document is scrupulously careful not to be — which is odd, because it is the section a judge scoring **Feasibility** will read most literally.

Two things follow:

- **Say plainly what is and is not tested.** "The approval control is demonstrated, not validated; validating it requires N clinician reviewers and is the first post-hackathon step." One honest sentence beats seven unrunnable studies.
- **Design against automation bias now, because you cannot test for it.** §10's first row — "show source image and extracted text side by side" — is precisely the design pattern that performs *worst* against automation bias, since approving requires no cognitive work beyond a plausibility glance. Cheap countermeasures that fit in the build:
  - **Force manual entry of high-risk fields.** Numeric thresholds, doses, units and escalation routes are typed by the reviewer, never pre-filled. The model's proposal is shown only *after* entry, as a diff.
  - **Rank the queue by extraction risk** so the reviewer's attention goes where it is needed rather than top-to-bottom.
  - **Make approval granular and costly in proportion to consequence** — one click for a patient-facing explanation, explicit confirmation for anything that can page a human.
  - **Log approval dwell time** and surface implausibly fast approvals in the audit trail.

  These are a day of work, they are genuinely novel in the demo, and they turn "we have a human in the loop" into "we have *evidence* the human was actually in the loop." That is a Responsible-AI story with teeth.

---

## 6. Coverage gaps against the brief's stated features

The challenge statement lists six features. Checked against the framework:

| Brief feature | Framework coverage | Assessment |
|---|---|---|
| Medication understanding | §12, §18 | Partial — deliberately constrained to approved text and reviewed templates. Defensible; verify it still satisfies "explain what medications are for." |
| Medication management | §16.3 | Thin — self-reported confirmation only. |
| Adherence support ("identifying barriers to adherence") | §6, §12, §17.4 | **Good.** The barrier-not-violation framing is on point and should be foregrounded. |
| Health tracking | §7B, §9 | **Strong.** |
| **Preventive health** ("screening, vaccination, lifestyle or follow-up needs") | **Absent** | "preventive" appears once, in §2, restating the brief. "screening" and "vaccination": **zero occurrences.** Not in §4 intended use, not in §16 MVP scope. |
| Healthcare preparation | §13 pre-visit summary | **Good** — but the brief says "doctor **or pharmacist**," and the pharmacist appears once in the whole document (§18) and not at all in the §3 role table. |

The preventive-health gap is a flat miss against an explicitly enumerated requirement, and it is not a hard one to close. A clinician-authored plan naturally contains dated follow-up items — HbA1c review, retinal screening, foot check, vaccination, appointment, prescription refill. Those are *already* plan instructions with schedules; the existing evaluator handles them with **no new machinery**, and they are the cheapest possible source of positive, non-alarming patient-facing content — which is exactly what §17's demo arc is starving for. This is the rare case of a scope *addition* that reduces risk and improves the demo.

The framework also never engages with the brief's "**Personalised** — adapt recommendations to the user's conditions, medications, goals and circumstances." Care Plan Bridge personalises to the *clinician's plan*, which is a different thing. The patient's goals and circumstances have no representation in the data model (§9). Even a single `PatientPreference` / `PatientGoal` record, influencing reminder timing and framing without touching clinical content, would close this and costs almost nothing. §16's "later possibilities" already gestures at it — pull it forward.

---

## 7. Competitive analysis is aimed at the wrong shelf

§2 and §20 benchmark against **Dexcom Clarity, Abbott Libre, Omron Connect** — consumer device dashboards. But the framework's claimed differentiation is *clinician-authored plan → home data → evidence-backed clinician handoff*, and none of those three products compete in that space at all. Beating them is not evidence of anything; they are not playing.

The real comparison set is remote patient monitoring and chronic-care-management platforms, and EHR-embedded care-plan tooling. **I have not browsed to verify the following and it should be checked before it goes in a submission**, but from prior knowledge the relevant names are roughly: EHR-embedded care plans and patient-companion modules from the major EHR vendors; RPM/CCM vendors such as Cadence, Huma, Biofourmis, Withings Health Solutions; and patient-communication/care-pathway tools such as Twistle.

Most importantly for a Singapore hackathon judged by Singapore clinicians: **Healthier SG**. As I understand it, that is a national programme in which an enrolled resident's family doctor develops a personalised health plan with them, delivered alongside HealthHub — which is, at the level of the one-line pitch, the same sentence as "turn the care plan you already have into clear home steps." A framework claiming this differentiation in Singapore that mentions MOH's AI guidelines and HSA's device guidance but **never mentions Healthier SG** has a conspicuous blind spot, and a local judge will notice it immediately.

This does not kill the idea. The honest and much stronger positioning is: *these programmes produce plans; they do not make the plan **executable** against home measurements with provenance and abstention semantics.* But you have to say that out loud, name the programme, and be ready for the follow-up question. **Action: verify Healthier SG's current care-plan capabilities before submission and add a §20 entry.**

---

## 8. Feasibility: 27 days

Today is 19 September. Submission closes **16 October 2026**. That is 27 days, and the framework contains **no timeline, no team size, no hours budget, and no cut list** — "deadline," "16 Oct" and "team size" appear zero times.

What §16's "minimum compelling prototype" actually enumerates: two front-ends (patient app + clinician console), a document ingestion and OCR path, an LLM extraction pipeline with source-span linking, a schema and conflict validator, a granular approval workflow, a versioned plan store with predecessor/reconciliation semantics, a typed rule DSL with units and intervals, a deterministic evaluator with three-valued logic, an observation quality-check layer, a grounded explanation service with output validation, a notification router with priority/service-hours/dedup/retry/fallback, a delivery-and-acknowledgement state machine, an audit log, a replayable event log, and an expert-annotated evaluation corpus with a test matrix. Plus §15's three human-subject studies.

That is a quarter of work for a funded team. §19 Q10 asks "what should be cut from the MVP to make the core loop reliably demonstrable?" — **this is the single most important question in the document and it is addressed to someone else.** Deferring the descope decision to an external reviewer at T-27 is the framework's most consequential failure as a working document.

A proposed answer is in §11 below.

### Submission mechanics that are missing entirely

Not product design, but they gate scoring and they consume calendar days:

- **CodeBuddy/WorkBuddy proof is mandatory: minimum 3 chat screenshots or a screen recording. "Without proof, the project will not proceed to scoring."** §2 mentions this in one clause and calls it "separate from our product architecture." True — and it is a *hard gate*, and the artifacts must be captured **while building**, not reconstructed on 15 October. This belongs as a standing item in §16's build sequence.
- **Short blurb: hard limit under 10 words.** The current one-liner (§1) is 15 words.
- **16:9 cover image** (≈380×216), required.
- **Demo video 5–8 min** — listed optional in the general submission table, but the healthcare challenge statement separately requires a "Demo Walkthrough — a live demonstration." Reconcile; `PROJECT_NOTES.md` currently states flatly that a demo is required, which is true of the track and not of the general table.
- **Project link (live URL): optional, earns bonus points.** Free points; deploy something.
- **Architecture Diagram: the track asks for "architecture, trust-boundary diagram, key design trade-offs."** §8 has trust boundaries as *prose beneath* the diagram and trade-offs scattered across §18. **Draw the trust boundaries into the diagram itself and write the trade-offs as an explicit list.** This is a direct, literal rubric item, currently half-met, and it is maybe an hour of work.
- **Naming.** The repo is `aura-health`; the product is "Care Plan Bridge." Project title is a required field — pick one.

---

## 9. The evaluation plan tests the wrong things at the wrong cost

- **CGMacros is scope with no payoff.** §15 proposes the PhysioNet CGMacros dataset, then immediately concedes it "cannot validate this workflow" because it contains no care plans. Correct — and the product's two testable claims are *extraction accuracy* and *rule-execution correctness*, for which CGMacros contains exactly nothing. It buys cosmetic realism in exchange for a real ingestion path, a licence review (§15 flags this), and days you do not have. **Cut it.** Synthetic streams with deliberately injected quality defects are cheaper, fully controllable, and directly targeted at what you actually need to demonstrate. (The brief suggests MIMIC-III or Kaggle as options, not requirements.)
- **§15.3's release gate is well-framed** — "zero unsupported rule activations in the curated test suite is a release gate for the demo, not evidence of clinical safety." Keep that sentence verbatim; it is the single most credible line in the evaluation section.
- **The test matrix is missing its two most dangerous cases**, both identified in §4 above: (a) a quality-failed reading that would have crossed an urgent threshold, and (b) a high-priority rule evaluating to `unknown`. Both are false-reassurance paths manufactured by safety mechanisms. Add them.
- **And the most likely real-world failure is missing from §10 entirely:** *the uploaded document contains no thresholds, no escalation route, and no monitoring schedule.* Most discharge notes and medication lists in the wild are exactly that. The framework's §10 table covers OCR errors, vague frequencies, and document conflicts — all cases where there is *something* to extract. It never handles the modal case where extraction yields almost nothing approvable and the product therefore has no content. That is not an edge case; for the average patient it is the default, and it is a direct threat to the **Feasibility** score.

---

## 10. Quantifying value without claiming outcomes

The framework's epistemic discipline (§15's "What this does not prove") collides with the submission's required "Business Value: quantifiable metrics or clearly defined impact." Both can be satisfied by quantifying **process fidelity** on a fixed synthetic corpus and being explicit that these are not clinical outcomes:

1. Alerts generated per patient-week, versus a threshold-only baseline evaluated on the same corpus.
2. Share of clinician alerts carrying a complete evidence chain (source span → rule → observations → evaluation).
3. Share of plan-defined urgent conditions detected at the **first** eligible evaluation.
4. False-escalation count on the corpus.
5. **Suppression audit: every plan-defined urgent condition that was *not* escalated, with its reason code.**

(5) is the one that does not currently exist anywhere in the framework, and it is the metric a patient-safety reviewer would most want to see. A system that reports its own near-misses is making a claim no competitor makes. It also directly instruments the hazard in §4.3.

§11's existing instinct — "measure alert volume and time spent per case so 'less overcautious' becomes testable rather than rhetorical" — is right. It just needs a defined baseline, and the baseline must not be a strawman "raw data view" (§15.6); it should be **the same rules with no quality gating, no dedup, and no abstention**, which is what a naive implementation would actually produce.

---

## 11. A concrete narrower MVP

Answering §19 Q10 and §18 row 1 rather than re-asking them.

**Pick hypertension only.** The brief explicitly permits it ("Teams may focus on a particular chronic condition"), and Scenario 3 is hypertension. BP is one numeric stream with a genuinely rich quality story — rest period, cuff position, repeat protocol, arm, post-exertion — which is *exactly* the framework's strongest material (§17.3). Glucose adds a second ingestion path, CGM-vs-fingerstick semantics, meal context, and the CGMacros dependency, for no additional narrative value. §18's first open question dissolves: **narrow it, today.**

**Keep, because it is the thesis:**
- Patient-first upload of a document the patient already has → AI structuring → immediate plain-language value, clearly labelled unapproved.
- Clinician gate narrowed to **thresholds, escalation triggers and contact routes only**, with forced manual entry of numeric fields.
- Typed rule schema; deterministic evaluator; three-valued logic with declared `on_unknown` per rule.
- Observation quality checks **with the asymmetric urgent-unverified path**.
- Evidence chain visible from every claim ("Why am I seeing this?").
- Generated / delivered / acknowledged, plus the outage fallback drill.
- Preventive/follow-up items as scheduled plan instructions — free positive content, reuses the evaluator, closes a brief requirement.
- Replayable event log. It makes the demo deterministic, which matters more than anything else on demo day.

**Cut or stub, explicitly and in writing:**
- Glucose/CGM and CGMacros entirely.
- Caregiver role (§3) — keep in the data model, no UI.
- Multilingual (§12) — the framework already gates it on reviewed translations; say "not in MVP."
- FHIR mapping (§8) — already labelled a design target; one paragraph in the submission, no code.
- Product-operator and administrator roles (§3) — configuration constants, not screens.
- Real dedup engine (§11) — one rule: same rule ID unresolved within N hours folds, and any *worsening* observation breaks the fold.
- All three human-subject studies (§15.5, §15.6, §18) — restate as post-hackathon, with N and method named so the intent is legible.
- Retry policies, service-hours calendars, backup routes (§10, §11) — one configured route plus one fallback; label the rest as designed-not-built.

**Suggested shape of the remaining time** (adjust to team size, which the framework should state):

- **Days 1–4:** Decide the six open items below. Write the two fictional documents (one with the deliberate ambiguity, one as the later revision, one carrying an injection payload). Write gold-standard expected outcomes *before* any code — §16's build sequence already says this and it is right.
- **Days 5–11:** Typed plan schema, versioning, deterministic evaluator, test matrix green. No AI yet.
- **Days 12–16:** Ingestion + quality checks, including the asymmetric urgent-unverified path.
- **Days 17–21:** AI extraction with source spans; ambiguity/conflict detection; grounded explanation with refusal; injection defence.
- **Days 22–24:** Notification router, delivery/ack states, outage drill, audit log.
- **Days 25–27:** Patient UI polish, accessibility pass, cover image, blurb, video, architecture + trust-boundary diagram, trade-offs list, CodeBuddy evidence assembly, deploy the live URL for bonus points.

Capture CodeBuddy/WorkBuddy chat logs continuously from day 1.

---

## 12. Six decisions to make this week

The framework's 18 open questions are mostly not blocking. These six are, and every one of them is answerable internally without a clinician interview:

1. **One condition or two?** (Recommend: hypertension only.)
2. **Does the patient get value before clinician approval?** (Recommend: yes, for explanation and scheduling; no, for thresholds and escalation.)
3. **What is the team size and weekly hours?** Everything above is unschedulable without it.
4. **What does a high-priority rule do when it evaluates to `unknown`?**
5. **What happens to a quality-failed reading that would have breached an urgent threshold?**
6. **What is the escalation behaviour on sustained silence?**

Items 4–6 are one-line additions to the rule schema and they close the three worst hazards in the design.

---

## 13. Smaller notes

- **§9's example rule contract is not executable, and it is the one place a reader looks for concreteness.** `"condition": "clinician_defined_persistent_pattern"` is a placeholder, and the text immediately admits it and adds that "a production design would prohibit free-text rule execution." Replace it with a real typed condition for one rule — operator, quantity, unit, interval, repeat count, `on_unknown`. Highest concretisation-per-line edit in the document.
- **§8's diagram has no edge for patient input back into the system.** §7B.5 and §17.4 both describe the patient answering clarification questions ("it was taken on another device"), and §9 has `ActionConfirmation`, but the flowchart shows only `U[Patient app]` as a sink. Add the return edge; a judge reading the architecture diagram will see a patient who cannot talk back.
- **§3's role table omits the pharmacist**, despite the brief naming pharmacists explicitly and §18 proposing pharmacist testing.
- **§11's "Open operational decisions"** (inbox owner, staffed hours, acknowledgement time, backup, unreachable patient) are correctly identified and then left open. For the hackathon, *invent* fictional answers and display them in the UI. An unanswered operational question reads as a hole; a fictional-but-specific answer reads as a design.
- **Hedging density.** Nearly every assertion is immediately retracted: "a proposed differentiation, not a claim"; "design inputs, not certification"; "a design target, not an MVP integration claim"; "not evidence of clinical safety"; "a potential gap to validate." Each is individually correct and the cumulative effect is that the document commits to nothing falsifiable. Keep the disclaimers in the places that matter for safety and regulatory claims (§4, §14, §15's "what this does not prove"); delete them from product and design choices, where they only signal that the decision has not been made.
- **§2's claim that the brief requires a live demo, architecture diagram and source code is accurate** — I verified it against the healthcare challenge statement, which also specifies a GitHub repository for the source code and asks the architecture diagram to include trust boundaries and key trade-offs.

---

## 14. What I verified, and what I did not

**Verified in-session** (text extracted from the bundled brief PDF): the two healthcare case studies and their three example scenarios; the six required solution features including preventive health; the "patient-facing prototype" wording; the "Empowering / Personalised / Longitudinal / Safe / Practical / Strictly bounded / Honest about uncertainty" qualities; the demo + architecture-diagram + source-code requirements and the trust-boundary/trade-offs wording; the mandatory CodeBuddy/WorkBuddy proof and the no-proof-no-scoring rule; the submission item list, the under-10-word blurb limit and the 16:9 cover image; the 16 October 2026 deadline and 3 November Demo Day; the ten 10-point judging dimensions; and that detailed preliminary track criteria are released only after registration. Also verified by inspection of `PRODUCT_FRAMEWORK.md`: zero occurrences of "screening," "vaccination," "empower," "Healthier SG," "team size," "deadline" or "silence"; one occurrence each of "preventive," "pharmacist" and "CodeBuddy."

**Not verified — check before relying on any of it:** the Healthier SG characterisation in §7 and the RPM/EHR competitor list, which come from prior knowledge and were not browsed in this session; the current contents of the external guideline and vendor links in `PRODUCT_FRAMEWORK.md` §20; the CGMacros licence terms; and my rubric-score predictions in §3, which are judgment, not fact. The preliminary judging criteria — the ones that actually determine whether the project reaches Demo Day — were not available to me and should be obtained from the organisers.
