# Architecture Diagram PPT — authoring source

Healthcare Challenge Statement 2 — "AI Healthier Every Day: Intelligent Support
for Long-Term Self-Care", Scenario1 — "Mental Health Maintenance for Working Adults
on Antidepressants". Name this chosen case at the opening of the presentation.

Produce **one actual PPTX under 10 MB**, proposed path
`assets/aura-health-deck.pptx`. This outline is not the required upload.
The same deck serves the presentation and required Architecture Diagram PPT;
do not produce a competing upload deck. Three slide-image pairs are available in
`../presentation/diagrams/` (system overview, agent investigation, safety precedence).
Use 16:9 slides, large text, dark ink on warm off-white and the AURA accent palette.
Export and inspect every slide; verify shapes/arrows/fonts remain readable.

2026-10-14 audit against `90e31ea`: [ARCHITECTURE_REVIEW.md](ARCHITECTURE_REVIEW.md).
Current diagrams are native editable shapes from
`../presentation/deck/native_diagrams.py`, on slides 11–13 of the actual deck.
The user's five-page architecture PDF has a corrected reference export at
`assets/aura-health-architecture-reviewed.pdf`; it is not a second required upload.

## Slide 1 — AURA: context between appointments

Subtitle: “Bounded record investigation; deterministic product policy.”

- Patient: quiet recap, medication information, dose/reasons, coming-up dates,
  optional suggestions, structured input and optional data inspection.
- Clinician demo: longitudinal charts, source-linked questions and review preparation.
- Intended use: stable clinician-managed antidepressant maintenance; demo synthetic-only.
- Not a diagnosis/relapse-prediction or treatment-changing system.

## Slide 2 — System and trust boundaries

Render `architecture.mmd` and simplify layout, not policy. Preserve these boundaries:

1. Patient/clinician demo UI — display and transport, not domain decisions.
2. FastAPI/application services — consent, idempotency, transactions and orchestration.
3. Deterministic longitudinal and safety components — authoritative state/policy.
4. AURA-Agent/model tools — bounded investigation, no write tools.
5. Repository interfaces/development SQLite — event history, outputs and audits.
6. Separate simulation/evaluation plane — only observable inputs cross; hidden truth does not.
7. Separate pinned resource/fallback path — outside generated text.
8. Read-only `GET /companion` projection and curated medication/suggestion content;
   typed `POST /medication/ask` questions go through patient safety first. The model
   selects a topic ID only; answers are curated, not generated treatment advice.

Show the actual live model provider as a configurable synthetic-data dependency,
not Tencent-hosted institutional infrastructure. Current site is Docker on the
development server through Cloudflare; Tencent mirror/on-prem/private-cloud are
future options, not shipped hosting claims.

## Slide 3 — What makes the agent agentic

Draw a bounded loop:

Question → choose read/analysis tools and windows → receive exact facts →
choose next tools or finish → draft cited claims → structural/numeric checks →
independent verifier → fresh-state guard → displayed answer/labelled fallback.

Default 8 model-loop steps/24 model-selected tool calls; verifier separate. The
90-second loop budget is checked between calls, with a 30-second provider timeout;
do not promise every HTTP answer finishes within 90 seconds. Show native scoped
tools: series, context, gaps, check-ins/routine, review items, window comparison,
weekday patterns. Stats are deterministic; the model chooses the investigation.
The visible trail reports actions/outcomes, not hidden chain-of-thought.

## Slide 4 — Governance is part of the product

- Anchored reference moves only via explicit commands; rolling reference adapts.
- Explained changes remain available for review; unrelated evidence stays active.
- Missing data stays missing; sensing and reference trust are orthogonal.
- Patient input remains safety-first; clinician questions are not patient reports.
- Safety outranks ordinary wording; generated text never owns safety transitions.
- Demo role toggle/caller actor are not production identity/authorization.
- Review preparation is Not sent; no autonomous clinician messaging or treatment action.

## Slide 5 — Evidence, trade-offs and final-product direction

- Six synthetic cases plus engineering regression tests; add the final release
  test count/version from `EVIDENCE_LEDGER.md`, never a stale count.
- Historical v9 Case B headlines 19/20 per role; not current Q&A/clinical validation.
- Trade-offs: deterministic state plus flexible language; quiet patient surface
  plus deep clinician inspection; strict checks plus honest fallback; isolated
  demo workspaces plus replaceable development persistence.
- Future: real consented wearables, institutional authentication/private deployment,
  sponsor-reviewed parameters/resources and patient-approved sharing/follow-ups.
- Clinical suitability remains for the sponsor to assess.

Presenter notes should name sources/versions and limitations. Do not add unmeasured
time savings, accuracy/suicide-risk claims, real patient data or provider credentials.

The companion is integrated in `f37af0c`: routine/review projection, curated
medication lookup/topic selection and optional curated suggestions. Re-render the
deck's system-overview slide from the shared native diagram source. Counts and
curated lookup are not autonomous agent actions. Content needs pharmacist review;
displayed dates do not imply push notifications or a booked appointment. Keep the
agentic Q&A loop distinct from these features.
