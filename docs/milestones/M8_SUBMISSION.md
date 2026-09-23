# M8 — Submission and Final Freeze

Status: PLANNED. Target: 2026-10-13 through 2026-10-15. Deadline: 2026-10-16.

## Goal

Submit a coherent, reproducible project without last-minute architectural risk. No major new feature starts in M8.

## Deliverables

- **Repository:** clean README, setup, architecture, intended use/limitations, demo instructions, tests, screenshots, source, and license/attribution as required.
- **Trust-boundary diagram:** patient/UI, application backend, deterministic longitudinal and safety engines, bounded AI, persistence, Simulation Data Agent/evaluation plane, and any actual external services.
- **Demo:** finalize [`docs/DEMO_SCRIPT.md`](../DEMO_SCRIPT.md), walkthrough/video/material, and reproducible setup.
- **Claims review:** never claim diagnosis, relapse prediction/prevention, suicide-risk determination, clinical monitoring, medication changes, or continuous human watching when none exists. Prefer “identifies changes from your usual pattern,” “supports antidepressant maintenance/routines,” and “helps prepare for clinician review.”
- **Known limits:** disclose synthetic evaluation, no clinical validation, engineering thresholds, no emergency monitoring/autonomous notification, non-production auth, and limited/optional integrations where true.
- **CodeBuddy/WorkBuddy:** include genuine contemporaneous M5–M7 evidence; never fabricate retrospective proof.
- **Final testing:** full automated suite, Cases A–F, UI, no-live-LLM fallback, and clean-checkout documented setup.
- **Submission text:** project summary, problem, solution, differentiation, architecture, safety/governance, technology, limitations, and future work.

After final acceptance identify/tag final commit, avoid unreviewed features, and permit only critical bug/documentation fixes. Complete when package/demo/diagram/claims/evidence/tests/source are ready and pushed by 2026-10-15.
