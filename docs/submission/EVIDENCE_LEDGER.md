# Submission evidence ledger

Snapshot code: `bf82b80` (2026-10-13). Update dates/versions explicitly before release.
No clinical-efficacy, patient-outcome or financial-return measurement exists.

| Claim | Evidence | Limit |
|---|---|---|
| Five product-agent skills | `aura_agent/roles.py` and skill files | Different levels of agency; Q&A is strongest, summaries constrained |
| Model-selected windows/tools, descriptive analysis and visible trail | `aura_agent/runtime.py`, `tools.py`, `aura_app/agent.py:investigation_trail` | Read-only, bounded; not autonomous care or clinical conclusions |
| Deterministic safety/longitudinal cores | Accepted M1–M4 implementation/review packets | Engineering properties, not clinical validation |
| Six synthetic scenarios A–F | M3/M4/M7 review evidence and simulator tests | Hidden truth evaluation-only; no real patient study |
| Historical clinician headlines 19/20 | `../evidence/deepseek-v9-reliability.json`, Case B clinician | Prompt v9, specific synthetic fixture; not current v11/Q&A reliability |
| Historical patient headlines 19/20 | Same, Case B patient | Two total fallbacks; flu groups not measured; no general clinical accuracy |
| HTTP preview p95 332 ms patient/496 ms clinician | Same report summary | Response timing, not visible screen paint |
| Generated headline HTTP p95 4462 ms patient/4242 ms clinician | Same report summary | Historical run, not all model paths or current UI performance |
| Current automated suite: 303 PASS | Full run on `bf82b80`, 2026-10-13; 356.315 seconds | Offline engineering regression, not live model or clinical validation |
| Live URL health | GET `/health`2026-10-13 returnedok andsynthetic_onlytrue | Not a full judge walkthrough, link uptime guarantee or auth review |
| CodeBuddy UI/Miora artwork implemented | Recent Git history and root handover | Original session logs/screenshots still need collecting; commits are not upload proof |

## Current run

Command: `.venv/bin/python -m unittest discover -s tests -q`

Result: **303 PASS / 356.315 seconds**, implementation commit `bf82b80`,
2026-10-13. Existing Starlette/httpx deprecation warning remains. No new paid
model calls, large reliability trial or deployment was performed for packaging.
Concurrent UI/browser edits appeared later in the shared worktree and were left
untouched. This is not the final release validation for those edits; rerun the
relevant checks on the eventual release commit before setting the package READY.

## Claims discipline

- Say engineering prototype, live model on synthetic data, source-linked
  descriptive observations and clinician-review preparation.
- Do not claim clinical accuracy, diagnosis, relapse prevention/prediction,
  suicide-risk determination, treatment guidance, emergency monitoring,
  automatic clinician transmission or real wearable integration.
- Institutional private/on-prem deployment, consented wearables, authentication,
  durable approval/sharing and governed follow-ups are future work.
- Do not say deployed on Tencent Cloud: current host is the development server
  through Cloudflare. Tencent provider support/tool artwork is a different fact.
- Do not call regex/independent model checks proof of clinical truth.
- Update numerical claims only from preserved evidence; do not quietly mix prompt versions.
