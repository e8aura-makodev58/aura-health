# WorkBuddy handoff brief (DRAFT until WP6 is reviewed)

2026-10-12. Claude. **User decisions (2026-10-12):** WorkBuddy creates its own branch, implements, and
finishes the product, but only after Codex has finished **all** remaining items, including
anything beyond WP6 (the voice and plain-language specs, leftover Next steps). Claude reviews.
The user decides who tests, who merges and who deploys. This brief is
what WorkBuddy reads first. It is a draft until Claude's WP6 review is recorded in
`HANDOVER.md`; section 3 is filled in at handoff.

## 1. Mission
Finish aura-health as a demo that a patient and a doctor can understand in minutes:
coherent, warm, plain-language, polished on desktop and phone, with a smooth three-minute
story. Use any approach inside the boundaries in section 4.

## 2. Starting point and branch rules
- Start from `main` after the user confirms WP6 acceptance. The user tags that commit
  `pre-workbuddy`.
- Create `workbuddy/final` (more branches are fine). Small commits, clear messages, no
  force push, no history rewriting. Do not push to `main` and do not deploy.
- The user merges. Claude reviews the diff against this brief first. Remote:
  `git@github.com:e8aura-makodev58/aura-health.git` (SSH key notes in `HANDOVER.md`).
- Read `HANDOVER.md` first. Add your own Log entry when you finish a work session. Other
  agents may edit the repo concurrently: pull and re-read before editing shared files.

## 3. Remaining work (filled in at handoff)
Claude fills this from the WP6 review. Expected themes: layout and visual polish of the
clinician and patient views, phone layout, empty and loading states, the demo guide and
three-minute story flow, plain-language and voice sign-off follow-ups, accessibility
(contrast, focus, labels, reduced motion), the demo video script. Plus any leftover items
listed under Next steps in `HANDOVER.md`.

## 4. Boundaries (non-negotiable)
**Safety and integrity**
- The pinned safety panel and resources stay visible, unchanged in wording and
  reachable on every screen. The patient-initiated help ("I want to mention something") stays
  at least as prominent as it is. Safety wording is never generated or edited by a model.
- Do not edit `aura_safety/`, `aura_longitudinal/`, `aura_communication/`, `aura_detectors/`,
  or `aura_agent/` (guard, grounding, validators, tools, roles, runtime, prompts), the
  database schema, or `aura_app/` behaviour. If a UI change needs backend work, stop,
  write the request in `HANDOVER.md`, and leave it for the user.
- No new write tools, no unguarded input paths, no changes to the hosted fixture
  allowlist, admin token handling or provider settings.
- No scores, risk labels, streaks, diagnosis, prediction, treatment or medication advice, and no
  cause language ("because", "due to"). Missing data is never shown as bad.
- Synthetic data only. No real personal data, keys, tokens or the admin dialog in
  screenshots, logs or commits.
- "Not sent" and every state chip stay truthful. Do not imply sharing, sending or clinical
  validation.

**Language** (see `docs/PATIENT_VOICE_SPEC.md`, `docs/PLAIN_LANGUAGE_SPEC.md`, DECISIONS §44)
- Patient: everyday words, warm and calm, no technical terms, no ISO dates, no source IDs.
- Clinician: keep all factual data (values, units, dates, data amounts, sources); remove
  only schema-like names and tags. No repeated inline caveats; disclaimers live on the
  Disclaimer page.
- The banned-terms list and the browser lint test must keep passing.

**Where you may change things:** `aura_ui/` (HTML, CSS, JS), the demo guide UI, UI-facing
copy within the rules above, browser tests under `tests/browser/`, and docs about the UI.

## 5. How to run and test
```sh
# setup (once)
UV_CACHE_DIR=/tmp/aura-uv-cache uv venv .venv
UV_CACHE_DIR=/tmp/aura-uv-cache uv pip install --python .venv/bin/python -r requirements.txt
# unit and integration tests (≈6 min)
.venv/bin/python -m unittest discover -s tests -q
# run the synthetic demo locally
.venv/bin/python -m aura_app.demo --db aura-m6-demo.sqlite3
AURA_DEMO_DB=aura-m6-demo.sqlite3 .venv/bin/python -m uvicorn aura_app.demo:create_demo_app --factory --host 127.0.0.1 --port 8000
# browser suites: see aura_ui/README.md and tests/browser/run.py
```
Before asking for a merge: the full test suite and all browser suites pass (including the
plain-language lint), screenshots of both views at 1280 and 390 px are attached to your
Log entry, and nothing under the protected paths in section 4 changed
(`git diff main --stat` shows only allowed paths). If you cannot run tests in your
environment, say so and ask the user to run them; do not claim they pass.

## 6. Review and acceptance
Claude reviews the branch: boundaries, language rules, safety panel and help access,
before/after screenshots, tests, a live pass of the story and each simulator event. The user
accepts the product. Findings go back as a short list. Nothing is deployed without the user.

## 7. Evidence (hackathon requirement)
Keep your own genuine, dated WorkBuddy conversation logs from this work (at least three
screenshots or a recording). Do not recreate or stage them later. Record in the Log which
sessions produced which changes.

## 8. Decisions (user, 2026-10-12)
1. Anything remaining beyond WP6 is finished by Codex (reviewed by Claude) **before**
   WorkBuddy starts. WorkBuddy begins from a state with no open build items except polish.
2. Who runs the tests and browser suites is decided on the fly: WorkBuddy if it can,
   otherwise Codex or Claude. Never record a test as passing unless it was actually run;
   state who ran it.
3. The user decides who merges and who deploys. No agent merges or deploys unprompted.
