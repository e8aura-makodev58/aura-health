# Submission work plan — 13 to 15 October 2026

Owner of this plan: Claude (coordination). User approves scope, merges, deploys and submits.
Target: everything READY on **15 Oct**; deadline **16 Oct** (buffer day).

Source of the findings: Claude's review of this folder on 13 Oct (see root `HANDOVER.md`).
Every agent: pull first, edit only the files assigned to you, commit with explicit paths,
add a Log entry to `HANDOVER.md`. Do not edit another agent's files; ask in `HANDOVER.md`.

## Decisions taken (user, 13 Oct: "fix all of those findings")

1. **Challenge:** Healthcare track (NTU LKC Medicine), **Challenge Statement 2 "AI Healthier
   Every Day", Scenario 1 "Mental Health Maintenance for Working Adults on Antidepressants"**.
   Every artifact opens with this. Mapping lives in `CHALLENGE_MAPPING.md`.
2. **Title:** `AURA Health` everywhere (repo name stays `aura-health`).
3. **One deck** serves as the presentation and the required "Architecture Diagram PPT":
   `assets/aura-health-deck.pptx` (≤10 MB) contains product, architecture and trust-boundary
   slides. `ARCHITECTURE_DECK.md` content becomes those slides.
4. **No relapse prediction or advice** is a deliberate safety choice, presented as such.
5. **Business value** adds clearly labelled *pilot metrics we would measure* (targets, not results).
6. **Demo Q&A question:** "When did sleep timing change, and was anything reported around then?"
7. Personal account email is removed from public files.

## Where each agent works (set up 2026-10-13 by Claude, user-directed)

One repository, one folder (git worktree) per agent, so switching branches never changes
another agent's files. Branch names are the user's (recorded by Codex in `HANDOVER.md`).

| Agent | Folder | Branch | Browser-test port |
|---|---|---|---|
| Integration and deploys (user-directed merges only) | `/home/makodev58/aura-health` | `main` | — |
| Claude | `/home/makodev58/aura-health-claude` | `improve/feature-claude` | 8026 |
| Codex | `/home/makodev58/aura-health-codex` | `improve/feature-codex` | 8036 |
| CodeBuddy | `/home/makodev58/aura-health-codebuddy` | `improve/feature-codebuddy` | 8046 |

- Work only in your own folder and branch; push only your branch (`git push -u origin <branch>`).
- Do not switch branches in `/home/makodev58/aura-health`; it stays on `main`, holds `.env`, and is
  the only folder `docker compose` runs from. Nobody merges or deploys without the user's direction.
- `.venv` in each worktree is a link to the main folder's environment (ignored via
  `.git/info/exclude`). `.env` exists only in the main folder.
- Run browser suites with your own port: `tests/browser/run.py --hosted --port <port> ...`.
- Other agents' commits are visible at once in every folder (`git log origin/<branch>` after a
  fetch, or the local branch name), without merging.
- The CodeBuddy branch used before, `improve/UI_UX`, is retired (fully merged into `main`).

## 13 Oct evening: feature freeze cancelled — patient companion build

User (2026-10-13): "Cancel feature freeze and let's go all in!" Build the four patient features in
**[`docs/PATIENT_COMPANION_SPEC.md`](../PATIENT_COMPANION_SPEC.md)** (medication understanding,
today's dose + adherence barriers, coming up, gentle suggestions). That spec's ownership table
(§4) and schedule (§5) take priority over the task lists below where they overlap:

| Agent | Build tasks (spec §4) | Then |
|---|---|---|
| Codex | Fixture prescription, schema, medication reason + gates, review items, `GET /companion` | X2, X1, X3–X5 |
| Claude | Medication content + `/medication/ask`, suggestions, integration | C1–C5 (script waits until features land) |
| CodeBuddy | The four patient-home cards + appointment items | B1–B4 |

No fixed cut-off (user, 2026-10-13): integrate as soon as all three agents report done in `HANDOVER.md`; merge order Codex → Claude → CodeBuddy, then a short freeze for QA and recording. The "Due" columns below are targets, not cut-offs.

## Status of the review findings

Done by Claude on 13 Oct (on `main`): challenge named in the form (finding 1),
`CHALLENGE_MAPPING.md` (2), no-relapse-prediction framed as a safety choice (3), title
AURA Health (4), pilot metrics as labelled targets (5), personal email removed (9),
question-chip styling, draft `docs/presentation/SCRIPT.md`, 13 live screenshots in
`docs/presentation/screenshots/`. Remaining work is below, by agent.

## Tasks by agent

Each task: deliverable, then **Done when**. Every agent: start by `git pull origin main` in your
own folder, push only your branch, add a `HANDOVER.md` Log entry, and report branch + commit +
what you verified. Nobody merges into `main` or deploys unless the user says so.

### Claude — `/home/makodev58/aura-health-claude`, `improve/feature-claude`

| ID | Task | Done when | Due |
|---|---|---|---|
| C1 | Revise `docs/presentation/SCRIPT.md` from the user's feedback | User approves the script | 14 Oct AM |
| C2 | Build the deck `docs/submission/assets/aura-health-deck.pptx` from the approved script: chosen challenge, problem, product screens, live Q&A + trail, appointment, safety, Codex's architecture diagrams, challenge-fit table, how we built it (genuine tool screenshots), pilot metrics, limits and roadmap | ≤10 MB, 16:9, every slide inspected as an image, no unsupported claim, speaker notes per slide | 14 Oct PM |
| C3 | Record the screen walkthrough per scene (1920×1080) following the script; assemble with slides into a draft video without voice | Video 5–8 min with scene timings matching the script; user records the voice-over | 15 Oct AM |
| C4 | Claims review of everything in `docs/submission/` against code and evidence before release | Written list of corrections, or "none", in `HANDOVER.md` | 15 Oct AM |
| C5 | When the user directs: review and merge agent branches, deploy UI fixes, verify live | Live site checked at 390 and 1280 px | as directed |

### Codex — `/home/makodev58/aura-health-codex`, `improve/feature-codex`

| ID | Task | Done when | Due |
|---|---|---|---|
| X1 | Three architecture diagrams from `ARCHITECTURE_DOCUMENT.md`: (a) system overview with trust boundaries, (b) Aura-Agent investigation loop, (c) safety precedence and pinned resources. AURA palette, warm off-white, labels readable at slide size | SVG + 1920×1080 PNG each in `docs/presentation/diagrams/`; every element maps to implemented behaviour; planned items dotted | 14 Oct PM |
| X2 | Rehearse the demo question "When did sleep timing change, and was anything reported around then?" on the live site, at most 5 runs | Every outcome (answer, partial, fallback, reason) recorded in `EVIDENCE_LEDGER.md`; no reruns to pick a winner | 14 Oct |
| X3 | Second-pair-of-eyes check of `CHALLENGE_MAPPING.md` and `FORM_CONTENT.md` against the code | Corrections listed in `HANDOVER.md` (Claude applies them) | 14 Oct |
| X4 | Bring `ARCHITECTURE_DECK.md` and `ARCHITECTURE_DOCUMENT.md` in line with the decisions above (chosen challenge; one deck) | Both mention the challenge and point to `aura-health-deck.pptx` | 14 Oct |
| X5 | Release checks on the release commit: full Python suite, browser suites, signed-out checks of live site and GitHub, update `EVIDENCE_LEDGER.md`, `ASSET_REGISTER.md`, `manifest.json`, run `preflight.py` | Preflight reports only items awaiting the user's approval | 15 Oct |

### CodeBuddy — `/home/makodev58/aura-health-codebuddy`, `improve/feature-codebuddy`

| ID | Task | Done when | Due |
|---|---|---|---|
| B1 | Cover image with Miora, following `COVER_BRIEF.md`: title "AURA Health", subtitle "Context between appointments", based on the real screens in `docs/presentation/screenshots/` | `docs/submission/assets/aura-cover.png` 16:9 under 1 MB, plus a 1920×1080 master; readable at 384×216 | 14 Oct |
| B2 | Fix the clinician view's "When things changed" strip: the "1", "2" and date labels are oversized | Labels match card text size at 390 and 1280 px; browser suites pass on port 8046 | 14 Oct |
| B3 | Phone and laptop device frames (SVG) for placing screenshots in slides, in the AURA style | `docs/presentation/frames/phone.svg` and `laptop.svg`, screen area documented in pixels | 14 Oct |
| B4 | Assemble `docs/submission/assets/development-history.pdf` from genuine CodeBuddy and Miora sessions supplied by the user, following `EVIDENCE_GUIDE.md` | ≥3 legible screenshots plus chat history, under 10 MB, nothing invented or edited to show success | 15 Oct |

### User

| ID | Task | Due |
|---|---|---|
| U1 | Review and approve the presentation script (C1) | 14 Oct AM |
| U2 | Collect genuine CodeBuddy and Miora session screenshots/exports for B4 (at least 3) | 14 Oct |
| U3 | Record the voice-over for the video (C3) and upload it; supply the link | 15 Oct |
| U4 | Approve artifacts, direct merges/deploys, submit the form | 15–16 Oct |

## Kickoff messages (paste into each tool)

**Codex:**
> First read `docs/PATIENT_COMPANION_SPEC.md`: your build tasks are its Codex rows (§4), due 14 Oct
> before X1–X5. No fixed deadline: report done in `HANDOVER.md` when finished. Work only in `/home/makodev58/aura-health-codex` on `improve/feature-codex`. First commit or
> stash your current `HANDOVER.md` edit, then `git pull origin main`. Read
> `docs/submission/WORKPLAN.md`; your tasks are X1–X5 with their "Done when" criteria. Browser
> tests on port 8036. No runtime changes, quota changes, merges or deploys. Push your branch and
> report branch, commit and what you verified.

**CodeBuddy:**
> First read `docs/PATIENT_COMPANION_SPEC.md`: your build task is the patient-home UI in §4 (four
> cards + appointment items), built against the §3 contract with mocks until the endpoints land,
> before B1–B4. No fixed deadline: report done in `HANDOVER.md` when finished. Work only in `/home/makodev58/aura-health-codebuddy` on `improve/feature-codebuddy` (already up
> to date with `main`). Read `docs/submission/WORKPLAN.md` and `docs/submission/COVER_BRIEF.md`;
> your tasks are B1–B4 with their "Done when" criteria. Use the screenshots in
> `docs/presentation/screenshots/`. Browser tests on port 8046. Keep genuine screenshots of your
> CodeBuddy and Miora sessions. Push with `git push -u origin improve/feature-codebuddy`; do not
> merge or deploy.
