# Handover

The shared handoff note for any agent (Claude, Sol, or others) working on this repo. **Read this first.** Update it before you finish a session.

## How to use and update this file

**On arrival:**
1. Read the whole file, newest log entry first.
2. Check that the "Current state" section still matches the repo: run the tests, `git log --oneline -5`, `git status`. If something here is wrong, correct it. Don't work around it.

**Before you finish (or at any milestone, decision, or blocker):**
1. Edit **Current state**, **Open decisions**, and **Next steps** in place so they describe the repo *now*. These sections are a snapshot, not history. Delete anything that is no longer true.
2. Add one entry at the **top** of the **Log**:
   ```
   ### YYYY-MM-DD — <agent name> — <one-line summary>
   - What changed (files/modules, commit hashes)
   - Verified: <command run and result, e.g. "69 tests pass">
   - Left unfinished / watch out for: ...
   ```
   Use absolute dates. Keep entries short, and link to longer documents (e.g. `MILESTONE4_REVIEW.md`) rather than copying them.
3. ~300 lines is the trigger to compact, not a hard limit. When the file passes it, or the log passes about 15 entries, condense the oldest log entries into a single "Earlier history" bullet list. If compacting would lose information still needed, you may let the file grow to about 500 lines; past that, compact regardless and move detail into a linked document.
4. Commit it with your work (`docs: update handover`) and push (see **Git & remote**).

**Rules:**
- State facts you verified. Mark anything unverified as *(unverified)*.
- Don't record secrets, tokens, or real patient data here.
- Record user decisions and preferences as they are given, with the date.
- **Updates are asynchronous.** Agents work on their own branches under **Git & remote** below. Before starting a new branch, fetch and branch from the latest `origin/main`; before continuing an existing branch, check its upstream and re-read the sections you will touch. Do not automatically merge/rebase other agents' work. Make small, targeted edits (add your own Log entry; edit only the lines you own) instead of rewriting the file. On a conflict, keep both sides' entries and resolve by hand; never overwrite another agent's entry. Order Log entries by when they were written, and treat a Current state line as possibly stale until you check the repo. In concurrent sessions, use separate worktrees so switching branches cannot change another agent's working files.
- **Review asynchronous updates with the human in the loop (HIL).** Another agent's entries made since your last session (decisions, specs, DECISIONS sections) were recorded from separate chats. Before building on them, list what changed (`git log`, newest Log entries) and confirm with the user anything that changes scope or behaviour. Do not treat a recorded decision as approved for implementation just because it is written here; the user has the final say.

---

## Current state (documentation updated 2026-10-16; implementation evidence dated below)

- **Codex worktree sync (2026-10-16):** latest fetched main `0f08fb2` integrated into `improve/feature-codex` at user request. Await further instructions; no runtime or deployment actions in this session.

- **Private pitch v2 review (Codex, 2026-10-16):** reviewed the shared version 2 at the owner-provided external path and added a dated §12 comment at user request. Existing body/comments preserved byte-for-byte; file remains ignored/untracked. Checked selected main source and cited primary references. No private pitch content copied into this repo; editor decides body changes.

- **Availability planning superseded:** the earlier Codex standby proposal remains in `docs/JUDGING_AVAILABILITY_PLAN.md` as history. Main now records Tencent Lighthouse blue/self-hosted green hosting and the demo lock; no operations performed in this sync.

- **Catch-up/calendar backend review:** original Codex findings remain in `docs/BACKLOG_AND_CALENDAR_REVIEW2_CODEX.md`; main records their resolution in spec §9.8 and commit `653058e`. This sync did not independently rerun those probes.
- **LOCKED for demo day (2026-10-16, user-approved):** tag `final-demo-day`. No code changes after this; operations only (`deploy/switch.sh status|blue|green`, see `deploy/SWITCH_HELP.md`). Public site served by **blue** (Tencent Cloud Lighthouse, Singapore), **green** (self-hosted) on standby; both run the same app build (from `73a762a`; later commits are tests/docs only). Live model OpenAI gpt-6-luna, reasoning medium, on both. The owner's Telegram agent (on a separate machine) watches `switch.sh status` and never switches. After judging: rotate/disable the AI keys and the TokenHub key.

- **Catch-up + calendar built (2026-10-15, Claude, final gate):** spec `docs/BACKLOG_AND_CALENDAR_SPEC.md` §9. Codex and Gemini had no commits on their branches by the deadline eve, so Claude built §9.2 (backend) and §9.4 (browser suite) too. Backend `aura_app/record_calendar.py` (update window, save past days as `reported_later` medication events, coverage, calendar + day detail with sharing filters) and `aura_app/medication_update.py` (interpret typed text: safety first, `medication_backfill` agent task, checked proposal). UI `aura_ui/catchup.js` (dose-card prompt, update dialog + preview, calendar page for patient and clinician, welcome back, coverage strip) plus a relearning line in `evidence.js`. Tests `tests/test_record_calendar.py`, `tests/test_medication_update.py`, browser `tests/browser/catchup_calendar.cjs` (phone + laptop).

- **Codex Q&A calculations (2026-10-14, branch delivery):** from main `eac0334`, added read-only `summarize_checkins` for arbitrary supported windows/categories, deterministic percentages/counts/coverage, cited derived facts and a bounded missing-answer repair. Prompt v12; exact calculated display sentences preserve denominator/dates/missingness. Existing engines and shared patient percentage restrictions unchanged. See `docs/CLINICIAN_QA_CALCULATIONS.md`. Full355 tests PASS/492.432s plus final focused10 PASS; Claude merges/deploys later, no live-model calls in this task.

- **Architecture PDF audited (Codex,2026-10-14):** against immutable main `90e31ea`; corrected `docs/submission/assets/aura-health-architecture-reviewed.pdf`, native deck slides11–13 and architecture sources. Main boundaries match: deterministic state/policy, read-only agent, curated medication and synthetic ingestion. Clarified90-s between-call budget/30-s provider timeout, separate verifier, resource-rendering versus assessment latency, built-in fallback, demo roles/Not-sent sharing and blocked/stale suppression. See `docs/submission/ARCHITECTURE_REVIEW.md`. Work isolated in `/tmp/aura-architecture-review`, branch `codex/architecture-review` from latestmain; existing named agent branches/worktrees preserved, no merge/deploy/live-model calls. Full334 Python PASS/459.063s; artifact checks and mock-clock probe PASS. Existing Starlette/httpx warning; source/model live status not re-read.
- **Live model (2026-10-13):** OpenAI `gpt-6-luna`, reasoning **medium**, set via settings. Settings now list the provider's models automatically (plus a free-text ID) and have a reasoning level (None/Low/Medium/High, default Medium) stored per provider. OpenAI agent calls with reasoning on use the Responses API (chat completions rejects tools + reasoning); its replies may be up to 256 KB. Guided-tour agent step, 5 live tries each, medium: gpt-6-sol 3/5, gpt-5.6-terra 5/5, gpt-6.1-sol 5/5 (71–112 s), gpt-6-luna 5/5 (47–60 s). "gpt-6-terra" does not exist for this key. User rejected recording PROHIBITED_CLAIM rule details in `grounding.py`; don't reapply.
- **Guided story implemented:** `aura_ui/tour.js` now has the manual nine-step story, patient-to-clinician transition, committed dose/reason demonstration, Q&A result/fallback and optional paced safety ending/reset. Inspected at `90e31ea` on2026-10-14; historical handoff recommendations are not pending implementation. New usability acceptance was not measured in this architecture review.
- **Codex companion docs/Q&A/X5 delivery:** merged requested main `f37af0c` into the
  feature branch preserving both logs. Submission/challenge/capability/architecture
  copy now reflects the integrated four-card companion; updated overview SVG/PNG
  requires Claude to re-render the deck. Post-flu diagnostics:2 live fallbacks
  (verifier stage and exact-number/date rejection), no timeout. Identical local
  fixture reproduced50,053-character verifier payload above40,000 limit; removed
  clinician-only duplicate patient wording fields →25,636, mock verified. No
  thresholds, guards, budgets, deployment or patient verifier projection changed.
  Two regressions PASS; candidate68372f3 full330 Python PASS/474.013s and15 hosted
  browser suites PASS, local registry3 checks PASS, redesign UX1 FAIL (quiet-card
  below first390×844 viewport).
  Signed-out liveA–F status/timeline/review andB/F companion reads PASS; GitHub404,
  strict preflight1. X5 is checked but NOT a green release gate. No merge/deploy.
- **Companion consolidation verified (2026-10-13):** Claude merged/deployed the three branches and supplied `missed_days` in `6c4e265`; later safety refresh and one-column fixes are included in candidate `495087d`. Codex independently verified327 Python PASS/469.072s,18 selected browser checks on8036, missing/UNKNOWN separated from MISSED, stable retry counts and signed-out liveB/F companion suppression. A reused-run-ID/changed-question gap was reproduced on that candidate; current90e31ea includes the subsequently verified question-hash fix. Main's newer37a2f32 script/tour change is outside this historical immutable run. Source404 was subsequently superseded by Claude's recorded2026-10-14 public200 check. User supplied screenshots in `docs/submission/screenshots/`; Claude owns narration. Neither was edited here. Earlier branch-delivery snapshots below are historical.
- **Feature freeze CANCELLED (user, 2026-10-13 evening):** "Cancel feature freeze and let's go all in!" Build the patient companion features in [`docs/PATIENT_COMPANION_SPEC.md`](docs/PATIENT_COMPANION_SPEC.md) to meet Challenge Statement 2 Scenario 1; ownership §4, schedule §5 (no fixed cut-off: integrate as soon as all agents report done; user, 2026-10-13). Earlier freeze lines below are superseded.
- **Patient companion backend implemented on Codex branch (user authorization,2026-10-13):** medication-reason validation/adapters, additive supply/refill/reason columns, explicit synthetic prescriptions, dose/day counts, review/refill dates, reason-linked Not-shared review items and read-only `GET /companion`. See `docs/PATIENT_COMPANION_BACKEND.md`. Accepted safety/longitudinal algorithms unchanged. Claude owns curated lookup/suggestions/medication-ask route; CodeBuddy owns the four-card UI. Default lookup/selector joins their modules after integration; isolated tests plus actual cross-worktree callback smoke passed. No merge or deploy.
- **Feature freeze cancellation confirmed by user (2026-10-13):** user requested proceeding with Claude's companion assignments. New scope is `docs/PATIENT_COMPANION_SPEC.md` on Claude/main (`8cbb478`); earlier bugs-only directions are superseded for those four features. The new freeze is planned for15 Oct morning. This does not authorize unscheduled engine changes or deployment.
- **Worktree isolation (user, 2026-10-13):** Codex works only in `/home/makodev58/aura-health-codex` on `improve/feature-codex`, browser port8036. Claude uses `/home/makodev58/aura-health-claude` / `improve/feature-claude` /8026; CodeBuddy uses `/home/makodev58/aura-health-codebuddy` / `improve/feature-codebuddy` /8046. Main folder is reserved for user-directed integration/deployment. Submission assignments #7, #8 and #17 are in Claude's pushed `9be2ff1` work plan; inspect with `git show origin/improve/feature-claude:docs/submission/WORKPLAN.md`, without merging.
- **Agent roster (updated 2026-10-14, Claude):** one worktree and branch per agent; `main` folder `/home/makodev58/aura-health` is for user-directed integration/deploy only.

  | Agent | Worktree | Branch | Local test port |
  |---|---|---|---|
  | Claude | `/home/makodev58/aura-health-claude` | `improve/feature-claude` | 8026 |
  | Codex | `/home/makodev58/aura-health-codex` | `improve/feature-codex` | 8036 |
  | CodeBuddy | `/home/makodev58/aura-health-codebuddy` | `improve/feature-codebuddy` | 8046 |
  | Gemini (Antigravity) | `/home/makodev58/aura-health-gemini` | `improve/feature-gemini` | 8056 (checked free 2026-10-14) |

  Pull `origin/main` before starting each task. Commit under your own name, e.g. `git -c user.name="Gemini" -c user.email="gemini@aura-health.local" commit …` (the repo default identity is "CodeBuddy"). No merges or deploys unless the user directs; Claude currently merges/deploys on the user's go.
- **Agent branch workflow (user, 2026-10-13):** CodeBuddy uses `improve/feature-codebuddy`, Claude uses `improve/feature-claude`, Codex uses `improve/feature-codex`. New branches start from latest `origin/main`. Each agent pushes only its own branch for independent review. The user will designate the reviewer and merger; branches are merged into `main` one at a time only on explicit direction. Earlier standing reviewer/merge assignments do not authorize future merges. This naming convention does not expand the current feature freeze or authorize deployment.
- **Submission preparation remains active alongside the approved companion build:** canonical folder [`docs/submission/`](docs/submission/README.md). Every agent must read its README/REQUIREMENTS and use FORM_CONTENT/manifest/asset register. Live link,5–8-minute video and architecture PPT required; history requires actual chat plus≥3 screenshots from CodeBuddy/WorkBuddy/Miora. Final assets/approval remain pending. Never submit/publish, fabricate evidence or invoke development tools without separate user direction.
- **Capability audit:** [`docs/CURRENT_CAPABILITIES.md`](docs/CURRENT_CAPABILITIES.md) includes the integrated companion update. Strongest product agent remains free-form record Q&A; automatic brief/recap is constrained selection/wording. No autonomous actions or conversational memory. New companion counts/curated cards are not autonomous agent actions; final-product plans remain distinct from implemented features.
- **Latest Q&A implementation:** explicit clinician attribution, exact clinician facts, routine/held/unknown-topic fallback, trace-derived investigation line, narrow medication-record false-positive handling and thousands-separator grounding are implemented in Claude's newer commits. Actor remains self-declared for synthetic demo only, not production authorization. User-approved demo allowance30/minute300/hour is configurable; unset code defaults10/60. Per-run budgets/guards remain; no root runtime/setting changes in submission preparation.
- **Breathing welcome now implemented/deployed by Claude:** user-approved once-per-session patient welcome, Continue/tap/keyboard dismissal, help still reachable, safety-path suppression and reduced-motion behavior; summary loads behind it. New Miora WebP/faded edges in `bf82b80`. Existing loader cleanup/pending-note fixes retained. This replaces the earlier recommendation-only snapshot; no root UI/deployment edits.
- **Latest reviewer delivery:** CodeBuddy UI redesign merged/deployed by Claude; `be3e795` fixes run-together clinician headings. Current prompt `aura-agent-v11` / arrival cache `arrival-v11`; v9 reliability evidence below is historical, not a v11/Q&A gate. One pre-existing redesign-suite assertion remains unresolved; no public deployment verification in this review.

- **DeepSeek v8 reliability trial (historical):** interrupted at 53/80; B clinician 18/20, patient 16/20. Superseded by the v9 result above.
- **Patient reliability v9: historical Case B gate PASS (2026-10-12).** Trial used `aura-agent-v9`; current prompt is v11. Run stopped by design at 40 samples (user: flu groups not needed for a demo). Clinician 19/20 and patient 19/20 validated headlines (gate 18/20), two fallbacks (UNSUPPORTED_CATEGORY, VERIFIER_REJECTED), no provider failures; HTTP preview p95 0.33–0.50 s, AI swap p95 4.2–4.5 s (not visual paint). Evidence `docs/evidence/deepseek-v9-reliability.json`. Flu groups not measured. No further reliability runs needed (demo priority).
- **Fallback/source-panel fixes retained in deployed v9:** `372e4ad` leads recent changes and mentions signal-specific gaps when there is room; updated samples in `docs/PATIENT_VOICE_REVIEW.md`. Same-fingerprint/source-protected disclosure handling remains. Codex made no deployment this session.

- **Project name:** officially **aura-health** (user, 2026-09-23). Care Plan Bridge (`PRODUCT_FRAMEWORK*.md`, `FRAMEWORK_CRITIQUE.md`) was dropped; those docs are marked superseded and kept for background only.
- **Product being built:** a longitudinal, wearable-first companion for adults on stable antidepressant maintenance treatment. Spec: `aura_health_framework_v1.0.md`. Safety policy: `aura_deterministic_safety_policy_state_machine_v1.2.md`.
- **Milestones 1–4 are complete; M4.5 documentation is complete.** The Milestone 4 engineering stop condition is met. See `MILESTONE3_REVIEW.md` and `MILESTONE4_REVIEW.md`.
  - `aura_safety/`: deterministic safety state machine (no LLM).
  - `aura_longitudinal/`: personal baseline, drift, context, held-for-review, and communication engines.
  - `aura_app/`: FastAPI + SQLite application layer. It handles idempotent event ingestion, atomic transactions, safety-first gating, the timeline, and the clinician review snapshot (never shared automatically).
- **M5 implemented and reviewed (Claude, 2026-10-02; no blocking findings):** [`MILESTONE5_REVIEW.md`](MILESTONE5_REVIEW.md). `aura_communication/` supplies bounded wording contracts, validator/fallback, optional HTTP gateway, fixture evaluation, and engineering configuration. `aura_app/communication.py` reads committed decisions/safety references and persists race-checked wording/audit. Accepted domain algorithms remain unchanged.
- **M6 implemented; reviewed by Claude 2026-10-03, no blocking findings:** [`MILESTONE6_REVIEW.md`](MILESTONE6_REVIEW.md). `aura_ui/` is a responsive, no-build-step patient web app. It uses existing APIs for check-ins, medication records, explicit explanations, review preview, and pinned safety. `PatientViewService` provides read-only latest-event/provenance links. The explicitly synthetic demo factory shows stable + Cases A–F with before/after explanation and gap/return checkpoints. Accepted safety/longitudinal algorithms and DB schema are unchanged.
- **Latest Codex tests (2026-10-13):** companion build full **320 PASS /426.774s**, plus final focused contract/fixture checks after timestamp-tie refinement. Five hosted suites (milestone7, workflows, agent, plain_language, dual_view) **31 assertions PASS** at8036; actual Claude lookup/select smoke PASS without model calls. The older milestone6 browser suite was incorrectly selected for hosted mode (local-signup case expects200 but host rejects403), and has pre-existing raw-wording assertions/dialog-cleanup cascades; recorded in backend notes, no frontend edits. Prior303 suite/rehearsal and v9 measurements remain historical. Merged new-card UI acceptance and final release tests still pending. Existing Starlette/httpx warning remains.
- **Warm patient voice / plain-language follow-up implemented and deployed (2026-10-12):** Claude's `PATIENT_VOICE_SPEC.md` and corrected `PLAIN_LANGUAGE_SPEC.md` now have versioned placeholder examples, friendly source fields, human dates/source labels, a warmer sourced fallback and plain Why panels. Patient budget 35 words total/25 per sentence; clinician 20-word contract and exact measurements/units/dates/counts retained. Shared term catalogue, closed Technical details/Developer tools and same-record disclosure preservation; fresh safety guard still required. Versions `aura-agent-v8` / `arrival-v9`; unchanged tool limit budgets actual model fields rather than duplicate UI disclosures. No accepted engine/threshold/schema/dependency/provider/quota changes. Fresh v7 DeepSeek B/flu attempts **0/2 generated, 2 source-grounded fallbacks**: sanitized trace reports `ProviderUnavailable` at MODEL_STEP; no retries or validator weakening. Evidence `docs/evidence/patient-voice-live-smoke.json`. User sign-off on five live/fallback voice examples remains open; do not declare M7 accepted.
- **Patient recap refinement implemented/deployed (user, 2026-10-11):** one calm heading and short natural sentence; measurements/check-in counts behind **See what changed**, exact recap citations/provenance behind **Why this summary?**, all retrieved evidence separately inspectable. Aura-Agent chooses phrasing/selected supported facts only; patient-specific style/alias/advice/reassurance checks plus unchanged grounding and independent verifier, source-bound factual fallback. Clinician analytics and accepted engines/thresholds/schema/dependencies/provider/quotas unchanged. Versions `aura-agent-v6` / `agent-engineering-v4` / `arrival-v7`. See [`docs/PATIENT_RECAP_REFINEMENT.md`](docs/PATIENT_RECAP_REFINEMENT.md), DECISIONS §45. Two fresh synthetic DeepSeek patient samples **2/2 validated** (B and B + flu), 3.588/3.773 s total HTTP; not the 20-run/p95 gate. User/Claude UX review still pending.
- **Final-dash WP1–WP5 implemented/deployed:** Claude WP2 review `19d3cea` PASS with follow-ups; user requested continuation. Added sourced deterministic overlap synthesis (clinician only), check-in counts/runs, approved context/gap/visit question selection; patient onset order/plain recap/no steady chip/appointment count; neutral units/icons, rounded Also recorded rows, core/also-moved/optional sparse charts and compact mobile guide. Synthesis uses the deterministic validated template, not optional extra model wording. Patient prompts remain in the communication layer, not clinician Worth asking chips. Engines/thresholds/schema/dependencies unchanged. Versions `aura-agent-v5` / `agent-engineering-v4` / `arrival-v6`. Evidence: [`docs/FINAL_DASH_EVIDENCE.md`](docs/FINAL_DASH_EVIDENCE.md). Latest four synthetic live samples: **2 validated, 2 fallback** (HEADLINE_JARGON, HEADLINE_BUDGET); no relaxed checks/retry loop. WP6 comprehensive HTTPS walkthrough, quantitative 20-run/p95 gate, final review/design lock/M7 acceptance remain pending.
- **M7 implementation:** existing deterministic scenario driver/replay/16 DEMO tests plus the approved life director, atomic intake/import/context, isolated synthetic workspaces and Docker. Diagram/runbook: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md). Healthy on **0.0.0.0:8017**, LAN `http://192.168.80.193:8017`; public `https://aura-health.makodev58.com` verified for Cases A–F reads and isolation/retry. **Claude/user implementation and UX review remain open; M7 not declared accepted.**
- **Demo capacity/cookie fixes deployed:** only `GET /demo/scenarios` allocates a private workspace. Shell/assets/probes no longer consume slots; cookie-less patient requests return `DEMO_SESSION_REQUIRED` without allocation. Capacity keeps existing sessions and provides visible retry/local resource fallback. Deployment retains `AURA_SECURE_COOKIE=true`, with ignored `.env` explicitly allowing HTTP demo cookies only for `192.168.80.193` through `AURA_HTTP_DEMO_HOSTS`. Public hostnames and HTTPS retain Secure; protected settings authorization is unchanged. Real phone-sized Chromium verified LAN page/API/reload and same-session retention. Restart retains old files/provider settings but gives browsers fresh synthetic workspaces; no domain policy/state transition changed.
- **Integration contradiction fixed:** application projector previously omitted the accepted domain's new-longitudinal-signal reopening input. It now forwards newly production-assessed persistent/divergent signals; DEMO11 verifies reopening with unchanged anchors. Safety/longitudinal domain algorithms and clinical configuration remain unchanged.
- **Scope (2026-10-09, DECISIONS §42):** focus is antidepressant maintenance; the architecture should stay open to other conditions later (condition-specific content in configuration). Nothing is built or claimed for other conditions. Patients often have several conditions; treat the whole person as the unit in design discussions (§42 addendum, not an approved feature).
- **Current product statement (2026-10-08):** [`docs/PRODUCT_VISION.md`](docs/PRODUCT_VISION.md) — purpose, layers, journeys, state, and an honest diagnosis of why the demo underwhelms plus ranked fixes.
- **Canonical plan:** [`docs/ROADMAP.md`](docs/ROADMAP.md), [`docs/DECISIONS.md`](docs/DECISIONS.md), [`docs/milestones/`](docs/milestones/), and [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md).
- **Operator provider settings:** gear supports OpenRouter, OpenAI, DeepSeek and Tencent; provider/model visible before unlock. **DeepSeek / deepseek-flash / live enabled**, public status verified 2026-10-09. Live transports remain hosted synthetic-only; HTTPS/loopback/admin protection and write-only keys unchanged. See [`docs/SYSTEM_SETTINGS.md`](docs/SYSTEM_SETTINGS.md). No secrets in traces or source control.
- **Not production-ready:** unvalidated demo detectors/verifier, patient authentication/sharing, institutional deployment, real wearable ingestion, sponsor clinical/content review. Ordinary non-demo gate still holds unassessed text. Existing user-managed Cloudflare container is preserved, not provisioned by Codex. Live model inputs remain synthetic only.
- **Ownership:** Codex has implementation authority (user, 2026-10-02). The 2026-10-13 branch workflow supersedes the earlier standing Claude reviewer assignment: the user will designate who reviews all branches and merges them into `main`.
- **Development delegation (user, 2026-10-11):** Luna for lightweight tasks, 6.1-Sol with medium effort for heavier tasks. Used for noisy-profile measurement/review and WP3–WP5 implementation respectively. This does not change the application's configured DeepSeek provider.
- **Copy rule (user, 2026-10-09; deployed 2026-10-10):** ordinary cards/explanations report neutral supported facts, without repeated "not an assessment/diagnosis" caveats. Removed the two patient-card remarks and routine/review/comparison repetition; scope stays in Disclaimer. Sources, operational states, Not sent, AI provenance and pinned safety remain. DECISIONS §44 records the rule; future acknowledged onboarding is not implemented here.
- **CodeBuddy workflow:** user controls timing. Genuine CodeBuddy UI redesign and Miora artwork were merged under later user instructions; do not claim a full clean rebuild. Required original chat/screenshots upload evidence still needs collecting. No automatic CodeBuddy/WorkBuddy invocation or fabricated proof.
- **Data:** synthetic only (simulator cases A–F).
- **Dual-view scope approved / implemented (user, 2026-10-07: "Proceed"):** clinician-first read-only workspace, shared historical evidence projection, Patient / Clinician demo toggle, minimal patient home and optional **See my full data**. Opens Case B; guide retains A–F/checkpoints. Explicit disclosure distinguishes full synthetic inspection from future patient-approved clinician access. `GET /patients/{id}/evidence` exposes committed snapshots/anchor versions without replay, mutation or generation. Quiet home has no default metrics/tasks; check-in/routine are collapsed. Questions/review items and temporary appointment preview remain not sent. Active/degraded/offline safety stays independently visible even without an episode. See `docs/DUAL_VIEW_IMPLEMENTATION.md`. Deployed on 8017; **Claude implementation review and user UX acceptance pending**. Accepted engines/schema/dependencies unchanged; additional data and CodeBuddy deferred.
- **Approved §39–41 implemented:** five aura-agent skills, scoped/batched read and descriptive analysis tools, exact structured findings and separate claim verifier; rejected claims are dropped, required findings restored as labelled extraction. Safety-gated free Q&A/notes, manual measurements, confirmed imports/context, print visit pack, Disclaimer and provider/model before unlock remain. See [`docs/APPROVED_AGENT_AND_SIMULATOR_IMPLEMENTATION.md`](docs/APPROVED_AGENT_AND_SIMULATOR_IMPLEMENTATION.md). The earlier optional/no-load behavior is superseded by the user-approved assessment-first experience below. Accepted engines/dependencies unchanged; `workflow_runs` and `agent_runs` remain the existing append-only trace stores.
- **I1–I8 implemented (user delegation approval, 2026-10-09):** planning then coding agents delivered [`docs/IMPRESSION_IMPLEMENTATION_PLAN.md`](docs/IMPRESSION_IMPLEMENTATION_PLAN.md) and [`docs/IMPRESSION_IMPLEMENTATION.md`](docs/IMPRESSION_IMPLEMENTATION.md). Immediate guarded extraction + fingerprint-cached automatic clinician assessment; default above-fold plain patient recap without charts; exact source/date chart links, scoped context markers/check-in axes; visible sourced Q&A; Evidence/Context/Details groups; real quick-event buttons/changed-line highlights; labelled guided story; opt-in raw comparison/export. Offline/unsafe state clears ordinary generated content. `arrival-v3`/`aura-agent-v3` require briefs to read retained/held evidence before finalizing (AW28), without weakening grounding. No new domain algorithms, tables, dependencies or clinical thresholds. Claude/user acceptance and live wording quality remain open.
- **I9 cards implemented (user "please execute", 2026-10-09):** Claude's c1f598b spec now has clinician finding grids, rounded human units, exact method/value/source disclosure behind Why?, shared-window finding bars/timeline and chart callouts; patient lay cards/relative dates without home charts. A steady-report card requires repeated non-held check-in answers in the last 30 recorded days, never absent data or a new stability inference. Empty assessment sections omitted; one Q&A input/chips, optional ranking in Details. UI/browser/docs only; no backend, engine, schema, model/validator or dependency changes. Details/limitations: `docs/IMPRESSION_IMPLEMENTATION.md` I9. Deployed; user/Claude UX review pending.
- **Life simulator complete for review:** guide-only bounded director/seeded generator with seven life events, sparse BP/weight/temperature/SpO₂, cross-advance recovery, feedback toggle, immutable traces/retries/replay and persisted session budgets. New research references use explicit synthetic review commands; original four anchors preserved. Models never write numeric telemetry or policy. Hidden plan/truth stays outside decision payloads; manual entry remains available. Sponsor overrides cover signal/detector/effects/question/context/resource content. All values are engineering defaults.
- **Live checks:** DeepSeek five-skill sweep, safety-gated free Q&A, import mapping and life planning/replay exercised. Actual per-skill outcomes are in the newest log; rejected drafts still use honest extraction. Earlier GPT-6 Luna results are historical. Model/semantic verification is not clinical validation; no guarantee every future draft validates.
- **Signal-registry foundation implemented (DECISIONS §41):** sponsor-editable/versioned `aura_longitudinal/signal_registry.json` and `AURA_SIGNAL_REGISTRY` override; `GET /signals`, typed scalar ingestion, source-linked research/display-only charts and agent evidence. Original four parameter values/rules retained; HRV/respiratory rate/skin deviation enabled E3_RESEARCH; SpO2/BP/thermometer/weight display-only. Calendar coverage is not cadence-discounted or interpolated. New-channel anchors require calendar coverage; configurable absolute spread floor handles zero-centered skin deviation (0.1 °C provisional default). No safety changes, DB schema/dependencies, real intake, simulator agent or flu generator in this step. Details: [`docs/SIGNAL_REGISTRY_IMPLEMENTATION.md`](docs/SIGNAL_REGISTRY_IMPLEMENTATION.md).

## Open decisions

- **Current scope (2026-10-16):** requested main sync and private pitch v2 review complete. No new implementation or operations assigned.

- **Private pitch:** owner/editor to consider the latest v2 review in the external deliberation document. Keep that document ignored and untracked; do not import its contents into public documentation.

- **Credential planning:** earlier CVM/SSM options remain historical; main records Lighthouse setup. SSM retrieval remains unimplemented. No credentials or host configuration inspected during this sync.

- **Judging resilience:** main records blue/green hosting and session restart on switching. Earlier topology questions are superseded by that operational handoff; live state was not independently checked in this sync.

- **Catch-up/calendar review findings:** main spec §9.8 records R1–R4 fixed and R5 denominator clarified; preserve the original reviews as historical evidence. No further review work assigned.

- **Medication request identity resolved:** current `MedicationAskService` includes the exact question hash in the patient event identity; changed text with a reused run ID gets a fresh safety assessment. Regression MED4b exists; historical495087d finding is closed in the code inspected at90e31ea.
- **Companion integration assumptions:** no booked-appointment field exists, so `coming_up` emits the stored medication review and refill estimate without an invented APPOINTMENT entry. Demo day is the latest recorded local day;08:00 is a configurable synthetic display hour. Counts are latest patient reports per day for the once-daily single-medication fixture, not verified adherence or a multi-dose regimen. Pharmacist/content review remains open. See backend notes for integration dependencies and stale M6 browser assertions.
- **Submission checks:** Claude recorded anonymous GitHub200/raw README200 on2026-10-14 in the manifest, superseding the2026-10-13 source-access blocker; not independently re-read in this code audit. Approved question rehearsal had1 partial generated answer /2 fallbacks in3 consecutive live runs. Exact outcomes and presentation issues are in `docs/submission/EVIDENCE_LEDGER.md`; no runtime fix inferred from documentation assignments. Final release, artifact availability and approval remain pending.
- **Submission approval/assets:** user must approve final form wording, supply genuine development-history screenshots, choose/upload the video and review cover/PPTX. Final release commit and signed-out links remain to verify. Packet isDRAFT, not submitted; no final M7/design-lock/clinical acceptance implied.
- **Final design push:** Claude passed WP2 with follow-ups (`19d3cea`), implemented in WP3–WP5. User's later patient wording/layout correction (§45) is deployed; review this newer experience rather than requiring the superseded default patient measurement grid. Quantitative 20-run/p95 gate, WP6 comprehensive HTTPS walkthrough and final review remain pending; no design lock. No engine expansion/validator weakening.
- **User approvals 2026-10-08 ("I approve all"):** all five items in `docs/CLAUDE_AGENT_REVIEW_AND_PROPOSALS.md` §7 are approved (see `docs/DECISIONS.md` §39). The DeepSeek configuration recorded that day is historical; see the latest dated model snapshot above. Also approved: show provider+model in the settings dialog without unlock (endpoint already public; UI-only change), and a demo-only **patient simulator agent** (§40, plan `docs/PATIENT_SIMULATOR_AGENT_PLAN.md`). User posture (2026-10-08, DECISIONS §41): developer proposal for a sponsor who owns clinical/regulatory judgment; new signals may enter the engine via a sponsor-editable **signal registry** (continuous wearable channels vs intermittent BP/thermometer/weight), see simulator plan §3.

- **No remaining implementation permission blocker for §39–41.** The approved paths are implemented; Claude/user review is next, not another prerequisite to building them. Sponsor clinical judgment is not claimed by implementation.

- **Agent review:** user authorized implementation of Claude's plan; approval is no longer blocked. Claude should review guard/scoping, grounding limitations, trace/race behavior and actual usefulness before acceptance. Safety doctrine remains unchanged; read-only synthesis sits outside policy ownership. Clinical/content governance remains open, not silently delegated to AI.

- **Experience acceptance / Claude implementation review:** scope is approved and implemented; review GP usefulness, minimal patient burden and source/chart fidelity before more features. No extra concern categories, ordinary deferral or persisted sharing were added. Five concern paths, saved approval and production clinician authorization still do not exist.

- **Asynchronous scope now authorized:** user explicitly requested planning-agent then coding-agent delegation for I1–I8 and §43. The default patient text recap and automatic guarded assessment are implemented; no other-condition feature was inferred from §42. Permission is not acceptance.
- **Performance/quality review:** v9 Case B clinician19/20 and patient19/20 passed; user closed reliability work after those40 entries, flu groups not measured. No active reliability trial. This covers headlines, not Q&A/current v11. HTTP timings are not visible generated-swap paint. No quota increase, repeated retry loop or relaxed grounding. Noisy quiet profile exposes existing transient sensitivity (8/20); sponsor/reviewer assessment needed, no threshold retuning.
- **Public URL:** HTTPS Cases A–F reads/isolation/retry verified; local browser fallback tests pass. Live unavailable-provider fallback and UI remain subject to broader reviewer evaluation. Do not assume repository sidecar is the hosting route.
- **Tencent Cloud mirror:** whether to also mirror the live demo to Tencent Cloud. The user will decide closer to the 2026-10-16 deadline (M8 window, 13–15 Oct).

## Claude recommendation — product reassessment (2026-10-07)

*Recommendation only. Not settled policy, not user-approved. Based on framework §2–3, 5, 17, 29–32, `docs/PRODUCT_REASSESSMENT.md` and a read of `aura_ui/index.html`. No code changed.*

**I agree with the diagnosis and add one cause:** Today shows a quiet card, check-in, routine, data strip, scope note, Talk button and three tabs at once. That contradicts §17 ("the more stable the patient, the less AURA asks") and §29. The demo also mixes three audiences (judge, patient, operator) on one surface. Fix the audience split first; restyling won't help.

**Patient value (one sentence):** *AURA quietly keeps track between doctor visits so you don't have to, speaks up only when one small question would help, and turns the last few months into a short note you can bring to your GP.*

**Journey ranking (design priority; the concern path must always be reachable regardless):**
1. **Ordinary day.** It defines the product (§2). Success is the patient needing to do almost nothing.
2. **Prompted clarification.** The differentiator (Cases A/B) and the only real "AURA speaks" moment.
3. **Review preparation.** The only tangible deliverable, and the clearest benefit to a GP.
4. **Patient-initiated concern.** It must exist and be safe, but today it is fixture-only. Entry is structured (below), not a chatbot.

**Default surface vs. everything else**
- *Default (one screen):* a calm status line ("Nothing needed from you today"), at most one primary action, a persistent "I need to say something" entry, and quiet access to "Prepare for my appointment". Safety panel unchanged.
- *Absent by default:* daily check-in card (patient-initiated only, not a stable-day prompt), data strip, scope note, three-tab navigation, reference/trust/held vocabulary.
- *Optional to inspect (§30, silence ≠ hidden):* "What AURA has noticed" (the old Patterns), timeline, "Why did AURA ask?", held items.
- *Operator/demo only:* demo bar, scenario selector, gear/settings, synthetic and fixture notices, limitations list (REESTABLISHING etc.), fixture buttons. Move into a separate **demo guide** shell with narration and a "fast-forward" control, wrapping a clean patient app.
- Rename "Talk to AURA": it promises a conversation we do not have.

**Walkthroughs (benefit → endpoint)**
- *Ordinary day:* at the usual dose time the patient taps "Took it" (or opens and sees "All quiet"). Endpoint: "Noted." ≤2 taps, ≤10 s, no questionnaire. Benefit: nothing to think about. A visit is not required, because passive signals carry the day.
- *Prompted clarification:* one plain sentence ("Your sleep has been later than usual for about ten days. Anything going on?") with chips (Travel / Work / Unwell / Not sure) and "Not now". The chip makes the existing explanation association behind the scenes. Endpoint: "Thanks. I'll stay quiet about this." and the card disappears. Skipping carries no guilt and no nag. Benefit: avoids the false alarm and a repeat question.
- *Patient-initiated concern:* "I need to say something" opens 5 taps: Feeling worse / Sleep / Medication missed or side effect / Thinking of stopping / Something else (free text secondary). Everything passes the safety gate first. Endpoint: a bounded acknowledgement ("worth raising with your clinician before changing anything") plus "Added to your appointment notes". Benefit: it is captured without retyping at review time. Structured taps work with today's safety routing, so this closes most of the "fixture-only" gap honestly.
- *Review prep:* ~150–200 words in sentences (what changed and when, what you told AURA, medication pattern, your questions), with per-item remove, then "Save / show at appointment". The screen says plainly **Not sent**. The 9 groups and checkboxes go behind "See details".

**Gaps UI cannot fix (none to be solved by bypassing safety or inventing clinical policy)**
1. Free-text concerns still need real detectors (not built); keep fixture-only or held, and say so only in the demo guide.
2. Review approval is not persisted. Needs an "approved summary" record (remove items, approve, show/export) and a deterministic sentence template from the existing snapshot. No sending (§32).
3. A signal→plain-sentence mapping is needed so the patient never sees category names. It is wording content and needs clinical review; Codex should not invent policy.
4. A web demo cannot push. AURA-initiated moments need a simulated reminder/clock in the demo guide.
5. Safety resources are still unreviewed; no governed REESTABLISHING exit; wearables are synthetic.

**Minimal storyboard (6 frames):** (1) quiet home → (2) "Took it" → Noted → (3) a later day: one question + chips → (4) thanks, quiet again → (5) "I need to say something" → 5 taps → added to notes → (6) "Prepare for my appointment" → short summary → remove an item → saved, **Not sent**.

**Acceptance criteria (informal usability, not clinical validation)**
- 5-second test: ≥4 of 5 non-team viewers state what AURA is for and whether they need to act.
- Ordinary day: ≤1 decision, ≤2 taps; default screen ≤~40 words, ≤1 primary action.
- Clarification answerable or deferrable in one tap with no navigation.
- Automated text scan: no baseline/drift/held/trust/provenance/synthetic/fixture/REESTABLISHING on the patient surface (demo guide exempt).
- Concern reachable in ≤2 taps from any screen; safety resources never behind a scroll or tab.
- Review summary readable in <60 s; removal works; sent/not-sent state unmistakable.
- No scores, risk labels or streaks (§29). A judge can see Cases A–F in the demo guide in ≤3 min.

**Questions for Codex:** (a) do the 5 structured concern taps map onto existing event types and the safety gate without new policy? (b) can a deterministic summary be built from the review snapshot? (c) which current UI code is reusable under a demo-guide shell? Then storyboard to the user for agreement before any code.

## Claude review of the dual-view plan (2026-10-07)

*Recommendation, not policy. Reviewed `docs/DUAL_VIEW_EXPERIENCE_PLAN.md`, `DECISIONS.md` §37 and the per-event baseline output in `aura_app/longitudinal.py`.*

**User direction restated (2026-10-07, via Claude session):** the **clinician view is the main part of the product**, and it is where the analytics live. Patient analytics are **on demand, not default**, so as not to overwhelm. If the patient wants them, they are **entitled** to them.

**Verdict:** the plan is sound and I support it. Three changes first, then answers to Q1–Q5.

**Required changes**
1. **Make the clinician workspace the centerpiece, not Stage 3.** The plan builds the patient frame first and treats the clinician view as an add-on. Reverse the emphasis. Build order: evidence contract → clinician workspace → minimal patient frame (it mostly reuses existing endpoints). The judge walkthrough should lead with the GP journey.
2. **Add the patient entitlement explicitly.** The plan only says retained information "remains inspectable". Add one patient entry, e.g. "See my full data", that opens the **same read-only projection and charts** the clinician sees, with patient framing and no gate by a clinician. One projection, two framings, so it costs almost nothing extra. It is opt-in, never a default card, and carries no scores or streaks (§29, §30).
3. **Fix the sharing contradiction in the clinician view.** §32 says a clinician sees only what the patient approved. The demo clinician view shows the *whole* synthetic record. Keep the "not a shared patient record" banner, and add: *"Demo shows the full synthetic record. In real use you would see only what the patient approves."* Without it the demo implies clinicians have default access to everything.

**Answers**
- **Q1.** Yes, this home is the right size. Emphasize the *ordinary day → one question* path for the patient. The demo's weight belongs on the GP journey (A–F, why it changed).
- **Q2.** Yes, it's the smallest useful workspace. Keep: a "what changed / when" strip (≤3 deterministic sentences, first on the page), four aligned charts, and a context/check-in/routine strip. Secondary: evidence drawer, safety section (collapsed unless a safety episode exists, as in Case F). Add a **display-only time window** (last 8 weeks / all). A GP won't read months. No new statistics.
- **Q3.** Agree: read-only first, approval/sharing as a separate later workflow. Do not fake approval in the demo. Label the appointment note "temporary preview".
- **Q4.** Boundaries look accurate. I checked that `aura_app/longitudinal.py` already emits per-event `baselines` (rolling mean/median/spread/slope/coverage, anchor, drift), so the historical rolling series is a read-only projection, no engine change. I did not verify anchor-version history from stored commands; Codex should confirm before promising it.
- **Q5. Wording/display that could still mislead:**
  - the anchored band drawn like a "normal range" (label it "your own reference");
  - Good/Okay/Rough drawn as a line (use dots or a categorical strip, never a trend);
  - coverage shown as a percentage that reads like a quality score;
  - "Held for review" reading as an unresolved clinical problem;
  - illness shading that visually clears unrelated signals (already noted in the plan);
  - any "monitored" language, and routine "acknowledged" read as verified adherence.

**Scope warning.** The deadline is 2026-10-16 and the M8 window is 13–15 Oct. Shell + toggle + new projection + clinician workspace + patient rewrite + human checks is a lot. Suggest cutting: the "Not now" deferral control (already flagged unresolved), extra concern categories, and the evidence drawer's depth. Ship one polished clinician case flow (B and D are the strongest) before A–F polish.

## Active task: M8 submission preparation — explicitly authorized, not complete

User explicitly requested submission preparation on2026-10-13. Canonical package:
[`docs/submission/README.md`](docs/submission/README.md); scope/gate:
[`docs/milestones/M8_SUBMISSION.md`](docs/milestones/M8_SUBMISSION.md). M7 formal
review/design-lock acceptance remains unrecorded; packaging does not grant it.
Accepted domain algorithms remain authoritative; no new feature development.

User approved §39–43/I1–I8 work is implemented within the existing product scope. Sponsor owns clinical/regulatory assessment;
engineering choices are configuration, not clinical claims. Safety doctrine is unchanged.

## Next steps

- **Private pitch owner/editor:** review the latest Codex v2 §12 entry in the external file and decide body changes there. No runtime or public pitch edits authorized by this task.

- **Codex:** wait for further user instructions after this requested main sync; respect the recorded demo lock.

- **Calendar final gate:** main records completion in spec §9.8; the prior Codex request for fixes is superseded.
- **Catch-up + calendar: done.** Review 2 from Codex and Gemini is consolidated in spec §9.8 (all P1/M findings fixed). No open work assigned; pull `main` before anything new.

- **Claude review/merge:** Codex's `docs/CLINICIAN_QA_CALCULATIONS.md` describes the new Q&A tool/harness and limits. Rehearse the original Rough-days percentage question after merge/deployment; check actual model tool selection and answer, not just mock success. Preserve concurrent patient-reply work when merging.

- **Ad soundtrack:** generate from `docs/submission/AURA_AD_SONG_v7.md` (current; the original `AURA_AD_SONG.md` is Codex's first draft). Review the actual audio/duration before using it; cut per `docs/presentation/video/SONG_CUT_PLAN.md`. Lyrics/prompt only are delivered; narration and video remain with their current owner.
- **Architecture reviewer/video owner:** inspect the corrected PDF/deck from `codex/architecture-review`, then update video frames separately if using them. Diagram budgets are checked between model calls; resource rendering has no model, while assessment may use one. The required upload remains the one18-slide deck; no merge/deploy is authorized by this review.
0. **All agents:** follow the agent-specific branch workflow below, publish work for review, and stop before merge/deployment. The user will choose who reviews and merges the branches; do not infer this authority from older log entries.
0b. **Companion is integrated:** preserve current endpoint/content/cards and question-hash retry fix; further runtime changes need their own scope. Historical branch-integration tasks are complete.
1. **Submission agents:** read `docs/submission/README.md` and current form requirements first; update only this canonical package. Complete cover, actual PPTX, genuine one-file chat/≥3-screen bundle, and7-minute video/link. Copy-ready description separates substantive agent investigation, deterministic policy and future product work; do not introduce unmeasured business/clinical benefits.
2. **Release operator/user:** review artifacts/claims, verify demo/GitHub/video as a signed-out viewer, record tested release commit and approval, then run `docs/submission/preflight.py --require-ready`. User performs actual form submission/publication and records confirmation. Do not infer authority to upload, change quotas or redeploy from preparation work.

0000000000. **User priority (2026-10-12): this is a hackathon demo, not a deployment; it must look sellable, not be perfect or exhaustively robust.** Prefer visible polish, a clear story and speed over extra reliability gates. The v9 reliability run is cut to the Case B groups (automatic stop at 20+20 samples; flu groups reported as not measured). No further large evidence runs unless the user asks. Keep safety panel, synthetic-only data and grounding checks.
000000000. **Earlier narrow follow-ups implemented:** Claude added investigation trail, medication-record false-positive fix, unknown-topic fallback and user-approved30/300 allowance. These are no longer pending permission choices. Preserve current guards and engineering limits; no new feature/reliability expansion during packaging.
00000000. **Review gates remain:** five updated fallbacks in `docs/PATIENT_VOICE_REVIEW.md`; voice/user sign-off and generated-swap paint p95 are not established by the closed v9 HTTP trial. HTTPS seven-event/five-story rehearsal completed with deterministic explicit plans and real AUTO communication; first timing failure remains disclosed. Claude final review/design lock/M7 acceptance still pending; no active reliability process.
0000000. **WorkBuddy handoff (historical 2026-10-12):** see `docs/WORKBUDDY_HANDOFF.md` and **Visual redesign SOW for CodeBuddy: `docs/CODEBUDDY_UI_SOW.md`**. Their older branch/base/reviewer instructions are superseded by the 2026-10-13 workflow: CodeBuddy uses `improve/feature-codebuddy` from latest `origin/main`, not `codebuddy/ui`, `improve/UI_UX`, or tag `pre-workbuddy`. The user decides who reviews, merges and deploys. Protected paths remain safety, longitudinal, communication, detectors and agent code, schema; new art/fonts go in `aura_ui/media/`, served at `/assets/media/<name>`.
000000. **Review the implemented plain-language/voice follow-up:** patient wording is simplified; clinician factual measurements remain visible. Review mobile/laptop home, Why panels, full-data and appointment views against `docs/PLAIN_LANGUAGE_SPEC.md`. User voice sign-off is still pending, not inferred from implementation permission.
00000. **Patient voice acceptance:** five actual live/fallback outputs (B, flu, stable, gap, check-ins only) remain a user-review item, not grounds for restarting reliability work. The request-specific DeepSeek JSON failure was fixed by Claude and the protected connection test passed; do not replace the accepted key or increase quotas. `docs/PATIENT_VOICE_SPEC.md` is implemented, but its user acceptance gate remains open.
0. **Finalize the current demo story and review, within the freeze.** Headline reliability work is closed by user decision; seven-event/five-story HTTPS rehearsal exists. Explain that summaries and Q&A are different model paths, preserve failures/measurement limits, and make the genuine Q&A investigation legible. No extra feature build, reliability resampling or optional clinician synthesis inferred; no design lock claimed.
1. **Claude: review I1–I9 and the approved agent/input work**, `docs/IMPRESSION_IMPLEMENTATION.md`, `docs/APPROVED_AGENT_AND_SIMULATOR_IMPLEMENTATION.md`, AW1–AW28 and AG1–AG20. Check rounded cards/exact disclosures, shared dates, steady-report meaning, arrival/cache/race/unsafe clearing, patient burden/source linkage, real guide actions, strict claim rejection and actual live usefulness. Respect §44: factual, neutral copy without repeated inline disclaimers. Registry archive/migration and sponsor policy-editing UI remain future work.
2. **User: reload the patient view** and try the short natural recap, **See what changed** and **Why this summary?** disclosures; clinician analytics/full-data access remain intact. Confirm UX acceptance before further expansion. No clinical or M7 acceptance claimed.
3. M8 packaging is now explicitly authorized; keep unrecorded M7 acceptance and model-quality limitations honest. No automatic CodeBuddy or feature expansion. Final submission remains a user action.
4. The user controls CodeBuddy timing. After product agreement, prepare the detailed rebuild SOW and capture actual evidence during the user-run rebuild.
5. Preserve known issues from `MILESTONE4_REVIEW.md` §13 and M6 limits:
   - Backend `safety_episode_references` still includes routine T0/null records; M6 filters null episode references in presentation only. Future sharing needs governance/filtering.
   - There is no governed exit from the `REESTABLISHING` state.
   - `reviewed_by` is caller-supplied and not authenticated.
   - Replay-per-event cost grows with the length of the event history.
   - M5 wording render also loads full history. Public routing helper is now `requires_safety_gate`; latest-event IDs are supplied by the read view.
   - Real-patient live-model consent/governance remains future work. Hosted synthetic wording is operator-configurable and defaults off until configured/enabled. Do not enable ordinary patient entry points implicitly.
   - Offline pending input is memory-only with same-key retries and an unload warning; no durable encrypted queue/cold-start offline app. Review selections are temporary previews, not saved approval/sharing.
   - Hosted session mappings are in-memory; restart keeps baseline but starts fresh browser workspaces. Abrupt-restart orphan files are retained; storage cleanup/abuse rate limiting is not production-grade.

## Quick reference

```sh
# setup (once)
UV_CACHE_DIR=/tmp/aura-uv-cache uv venv .venv
UV_CACHE_DIR=/tmp/aura-uv-cache uv pip install --python .venv/bin/python -r requirements.txt

# tests
.venv/bin/python -m unittest discover -s tests -q

# synthetic cases A–F through the app service
.venv/bin/python -m aura_app.simulator --case ALL --seed 7 --db-dir /tmp/aura-app-cases

# M5 wording fixtures and no-model fallback evaluation
.venv/bin/python -m aura_communication.evaluation --save /tmp/aura-m5-evaluation.json
.venv/bin/python -m aura_communication.evaluation --behavior disabled

# API
.venv/bin/python -m uvicorn aura_app.api:app --host 127.0.0.1 --port 8000

# M6 patient app + explicit synthetic demo (initial seed ~30 seconds)
.venv/bin/python -m aura_app.demo --db aura-m6-demo.sqlite3
AURA_DEMO_DB=aura-m6-demo.sqlite3 .venv/bin/python -m uvicorn aura_app.demo:create_demo_app --factory --host 127.0.0.1 --port 8000
# Open http://127.0.0.1:8000/; Explore demo selects checkpoint.
# Optional Playwright setup/runner: aura_ui/README.md
```

## Live demo hosting

- **Primary host (user decision, 2026-09-24):** this server (`makodev58-thinkcentre-m920`), exposed publicly through **Cloudflare Zero Trust**. The server already hosts several live apps this way.
- **Configured pattern:** Compose app plus optional dedicated cloudflared sidecar. User manages tunnel/hostname in Zero Trust. Token stays in a protected external file mounted as a Compose secret; only its path goes in ignored `.env`. See `docs/DEPLOYMENT.md`. Keep `AURA_SECURE_COOKIE=true`; explicit `AURA_HTTP_DEMO_HOSTS=192.168.80.193` permits synthetic LAN HTTP only on that IP. No public hostname exception; protected gear still requires HTTPS/loopback. Configuration is persistent in ignored `.env`, not runtime-only.
- Public URL: `https://aura-health.makodev58.com`; basic HTTPS health/status/registry verified 2026-10-08. Redeploy: `docker compose build app`, then `docker compose up -d app`; retain volumes and the existing user-managed Cloudflare container.
- **2026-10-07 user decision:** publish host port on `0.0.0.0:8017`; override with `AURA_DEMO_BIND=127.0.0.1` if needed. Direct HTTP remains synthetic-only/unencrypted/unauthenticated. Public HTTPS cases/isolation verified 2026-10-09.
- A possible Tencent Cloud mirror is pending (see Open decisions). Keep the deployment portable: one-command start, config via environment variables, no host-specific paths.

## Git & remote

- `origin` = `git@github.com:e8aura-makodev58/aura-health.git`; `main` is the integration branch.
- **Required agent branches (user, 2026-10-13):**

  | Agent | Branch |
  |---|---|
  | CodeBuddy | `improve/feature-codebuddy` |
  | Claude | `improve/feature-claude` |
  | Codex | `improve/feature-codex` |

- **Start new work:** check status, preserve unrelated changes, run `git fetch origin`, then create your branch from `origin/main` (e.g. `git switch -c improve/feature-codex origin/main`). If your branch already exists, inspect its history/upstream and continue it; never reset or recreate it over existing work. Use a separate worktree when other agents share this checkout.
- **Publish for review:** commit your work and `HANDOVER.md` on your own branch, then `git push -u origin <your-agent-branch>`. Report branch, commit, changes and verification. Do not push feature work directly to `main`, rename another agent's branch, merge another branch, or deploy without explicit user direction.
- **Review/merge:** branches are reviewed independently and merged one at a time into `main` by whoever the user designates. No agent is the standing reviewer or merger. Resolve handover conflicts by preserving each agent's entries and the latest explicit user decisions. Older SOW/log branch instructions are historical and superseded by this workflow.
- Push with the SSH key `~/.ssh/e8aura-makodev58`. It is already set in the repo-local `core.sshCommand`, so a plain `git push` works. The default `~/.ssh/id_ed25519` authenticates as a different account and fails with "Repository not found".
- The `gh` CLI is not installed.
- Commit author email doesn't matter (user, 2026-09-23).
- `*.sqlite3`, `.venv/`, and `__pycache__/` are gitignored. Never commit the development databases.

---

## Log

### 2026-10-16 — Codex — Private pitch version 2 review
- Reviewed the owner-provided shared v2 and added only a dated §12 comment. Existing body and earlier comments preserved; no private text or review copied to the public repo. Main checkout and fetched origin/main both `0f08fb2`; no further main merge needed.
- Verified: selected tour/sharing source, primary external references, ignored/untracked target, byte-preservation insertion check; UI media smoke 2 PASS/0.164s (existing Starlette/httpx warning). No full suite/browser/live-model/deployment check. Updated this handover only in the tracked worktree.
- Left: editor/owner to decide body changes; no app changes, model calls, publication or deployment.

### 2026-10-16 — Codex — Sync latest main and wait
- User requested latest main in this worktree, then wait. Merged `origin/main` at `0f08fb2` into `improve/feature-codex`; resolved only HANDOVER.md conflicts, preserving both histories and main's newer lock/completed-review status. Older logs archived to keep this note readable.
- Verified: clean starting worktree, fetch/history, UI media smoke 2 PASS/0.180s (existing Starlette/httpx warning). Full suite/browser/live deployment not rechecked; main's recorded results remain attributed to their authors.
- Left: await user instructions; no app edits, model calls, deployment or switching performed.

### 2026-10-16 — Codex — Private pitch deliberation
- Added the requested dated entry only to §12 of the external ignored pitch; preserved all pre-existing text. Discussed the five opening questions using selected locked-tag source and identified claims needing qualification. No pitch copy/content added to the repo; this handover is the only tracked change.
- Verified: fetched origin; clean starting status/history; tag `final-demo-day` resolves to `d043803`; external file ignored/untracked before writing; insertion preservation check PASS. Local `test_ui_media.py`: 2 PASS/0.141s (existing Starlette/httpx warning); no full-suite, browser, live/model or deployment verification. Original brief PDF extraction unavailable with installed tools; scoring-list reconciliation explicitly marked [to verify].
- Left: owner/editor choices and unresolved evidence in the private document. No body edits, implementation, merge or deployment.


### 2026-10-16 — Claude — LOCK: final-demo-day
- User approved the lock after their testing. Final state verified: 396 Python tests OK; 16 hosted browser suites PASS (final_dash 5/5 after the test fix); live on blue 5/5 full guided stories plus past-days update, safety reset, language menu and agent light; green standby full story OK; both servers healthy, AI live, one connector (blue), 10/10 public answers from blue.
- Tagged `final-demo-day` and pushed. Untracked local files left out on purpose (Tencent ADP guide must never be committed; cover/Miora reference images not requested).


### 2026-10-16 — Claude — Full test round before the lock (user request)
- Python: **396 OK** (708 s). Browser (local hosted): catchup_calendar 18, companion 10, milestone7 7, workflows 5, agent 5, plain_language 2, dual_view 12, welcome 3, landing 2, tour 5, cards 4, impression 5, qa_display 2, story_charts 3, settings 1 PASS; final_dash failed intermittently (3 of 5 at one point): the patient summary re-renders once after the flu refresh and the test read a freshly closed fold. Test now reopens the folds before reading; 5/5 PASS after (test-only change, no app change).
- Live (public, blue): 5/5 full guided stories, every step successful (step 5 saved in 17–19 s, clinician answer checked in 24–34 s, ~61–69 s per story); typed past-days update (question shown, 13 days saved, calendar marks); safety-panel reset; language menu and agent light (blue, Tencent Cloud Lighthouse, gpt-6-luna). Green (standby, direct): full story OK.


### 2026-10-16 — Claude — Guided story step 5 robust to slow AI replies (user report)
- User saw "This couldn't be saved just now" after a long wait on step 5. Blue's session showed the typed sentence safety-cleared (normal) but no days saved. Cause: the step waited 60 s for the interpret reply, then tapped days while the reply was still in flight; the late reply added the confirming question, which disables Save, so Save did nothing. Interpret on blue measured 6 s afterwards (transient provider slowness).
- `aura_ui/tour.js`: wait up to 100 s and never tap while a reply may still arrive; if still reading, close the dialog and say "AURA is taking longer than usual right now…"; answer a visible confirming question before saving and wait for Save to unlock.
- Verified: simulated 70 s reply → saved via the typed path; 110 s → clean "taking longer" message; tour.cjs 5 PASS.


### 2026-10-16 — Claude — Guided story: visible "AURA agent is working" state (user request)
- `aura_ui/tour.js` + styles: while a step's real work runs, the status line shows a spinner and "AURA agent is working…" (or "…asking again…"); hovering the button row while Next waits shows a dark overlay "AURA agent is working, please wait…" covering only the Back/Next row (click-through, so Back still works); Next shows a progress cursor. Spinner is still under reduced motion.
- Verified: tour.cjs 5 PASS incl. a new check on step 8 (record_qa slowed 5 s in the test): busy status text and hover overlay visible (opacity > 0.9); screenshot reviewed at 390 px (no text covered).


### 2026-10-16 — Claude — Language moved to a header menu (user request)
- The home Language card is replaced by a globe "EN" button in the header (`#language-button` / `#language-menu`, in `aura_ui/catchup.js`): English ticked; 中文, Bahasa Melayu, தமிழ் greyed, each with "coming soon" in its own language (即将推出 / Akan datang / விரைவில்), plus the future-release note. Menu is placed under the button but clamped on-screen; closes on outside click, Escape, scroll or resize.
- Header fit on phones: at ≤420 px "Disclaimer" becomes a drawn "i" icon (accessible name unchanged); the agent light is dot-only at ≤400 px. Font subsets rebuilt to include the "coming soon" words (~1.5–2 KB each, renamed Aura Han / Aura Tamil). Docs (§15.1, roadmap) updated to "header menu".
- Verified: no horizontal scroll at 320/360/390/414/1280; catchup_calendar 18 (CU1c language menu; one earlier partial run stopped at 10 checks without an error, not reproduced in 3 later full runs), settings, welcome, landing, tour, companion, dual_view PASS; ui_media OK.


### 2026-10-16 — Claude — Language card (Singapore's four languages, English only for now) + multilingual design
- User: show multi-language support for Singapore, greyed out, English default. Patient home `#language-card`: English (selected), 中文, Bahasa Melayu, தமிழ் (disabled, own scripts), note "Chinese, Malay and Tamil are coming in a future release. Each will be safety-tested before it is switched on." No behaviour change; nothing else translated.
- Fonts: `aura_ui/media/aura-zh.woff2` / `aura-ta.woff2` (~1 KB subsets of Noto Sans SC / Noto Sans Tamil, regular, renamed Aura Han / Aura Tamil; SIL OFL licences beside them; rebuild notes in `aura_ui/media/README.md`) so the names render without system CJK/Tamil fonts.
- Docs: architecture document §15 item + §15.1 (safety-first multilingual design: per-language safety validation, reviewed translations, AI text checked in English then translated with back-translation, Tencent hy-mt2 candidates, clinician side English); `docs/ROADMAP.md` "After the hackathon".
- Verified: catchup_calendar (18 incl. CU1c language card), welcome, landing, tour, companion, cards PASS; ui_media OK; no horizontal scroll at 320/390/1280.


### 2026-10-16 — Claude — Tencent models dropped for now (user decision)
- User: drop Tencent models for now; they would need prompt tuning and burned more tokens than gpt-6-luna. Live model stays OpenAI gpt-6-luna medium on both servers (green restored, connection PASS; blue never changed).
- Findings kept for later: TokenHub key reaches 88 listed models; only those with an activated trial answer (others HTTP 402). Hy4 preview: fine for short JSON tasks without tools (activity tagging 34/40 vs luna 36/40 on a 40-note set, ~2.5 s), but ignores tools in JSON mode and fails AURA's agent; with thinking on it can spend 8,000 tokens without answering. Kimi K3: calls tools correctly, but slow (17–29 s per tool step with thinking; 2 of 2 stories timed out on the clinician question even with thinking off; summary 17–23 s).
- Code kept (Tencent-only, tested): TokenHub thinking controls and no JSON mode when tools are offered (`aura_communication/vendor.py`). The user's TokenHub key remains stored on green (unused); `~/hy.token` is 0600.


### 2026-10-16 — Claude — Tencent Hy4 preview trial on green (not adopted)
- User's TokenHub key (file `~/hy.token`, tightened to 0600) stored on green only. TokenHub needed the Hy4 free trial claimed first (HTTP 402 "service ID does not exist" until then).
- Transport fixes for TokenHub (`aura_communication/vendor.py`, tests in `test_reasoning_setting.py`): thinking off on short wording calls (5 s deadline); agent calls send thinking off for reasoning "none", else `reasoning_effort`; no JSON mode when tools are offered (Hy4 ignores native tools in JSON mode). Legacy Hunyuan endpoint and other providers unchanged.
- Result: not usable for AURA's agent without prompt/format rework. Medium reasoning: ~30 s per small task, page requests queued behind them, stories stalled. Reasoning none: past-days sentence failed every time (~41 s, tap fallback); clinician agent 0/6 (first never called tools in JSON mode, then plain-text replies → MALFORMED_JSON). Green restored to OpenAI gpt-6-luna medium (connection PASS, story OK). Blue/public never touched. Pitch line: AURA supports Tencent TokenHub (tested with Hy4 preview); production model choice is the institution's.


### Earlier history
- Older entries from both branches are preserved verbatim in [the main-sync log archive](docs/history/HANDOVER_LOG_2026-10-16_MAIN_SYNC.md), including the link to the earlier pre-architecture snapshot.
