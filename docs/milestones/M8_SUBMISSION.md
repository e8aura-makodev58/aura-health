# M8 — Submission and Final Freeze

Status: PLANNED. Target: 2026-10-13 through 2026-10-15. Deadline: 2026-10-16.

## Goal

Submit a coherent, reproducible project without last-minute architectural risk. No major new feature starts in M8.

## Required submission items (from the hackathon brief, §8)

The brief says projects without CodeBuddy/WorkBuddy proof **do not proceed to scoring**. Submit via the link in the brief (§10, Step 4).

| Item | Status in brief | Requirement |
|---|---|---|
| Project title | Required | `aura-health` (user decision, 2026-09-23). |
| Short blurb | Required | Hard limit: **under 10 words**. |
| Project description | Required | Four parts: (1) overview: target scenarios, users, value proposition; (2) real-world insight: source of pain points, audience, core problems; (3) solution design: business and technical architecture, **and how prompts drive the AI generation**; (4) business value: **quantifiable metrics** or clearly defined impact. |
| CodeBuddy/WorkBuddy conversation history | Required | **At least 3 screenshots or a screen recording of chat logs** from CodeBuddy/WorkBuddy during development. |
| Cover image | Required | **16:9**, recommended 380×216 px, for the online showcase. |
| Demo video | Optional | 5–8 min: project overview, core agent features and usage, and a short reflection on the build approach with CodeBuddy/WorkBuddy tips. |
| Project link | Optional, **earns bonus points** | **We will submit one** (user decision, 2026-09-24): the live hosted demo URL from M7. Verify it works and resets on the day of submission. |
| Challenge-statement items | Per healthcare track | Demo walkthrough (live), architecture + trust-boundary diagram with key design trade-offs, full source on GitHub. |

Before freezing, check the submission against the ten judging dimensions (brief §11, 10 points each): Impact & Relevance, Human-Centered Design, AI Interaction, Technical Execution, Feasibility, Demo & Storytelling, Innovation & Creativity, UX & Accessibility, Responsible AI & Ethics, Overall Quality.

## Deliverables

- **Repository:** clean README, setup, architecture, intended use/limitations, demo instructions, tests, screenshots, source, and license/attribution as required.
- **Trust-boundary diagram:** patient/UI, application backend, deterministic longitudinal and safety engines, bounded AI, persistence, Simulation Data Agent/evaluation plane, and any actual external services.
- **Demo:** finalize [`docs/DEMO_SCRIPT.md`](../DEMO_SCRIPT.md), walkthrough/video/material, and reproducible setup.
- **Claims review:** never claim diagnosis, relapse prediction/prevention, suicide-risk determination, clinical monitoring, medication changes, or continuous human watching when none exists. Prefer “identifies changes from your usual pattern,” “supports antidepressant maintenance/routines,” and “helps prepare for clinician review.”
- **Known limits:** disclose synthetic evaluation, no clinical validation, engineering thresholds, no emergency monitoring/autonomous notification, non-production auth, and limited/optional integrations where true.
- **CodeBuddy/WorkBuddy:** include genuine contemporaneous M5–M7 evidence; never fabricate retrospective proof.
- **Final testing:** full automated suite, Cases A–F, UI, no-live-LLM fallback, and clean-checkout documented setup.
- **Submission text:** title, sub-10-word blurb, and the four-part project description above (including how prompts drive AI generation and quantified process metrics), plus safety/governance, limitations, and future work.
- **Cover image:** 16:9 (380×216 px recommended).

After final acceptance identify/tag final commit, avoid unreviewed features, and permit only critical bug/documentation fixes. Complete when package/demo/diagram/claims/evidence/tests/source are ready and pushed by 2026-10-15.
