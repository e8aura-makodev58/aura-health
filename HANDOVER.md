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
- **Tests:** 140 pass (`.venv/bin/python -m unittest discover -s tests -q`), including all previous gates and 16 M7 checks. Real Chromium: UI1–UI15 + OFFLINE + MANUAL_RETRY **17 PASS**, plus hosted **6 PASS**, no page errors; 320/390/1280 widths checked. The only Python warning is the existing Starlette/httpx deprecation. Timing/replay evidence is in `MILESTONE7_REVIEW.md`.
- **M7 local implementation:** `aura_simulation/` validated scenario planning, deterministic observable-only driver/replay, 16 DEMO tests; atomic initial seeding and recoverable operator reset; `aura_app.hosted` isolated synthetic browser workspaces with fixture-only writes/reset; Docker + optional file-secret Cloudflare sidecar. Diagram/runbook: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md). Demo is healthy on **0.0.0.0:8017** (user-requested network publishing); LAN address `http://192.168.80.193:8017`. **User reports live hosting; public hostname/HTTPS unverified; M7 not complete.**
- **Integration contradiction fixed:** application projector previously omitted the accepted domain's new-longitudinal-signal reopening input. It now forwards newly production-assessed persistent/divergent signals; DEMO11 verifies reopening with unchanged anchors. Safety/longitudinal domain algorithms and clinical configuration remain unchanged.
- **Canonical plan:** [`docs/ROADMAP.md`](docs/ROADMAP.md), [`docs/DECISIONS.md`](docs/DECISIONS.md), [`docs/milestones/`](docs/milestones/), and [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md).
- **Not configured/built by Codex yet:** live model/gateway, real safety detectors, production auth, clinician-sharing workflow, repository Cloudflare sidecar. User-managed live hosting is reported but not externally verified. Simulation planner defaults to offline templates; optional gateway is mock-tested, not live AI evidence. Supplied API/demo entry points explicitly disable models pending informed-consent governance. Public non-demo safety gate holds unassessed text; hosted demo rejects non-fixture input before storing.
- **Ownership (user, 2026-10-02):** Codex has implementation authority; Claude Sonnet 5.5 is reviewer.
- **CodeBuddy workflow (user, 2026-10-02):** do not run CodeBuddy automatically. Finish and agree on our product first, then prepare a detailed SOW for the user to manually trigger a clean rebuild. Compare the completed apps and reuse reviewed improvements; our version may be submitted. Collect actual evidence during that rebuild; none is claimed yet.
- **Data:** synthetic only (simulator cases A–F).
- **Current user revision (2026-10-07):** enable live-model wording on synthetic data; future institutional model intended on-prem/private cloud (not implemented/validated readiness). Dedicated UI/UX agent completed a read-only purpose-led mobile portrait/laptop review. Proposal: `docs/PATIENT_UX_REDESIGN.md`; provider plan: `docs/SYNTHETIC_LIVE_MODEL.md`. Runtime still uses disabled providers/current UI; this session records the decision/design, not a live-model or redesigned-UI implementation. Additional synthetic data is deferred.

## Open decisions

- **Live provider configuration:** user must identify provider/model/endpoint and protected credential provisioning (configuration names/file path only, never secret values). Existing adapter expects a neutral JSON gateway, not a vendor-native chat API. No live call is configured or claimed. New synthetic-only enablement must not enable the ordinary patient API.
- **Public URL verification:** user reports the demo is live; hostname is not supplied, so external HTTPS remains unverified. Repository sidecar has not been provisioned by Codex; do not assume it is the user's hosting route or request a token unnecessarily.
- **Tencent Cloud mirror:** whether to also mirror the live demo to Tencent Cloud. The user will decide closer to the 2026-10-16 deadline (M8 window, 13–15 Oct).

## Active milestone: M7 — local integration implemented; public-link gate pending

Scope/gate: [`docs/milestones/M7_DEMO_AND_INTEGRATION.md`](docs/milestones/M7_DEMO_AND_INTEGRATION.md); local evidence: [`MILESTONE7_REVIEW.md`](MILESTONE7_REVIEW.md). M5/M6 were accepted by Claude. Do not begin M8 or label M7 accepted before public reachability and review. Domain algorithms remain authoritative.

Current priority is the user's live-synthetic-model and mobile-first UX revision;
additional scenario/data generation waits until those are addressed. UX review was
delegated at explicit user request; no new runtime changes in this planning session.

## Next steps

1. Resolve live provider/model/configuration, then integrate synthetic-only wording with existing validation/fallback and truthful configuration/per-response disclosure. Implement the mobile-first Today/Patterns/Review hierarchy from the UX proposal, persistent help, progressive details, laptop adaptation and keyboard/safety/offline checks. Do not expand arbitrary chat, safety detectors or clinical policy. Defer additional synthetic data. No automatic CodeBuddy run.
2. Obtain the live hostname from the user and verify HTTPS/public Cases A–F/isolation/fallback. User reports it is live and requested `0.0.0.0:8017` publishing. Record the URL only after verification; then seek M7 acceptance. Do not invent clinical policy to smooth the demo.
3. The user controls CodeBuddy timing. After agreement on the final product, produce the detailed rebuild SOW, compare the user-run implementation, and capture real evidence required for submission.
4. Preserve known issues from `MILESTONE4_REVIEW.md` §13 and M6 limits:
   - Backend `safety_episode_references` still includes routine T0/null records; M6 filters null episode references in presentation only. Future sharing needs governance/filtering.
   - There is no governed exit from the `REESTABLISHING` state.
   - `reviewed_by` is caller-supplied and not authenticated.
   - Replay-per-event cost grows with the length of the event history.
   - M5 wording render also loads full history. Public routing helper is now `requires_safety_gate`; latest-event IDs are supplied by the read view.
   - Real-patient live-model consent/governance remains future work. User now authorizes live synthetic demo wording, but runtime is still disabled pending selected provider/configuration. Do not enable ordinary patient entry points implicitly.
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

### 2026-10-03 — Claude — M6 review: accepted, no blocking findings
- Read `aura_app/api.py`, `patient_view.py`, `demo.py`, simulator/communication/service diffs and `aura_ui/app.js`. Confirmed: UI renders server state only (no drift/trust/safety logic in the browser); safety panel is not dismissable by navigation; offline state keeps built-in resources and holds input in memory with same-key retry; demo gate fails closed on unknown text; demo patients are restricted by id; model provider forced to `DisabledProvider`; `aura_safety/` and `aura_longitudinal/` untouched; CSP/no-store headers set.
- Verified: 124 tests pass (110 s); `git diff --check` clean.
- Not verified: real Chromium suite (Playwright not installed on this host; run needs `aura_ui/README.md` setup).
- Non-blocking notes for M7: `/assets` serves the whole `aura_ui/` dir (incl. README); the strict CSP will block FastAPI `/docs` assets (CDN); disable or relax docs on the hosted demo.

### 2026-10-03 — Codex Sol — M6 patient app ready for review
- Added responsive patient UI, read-only latest-event/provenance view, explicitly synthetic checkpoint server, and API/browser acceptance tests. Reused accepted commands/engines; no schema or safety/longitudinal algorithm changes. See `MILESTONE6_REVIEW.md` and `aura_ui/README.md`.
- Verified: **124 Python tests PASS**; real Chromium **UI1–UI15 + OFFLINE + MANUAL_RETRY (17 PASS)**, 320/390/1280 widths, no page errors. `git diff --check` clean. Fixed narrow-screen flex overflow and verified medication taps use the existing uppercase transport enum.
- M5 review notes handled: latest committed event reference supplied; routing helper public; live-provider startup disabled pending consent. History scaling remains. Separate resources persist offline; retry preserves event key. Preview selections are not approval/sharing.
- Left: Claude/user M6 review. M7 has not started; clinical content/resources, real detectors, governed REESTABLISHING exit, durable offline queue and prod auth remain absent. No CodeBuddy used; later rebuild remains user-controlled.

### 2026-10-02 — Claude — M5 review: accepted, no blocking findings
- Read `aura_app/communication.py`, `validation.py`, `provider.py`, API/persistence diffs. Confirmed: provider gets data only; model output must exactly match an approved candidate; state is rechecked in a second transaction and stale output is discarded; T3/T4/degraded/offline/STAY_QUIET make zero provider calls; `BEGIN IMMEDIATE` serializes duplicate requests so only one output commits; provider URL is HTTPS/localhost-only, no redirects, size/time bounded; `aura_safety/` and `aura_longitudinal/` untouched since `110218c`.
- Verified: 106 tests pass; `aura_communication.evaluation --behavior disabled` all nine fixtures PASS; `git diff --check` clean.
- Changed: fixed a misindented line in `aura_app/persistence.py` (cosmetic). Non-blocking notes are in **Next steps**.
- Not verified: live provider (none configured); regex checks are defense-in-depth only, as M5 states.

### 2026-10-02 — Codex Sol — M5 bounded communication and current user workflow
- Added wording contracts/catalog/config, deterministic candidate/claim validation, optional HTTP provider, fixed fallbacks, and nine prompt fixtures. Application communication service reads committed gate results/current safety state and rejects stale generated output. New command endpoint and append-oriented output/audit persistence; core domain engines unchanged. See `MILESTONE5_REVIEW.md`.
- Verified: `.venv/bin/python -m unittest discover -s tests -q` — **106 tests PASS** (69 prior + 37 M5). Nine fixtures PASS with fixture provider and with provider disabled; cached replay matches. `git diff --check` clean.
- User decisions: Codex is implementation owner, Claude reviewer; user alone controls CodeBuddy. Build/review final product first, then detailed SOW for a manual clean rebuild, compare/adopt useful improvements, choose submission version. Updated decisions/roadmap/M5–M7 notes; no CodeBuddy implementation/evidence claimed.
- Next: M5 review, then M6. Live provider, reviewed safety questions/content/resources, production auth, and inherited M4 issues remain open; no clinical policy was invented.

### 2026-09-24 — Claude — Hosting decided: this server via Cloudflare
- User decision: host the live demo on this server via Cloudflare; decide on a Tencent Cloud mirror near the deadline.
- Added a **Live demo hosting** section here (corrected: cloudflared runs as per-app Docker containers, not a host install), and updated `DECISIONS.md` §31 and `M7_DEMO_AND_INTEGRATION.md`.

### 2026-09-24 — Claude — Live hosted demo decided
- User decision: aura-health **will have a live hosted demo** (the brief gives bonus points for a live link).
- Updated `DECISIONS.md` §31, `ROADMAP.md` (M7 and priorities), `M7_DEMO_AND_INTEGRATION.md` (new required "Live hosted demo" section and gate), and `M8_SUBMISSION.md` (project link will be submitted).
- Still open: which hosting provider to use.

### 2026-09-24 — Claude — Reviewed M4.5 docs; filled submission gaps
- Verified Codex Sol's M4.5: every P1–P18, L1–L14, and A1–A20 ID and the cited test names exist in `tests/`; M4 safety-first flow matches the code; M5 matches safety spec §35 LLM containment. Only docs changed in `358f5c9`.
- Fixed:
  - `M8_SUBMISSION.md` omitted brief-required items: title, <10-word blurb, 16:9 cover image, the four-part description (incl. "how prompts drive AI generation" and quantified value), ≥3 CodeBuddy/WorkBuddy chat screenshots. Also added the optional video/live-link details and the judging rubric.
  - `DECISIONS.md` §2 now states the user's official name, aura-health. §32 now gives the brief's exact evidence minimum and an evidence location (`docs/evidence/`).
  - M5 now includes T1/T2 generation limits from spec §35.
  - M7 and Open decisions now flag the live-link bonus.
  - README now links `docs/`.
- Not verifiable from the repo: M1/M2 review chronology (no M1/M2 review packets are committed). Behavior is backed by the cited tests.

### 2026-09-24 — Codex Sol — M4.5 project canonicalization
- Created `docs/ROADMAP.md`, `docs/DECISIONS.md`, all eight `docs/milestones/` specs, and `docs/DEMO_SCRIPT.md`; no runtime code changed.
- Verified all historical P1–P18, L1–L14, and A1–A20 IDs against tests/review packets. No acceptance criterion required `(reconstructed)`.
- Corrected chronology: CLOSED/degraded, immutable CLOSED, and configured high-tier defaults were accepted with the M1 review, not first decided in M2. Corrected M4 event-flow shorthand to safety-first for safety-relevant input; clarified that M7's explicit ground-truth isolation test is still future work.
- Verified: `.venv/bin/python -m unittest discover -s tests -q` — 69 tests pass. M5 is next; it has not begun.

### 2026-09-23 — Claude — M4.5 instructions for Sol
- Sol 6 proposed M4.5 (Project Canonicalization) and the M5–M8 sequence; the user asked Claude to pass its adjustments to Sol via this file. See **Active milestone** above.
- Watch out for: don't duplicate this handover file under `docs/`.

### 2026-09-23 — Claude — Care Plan Bridge dropped; project named aura-health
- User decision: drop Care Plan Bridge, and use aura-health as the official project name.
- Updated the README intro and doc list. Added a "Superseded" banner to `PRODUCT_FRAMEWORK.md`, `PRODUCT_FRAMEWORK_V2.md`, and `FRAMEWORK_CRITIQUE.md` (no other content changed).
- Watch out for: the frameworks and code still say "AURA" in places. That's the same product, so no renaming is needed unless the user asks.

### 2026-09-23 — Claude — Status review, first push, handover created
- Reviewed Milestone 4 and re-ran the tests: 69 pass.
- Committed all milestone 1–4 work (`527cc13`) and merged the remote's LICENSE-only initial commit (`97aad5b`), with no force-push. Pushed to `origin/main`.
- Created this `HANDOVER.md`.
- Watch out for: the product-direction mismatch (resolved in the entry above).

### 2026-09-23 — Sol — Milestones 1–4
- Built `aura_safety`, `aura_longitudinal`, and `aura_app` along with the tests and review packets (`MILESTONE3_REVIEW.md`, `MILESTONE4_REVIEW.md`). *(Summarized by Claude from the repo; Sol did not write this entry.)*
