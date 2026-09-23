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

## Current state (as of 2026-09-24)

- **Project name:** officially **aura-health** (user, 2026-09-23). Care Plan Bridge (`PRODUCT_FRAMEWORK*.md`, `FRAMEWORK_CRITIQUE.md`) was dropped; those docs are marked superseded and kept for background only.
- **Product being built:** a longitudinal, wearable-first companion for adults on stable antidepressant maintenance treatment. Spec: `aura_health_framework_v1.0.md`. Safety policy: `aura_deterministic_safety_policy_state_machine_v1.2.md`.
- **Milestones 1–4 are complete; M4.5 documentation is complete.** The Milestone 4 engineering stop condition is met. See `MILESTONE3_REVIEW.md` and `MILESTONE4_REVIEW.md`.
  - `aura_safety/`: deterministic safety state machine (no LLM).
  - `aura_longitudinal/`: personal baseline, drift, context, held-for-review, and communication engines.
  - `aura_app/`: FastAPI + SQLite application layer. It handles idempotent event ingestion, atomic transactions, safety-first gating, the timeline, and the clinician review snapshot (never shared automatically).
- **Tests:** 69 pass (`.venv/bin/python -m unittest discover -s tests -q`). The only warning is a Starlette/httpx deprecation, which doesn't affect results.
- **Canonical plan:** [`docs/ROADMAP.md`](docs/ROADMAP.md), [`docs/DECISIONS.md`](docs/DECISIONS.md), [`docs/milestones/`](docs/milestones/), and [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md). M5 is next and has not started.
- **Not built yet:** patient UI, any LLM/generated text, real safety detectors, auth, clinician-sharing workflow.
- **Data:** synthetic only (simulator cases A–F).

## Open decisions

- **Hosted live demo link?** The brief (§8) gives bonus points for an optional live URL/demo link. `ROADMAP.md`/M7 currently treat cloud hosting as stretch work. The user should decide whether a simple hosted synthetic-data demo is in scope for M7.

## Active milestone: M5 — AI Communication Layer (not started; target 2026-09-30)

Scope and gate: [`docs/milestones/M5_AI_COMMUNICATION_LAYER.md`](docs/milestones/M5_AI_COMMUNICATION_LAYER.md). Do not reopen accepted safety or longitudinal algorithms without an integration contradiction. Genuine CodeBuddy/WorkBuddy work and contemporaneous evidence start in M5.

## Next steps

1. Start M5's bounded AI communication layer; do not start a generic therapy chatbot.
2. Begin genuine CodeBuddy/WorkBuddy development and evidence capture immediately in M5.
3. M6 patient application may overlap after M5 contracts stabilize.
4. Preserve known issues from `MILESTONE4_REVIEW.md` §13; do not invent clinical policy to close them:
   - The review snapshot's `safety_episode_references` includes routine T0 records with null episode IDs, so it needs filtering.
   - There is no governed exit from the `REESTABLISHING` state.
   - `reviewed_by` is caller-supplied and not authenticated.
   - Replay-per-event cost grows with the length of the event history.

## Quick reference

```sh
# setup (once)
UV_CACHE_DIR=/tmp/aura-uv-cache uv venv .venv
UV_CACHE_DIR=/tmp/aura-uv-cache uv pip install --python .venv/bin/python -r requirements.txt

# tests
.venv/bin/python -m unittest discover -s tests -q

# synthetic cases A–F through the app service
.venv/bin/python -m aura_app.simulator --case ALL --seed 7 --db-dir /tmp/aura-app-cases

# API
.venv/bin/python -m uvicorn aura_app.api:app --host 127.0.0.1 --port 8000
```

## Git & remote

- `origin` = `git@github.com:e8aura-makodev58/aura-health.git`, branch `main`.
- Push with the SSH key `~/.ssh/e8aura-makodev58`. It is already set in the repo-local `core.sshCommand`, so a plain `git push` works. The default `~/.ssh/id_ed25519` authenticates as a different account and fails with "Repository not found".
- The `gh` CLI is not installed.
- Commit author email doesn't matter (user, 2026-09-23).
- `*.sqlite3`, `.venv/`, and `__pycache__/` are gitignored. Never commit the development databases.

---

## Log

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
