# M7 — Demo and Integration

Status: PLANNED. Target: complete by 2026-10-12.

## Goal

Make AURA reproducible and convincing under real demo conditions. Prefer integration/evidence over feature count.

## End-to-end path

Cases A–F should run synthetic input → backend → longitudinal/safety engines → approved AI phrasing where allowed → patient UI → timeline/review snapshot. Demo reset must be deterministic.

## Simulation Data Agent

This development/evaluation-only agent translates high-level scenario ideas into structured scenario specifications: baseline characteristics, timeline length, events/signal changes, missingness, check-ins, contexts, explanations, safety fixtures, and seed. A deterministic fixed-seed simulator then generates numeric timelines. The agent never manipulates production decisions.

## Mandatory ground-truth isolation

Add an explicit integration/property test that scenario ID, latent truth, expected outcome, useful-interruption windows, and synthetic labels cannot reach application decision inputs. Only observable/patient-reported events cross the simulation boundary. M3/M4 fixtures appear to keep hidden truth out of production calls, but the explicit isolation test is future M7 work, not an already accepted M4 test.

## Adversarial combinations

Test illness plus worsening check-in plus missing wearable; benign schedule change followed by new signal; long gap with stable self-report; contradictory sensor/self-report; figurative language; detector/service failure; stale/replayed events; invalid/timeout LLM output; and held drift reopened by new evidence. These are engineering tests, not clinical validation.

## Architecture and reliability

Create submission-ready trust-boundary diagram with patient UI, API, longitudinal/safety engines, bounded AI, persistence, simulation/evaluation plane, and optional integrations. Show no Simulation Data Agent production decision path.

Provide fixed demo seed, fixture reset, one-command backend/frontend starts, health check, model-unavailable deterministic fallbacks, and an offline demo option where practical. Measure enough startup, API/LLM latency, history-replay cost, and reset time to prevent demo failure; do not over-optimize.

Address or explicitly defer routine T0/null snapshot reference filtering, undefined governed REESTABLISHING exit, non-production reviewer authorization, and replay-per-event scaling. Do not invent clinical policy to close these.

## Live hosted demo (required)

The user decided on 2026-09-24 that there will be a live demo; the brief awards bonus points for a live link. Deploy the patient UI and backend to a public URL. Requirements:
- synthetic data only
- deterministic reset to the fixed demo dataset
- no real patient data or sign-up
- the model API key is held server-side only
- the prototype/limitations notice is visible
- deterministic fallbacks work if the model is unavailable

Record the URL, host, and redeploy steps in `HANDOVER.md`. Choosing the hosting provider is still open (see `HANDOVER.md`).

## Stretch

Only after the stable hosted demo, consider Garmin/other connector, hosted production database, or another model provider. Integrations must preserve accepted interfaces.

## Acceptance and stop condition

Use a nonconflicting test prefix such as `DEMO1` (D1–D6 already names detector interfaces). Require the live hosted demo reachable at its public URL with reset working, A–F visible end-to-end, hidden-truth isolation, no-live-LLM and invalid-output fallbacks, reset/replay, accurate architecture diagram, no UI policy computation, and genuine CodeBuddy/WorkBuddy M7 evidence. Stop when the system demonstrates from beginning to end without manual database surgery or hidden policy logic.
