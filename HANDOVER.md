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
3. Keep the file under ~300 lines. When the log grows past about 15 entries, condense the oldest ones into a single "Earlier history" bullet list.
4. Commit it with your work (`docs: update handover`) and push (see **Git & remote**).

**Rules:**
- State facts you verified. Mark anything unverified as *(unverified)*.
- Don't record secrets, tokens, or real patient data here.
- Record user decisions and preferences as they are given, with the date.

---

## Current state (as of 2026-10-07)

- **Project name:** officially **aura-health** (user, 2026-09-23). Care Plan Bridge (`PRODUCT_FRAMEWORK*.md`, `FRAMEWORK_CRITIQUE.md`) was dropped; those docs are marked superseded and kept for background only.
- **Product being built:** a longitudinal, wearable-first companion for adults on stable antidepressant maintenance treatment. Spec: `aura_health_framework_v1.0.md`. Safety policy: `aura_deterministic_safety_policy_state_machine_v1.2.md`.
- **Milestones 1–4 are complete; M4.5 documentation is complete.** The Milestone 4 engineering stop condition is met. See `MILESTONE3_REVIEW.md` and `MILESTONE4_REVIEW.md`.
  - `aura_safety/`: deterministic safety state machine (no LLM).
  - `aura_longitudinal/`: personal baseline, drift, context, held-for-review, and communication engines.
  - `aura_app/`: FastAPI + SQLite application layer. It handles idempotent event ingestion, atomic transactions, safety-first gating, the timeline, and the clinician review snapshot (never shared automatically).
- **M5 implemented and reviewed (Claude, 2026-10-02; no blocking findings):** [`MILESTONE5_REVIEW.md`](MILESTONE5_REVIEW.md). `aura_communication/` supplies bounded wording contracts, validator/fallback, optional HTTP gateway, fixture evaluation, and engineering configuration. `aura_app/communication.py` reads committed decisions/safety references and persists race-checked wording/audit. Accepted domain algorithms remain unchanged.
- **M6 implemented; reviewed by Claude 2026-10-03, no blocking findings:** [`MILESTONE6_REVIEW.md`](MILESTONE6_REVIEW.md). `aura_ui/` is a responsive, no-build-step patient web app. It uses existing APIs for check-ins, medication records, explicit explanations, review preview, and pinned safety. `PatientViewService` provides read-only latest-event/provenance links. The explicitly synthetic demo factory shows stable + Cases A–F with before/after explanation and gap/return checkpoints. Accepted safety/longitudinal algorithms and DB schema are unchanged.
- **Tests:** 170 pass (`.venv/bin/python -m unittest discover -s tests -q`, 234.226 s), including six capacity regressions, EV1–EV14 and previous gates. Latest Chromium: dual-view **12 PASS**, hosted **7 PASS** (including capacity message/retry), settings UI PASS, and **8 layout checks PASS**; 320/390/1280 plus short-screen safety/composer. Existing patient/offline/retry **17 PASS** in the prior dual-view session. Provider checks use mocks, not paid/live calls. Existing Starlette/httpx deprecation remains.
- **M7 local implementation:** `aura_simulation/` validated scenario planning, deterministic observable-only driver/replay, 16 DEMO tests; atomic initial seeding and recoverable operator reset; `aura_app.hosted` isolated synthetic browser workspaces with fixture-only writes/reset; Docker + optional file-secret Cloudflare sidecar. Diagram/runbook: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md). Demo is healthy on **0.0.0.0:8017** (user-requested network publishing); LAN address `http://192.168.80.193:8017`. **User reports live hosting; public hostname/HTTPS unverified; M7 not complete.**
- **Demo capacity fix deployed:** only `GET /demo/scenarios` allocates a private workspace. Shell/assets/probes no longer consume slots; cookie-less patient requests return `DEMO_SESSION_REQUIRED` without allocation. Capacity keeps existing sessions and provides visible retry/local resource fallback. Deployment retains `AURA_SECURE_COOKIE=true`: public HTTPS is required; LAN HTTP needs the explicit false override in the runbook. Restart retains old files/provider settings but gives browsers fresh synthetic workspaces; no domain policy/state transition changed.
- **Integration contradiction fixed:** application projector previously omitted the accepted domain's new-longitudinal-signal reopening input. It now forwards newly production-assessed persistent/divergent signals; DEMO11 verifies reopening with unchanged anchors. Safety/longitudinal domain algorithms and clinical configuration remain unchanged.
- **Canonical plan:** [`docs/ROADMAP.md`](docs/ROADMAP.md), [`docs/DECISIONS.md`](docs/DECISIONS.md), [`docs/milestones/`](docs/milestones/), and [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md).
- **Operator provider settings implemented:** header gear supports OpenRouter, OpenAI, DeepSeek and Tencent (TokenHub Singapore/Guangzhou, legacy Hunyuan). Fixed-host native transports are injected only into hosted synthetic workspaces; ordinary patient API remains disabled. Admin unlock requires HTTPS/loopback origin plus private server token. Keys are write-only and stored separately in owner-only plaintext files, not encrypted/prod secrets management. See [`docs/SYSTEM_SETTINGS.md`](docs/SYSTEM_SETTINGS.md). Live calls default off pending operator key/model/enablement; no real provider call verified. Per-response/configuration disclosure is truthful. Accepted domain algorithms unchanged.
- **Not built/verified by Codex:** real safety detectors, production patient auth, clinician-sharing workflow, institutional on-prem/private-cloud deployment, repository Cloudflare sidecar. User-managed hosting is reported but public HTTPS unverified. Simulation planner stays offline; optional gateway is mock-tested. Public non-demo safety gate holds unassessed text; hosted demo rejects non-fixture input before storing.
- **Ownership (user, 2026-10-02):** Codex has implementation authority; Claude Sonnet 5.5 is reviewer.
- **CodeBuddy workflow (user, 2026-10-02):** do not run CodeBuddy automatically. Finish and agree on our product first, then prepare a detailed SOW for the user to manually trigger a clean rebuild. Compare the completed apps and reuse reviewed improvements; our version may be submitted. Collect actual evidence during that rebuild; none is claimed yet.
- **Data:** synthetic only (simulator cases A–F).
- **Dual-view scope approved / implemented (user, 2026-10-07: "Proceed"):** clinician-first read-only workspace, shared historical evidence projection, Patient / Clinician demo toggle, minimal patient home and optional **See my full data**. Opens Case B; guide retains A–F/checkpoints. Explicit disclosure distinguishes full synthetic inspection from future patient-approved clinician access. `GET /patients/{id}/evidence` exposes committed snapshots/anchor versions without replay, mutation or generation. Quiet home has no default metrics/tasks; check-in/routine are collapsed. Questions/review items and temporary appointment preview remain not sent. Active/degraded/offline safety stays independently visible even without an episode. See `docs/DUAL_VIEW_IMPLEMENTATION.md`. Deployed on 8017; **Claude implementation review and user UX acceptance pending**. Accepted engines/schema/dependencies unchanged; additional data and CodeBuddy deferred.

## Open decisions

- **Experience acceptance / Claude implementation review:** scope is approved and implemented; review GP usefulness, minimal patient burden and source/chart fidelity before more features. No extra concern categories, ordinary deferral or persisted sharing were added. Five concern paths, saved approval and production clinician authorization still do not exist.

- **Live provider smoke test:** operator selects provider/model and supplies keys through the protected gear dialog, not chat. Native transports are mock-tested; actual provider/model access remains unverified until an operator runs the synthetic connection test. Do not enable the ordinary patient API.
- **Public URL verification:** user reports the demo is live; hostname is not supplied, so external HTTPS remains unverified. Repository sidecar has not been provisioned by Codex; do not assume it is the user's hosting route or request a token unnecessarily.
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

## Active milestone: M7 — Dual-view implementation ready for review

Scope/gate: [`docs/milestones/M7_DEMO_AND_INTEGRATION.md`](docs/milestones/M7_DEMO_AND_INTEGRATION.md); local evidence: [`MILESTONE7_REVIEW.md`](MILESTONE7_REVIEW.md). M5/M6 were accepted by Claude. Do not begin M8 or label M7 accepted before public reachability and review. Domain algorithms remain authoritative.

User approved the revised scope and implementation is deployed on 8017. Current
priority is Claude review and user experience feedback, not new features. The
public-link gate remains open. No new clinical scope is authorized.

## Next steps

1. **Claude: review the approved dual-view implementation**, `docs/DUAL_VIEW_IMPLEMENTATION.md`, `aura_app/evidence.py`, repository read method and UI/tests. Check no engine replay/mutation or hidden truth; exact source/anchor values and gaps; same-patient zero-write toggle; active/degraded/offline safety independent of episode presence; honest sharing/temporary preview; clinician read-only and protected gear. User should review the live experience (start B, then D; switch Patient, open full data). Do not expand scope until feedback. No automatic CodeBuddy run.
2. Obtain the live hostname from the user and verify HTTPS/public Cases A–F/isolation/fallback. User reports it is live and requested `0.0.0.0:8017` publishing. Record the URL only after verification; then seek M7 acceptance. Do not invent clinical policy to smooth the demo.
3. The user controls CodeBuddy timing. After agreement on the final product, produce the detailed rebuild SOW, compare the user-run implementation, and capture real evidence required for submission.
4. Preserve known issues from `MILESTONE4_REVIEW.md` §13 and M6 limits:
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
- **Configured pattern:** Compose app plus optional dedicated cloudflared sidecar. User manages tunnel/hostname in Zero Trust. Token stays in a protected external file mounted as a Compose secret; only its path goes in ignored `.env`. See `docs/DEPLOYMENT.md`. Local HTTP testing uses `AURA_SECURE_COOKIE=false`; public HTTPS must restore true.
- Record the public URL and redeploy steps here once live.
- **2026-10-07 user decision:** publish host port on `0.0.0.0:8017` for network access; override with `AURA_DEMO_BIND=127.0.0.1` if needed. Direct HTTP remains synthetic-only, unencrypted and unauthenticated. User reports live hosting; public hostname/reachability still unverified by Codex.
- A possible Tencent Cloud mirror is pending (see Open decisions). Keep the deployment portable: one-command start, config via environment variables, no host-specific paths.

## Git & remote

- `origin` = `git@github.com:e8aura-makodev58/aura-health.git`, branch `main`.
- Push with the SSH key `~/.ssh/e8aura-makodev58`. It is already set in the repo-local `core.sshCommand`, so a plain `git push` works. The default `~/.ssh/id_ed25519` authenticates as a different account and fails with "Repository not found".
- The `gh` CLI is not installed.
- Commit author email doesn't matter (user, 2026-09-23).
- `*.sqlite3`, `.venv/`, and `__pycache__/` are gitignored. Never commit the development databases.

---

## Log

### 2026-10-07 — Codex Sol — Fix demo session exhaustion
- User reported `DEMO_BUSY`. Hosted requests previously allocated workspaces for shell/assets/probes and each missing-cookie API call. Now only explicit catalog bootstrap allocates; cookie-less APIs fail clearly without new processing. Static shell loads at capacity; retry is visible with independent local resources. Existing sessions remain protected, bounds unchanged. See `docs/DEPLOYMENT.md`.
- Verified: baseline 164 PASS; final **170 Python tests PASS** (234.226 s); six allocation regressions, Chromium dual-view 12 PASS, hosted 7 PASS including initial 503/retry, settings PASS, layout 8 PASS. `git diff --check` clean. Rebuilt Docker healthy on 0.0.0.0:8017; shell/assets 200 and missing-cookie error verified. No paid model calls or domain/schema/dependency changes.
- Deployment uses Secure cookies; public HTTPS remains unverified pending user URL. Direct LAN HTTP needs explicit false override, not an automatic weakening of public cookie security. Restart gives browsers fresh synthetic clones while retaining old files/settings. Claude/user dual-view review remains pending; no new milestone started.

### 2026-10-07 — Codex Sol — Clinician-first dual view and minimal patient experience
- User approved the revised plan with "Proceed". Added shared `EvidenceViewService`/repository snapshot read/GET evidence endpoint, `aura_ui/evidence.js` native charts, same-record demo toggle, clinician-first B, minimal patient home/full-data entitlement and factual temporary appointment preview. Documentation: `docs/DUAL_VIEW_IMPLEMENTATION.md`; plan/decisions/UI README updated. No accepted engine/schema/dependency changes or additional data.
- Charts use exact committed values/versions, explicit gaps and signal-linked contexts; categorical reports, questions/review items and safety provenance stay descriptive. Unsupported hosted illness explanations are not offered as submit actions; exact prepared D fixture still invokes production hold. Gear, idempotency, pinned resources/offline and fixture-only writes preserved. Toggle is not authorization/sharing.
- Verified: **164 Python tests PASS** (236.044 s); Chromium patient **17 PASS**, dual view **12 PASS**, hosted **6 PASS**, settings PASS, layout **8 PASS**; no page errors. Historical v2 reanchor/reload and zero-write toggle checked. `git diff --check` clean; Docker rebuilt/healthy on **0.0.0.0:8017**. Artifacts `/tmp/aura-dual-hosted-browser`, `/tmp/aura-dual-m6-regression`; no paid model call or CodeBuddy run.
- Review next, not acceptance: user UX feedback and Claude implementation review. Public HTTPS remains unverified; governance/clinical limits remain. No M8/additional-data/auth/sharing work started.

### 2026-10-07 — Codex Sol — Revised clinician-first plan after Claude review
- Addressed Claude's three required changes and scope cuts in `docs/DUAL_VIEW_EXPERIENCE_PLAN.md`; recorded relayed user direction in `docs/DECISIONS.md` §37. Same read projection, patient entitlement, exact synthetic sharing disclosure, display-only 8-week/all filter, B/D-first clinician build and minimal patient follow-up. No runtime/deployment changes.
- Verified source: committed event results contain anchor version/reference/creation/reviewer and rolling snapshots; current repository event reads discard those results, so a new read interface is still needed. Mutable latest baselines are not a version ledger. Corrected proposed safety collapsing: active/degraded policy and resources stay visible even without an episode ID.
- Verified: `.venv/bin/python -m unittest discover -s tests -q` — **150 PASS** (198.324 s); `git diff --check` clean. User agreement next, not implementation. Additional data and CodeBuddy remain deferred.

### 2026-10-07 — Codex Sol — Delegated patient/clinician dual-view planning
- User identifies the missing audience split: very simple, intuitive, more visual patient experience; separate analytical clinician dashboard; Patient / Clinician demo toggle. Delegated planning to `/root/dual_view_planning` explicitly as requested. Proposal: `docs/DUAL_VIEW_EXPERIENCE_PLAN.md`; user direction recorded in `docs/DECISIONS.md` §37. No implementation/deployment changes.
- Main reviewed endpoint/repository evidence: current status vs saved per-event baselines, source observations/timeline, snapshot limits, synthetic allowlist and safety boundary. Plan distinguishes new read-only projections from new approval/deferral/concern workflows, preserves same selected synthetic patient across toggle, and makes the toggle neither permission nor sharing. Existing before/after checkpoints are different seeded records, not fabricated continuous transitions.
- Verified: `.venv/bin/python -m unittest discover -s tests -q` — **150 PASS** (201.321 s); `git diff --check` clean. These are unchanged engineering tests, not acceptance of the proposed UX. **Claude review next**, through this file; detailed user agreement required before coding. Additional data and CodeBuddy remain deferred.

### 2026-10-07 — Claude — Review of dual-view plan; clinician-first, patient entitlement
- Read `docs/DUAL_VIEW_EXPERIENCE_PLAN.md`, `DECISIONS.md` §37, `aura_app/longitudinal.py`. Wrote "Claude review of the dual-view plan" above. Recorded user direction: clinician view is the main product; patient analytics on demand, patient entitled to them. Three required changes, Q1–Q5 answers, scope warning. Docs only.
- Verified: nothing run beyond reading; anchor-version history not verified. Not user-approved.

### 2026-10-07 — Codex Sol — Response to Claude and proposed patient walkthrough
- Read Claude's recommendation, inspected actual demo/hosted allowlists, safety adapter and review snapshot. Agree on ordinary-day minimal burden and patient/demo/operator separation. Added `docs/PATIENT_EXPERIENCE_STORYBOARD.md` with four journeys, reuse analysis and answers a–c.
- Corrections: five concern categories are not currently resolved paths; chips cannot automatically clear independent evidence; work stress is risk context; held input cannot be promised as an assessed appointment note; versioned note saving is new work. Keep visible synthetic disclosure, optional inspection and complete accessible safety resources. No runtime changes or deployment actions.
- Verified: `.venv/bin/python -m unittest discover -s tests -q` — **150 PASS** (199.344 s); `git diff --check` clean. Docs only. User agreement remains required before implementation; tests are not usability evidence.

### 2026-10-07 — Claude — Product reassessment recommendation
- Read `HANDOVER.md`, `docs/PRODUCT_REASSESSMENT.md`, framework §2–3/5/17/29–32 and `aura_ui/index.html`. Wrote the recommendation section above: value sentence, journey ranking, default/optional/demo split, walkthroughs, non-UI gaps, storyboard, acceptance criteria, three questions for Codex. Docs only (`HANDOVER.md`).
- Verified: repo clean at `97dd66a` on arrival. Tests not re-run (no code touched).
- Watch out for: this is a recommendation, not user-approved. No implementation until Codex responds and the user agrees.

### 2026-10-07 — Codex Sol — Pause implementation for joint product reassessment
- User says the application remains extremely unintuitive, overwhelming and unclear in purpose; asks to step back and deliberate with Claude before continuing. Recorded this as a blocking product decision, not an invitation to restyle again.
- Re-read the complete canonical framework; prepared `docs/PRODUCT_REASSESSMENT.md` with code/screenshot-grounded concerns, patient journeys and a concrete request for Claude through this file. Marked the previous redesign as technically implemented but not accepted as a satisfactory experience. No runtime/test/configuration/deployment changes.
- Verified: clean worktree on arrival, HEAD `84a272e`; `.venv/bin/python -m unittest discover -s tests -q` — **150 PASS** (199.858 s), `git diff --check` clean. These remain engineering checks, not patient-usability evidence. Claude has not yet responded; no joint agreement is claimed. Next: Claude recommendation, Codex deliberation, then user agreement before coding.

### 2026-10-07 — Codex Sol — Implement patient-first mobile/laptop redesign
- User explicitly requested the actual redesign after clarifying that the previous release only added settings. Rebuilt `aura_ui/index.html`, `styles.css` and presentation logic: compact Today, expandable routine, persistent help, three primary tabs/laptop rail, progressive reference/review details, temporary-preview labels and honest synthetic-example composer. Independent safety region remains across pages, focusable/scrollable on short screens. No backend/domain/schema/dependency changes or additional data generation.
- Verified: full Python suite **150 PASS**; existing Chromium **17 PASS**, hosted **6 PASS**, settings UI PASS, new UX1–UX8 **8 PASS**, no page errors. Phone widths 320/390, laptop 1280, safety 390×500, compact composer 390×360. Inspected screenshots; `git diff --check` clean. Updated obsolete visual assertions, preserving original behavioral gates. Docker rebuilt on 0.0.0.0:8017.
- Delivery notes: `docs/PATIENT_UX_REDESIGN.md`, `aura_ui/README.md`; screenshot/results `/tmp/aura-redesign-browser-artifacts`. Left: user/reviewer design feedback, operator live synthetic smoke test, public hostname verification. No CodeBuddy run or clinical validation claim.

### 2026-10-07 — Codex Sol — Protected provider settings gear
- Adapted Compass's write-only credential/per-provider model pattern. Added `aura_app/system_settings.py`, `aura_communication/vendor.py`, settings dialog/script, native OpenRouter/OpenAI/DeepSeek/Tencent transport and synthetic-only hosted injection. Owner-only atomic files, admin token/secure-origin gate, bounded calls, discovery/test and revision-based cache invalidation. Disclosure reflects actual generation/fallback. See `docs/SYSTEM_SETTINGS.md`.
- Verified: full Python suite **150 PASS**; Chromium patient checks **17 PASS**, hosted checks **6 PASS**, settings UI PASS at 320/390/1280 widths. Mocks only: no paid/live provider call and no real credential read/printed. `git diff --check` clean. Docker rebuilt on 0.0.0.0:8017. Fixed navigation stacking so the sticky safety panel cannot block bottom navigation; no domain policy change.
- Left: operator credentials/model and live synthetic smoke test, broader UX redesign, public hostname verification. No additional data generation, patient model enablement or clinical logic changes.

### 2026-10-07 — Codex Sol — Live synthetic AI decision and dedicated UX review
- User requests live model on synthetic data and future institution-managed on-prem/private-cloud direction; rejects “no live model” as a permanent stance. Recorded decision §36, integration boundary/configuration needs in `docs/SYNTHETIC_LIVE_MODEL.md`.
- Explicitly delegated read-only UI/UX review: mobile portrait-first Today/Patterns/Review, persistent help, compact routine/check-ins, progressively disclosed context/reference/review, honest fixture composer and laptop reading-column adaptation. Proposal in `docs/PATIENT_UX_REDESIGN.md`; no UI/domain/runtime changes yet.
- Verified: `.venv/bin/python -m unittest discover -s tests -q` — 140 tests PASS (168.416 s); `git diff --check` clean. Documentation only. Additional synthetic data deferred by user. Provider/model/endpoint/secret provisioning is unresolved; actual live use is not claimed. User alone controls CodeBuddy.

### 2026-10-07 — Codex Sol — Publish demo on all network interfaces
- User requested `0.0.0.0`. Compose now defaults to `0.0.0.0:8017` with `AURA_DEMO_BIND` override; deployment/example configuration updated. Domain logic unchanged.
- User reports hosting is live; hostname is not yet supplied, so public HTTPS verification remains open. No tunnel credentials requested or changed in this task.
- Verified: Docker publishes `0.0.0.0:8017->8000`, container healthy, loopback and LAN health return synthetic-only OK; full suite 140 tests PASS (165.953 s), `git diff --check` clean. Direct HTTP remains unencrypted; use only synthetic fixtures.

### 2026-10-07 — Codex Sol — M7 local integration and synthetic deployment
- Added scenario planner/validated gateway interface, observable-only replay driver, DEMO1–DEMO16, atomic seed/reset, private fixture-only hosted sessions, Docker/Cloudflare file-secret configuration, diagram and demo/runbook. See `MILESTONE7_REVIEW.md` for commands/results and limitations.
- Integration contradiction: forwarded existing domain new-signal reopening input from application projector; anchors and accepted safety/longitudinal algorithms/configuration unchanged. Replay compares semantic state/actions with review rows ordered by stable source references, not random SQL IDs.
- Verified: 140 Python tests PASS; real Chromium 17 existing + 6 hosted PASS; 150-entry semantic replay exact; Docker loopback healthy. Timing: 30.828 s initial prepare, 12.840 ms median status, 17.768 ms reset. Public Cloudflare URL remains pending user hostname/token-file path; M7 remains active. No M8 or CodeBuddy work started.

### Earlier history — 2026-09-23 to 2026-10-03
- M6 implemented and accepted by Claude on 2026-10-03; 124 Python tests PASS, Chromium UI1–UI15/offline/retry 17 PASS at 320/390/1280. Read-only provenance, fixture-only demo, independent safety/resources and same-key retry; no domain/schema changes. M7 subsequently restricted assets and disabled CDN-backed docs. See `MILESTONE6_REVIEW.md`.
- M5 implemented and accepted by Claude (2026-10-02), 106 tests PASS, nine wording fixtures PASS with fixture/disabled providers. Candidate validation, race-checked commit, static prohibited modes and append-oriented wording/audit verified; domain engines unchanged. Live provider not tested. See `MILESTONE5_REVIEW.md`; regex validation remains defense-in-depth only. User assigned implementation ownership to Codex and CodeBuddy timing to themselves; product-first/manual rebuild workflow supersedes older scheduling.
- Milestones 1–4 implemented, 69 tests PASS; Claude reviewed M4, created this handover, and pushed repository history (initial implementation `527cc13`, LICENSE merge `97aad5b`). Canonical evidence: `MILESTONE3_REVIEW.md`, `MILESTONE4_REVIEW.md`.
- User named the project `aura-health` and superseded Care Plan Bridge (2026-09-23); older framework files retain explicit superseded banners.
- M4.5 canonicalized roadmap/decisions/M1–M8/demo script; P1–P18/L1–L14/A1–A20 trace to tests. No reconstructed criterion; corrected accepted CLOSED/high-tier correction chronology and safety-first M4 shorthand. 69 tests PASS; docs-only `358f5c9`.
- Claude reviewed M4.5 and added submission requirements, exact CodeBuddy evidence minimum, intended-use/safety containment details and live-link gate. M1/M2 review chronology has no separate committed packets; actual tests back behavior.
- User required a live demo on this server via Cloudflare (2026-09-24); optional per-app sidecar rather than host install. Tencent mirror deferred until near the deadline. Current hosting/CodeBuddy decisions above supersede older timing instructions.
