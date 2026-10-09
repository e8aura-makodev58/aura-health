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
- **Updates are asynchronous.** Claude and Codex may work and edit this file at the same time, so it can change under you. Before editing, `git pull --rebase` and re-read the sections you will touch. Make small, targeted edits (add your own Log entry; edit only the lines you own) instead of rewriting the file. On a conflict, keep both sides' entries and resolve by hand; never overwrite another agent's entry. Order Log entries by when they were written, and treat a Current state line as possibly stale until you check the repo.
- **Review asynchronous updates with the human in the loop (HIL).** Another agent's entries made since your last session (decisions, specs, DECISIONS sections) were recorded from separate chats. Before building on them, list what changed (`git log`, newest Log entries) and confirm with the user anything that changes scope or behaviour. Do not treat a recorded decision as approved for implementation just because it is written here; the user has the final say.

---

## Current state (as of 2026-10-08)

- **Project name:** officially **aura-health** (user, 2026-09-23). Care Plan Bridge (`PRODUCT_FRAMEWORK*.md`, `FRAMEWORK_CRITIQUE.md`) was dropped; those docs are marked superseded and kept for background only.
- **Product being built:** a longitudinal, wearable-first companion for adults on stable antidepressant maintenance treatment. Spec: `aura_health_framework_v1.0.md`. Safety policy: `aura_deterministic_safety_policy_state_machine_v1.2.md`.
- **Milestones 1–4 are complete; M4.5 documentation is complete.** The Milestone 4 engineering stop condition is met. See `MILESTONE3_REVIEW.md` and `MILESTONE4_REVIEW.md`.
  - `aura_safety/`: deterministic safety state machine (no LLM).
  - `aura_longitudinal/`: personal baseline, drift, context, held-for-review, and communication engines.
  - `aura_app/`: FastAPI + SQLite application layer. It handles idempotent event ingestion, atomic transactions, safety-first gating, the timeline, and the clinician review snapshot (never shared automatically).
- **M5 implemented and reviewed (Claude, 2026-10-02; no blocking findings):** [`MILESTONE5_REVIEW.md`](MILESTONE5_REVIEW.md). `aura_communication/` supplies bounded wording contracts, validator/fallback, optional HTTP gateway, fixture evaluation, and engineering configuration. `aura_app/communication.py` reads committed decisions/safety references and persists race-checked wording/audit. Accepted domain algorithms remain unchanged.
- **M6 implemented; reviewed by Claude 2026-10-03, no blocking findings:** [`MILESTONE6_REVIEW.md`](MILESTONE6_REVIEW.md). `aura_ui/` is a responsive, no-build-step patient web app. It uses existing APIs for check-ins, medication records, explicit explanations, review preview, and pinned safety. `PatientViewService` provides read-only latest-event/provenance links. The explicitly synthetic demo factory shows stable + Cases A–F with before/after explanation and gap/return checkpoints. Accepted safety/longitudinal algorithms and DB schema are unchanged.
- **Tests:** **211 PASS** (`.venv/bin/python -m unittest discover -s tests -q`, 270.742 s); SR1–SR16 plus AG1–AG20 focused **36 PASS** (34.329 s). Chromium: hosted agent **5 PASS**, dual view **12 PASS**, settings PASS at 320/390/1280; new research/display-only chart suite **3 PASS** at 390/1280 with typed synthetic measurements. Earlier development patient/offline/retry **17 PASS** remains historical evidence. No paid calls in the registry session; provider tests are mocked and historical live smokes are not clinical validation. Existing Starlette/httpx deprecation remains.
- **M7 local implementation:** `aura_simulation/` validated scenario planning, deterministic observable-only driver/replay, 16 DEMO tests; atomic seeding/reset; `aura_app.hosted` isolated synthetic workspaces with fixture-only writes; Docker + optional Cloudflare sidecar. Diagram/runbook: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md). Healthy on **0.0.0.0:8017**, LAN `http://192.168.80.193:8017`; public HTTPS health/status/registry verified at `https://aura-health.makodev58.com`. **Full public case/isolation/fallback checks and review remain open; M7 not complete.**
- **Demo capacity/cookie fixes deployed:** only `GET /demo/scenarios` allocates a private workspace. Shell/assets/probes no longer consume slots; cookie-less patient requests return `DEMO_SESSION_REQUIRED` without allocation. Capacity keeps existing sessions and provides visible retry/local resource fallback. Deployment retains `AURA_SECURE_COOKIE=true`, with ignored `.env` explicitly allowing HTTP demo cookies only for `192.168.80.193` through `AURA_HTTP_DEMO_HOSTS`. Public hostnames and HTTPS retain Secure; protected settings authorization is unchanged. Real phone-sized Chromium verified LAN page/API/reload and same-session retention. Restart retains old files/provider settings but gives browsers fresh synthetic workspaces; no domain policy/state transition changed.
- **Integration contradiction fixed:** application projector previously omitted the accepted domain's new-longitudinal-signal reopening input. It now forwards newly production-assessed persistent/divergent signals; DEMO11 verifies reopening with unchanged anchors. Safety/longitudinal domain algorithms and clinical configuration remain unchanged.
- **Scope (2026-10-09, DECISIONS §42):** focus is antidepressant maintenance; the architecture should stay open to other conditions later (condition-specific content in configuration). Nothing is built or claimed for other conditions. Patients often have several conditions; treat the whole person as the unit in design discussions (§42 addendum, not an approved feature).
- **Current product statement (2026-10-08):** [`docs/PRODUCT_VISION.md`](docs/PRODUCT_VISION.md) — purpose, layers, journeys, state, and an honest diagnosis of why the demo underwhelms plus ranked fixes.
- **Canonical plan:** [`docs/ROADMAP.md`](docs/ROADMAP.md), [`docs/DECISIONS.md`](docs/DECISIONS.md), [`docs/milestones/`](docs/milestones/), and [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md).
- **Operator provider settings:** header gear supports OpenRouter, OpenAI, DeepSeek and Tencent; live transports are hosted synthetic-only. Admin unlock still requires HTTPS/loopback plus private server token; write-only owner-only files are not production secrets management. **Current provider is DeepSeek / deepseek-flash / live enabled**, verified 2026-10-08 at `https://aura-health.makodev58.com/system/status`. No paid model calls in the registry session. Earlier OpenAI/gpt-6-luna connectivity/agent smokes remain historical evidence, not the current configuration. See [`docs/SYSTEM_SETTINGS.md`](docs/SYSTEM_SETTINGS.md).
- **Not built/verified by Codex:** real safety detectors, production patient auth/sharing, institutional deployment or provisioning the existing Cloudflare container. Public HTTPS health/status/registry now verified; complete public case flow remains unchecked. Simulation planner stays offline; gateway mock-tested. Public non-demo safety gate holds unassessed text; hosted rejects non-fixture input before storing.
- **Ownership (user, 2026-10-02):** Codex has implementation authority; Claude Sonnet 5.5 is reviewer.
- **CodeBuddy workflow (user, 2026-10-02):** do not run CodeBuddy automatically. Finish and agree on our product first, then prepare a detailed SOW for the user to manually trigger a clean rebuild. Compare the completed apps and reuse reviewed improvements; our version may be submitted. Collect actual evidence during that rebuild; none is claimed yet.
- **Data:** synthetic only (simulator cases A–F).
- **Dual-view scope approved / implemented (user, 2026-10-07: "Proceed"):** clinician-first read-only workspace, shared historical evidence projection, Patient / Clinician demo toggle, minimal patient home and optional **See my full data**. Opens Case B; guide retains A–F/checkpoints. Explicit disclosure distinguishes full synthetic inspection from future patient-approved clinician access. `GET /patients/{id}/evidence` exposes committed snapshots/anchor versions without replay, mutation or generation. Quiet home has no default metrics/tasks; check-in/routine are collapsed. Questions/review items and temporary appointment preview remain not sent. Active/degraded/offline safety stays independently visible even without an episode. See `docs/DUAL_VIEW_IMPLEMENTATION.md`. Deployed on 8017; **Claude implementation review and user UX acceptance pending**. Accepted engines/schema/dependencies unchanged; additional data and CodeBuddy deferred.
- **aura-agent implemented (user request 2026-10-07; completed 2026-10-08):** five server-owned `aura_agent/skills/*/SKILL.md` capabilities: clinician brief, record Q&A, patient recap, visit draft and approved-question ranking. Native model-selected read-tool loop, NORMAL-only/assessed-input guard, grounded structured claims, budgets, honest extraction fallback, race/idempotency checks and additive append-only `agent_runs` trace storage. Hosted provider settings only; accepted safety/longitudinal algorithms and dependencies unchanged. UI adds explicit brief/Q&A/source/trace controls, optional collapsed monthly mini-charts and removable **Not sent** visit draft. No automatic calls on load/toggle. See [`docs/AURA_AGENT_IMPLEMENTATION.md`](docs/AURA_AGENT_IMPLEMENTATION.md); decision §38. Deployed healthy on 8017; Claude review pending.
- **Live agent smoke:** OpenAI `gpt-6-luna` clinician brief PASS (six read tools, three cited findings, 11,705 ms); record Q&A PASS (different six-tool order, two cited sentences, 11,869 ms). Both exact retry drafts reused persisted runs. Earlier conservative vocabulary rejections/timeouts fell back safely; separate agent timeout is 15 s within 50 s overall, M5 timeout unchanged. Other skills are mocked/offline-tested, not a claimed live sweep or clinical validation. Final test summary is in the newest log.
- **Signal-registry foundation implemented (DECISIONS §41):** sponsor-editable/versioned `aura_longitudinal/signal_registry.json` and `AURA_SIGNAL_REGISTRY` override; `GET /signals`, typed scalar ingestion, source-linked research/display-only charts and agent evidence. Original four parameter values/rules retained; HRV/respiratory rate/skin deviation enabled E3_RESEARCH; SpO2/BP/thermometer/weight display-only. Calendar coverage is not cadence-discounted or interpolated. New-channel anchors require calendar coverage; configurable absolute spread floor handles zero-centered skin deviation (0.1 °C provisional default). No safety changes, DB schema/dependencies, real intake, simulator agent or flu generator in this step. Details: [`docs/SIGNAL_REGISTRY_IMPLEMENTATION.md`](docs/SIGNAL_REGISTRY_IMPLEMENTATION.md).

## Open decisions

- **User approvals 2026-10-08 ("I approve all"):** all five items in `docs/CLAUDE_AGENT_REVIEW_AND_PROPOSALS.md` §7 are approved (see `docs/DECISIONS.md` §39). DeepSeek `deepseek-flash` is active (public `/system/status` confirmed it, live). Also approved: show provider+model in the settings dialog without unlock (endpoint already public; UI-only change), and a demo-only **patient simulator agent** (§40, plan `docs/PATIENT_SIMULATOR_AGENT_PLAN.md`). User posture (2026-10-08, DECISIONS §41): developer proposal for a sponsor who owns clinical/regulatory judgment; new signals may enter the engine via a sponsor-editable **signal registry** (continuous wearable channels vs intermittent BP/thermometer/weight), see simulator plan §3.

- **Approved, not yet implemented:** agent-readable claim verification/verifier/parametrized analysis tools, consolidated Disclaimer page, provider/model visible before unlock, structured demo entry/import, layered raise-only free-text gate, and patient simulator. The detector is already approved under §39; it is not a remaining permission blocker. Existing hosted fixture-only intake and conservative agent guard remain until the gated paths exist. Registry foundation is the first simulator dependency, not simulator completion.

- **Agent review:** user authorized implementation of Claude's plan; approval is no longer blocked. Claude should review guard/scoping, grounding limitations, trace/race behavior and actual usefulness before acceptance. Safety doctrine remains unchanged; read-only synthesis sits outside policy ownership. Clinical/content governance remains open, not silently delegated to AI.

- **Experience acceptance / Claude implementation review:** scope is approved and implemented; review GP usefulness, minimal patient burden and source/chart fidelity before more features. No extra concern categories, ordinary deferral or persisted sharing were added. Five concern paths, saved approval and production clinician authorization still do not exist.

- **Public URL:** `https://aura-health.makodev58.com` is now supplied by Claude and its public HTTPS `/system/status` responds. Public Cases A–F/isolation/fallback have not yet been fully verified; M7 acceptance remains open. Do not assume repository sidecar is the hosting route.
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

## Active milestone: M7 — Approved agent improvements and simulator foundation

Scope/gate: [`docs/milestones/M7_DEMO_AND_INTEGRATION.md`](docs/milestones/M7_DEMO_AND_INTEGRATION.md); local evidence: [`MILESTONE7_REVIEW.md`](MILESTONE7_REVIEW.md). M5/M6 were accepted by Claude. Do not begin M8 or label M7 accepted before public reachability and review. Domain algorithms remain authoritative.

User approved §39–41 work; signal registry is implemented for review. Sponsor owns
clinical/regulatory assessment; engineering choices are configuration, not clinical
claims. Safety doctrine is unchanged. Full simulator and input paths remain unfinished.

## Next steps

1. **Claude: review registry foundation**, `docs/SIGNAL_REGISTRY_IMPLEMENTATION.md` and SR1–SR16. Check original defaults, sparse coverage/anchor guard, zero-centered floor, disabled-channel isolation and retained history. Configuration archive/migration and sponsor settings UI are not implemented. This dependency was built first in response to the user's latest registry direction.
2. **Codex: remaining approved items** (then `docs/IMPRESSION_SPEC.md` I1–I8, order I1→I2→I5→I3→I4→I6→I7→I8): clean facts + structured claim verification/verifier + parametrized tools; Disclaimer page; provider/model line before unlock; structured entry/import; layered free-text gate; patient simulator/life director/seeded flu generator and demo controls. Use `docs/CLAUDE_AGENT_REVIEW_AND_PROPOSALS.md` and `docs/PATIENT_SIMULATOR_AGENT_PLAN.md`. Claude reviews each step. Do not claim any of these is finished from the registry work.
3. Verify full public Cases A–F/isolation/fallback at the now-known HTTPS hostname, obtain user UX feedback, then seek M7 acceptance. Read-only agent remains conservative/lexical until approved replacement is built. No automatic CodeBuddy.
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

### 2026-10-09 — Claude — Note for Codex: review these async updates with HIL
- Since your last session Claude recorded, from chat with the user: `docs/PRODUCT_VISION.md` (diagnosis), `docs/IMPRESSION_SPEC.md` I1–I8, DECISIONS §42 (focus stays antidepressant; architecture open to other conditions; patients may have several conditions, not approved scope) and §43 (patient home = layperson text recap, no charts). Please confirm with the user before implementing, and tell them if anything conflicts with your in-progress work.
### 2026-10-09 — Claude — Patient recap decision
- User: clinician-first is about analytics depth; the patient is not lower. Default patient home gets a short layperson recap written by aura-agent, no charts; charts on demand. Recorded `docs/DECISIONS.md` §43 and rewrote `docs/IMPRESSION_SPEC.md` I6 (supersedes mini-charts in `AURA_AGENT_PLAN.md` §7). Docs only. Suggest moving I6 up in the order; not yet re-ranked.
### 2026-10-09 — Claude — Recorded architecture-openness constraint
- User clarified: focus remains antidepressant maintenance; the high-level architecture should allow other conditions in future. I first overstated this as "condition-agnostic product" and corrected it. `docs/DECISIONS.md` §42, `docs/PRODUCT_VISION.md` scope note, README line, Current state bullet. Docs only; no code audit done.
### 2026-10-09 — Claude — Impression spec for Codex
- User agreed with the `docs/PRODUCT_VISION.md` diagnosis and fixes. Wrote `docs/IMPRESSION_SPEC.md` (I1–I8: assessment on arrival, story on charts, living demo, always-visible Q&A, plain language, patient benefit, 3-minute story, before/after). Docs only; Codex implements, Claude reviews.
### 2026-10-08 — Claude — Current product statement and diagnosis
- User asked for up-to-date documentation and said the app does not impress. Wrote `docs/PRODUCT_VISION.md` after viewing live clinician/patient pages (Playwright with `LD_LIBRARY_PATH=~/rendertest/libs/usr/lib/x86_64-linux-gnu`). Main findings: AI hidden behind a button, demo is a replay, no narrative synthesis, fine print/engineering vocabulary, empty patient screen. Ranked fixes in §8. Docs only.
- Not seen: live agent output, phone layout.

### 2026-10-08 — Codex Sol — Sponsor signal registry and sparse-channel safeguards
- Implemented §41 / simulator plan §3 foundation: versioned external registry, per-channel configuration, HRV/respiratory/skin signals, display-only SpO2/BP/thermometer/weight, typed scalar ingestion, read-only metadata/charts/agent evidence, configuration-linked agent cache and `/signals`. No safety changes, DB schema/dependencies, unguarded hosted intake or full patient simulator. Existing four rules/defaults retained; new-channel calendar anchor coverage and zero-centered scale are explicit engineering additions. See `docs/SIGNAL_REGISTRY_IMPLEMENTATION.md`.
- Verified: baseline 195 PASS; final full **211 PASS** (270.742 s), focused registry/agent **36 PASS**. Hosted browser dual view 12 PASS, agent 5 PASS, settings PASS; new scalar/research/display-only/layout 3 PASS. `git diff --check` clean. No paid model calls; public HTTPS status confirms DeepSeek/deepseek-flash live synthetic-only.
- Deployed/rebuilt on 0.0.0.0:8017; local health and public HTTPS health/status/registry respond. Provider settings survived (DeepSeek/deepseek-flash). Restart creates fresh browser workspaces; existing Cloudflare container was left untouched. Registry dependency was implemented first for the latest direction; Claude review next. Other §39 items, input/import, life director/flu generator and simulator UI remain unfinished. Manual-source consent/configuration archival remain documented work. M7 not accepted; no M8/CodeBuddy.

### 2026-10-08 — Claude — Posture clarified: technical proposal for sponsor
- User: wearables must be realistic (BP etc. intermittent); user is a developer, sponsor owns clinical/regulatory decisions. Added DECISIONS §41; rewrote simulator plan §3 as a config-driven signal registry with cadence classes and engine/display flags. Retracted my earlier 'unauthorized' framing. Docs only; Codex implements.

### 2026-10-08 — Claude — User approvals recorded; patient simulator plan
- User approved all proposals, switched to DeepSeek, asked for provider/model in the settings dialog without unlock, and a demo-only patient simulator agent (synthetic telemetry incl. flu with raised temperature; manual inputs always allowed). Added DECISIONS §39–40 and `docs/PATIENT_SIMULATOR_AGENT_PLAN.md` (LLM life director + deterministic seeded generator, display-only extra channels, safety-gated notes, acceptance criteria).
- Verified: public `https://aura-health.makodev58.com/system/status` returns provider DeepSeek, model deepseek-flash, live_enabled true. No code changed; Codex implements.

### 2026-10-08 — Claude — aura-agent review, disclaimer plan, agent feature proposals
- Reviewed `aura_agent/*`, `aura_app/agent.py`, `hosted.py`, UI strings. Wrote `docs/CLAUDE_AGENT_REVIEW_AND_PROPOSALS.md`: lexical whitelist blocks readable output; zero-arg tools make the loop non-agentic (~12 s); Q&A is 4 canned questions; disclaimers live in fact text; whole-history held block too broad; provider/model discrepancy (handover says gpt-6-luna, user says DeepSeek flash).
- Verified: `tests.test_agent` 20 PASS. Not verified: live calls, browser UI, full suite. Docs only; not user-approved.

### 2026-10-08 — Codex Sol — Read-only aura-agent and five skills
- Implemented Claude's proposal following user authorization: `aura_agent/`, five versioned skill files, `aura_app/agent.py`, native function calling through existing synthetic provider settings, API, additive append-only trace table and audit. Explicit UI brief/Q&A/recap/visit/ranking controls with source links, step inspection and honest fallback. Docs/architecture/decision §38 updated; no accepted engine/dependency changes, real detectors, sharing, additional scenarios or CodeBuddy.
- Verified live: `gpt-6-luna` brief and record Q&A both VALIDATED_MODEL_DRAFT, six model-selected read tools each, three/two cited claims, exact persisted retries; 11,705/11,869 ms. Initial vocabulary/timeouts safely rejected/fell back; only grammatical vocabulary and separate agent timeout adjusted. No secrets/cookies/raw provider errors printed or committed. Docker rebuilt/healthy on 0.0.0.0:8017; reload creates a fresh synthetic browser session.
- Verified: full Python **195 PASS** (267.543 s); strengthened focused AG1–AG20 **20 PASS** (32.936 s). Browser: agent **5 PASS**, dual view **12 PASS**, settings PASS at phone/laptop widths; development patient/offline/retry **17 PASS**. Source-and-text coverage and LAN HTTP UUID fallback checked. Development free-text suite runs without `--hosted` (hosted correctly rejects non-fixtures). `git diff --check` clean.
- Review next: Claude/user acceptance, broader live/injection/semantic evaluation and public hostname verification. Grounding is not proof of clinical truth; shared model budgets can cause extraction fallback. M7 is not declared accepted; M8 not started.

### 2026-10-07 — Codex Sol — Enable approved GPT-6 Luna for synthetic demo
- User explicitly approved switching to `gpt-6-luna`. Saved OpenAI/default model through existing loopback-authorized settings API, tested while disabled, then enabled live wording only after PASS. No runtime code/dependency/domain/auth changes or restart; no credentials printed/committed. Ordinary patient API remains disabled; safety/validator/fallback/call budgets unchanged.
- Verified: model access HTTP 200; existing synthetic exact-candidate connection test PASS; public status reports OpenAI / gpt-6-luna / live_enabled=true / synthetic_only=true. Focused administrator/secure-origin test 1 PASS. Official OpenAI documentation checked; existing adapter works without parameter changes. Prior full suite remains 175 PASS; not rerun for configuration/docs-only work.
- Left: broader live fixture evaluation and UX/reviewer feedback; this is a connectivity smoke test, not clinical validation or a general chatbot. Public hostname and agent-plan approval remain unresolved.

### 2026-10-07 — Codex Sol — Retry replacement OpenAI key; model mismatch confirmed
- User replaced the disabled key in the same file. Reloaded it through existing protected loopback settings API; no credentials printed/committed, no runtime/auth/domain changes. Retained exact requested model `gpt-6.1-luna`; synthetic connection test UNAVAILABLE, model probe HTTP 404/model_not_found.
- Verified: replacement key catalog HTTP 200; `gpt-6.1-luna` absent, `gpt-6-luna` listed. Official OpenAI model page confirms `gpt-6-luna`; no automatic substitution. Focused admin/secure-origin test 1 PASS. Live wording remains disabled and deterministic fallback active.
- Next: user approval to switch to `gpt-6-luna`, then one synthetic connection test. No successful generation or broader model/clinical validation is claimed.

### 2026-10-07 — Codex Sol — Save OpenAI credential and test exact requested model
- User has no HTTPS and explicitly authorized local key import and synthetic test with `gpt-6.1-luna`. Found the matching key file at `/home/makodev58/aura-health.key`; saved via existing loopback-authorized settings API, not LAN credential transport or auth bypass. Credential/config files verified 0600; no key/admin token printed or committed. No runtime code changes.
- Verified: focused administrator/secure-origin test 1 PASS; actual OpenAI model probe HTTP 401, production synthetic connection test UNAVAILABLE. Saved provider OpenAI/model exactly requested, live wording disabled, deterministic fallback retained. No successful generation/model-access claim. Official OpenAI documentation checked without substituting models.
- Remote recovery verified: origin/main contained `a0afac0` and the earlier LAN fix on arrival. Left: user must verify/replace the OpenAI credential before retry; public URL, dual-view acceptance and Claude agent-plan decisions remain unresolved.

### 2026-10-07 — Claude — aura-agent role and scaffold plan
- User: app must be agentic; patient main page lost its insight. Wrote `docs/AURA_AGENT_PLAN.md`: deterministic-vs-agent table, five read-only roles (clinician brief first), guard/grounding/trace architecture, scripted no-key provider, scaffold file layout, 'month at a glance' patient card (revises my earlier minimal-surface advice), acceptance criteria, user decisions. Docs only.
- Verified: read safety policy §35 tier limits, `aura_communication` provider interface, `aura_simulation/agent.py`. Nothing run. Not user-approved; no code written.

### 2026-10-07 — Codex Sol — Restore LAN demo cookie retention
- User reported the missing-cookie error after the capacity fix. Added explicit private-IP HTTP cookie exception, default empty (`AURA_HTTP_DEMO_HOSTS`); public hostnames and HTTPS remain Secure. Configured this server's verified LAN IP in ignored `.env`, rebuilt/restarted Docker. No wildcard/public IP exception, forwarded-host trust, global cookie weakening or settings-auth change. Accepted engines/schema/dependencies unchanged.
- Verified: baseline 170 PASS; final **175 tests PASS** (232.528 s), including 11 capacity/cookie regressions; actual deployed 390px Chromium LAN page/API 200/reload retained the same HttpOnly/SameSite=Strict cookie, no page errors. Public Host probe still receives Secure; container healthy on 0.0.0.0:8017; `git diff --check` clean. No cookie values/credentials printed or paid model calls.
- Left: public URL still needed to verify the actual external route; user/Claude dual-view acceptance remains pending. LAN HTTP is unencrypted synthetic demo access only. Restart begins fresh synthetic sessions, old files/settings retained.
- Delivery: committed/deployed locally; GitHub rejected push attempts with remote Internal Server Error. Push is pending retry after the remote recovers; no successful remote delivery is claimed.

### 2026-10-07 — Codex Sol — Fix demo session exhaustion
- User reported `DEMO_BUSY`. Hosted requests previously allocated workspaces for shell/assets/probes and each missing-cookie API call. Now only explicit catalog bootstrap allocates; cookie-less APIs fail clearly without new processing. Static shell loads at capacity; retry is visible with independent local resources. Existing sessions remain protected, bounds unchanged. See `docs/DEPLOYMENT.md`.
- Verified: baseline 164 PASS; final **170 Python tests PASS** (234.226 s); six allocation regressions, Chromium dual-view 12 PASS, hosted 7 PASS including initial 503/retry, settings PASS, layout 8 PASS. `git diff --check` clean. Rebuilt Docker healthy on 0.0.0.0:8017; shell/assets 200 and missing-cookie error verified. No paid model calls or domain/schema/dependency changes.
- Deployment uses Secure cookies; public HTTPS remains unverified pending user URL. Direct LAN HTTP needs explicit false override, not an automatic weakening of public cookie security. Restart gives browsers fresh synthetic clones while retaining old files/settings. Claude/user dual-view review remains pending; no new milestone started.

### 2026-10-07 — Codex Sol — Clinician-first dual view and minimal patient experience
- User approved the revised plan with "Proceed". Added shared `EvidenceViewService`/repository snapshot read/GET evidence endpoint, `aura_ui/evidence.js` native charts, same-record demo toggle, clinician-first B, minimal patient home/full-data entitlement and factual temporary appointment preview. Documentation: `docs/DUAL_VIEW_IMPLEMENTATION.md`; plan/decisions/UI README updated. No accepted engine/schema/dependency changes or additional data.
- Charts use exact committed values/versions, explicit gaps and signal-linked contexts; categorical reports, questions/review items and safety provenance stay descriptive. Unsupported hosted illness explanations are not offered as submit actions; exact prepared D fixture still invokes production hold. Gear, idempotency, pinned resources/offline and fixture-only writes preserved. Toggle is not authorization/sharing.
- Verified: **164 Python tests PASS** (236.044 s); Chromium patient **17 PASS**, dual view **12 PASS**, hosted **6 PASS**, settings PASS, layout **8 PASS**; no page errors. Historical v2 reanchor/reload and zero-write toggle checked. `git diff --check` clean; Docker rebuilt/healthy on **0.0.0.0:8017**. Artifacts `/tmp/aura-dual-hosted-browser`, `/tmp/aura-dual-m6-regression`; no paid model call or CodeBuddy run.
- Review next, not acceptance: user UX feedback and Claude implementation review. Public HTTPS remains unverified; governance/clinical limits remain. No M8/additional-data/auth/sharing work started.

### 2026-10-07 — Claude — Review of dual-view plan; clinician-first, patient entitlement
- Read `docs/DUAL_VIEW_EXPERIENCE_PLAN.md`, `DECISIONS.md` §37, `aura_app/longitudinal.py`. Wrote "Claude review of the dual-view plan" above. Recorded user direction: clinician view is the main product; patient analytics on demand, patient entitled to them. Three required changes, Q1–Q5 answers, scope warning. Docs only.
- Verified: nothing run beyond reading; anchor-version history not verified. Not user-approved.

### 2026-10-07 — Claude — Product reassessment recommendation
- Read `HANDOVER.md`, `docs/PRODUCT_REASSESSMENT.md`, framework §2–3/5/17/29–32 and `aura_ui/index.html`. Wrote the recommendation section above: value sentence, journey ranking, default/optional/demo split, walkthroughs, non-UI gaps, storyboard, acceptance criteria, three questions for Codex. Docs only (`HANDOVER.md`).
- Verified: repo clean at `97dd66a` on arrival. Tests not re-run (no code touched).
- Watch out for: this is a recommendation, not user-approved. No implementation until Codex responds and the user agrees.

### Earlier history — 2026-09-23 to 2026-10-03
- 2026-10-07 planning/review: user-requested delegated dual-view plan revised after Claude's clinician-first/patient-entitlement review; `docs/DUAL_VIEW_EXPERIENCE_PLAN.md`, `docs/PATIENT_EXPERIENCE_STORYBOARD.md`. Source inspection confirmed per-event anchor versions; no runtime changes; 150 tests PASS on each docs-only turn. Later approved implementation supersedes those planning blockers.
- 2026-10-07 product reassessment pause: `docs/PRODUCT_REASSESSMENT.md`, full framework reread and Claude deliberation requested; no runtime changes, 150 tests PASS. Later approved dual-view/agent directions supersede the blocker, not the clinical boundaries.
- 2026-10-07 protected settings gear: Compass-style write-only server keys, native four-provider adapters, secure-origin/admin gate and budgets; 150 tests PASS, Chromium 17 patient + 6 hosted + settings/layout PASS. `docs/SYSTEM_SETTINGS.md`; later live smoke supersedes the then-unconfigured provider state.
- User approved live models on synthetic data and future institutional on-prem/private-cloud direction (2026-10-07); decision §36 and `docs/SYNTHETIC_LIVE_MODEL.md`. Delegated mobile-portrait UX review documented in `docs/PATIENT_UX_REDESIGN.md`; docs-only stage, 140 tests PASS. Additional data deferred and CodeBuddy remains user-controlled.
- Initial patient UI redesign (2026-10-07): compact Today/progressive disclosures, independent safety, mobile/laptop layouts; no domain/schema changes. 150 Python tests PASS, Chromium 17 patient + 6 hosted + settings + 8 layout checks PASS. See `docs/PATIENT_UX_REDESIGN.md`; later patient/clinician reassessment and approved dual view supersede its layout.
- M7 initial local integration (2026-10-07): scenario planner, observable-only replay, DEMO1–DEMO16, atomic seed/reset and isolated hosted sessions/Docker/runbook; forwarded the existing new-signal reopening input without domain changes. 140 Python tests PASS, Chromium 17 patient + 6 hosted PASS, 150-entry replay exact. User authorized 0.0.0.0:8017 publishing; health verified over loopback/LAN. Public hostname remained unverified. See `MILESTONE7_REVIEW.md`.
- M6 implemented and accepted by Claude on 2026-10-03; 124 Python tests PASS, Chromium UI1–UI15/offline/retry 17 PASS at 320/390/1280. Read-only provenance, fixture-only demo, independent safety/resources and same-key retry; no domain/schema changes. M7 subsequently restricted assets and disabled CDN-backed docs. See `MILESTONE6_REVIEW.md`.
- M5 implemented and accepted by Claude (2026-10-02), 106 tests PASS, nine wording fixtures PASS with fixture/disabled providers. Candidate validation, race-checked commit, static prohibited modes and append-oriented wording/audit verified; domain engines unchanged. Live provider not tested. See `MILESTONE5_REVIEW.md`; regex validation remains defense-in-depth only. User assigned implementation ownership to Codex and CodeBuddy timing to themselves; product-first/manual rebuild workflow supersedes older scheduling.
- Milestones 1–4 implemented, 69 tests PASS; Claude reviewed M4, created this handover, and pushed repository history (initial implementation `527cc13`, LICENSE merge `97aad5b`). Canonical evidence: `MILESTONE3_REVIEW.md`, `MILESTONE4_REVIEW.md`.
- User named the project `aura-health` and superseded Care Plan Bridge (2026-09-23); older framework files retain explicit superseded banners.
- M4.5 canonicalized roadmap/decisions/M1–M8/demo script; P1–P18/L1–L14/A1–A20 trace to tests. No reconstructed criterion; corrected accepted CLOSED/high-tier correction chronology and safety-first M4 shorthand. 69 tests PASS; docs-only `358f5c9`.
- Claude reviewed M4.5 and added submission requirements, exact CodeBuddy evidence minimum, intended-use/safety containment details and live-link gate. M1/M2 review chronology has no separate committed packets; actual tests back behavior.
- User required a live demo on this server via Cloudflare (2026-09-24); optional per-app sidecar rather than host install. Tencent mirror deferred until near the deadline. Current hosting/CodeBuddy decisions above supersede older timing instructions.
