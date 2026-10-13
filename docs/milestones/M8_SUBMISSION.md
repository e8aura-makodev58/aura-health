# M8 — Submission and Final Freeze

Status: PREPARATION ACTIVE (user-authorized 2026-10-13), not complete.
Target: 2026-10-13 through 2026-10-15. Deadline: 2026-10-16.
Canonical package: [`docs/submission/README.md`](../submission/README.md).
Packaging authorization does not retrospectively accept all M7 review gates.

## Goal

Submit a coherent, reproducible project without last-minute architectural risk. No major new feature starts in M8.

## Required submission items (current form supplied 2026-10-13)

Use the user's current form requirements captured in
[`REQUIREMENTS.md`](../submission/REQUIREMENTS.md). They supersede the older
brief's optional video/live-link wording. The actual form URL has not been supplied.

| Item | Status in brief | Requirement |
|---|---|---|
| Project title | Required | `aura-health` (user decision, 2026-09-23). |
| Short blurb | Required | Hard limit: **under 10 words**. |
| Project description | Required | Four parts: (1) overview: target scenarios, users, value proposition; (2) real-world insight: source of pain points, audience, core problems; (3) solution design: business and technical architecture, **and how prompts drive the AI generation**; (4) business value: **quantifiable metrics** or clearly defined impact. |
| Development conversation history | Required | Chat history **and at least 3 screenshots** from CodeBuddy, WorkBuddy **or Miora** development; **one supported file ≤10MB**. |
| Cover image | Required | **16:9**, recommended 380×216 px; **one supported file ≤1MB**. |
| Demo video link | Required | **5–8 min**: overview, core agent features/use and reflection on build approach/tool tips. |
| Project web link | Required | Browser-accessible project experience; verify signed-out access/reset before submission. |
| Architecture Diagram PPT | Required | **One supported file ≤10MB**; actual PPT/PPTX, not only Markdown. |
| Source code | Required | GitHub repository URL. |
| Social Media Post Link | Optional bonus | Genuine published link with #WorkBuddy #CodeBuddy #Miora #TencentCloudHackathon. |

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
