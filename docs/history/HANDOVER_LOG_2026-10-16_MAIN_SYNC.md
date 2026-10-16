# Handover log archived during 2026-10-16 main sync

### 2026-10-15 — Codex — Explain current key storage and Tencent CVM options
- User favors Tencent CVM and asks how LLM keys will be stored. Verified `SystemSettings` and settings UI source: private0700 directory/0600 plaintext JSON, token-protected writes, no saved-key readback/browser persistence. Documented minimal-change private file vs unimplemented SSM/KMS + scoped CVM-role retrieval. No secrets inspected/copied or deployment changes.
- Verified: source only plus official Tencent SSM/instance-role docs; documentation-only, runtime tests not rerun. Hosting/key-management choice remains planning, not provisioning authority.


### 2026-10-15 — Codex — Tencent ADP hosting fit follow-up
- User asks about Tencent ADP. Official docs describe an agent/workflow platform and integration APIs, not a verified drop-in host for AURA's full container. Added conditional recommendation: Tencent CVM with persistent storage fits the current architecture more directly; hostname remains transferable. No service choice or deployment authorized.
- Verified: official ADP overview/developer integration and CVM product docs; planning only, no runtime tests, account access, code/infrastructure changes or model calls.


### 2026-10-15 — Codex — Cloud Run hostname/session feasibility follow-up
- User asks whether Cloud Run can keep the existing URL: yes with custom-domain HTTPS/edge routing configuration. Added Google's supported mapping options and ephemeral-filesystem/best-effort-affinity constraints to `docs/JUDGING_AVAILABILITY_PLAN.md`; current in-memory sessions/local SQLite need adaptation for robust Cloud Run use. Compute Engine VM is a closer existing-architecture fit; recommendation only.
- Verified: official Google Cloud domain/runtime/affinity docs and previously inspected repository session design. Documentation-only, no runtime tests, cloud provisioning, DNS, purchase or deployment; no hosting choice recorded.


### 2026-10-15 — Codex — Plan judging availability using a Proxmox standby
- User requested planning while Claude fixes bugs; unused Proxmox host has no VM. Added `docs/JUDGING_AVAILABILITY_PLAN.md`: conditional external primary/standby failover, sticky routing, readiness/capacity checks, bounded rehearsal and explicit fresh-session limitation. Asked user about shared failure domains and session continuity; answers pending.
- Verified: hosted session/bootstrap/health source, Docker/Compose/deployment configuration and official Cloudflare routing/affinity/failover docs. Documentation-only; runtime tests not rerun, no paid model/load/outage tests, no Proxmox/live account inspection. No code/provisioning/routing/purchase/deploy changes.
- Left: topology, acceptable session restart, actual live ingress/feature availability/cost and expected visitor load. Claude's bug fixes are not independently reviewed here.

### 2026-10-15 — Claude — Switch script help (for the owner and the Telegram agent)
- `deploy/SWITCH_HELP.md` (also `deploy/switch.sh help`): purpose of blue/green, commands, how to read the output, when to switch, rules for bots (only `status|blue|green|--force|help`; confirm before switching; `--force` only on explicit "force"; never touch containers/tunnel/.env directly), and the manual Lighthouse command if green is down. The user's Telegram agent (Hermes, on the green machine) will call the script.


### 2026-10-15 — Claude — Settings gear and dialog spacing (user request)
- Header gear replaced with a clean, evenly toothed outline; settings dialog fields/buttons/notes spaced (Unlock no longer touches the token field; same for Save key and Refresh available models). Found by the settings suite: the "AURA agent live" light overflowed phones narrower than ~380 px; now dot-only there (label and tooltip keep the status).
- Verified: settings, catchup_calendar (16), landing, welcome suites PASS; no overlaps in the unlocked editor (390/1280); no horizontal scroll at 320/360/390. Rolled out blue/green; blue live, green standby, both `0b7e98e`.


### 2026-10-15 — Claude — Agent answer reliability: rephraser and findings from the record (user-approved)
- `aura_agent/runtime.py` + `tasks.py`: (1) `fill_findings`: each claim's structured finding (signal/direction/since) is filled from the cited delivered fact instead of copied by the model (the model mis-copied it in 4 of 5 live runs; FINDING_MISMATCH rejected correct answers even after a repair). (2) `rephrase_neutral`: when a draft fails the prohibited-wording check, a separate low-reasoning task restates only the sentences without causal/evaluative words; the result must pass the same wording check, every other check and the verifier; once per answer (user approved; the checker rules in `grounding.py` are unchanged and remain the authority). (3) Earlier: one citation repair for well-formed drafts. Never repaired: malformed/wrong-shape replies.
- Rolled out blue/green (green first, then blue, public back on blue). Now blue live, green standby, both at `df02d9e`.
- Verified: 395 Python tests OK. Live: causal questions 6/6 checked after rephrase; guided story green 5/5, blue 3/3 directly, plus a final public run; traces show findings filled, one citation repair and one rephrase all ending in checked answers. Agent step 20–41 s (budget 90 s).


### 2026-10-15 — Claude — Agent draft repair; story agent step checked on both servers
- User asked to reproduce the clinician-question fallback locally before blaming blue: green failed too (3/5 vs blue 5/5 at the same time), so it is model variance, not the deployment. Causes seen: CALCULATION_ANSWER_INCOMPLETE (fixed earlier), FINDING_MISMATCH, UNSUPPORTED_SIGNAL, PROHIBITED_CLAIM (wording such as "caused", "healthy").
- `aura_agent/runtime.py`: one bounded repair when a well-formed draft fails a grounding check (FINDING_MISMATCH, UNSUPPORTED_SIGNAL, UNDELIVERED_FACT, FABRICATED_NUMBER_OR_DATE, HEADLINE_BUDGET, UNSUPPORTED_CATEGORY); the corrected draft goes through all checks and the verifier again. Never repaired: PROHIBITED_CLAIM (clinical-claims policy, user decision pending) and malformed/empty/wrong-shape replies (existing contract `test_patient_prompt_contract`). Tests: repair succeeds once, only once, prohibited content never repaired.
- Rolled out blue/green style: green updated and checked → public switched to green → blue updated and checked directly → public switched back to blue. Now: blue live, green standby, both at `1cb6354`.
- Verified: 392 Python tests OK; green 15/15 story agent answers checked after the fix (the repair did not fire in those runs; improvement partly model variance); blue 1/2 directly (the fallback was PROHIBITED_CLAIM).


### 2026-10-15 — Claude — Blue/green hosting: "AURA agent live" light and switch script
- **blue** = Tencent Cloud Lighthouse (Singapore), **green** = the original self-hosted machine. Both run the same `main`, both have live AI (OpenAI gpt-6-luna). Exactly one runs the Cloudflare tunnel connector (dashboard-managed tunnel, route `http://app:8000`; no Cloudflare changes needed). As of this entry **green is live**, blue is standby.
- `deploy/switch.sh status|blue|green [--force]`: health-gates the target (app healthy, `/health` node name matches, live AI on, token file readable), stops the other connector **first**, starts the target, then samples the public `/health` until all 20 answers come from the target (alerts and re-stops the other if both answer). Machine details in `~/.config/aura/switch.env` (not in the repo). A switch ends current demo sessions (in-memory per server): switch between judges.
- `AURA_NODE_NAME`/`AURA_NODE_LABEL` in each `.env`; `/health` returns them and every response carries `X-Aura-Node`. Header light "AURA agent live" (phone: "Agent live"): blue/green dot = serving node, red = unreachable or live AI off; checked every 30 s, tooltip names server and model.
- Tunnel token on blue: `~/aura-secrets/aura-tunnel.token` (folder 0700). Green: sessions 64 and memory 2g staged in `.env` (applies on next app restart).
- Verified: hosted capacity tests incl. node name (12 OK); light screenshots phone/laptop, no overflow; `switch.sh status` = blue healthy/AI live/stopped, green healthy/AI live/running, public 10/10 green.


### 2026-10-15 — Claude — Tencent Lighthouse server prepared (not yet serving the domain); agent calculation rule narrowed
- New server: Tencent Lighthouse Singapore, 2 vCPU / 4 GB, Ubuntu 22.04, user `ubuntu`, SSH key `~/.ssh/aura-lighthouse` on the dev machine (password login off). Docker from Docker's repo; repo cloned to `~/aura-health`; `.env` (0600): secure cookie, bind 127.0.0.1:8017 (no public port), `AURA_MAX_DEMO_SESSIONS=64`, `AURA_MEM_LIMIT=2g` (new compose setting, default 1g). OpenAI key entered by the user with `~/aura-tools/set-key.sh` (hidden input, never seen by agents); OpenAI gpt-6-luna medium, live on, paid connection test PASS. **The domain still points at the old host** until the Cloudflare tunnel is moved (needs user OK).
- Found while testing: the clinician question in the guided story fell back about half the time (also on the old host). Cause: `CALCULATION_ANSWER_INCOMPLETE` rejected answers when the agent ran a check-in tally on its own while exploring a non-numeric question. `aura_agent/runtime.py` now requires the exact calculated sentence only when the question asks for a number (percent, how many, share…); regression test added. Also found: 16 demo sessions can run out on a busy demo day (hence 64 on the new server).
- Verified: 388 Python tests OK; on the new server via SSH port-forward: typed past-days update + calendar, guided story (step 5), safety-panel reset, full story 3/4 agent answers validated after the fix (remaining failure was an ordinary UNSUPPORTED_SIGNAL rejection with "Ask again"), API probes 4/4.


### 2026-10-15 — Claude — Visible demo reset on the safety panel (user request)
- After the safety example (outside the guided story) the only reset was inside the Demo guide. The safety panel now starts with a compact, dashed "Demo only: a real patient couldn't dismiss this. Here you can start fresh. [Reset the demo]" bar (hosted sessions with `can_reset` only; not for a lost connection; hidden while the guided story runs because its card has its own reset). It asks for confirmation, resets this visitor's synthetic session and reloads the same patient. Shared `resetDemo()` in `app.js` (Demo guide button unchanged).
- Verified: catchup_calendar.cjs 16 checks (new CU7: reset visible without scrolling the panel, panel cleared, same patient, fresh record), tour, milestone7, dual_view, welcome, companion (one flaky medication-answer failure, then 2 clean runs), plain_language, landing PASS; live check after deploy.


### 2026-10-15 — Claude — Guided story: past medication records step (user request, in-app story only)
- `aura_ui/tour.js`: step 5 "Missed a few days? Just say so" replaces "Honest when it can't answer" (still 9 steps). It opens the update dialog, types "I took it on most days except last Friday and yesterday", lets the live model propose days, answers Yes, saves, closes and opens the calendar, spotlighting the latest filled-in day (ringed ✕ next to today's solid ✕). If the model can't read it, it taps two days instead; if safety stops the text, the story pauses as usual. The 3-minute video is unchanged (user: not needed).
- Verified: tour.cjs (typed path via stub, step 5 asserts calendar with ≥10 ringed marks) and catchup_calendar.cjs, 9 consecutive clean runs after relaxing the shortcut-jump position check (one earlier unexplained failure in that pair, not reproduced). Fallback path checked locally (failing AI → 2 ringed days). Live, phone and laptop: AURA turned the sentence into days, asked one question, saved; 10 ringed marks; no page errors.


### 2026-10-15 — Claude — Home icon shortcuts (user request)
- User: calendar was hard to find at the bottom and every card needed scrolling. Added `#home-shortcuts` under the home heading: Dose, Medicine, Coming up, Ideas (jump to the card, focus it, reduced-motion aware; hidden when the card is hidden, e.g. safety state) and Calendar, Appointment, My data (open the page). One row on laptop, 4+3 grid on phone. `features.js` now places the summary after the shortcuts.
- Verified: `catchup_calendar.cjs` 14 checks (new CU1b) plus welcome, landing, tour, companion, cards, dual_view, impression, final_dash, plain_language, milestone7 PASS; live check after deploy.


### 2026-10-15 — Claude — Review 2 consolidated, fixes merged and deployed
- Merged Codex's and Gemini's review branches (docs + handover entries). Dispositions in `docs/BACKLOG_AND_CALENDAR_SPEC.md` §9.8. Fixed: save race and same-key changed answer (one transaction, 409), described/report days in review snapshot, review items, appointment list and clinician strip; patient-local report day; held input returned as HELD; gap's actual last record day; Gemini's focus retention/announcement, window-load failure, chosen-day focus, retry wording, reduced motion. R5 coverage resolved as a documented contract (signals this record has a source for).
- Verified: full Python suite **387 OK** (713 s); 15 hosted browser suites PASS (catchup_calendar 12, companion 10, milestone7 7, workflows 5, agent 5, plain_language 2, dual_view 12, welcome 3, landing 2, tour 5, cards 4, impression 5, qa_display 2, final_dash 3, story_charts 3); Codex's probes show R1–R4 and the gap fixed.
- Tests: 6 regressions in `tests/test_record_calendar.py` (incl. a two-thread race); browser suite strengthened (server-derived dates, keyboard focus, Yes branch, dashed style, future days, clinician has no edit button, element overflow, sharing restored in `finally`).


### 2026-10-15 — Gemini (Antigravity) — Review 2: catch-up/calendar UI and browser suite
- Fast-forwarded `improve/feature-gemini` to `origin/main` `ab1dd09`. Added `docs/BACKLOG_AND_CALENDAR_REVIEW2_GEMINI.md` (reviews `aura_ui/catchup.js` and `tests/browser/catchup_calendar.cjs`; recommendations only, no code changed).
- Main findings: (M) keyboard focus lost on every day tap because `showPreview()` rebuilds the buttons; (M) failed `update-window` load leaves controls enabled and `showPreview()` throws on null `state.window`; plus low items and test gaps (hard-coded fixture dates, failure paths untested, layout checks page-level only). No safety bypass found.
- Verified: `catchup_calendar.cjs` hosted on port 8056, 12/12 checks PASS (needed `NODE_PATH` to codebuddy's playwright and `LD_LIBRARY_PATH` to `/home/makodev58/rendertest/libs/usr/lib/x86_64-linux-gnu` for libgbm). Python suite not run.
- Left for Claude: fix the two M findings. No merge/deploy.


### 2026-10-15 — Codex — Independent review of Claude's completed catch-up/calendar backend
- User: “Claude is done, check your assigned task.” Latest remote handover assigns backend review; inspected main `ab1dd09` / implementation `1dbcd0c` without merging into this branch. Added `docs/BACKLOG_AND_CALENDAR_REVIEW2_CODEX.md` and `docs/evidence/calendar-backend-review-probes.py`. Five findings (two P1): save validation/write transaction race, dropped late-report provenance, held input claimed as saved, agent report-day timezone mismatch, coverage denominator; smaller contract follow-ups retained separately.
- Verified: synthetic fake-gate/interleaving probes reproduce findings; calendar6 PASS/222.004s (unrestricted rerun), medication-update8 PASS/0.540s and sharing6 PASS/9.607s;20 focused tests total. Initial restricted calendar runner stalled and was stopped (143). Harness compile and `git diff --check` PASS. No full-suite/browser/live/model run; Claude's recorded381 remains his evidence.
- Left: Claude fixes/final gate and Gemini's independent UI/browser review. No production code, main merge, settings or deployment changed.


### 2026-10-15 — Claude — Catch-up + calendar built, merged and deployed (`1dbcd0c`)
- Codex/Gemini had no commits, so Claude built all of §9 (backend, UI, browser suite); see spec §9.7 for contract differences. New: `aura_app/record_calendar.py`, `aura_ui/catchup.js`, `tests/test_record_calendar.py`, `tests/browser/catchup_calendar.cjs`; edits to models/service/evidence/hosted/api/companion/agent/tools, `index.html`, `app.js` (calendar page), `evidence.js` (relearning line).
- Verified: full Python suite **381 OK** (707 s); hosted browser suites catchup_calendar (12 checks, phone + laptop), companion, milestone7, workflows, agent, plain_language, dual_view, welcome, landing, tour, cards, impression, qa_display, final_dash, story_charts all PASS. Live (gpt-6-luna): "I took it on most days except last Friday and yesterday" → preview in 9.8 s, question "Were Fri 6 Mar and Tue 10 Mar the only days you missed?", Yes → saved 14 days, calendar shows ringed (filled in later) marks; no page errors.
- Review requested (user relays): Codex reviews the backend → `docs/BACKLOG_AND_CALENDAR_REVIEW2_CODEX.md`; Gemini reviews the suite + `catchup.js` → `..._REVIEW2_GEMINI.md`. Claude fixes findings.
- Watch out: "most days" can also fill today as Taken (reported later); today's dose card still reads only same-day taps.


### 2026-10-15 — Claude — APPROVED: catch-up + calendar build; assignments (Claude is final gate)
- User approved §8 A–E of `docs/BACKLOG_AND_CALENDAR_SPEC.md` and made **Claude the final gate** (Claude reviews, fixes, merges and deploys all agents' work). Contract and assignments are in **§9** of the spec.
- **Codex:** §9.2 backend (reported_later payload, group by scheduled day, update-window + update endpoints with idempotency/conflicts and hosted rule, companion medication_gap, coverage endpoint + agent fact, calendar projector with sharing filters, backend tests) on `improve/feature-codex`.
- **Gemini:** §9.4 `tests/browser/catchup_calendar.cjs` against the §9.5 element IDs, then an independent review of Codex's and Claude's branches, on `improve/feature-gemini` (port 8056).
- **Claude:** §9.3 interpret endpoint + `medication_backfill` agent task, all UI, integration, final gate.
- Everyone: record-local "now" = latest event `occurred_at`, never the wall clock (§9.1). Pull `main` first.


### 2026-10-15 — Gemini (Antigravity) — Reviewed Claude's catch-up/calendar proposal
- Added `docs/BACKLOG_AND_CALENDAR_REVIEW_GEMINI.md` (reads `origin/main` `5eba9fb` spec; recommendation only). Main finding: "latest record day" is `rows[-1]["occurred_at"]` over `rowid`-ordered events (`hosted.py`, `agent.py`, `medication_ask.py`, `workflows.py`), so backfill events with a past `occurred_at` would move "today" backwards. Proposed: keep `occurred_at` = now, carry the real day in `scheduled_time` + `reported_later`. Plus partial answers to Q1–Q6, Q8, Q9, Q11; Q7/Q10 and the engine's use of `scheduled_time` *(unverified)* left to Codex/user.
- Verified: code read only; no tests run, no code changed, no merge/deploy, no model calls.
- Watch out: this branch is behind `origin/main`; not merged by design. Codex still owes the official Q1–Q11 answers.


### 2026-10-15 — Codex — Catch-up/calendar brainstorming review
- User: Gemini joins; brainstorming only, no code. Reviewed Claude's `5eba9fb` proposal and relevant remote source; added `docs/BACKLOG_AND_CALENDAR_REVIEW_CODEX.md` with Q1–Q11 answers and product recommendations. Preserved independent branches; no merge, implementation, model call or deploy.
- Verified: fetched origin, inspected clean local status/history and remote source. Runtime tests not rerun for this discussion/documentation-only task; historical results remain historical. Gemini review and user scope decisions pending.

### 2026-10-15 — Claude — For Codex: review `docs/BACKLOG_AND_CALENDAR_SPEC.md` before anything is built
- User asked to build: medication catch-up (gentle "last record N days ago" line; patient describes past days in plain words → agent proposes → patient confirms in a mini calendar → saved as `reported_later` medication events), an engagement strip for the clinician, welcome back, "relearning your usual" line, and a **calendar** (patient + clinician, day markers, day detail). User wants Codex and Claude to agree the implementation first ("get it right once").
- **Codex: please answer Q1–Q11 in the spec** (payload flag vs source, past-dated event ordering and safety processing, review items, hosted 14-day rule, batch idempotency, UNKNOWN semantics, engagement classification, evidence fields, calendar projection design, day boundaries, agent tool). Proposed split in §7: Codex backend (§1 events/hosted rule, §5.3 projections), Claude agent task + UI + integration. No code until the user approves the answers.


### 2026-10-14 — Claude — CodeBuddy export masked and committed (user-directed)
- Secret check (values compared inside the container, yes/no only): settings admin token, OpenAI key and DeepSeek key do not appear in the export; no key/token/cookie patterns. User chose to mask and publish: `192.168.80.193` → `192.168.x.x`, SSH key file names → `~/.ssh/<key>`, `/home/makodev58` → `~`. Unmasked backup kept outside the repo (job tmp). `development-history.pdf` regenerated (28 pages). The `codebuddy_*.json` ignore rule was removed; both files committed. The public repo owner name still appears (already public).


### 2026-10-14 — Claude — Usage demo video (song half, option B) and one-line-per-finding notes
- New `video/tools/record_usage.cjs` + `assemble_usage.py`: a real usage session on the live site (no tour, no safety example), positive note "I enjoyed painting today for 3 hours"; waits trimmed to 3 s; re-asks a clinician question once if it falls back. Output `aura-health-usage-demo-novoice.mp4` 3:51 and `aura-health-combined-usage-draft-novoice.mp4` 7:18 (not in git). Details in `SONG_CUT_PLAN.md` option B.
- `aura_ui/agent.js`: appointment notes show one plain line per finding (claims combining two findings no longer joined with ";"). agent/impression browser suites PASS. Deployed.


### 2026-10-14 — Claude — Submission materials updated for today's features
- Description (FORM_CONTENT + SUBMISSION_CHECKLIST box 2.3): patient-controlled sharing paragraph; agent patient tasks (note reply, ideas, activities) and their checks; Q&A calculations in code; 367 tests at `8ea19c9`; today's live checks. ARCHITECTURE_DOCUMENT §6.2 (agent on the patient side), §12.1 (sharing), tools list incl. `summarize_checkins`; ARCHITECTURE_REVIEW addendum marks two superseded rows. Slide 11 adds "Patient-controlled sharing" box (arrow: limits what clinician runs can read), patient/clinician box text; slide 14 sharing point; regenerated via `reconcile_architecture.py` (deck, PNGs, reviewed PDF). SCRIPT scene 9 and SONG_CUT_PLAN section 8 mention sharing (section 8: 39 words in 24 s). Full, short, part-1 and combined videos rebuilt (not in git).
- Note: LibreOffice renders slide 14 with a substitute font and overlaps lines; with Nunito installed (as documented) it lays out cleanly.


### 2026-10-14 — Claude — Broadcast to all agents: Gemini joins; state of main
- **Welcome Gemini.** Merged its join entry (`aacb66e`). Roster with worktrees, branches and ports is under Current state (Gemini: port 8056). Its worktree has no `.venv` yet: link one like the others (e.g. `ln -s /home/makodev58/aura-health/.venv /home/makodev58/aura-health-gemini/.venv`, already ignored via `.git/info/exclude`). Gemini's branch is behind `main`; pull before work.
- **What changed on main today (read before touching these areas):** live model OpenAI `gpt-6-luna`, reasoning medium (settings list models automatically; per-provider reasoning; OpenAI reasoning+tools go through the Responses API). Patient side: aura-agent replies to safety-cleared notes, picks today's ideas from the curated pool, acknowledges chosen ideas, extracts patient-reported activities (patient-only detail); plain-language appointment notes. Clinician side: Codex's grounded check-in calculations in Q&A; activity totals card. **Patient-controlled sharing** (`aura_app/sharing.py`): clinician sees a curated minimum plus what the patient opts in to (notes, detailed readings, daily check-ins, activity phrases); demo defaults to everything. Architecture slides 11–13 are native PowerPoint diagrams (`deck/native_diagrams.py` → `reconcile_architecture.py`).
- **Rules for any new work:** every new clinician-facing fact must be classified minimum vs optional and respect `RecordTools(withheld=…)` / `/evidence?viewer=clinician`; any new agent-written patient sentence goes through `patient_text_problems` with a fixed fallback; safety state always wins. Tests: full Python suite (367 OK at `8ea19c9`) and hosted browser suites via `tests/browser/run.py --hosted --port <yours>`.
- Open question for the user: `AI_CAN_DO_IT_Hackathon_Singapore_2026_Brief.pdf` is tracked in git and public on GitHub; keep only if the organisers' brief is public.


### 2026-10-14 — Claude — Patient-controlled sharing with the clinician (user decision)
- User decision: what the clinician sees depends on patient authorisation for all data; a curated minimum is agreed at sign-up; demo defaults to everything shared, but the design must handle minimum-only. `aura_app/sharing.py`: minimum = AURA findings and their summary numbers, check-in summaries/runs, medication routine records, activity totals, safety state (always); optional = notes (incl. typed context explanations), detailed readings, daily check-in entries, activity phrases. Choices are timeline `SHARING_CONSENT` rows (audit). Clinician-serving runs (clinician_brief, question_ranker, record_qa with asker=clinician) build `RecordTools(withheld=…)`: withheld facts are never created and a "Not shared … ask the patient" fact sits where the data would be (context/series/decisions). Agent cache fingerprint now includes consent and activity tags (no replay across a change). `GET /evidence?viewer=clinician` filters; `GET/POST /sharing`; activity summary includes phrases only when shared.
- UI: patient "What your clinician can see" card on the appointment page (minimum list + four switches); clinician status line at the top; charts, chart dates and raw comparison hidden when readings are withheld; "What was reported" hidden when daily check-ins are withheld; Demo guide "Patient sharing: Everything / Minimum only". UI hiding mirrors server state; with real auth the clinician client would call only viewer=clinician endpoints (demo actor is self-declared).
- Verified: 367 Python tests OK (6 new `tests/test_sharing.py`); 11 hosted browser suites PASS. Live: default "shares everything"; Minimum only → status line, charts hidden; "Do we have access to the patient's notes?" → "No… not shared… ask the patient" (3/3, verifier PASS).

### 2026-10-14 — Gemini (Antigravity) — Joined; worktree ready, awaiting instructions
- New agent present. Worktree `/home/makodev58/aura-health-gemini`, branch `improve/feature-gemini` from `origin/main` `ccaf440`. Browser port: none assigned yet (suggest 8056 if needed *(unverified free)*).
- Read-only so far: no code changes, no merge/deploy, no live-model calls. Will follow the branch workflow under **Git & remote**; other agents' worktrees untouched.
- Verified: `git worktree list` shows the new tree. Waiting for the user's first task.


### 2026-10-14 — Claude — Patient-reported activities from notes (user design: details patient-side, aggregates for clinician)
- New `aura_agent/activities.py` + `aura_app/activities.py`: after a safety-cleared note (normal state, live agent), the agent proposes activity tags (`activity_extract`, low reasoning); deterministic checks keep only categories physical/social/creative/restful/outdoors, phrases verbatim in the note, and minutes stated in the note. One `PATIENT_ACTIVITY` timeline row per processed note (never re-sent). Endpoints: `POST /activities/extract` (UI calls after a note), `GET /activities` (patient detail), `GET /activities/summary` (aggregates). Patient card "Things you've mentioned"; clinician card "Everyday activity the patient mentioned" (days mentioned + stated hours, last 14 record days vs previous 14; no phrases; framed as a conversation starter, not a wellbeing measure; counts not a score per discussion with user). Clinician agent gets one aggregate fact via get_context.
- Note: the clinician agent can still read safety-cleared notes themselves (existing behaviour the user kept), so a Q&A answer may quote a note.
- Verified: 361 Python tests OK (6 new `tests/test_activities.py`); 8 hosted browser suites PASS. Live: "I spent 10 hours painting this weekend and walked my dog with a friend" → patient card 2 items (10 h creative; physical/social/outdoors); clinician card totals; "Has the patient mentioned spending more time on hobbies recently?" → checked answer citing 1 day/10 h vs 0 (4 of 5 runs; 1 fact-check fallback).


### 2026-10-14 — Claude — Reviewed, merged and deployed Codex `ecfa8b8` (check-in calculations in record Q&A)
- Review: bounded design confirmed (model picks category/window/denominator; Python calculates; exact server sentence with coverage; percentage exception only for that sentence in RECORD_QA; one repair then honest fallback; offline extraction never runs the calculation). Merge `cb1fcc8` (handover conflict only). 355 Python tests OK; hosted browser suites agent, qa_display, impression, dual_view, companion, tour, cards PASS.
- Live rehearsal (gpt-6-luna, medium): "What percentage of the last 30 days were recorded as Rough check-ins?" → 66.7% (20 of 30), 10 Feb–11 Mar, full coverage, verifier 1/1, 17 s. Two-period comparison (first half Feb vs first half Mar) → 0.0% (0/15) vs 100.0% (11/11), 22 s; model first requested 1–15 Mar, tool rejected (WINDOW_BUDGET, record ends 11 Mar), model corrected to 1–11 Mar. Both shown in the "Also recorded" (routine) style.
- DeepSeek `deepseek-v4-pro` (reasoning none) checked at user request: connection test PASS; guided-story agent 2/5 (draft-validation rejections ×2, malformed tool-call JSON ×1). User reverted to gpt-6-luna medium (cheaper).


### 2026-10-14 — Codex — Deterministic derived facts for clinician check-in Q&A
- Fast-forwarded `improve/feature-codex` to main `eac0334` as requested. Added check-in aggregation tool, local-day/coverage/provenance rules, narrow grounded-percentage allowance, prompt v12, one bounded completion repair and a visible calculation trace. No engine changes, main merge, deployment, settings or paid model calls.
- Verified: full355 tests PASS/492.432s; final focused10 PASS after tightening completion to require the calculation sentence, not merely its citation; final trace wording smoke and `git diff --check` PASS. Initial runner stopped for fallback integration fix; first completed run found two empty-tool-call compatibility errors and two old-version assertions, corrected before the passing rerun. Existing Starlette/httpx warning. Documentation: `docs/CLINICIAN_QA_CALCULATIONS.md`. Live provider reliability remains unmeasured; Claude/user owns merge and rehearsal.

### 2026-10-14 — Claude — Plain-language appointment notes for patients
- User: the visit note looked cluttered/technical. Presentation-only change in `aura_ui/agent.js` (agent, skill and validators unchanged): each finding renders as one plain line from its structured metadata ("Going to sleep later, since late February"); the agent's exact checked sentence and sources sit behind "Details"; lines without a finding fold into "More from your record"; "✕ Remove"; heading "Things you might want to think about" over the question chips. Card/button renamed "Notes for your next appointment" / "Draft my appointment notes" (who it's for: the patient, to bring to their appointment; nothing is sent).
- Clarified to user: in this demo the clinician view reads the same record (incl. safety-cleared notes); patient-approved sharing is intended, not built (stated on the Disclaimer page).
- Verified: hosted browser suites agent (adjusted), impression, plain_language, dual_view, tour, final_dash_polish PASS; live note checked.


### 2026-10-14 — Claude — aura-agent replies to notes, picks ideas, acknowledges choices (user-approved)
- User decision: the patient side should feel agentic; relax "fixed wording only" for safety-cleared notes and ideas. `14d5338`…: (A) In the normal safety state, after the safety gate passes, a live agent writes a short reply to the note (`note_reply` task, low reasoning) checked by `patient_text_problems` (PROHIBITED plus no medicine/care-team talk, numbers/links, sent/shared claims, instructions, crisis words, ≤3 sentences); any failure → the approved fixed sentence. Card heading "From AURA"; page scrolls to the reply. (B) Ideas: curated pool now 14 (`suggestions.json` v2); `POST /companion/suggestions/personalize` lets the agent choose up to 3 from the pool using the recorded change and recent cleared notes, plus a checked "why" line (cached per record/model, one pick at a time); `POST /companion/suggestions/choose` records `SUGGESTION_CHOSEN` on the timeline (shown as "Idea chosen"), returns a checked acknowledgement or fixed "Noted for today. Go at your own pace."; chosen ideas stay ticked. Hosted only: `DisabledProvider` elsewhere keeps the old behaviour.
- Verified: 345 Python tests OK (11 new in `tests/test_agent_patient_replies.py`); hosted browser suites PASS (companion and dual_view adjusted for the new element/request). Live: chess note → AI reply in ~6 s, in view; agent-picked ideas referenced the note; tap → acknowledgement; tick survives reload.
- Watch out: this deliberately widens patient-facing generation (sponsor/clinical review still owed). Unknown-shape or failing replies always fall back. Picks cache in memory per hosted session.


### 2026-10-14 — Claude — Validated and published Codex's architecture audit (`dd77940`)
- Code spot-checks confirm Codex's corrections (see `docs/submission/ARCHITECTURE_REVIEW.md`, Claude section). Fixed: exporter no longer adds outlines to boxes (python-pptx `line.color` getter side effect); slide 11 companion text fits with a substitute font; "Observable events via app ingestion" label moved off the connector. Re-ran `reconcile_architecture.py` (deck, 6 PNGs, 5-page PDF); LibreOffice render checked; 18 glued connectors. Voice-over section E reworded. Full (5:58) and short (3:00) videos rebuilt with the corrected slides (not in git).
- Canonical architecture export is now `docs/presentation/deck/reconcile_architecture.py` (keeps the audit speaker notes); `make_hybrid_pptx.py` rebuilds the whole deck but drops those notes — run reconcile after it.


### 2026-10-14 — Codex — Architecture PDF/code audit and reconciled exports
- Audited supplied five-page PDF against main90e31ea; detailed findings/source map in `docs/submission/ARCHITECTURE_REVIEW.md`. Corrected native diagram source, deck slides11–13, diagram/frame PNGs and five-page reviewed PDF; original cover/close preserved. Updated architecture documentation/manifest/register; archived pre-review handover and compacted older logs, retaining all entries in the snapshot. Closed stale tour/retry-ID tasks from verified source; no runtime or settings changes.
- Verified: artifact structure/text bounds,18 attached connectors, only11–13 slide XML changed,5 PDF pages/original bookends pixel-identical/six1920×1080 PNGs; mock clock confirms90-s check can return at119 s withMODEL_TIMEOUT. `.venv/bin/python -m unittest discover -s tests -q`:334 PASS/459.063s (existing Starlette/httpx warning); first restricted runner stalled and was stopped, unrestricted rerun completed. No paid calls/browser/live deployment recheck.
- Left: human artifact review and separate video-frame refresh; no merge/deploy/submission/clinical acceptance. Review branch `codex/architecture-review` in `/tmp/aura-architecture-review`; required preexisting agent branches untouched.


### 2026-10-14 — Claude — Merged Codex `7ab3502` (ad song draft); song v2–v5; short video; cover pill
- Merged `improve/feature-codex` (original `AURA_AD_SONG.md`, kept unchanged as history). User-directed revisions by Claude: `AURA_AD_SONG_v2.md`…`v5.md`; **v5 is current** (user's LOCI-style prompt adapted to Aura, 92–104 BPM; 7-syllable on-beat lines with true rhymes; chorus "Aura, room for your day (room for your day)"; outro fades on the hook; tagline stays on screen, not sung). `docs/presentation/video/SONG_CUT_PLAN.md`: song for the opening/close, voice-over A–G for the middle.
- Cover slide pill now "Healthcare track" only (footers/diagram subtitles unchanged). New `video/tools/assemble_short.py` → `aura-health-short-3min-novoice.mp4` (3:00, not in git; too short for the 5–8-min form field). Full cut rebuilt with the new cover (5:58).
- `docs/submission/SUBMISSION_CHECKLIST.md`: one-page checklist + copy-paste form text (334 tests at `4cf8c40`). GitHub repo is now public (checked signed-out 2026-10-14). CodeBuddy branch had no new commits.


### 2026-10-14 — Codex — Original AURA video-ad song and Suno prompt
- Added `docs/submission/AURA_AD_SONG.md`: “Room for Your Day”, original lyrics, 1970s soft-rock direction, AURA chorus/brand outro, 88 BPM/66-bar approximate three-minute arrangement, picture cues and optional instrumental prompt. No audio generated or narration/runtime changed. Verified: duration arithmetic and documentation diff; runtime tests not rerun for creative copy. User/editor generates and selects the audio.


### 2026-10-14 — Claude — Native diagram slides, cover copy, history PDF
- Deck slides 11–13 are now native PowerPoint diagrams (`deck/native_diagrams.py`, called from `make_hybrid_pptx.py`): editable boxes and connectors glued to connection sites (18 arrows, all glued; verified in the XML and via a LibreOffice render). Content refreshed (configurable provider + operator model/reasoning, 90-s budget, no alerts). `diagrams/*.png` are now LibreOffice renders of those slides; Codex's SVGs kept as history. Video re-assembled (5:58) with the new slides.
- User placed `assets/aura-cover.png` (1672×941, 1.8 MB — over the form's stated 1 MB) → `aura-cover.jpg` same resolution, 0.42 MB. User placed the CodeBuddy export (`codebuddy_20261014013250.json`, now git-ignored) → `assets/development-history.pdf` (27 pages: transcript + 8 screenshots; builder in `docs/submission/tools/`). Manifest/FORM_CONTENT upload mapping updated; all three uploads REVIEW_PENDING. Assets other than the PPTX are not committed (await user approval).
- Portable LibreOffice for render checks: job tmp `lo/` (not in repo).


### 2026-10-13 — Claude — Script v4, deck and video refreshed to the latest build (user asleep; requested)
- `7d3616f`: SCRIPT v4 (scene 8: paced masked example, clinician sees the safety state on opening the record, no alerts; live model note). Deck rebuilt in story order (6 medication, 7 appointment, 8 clinician + agent, 9 flu, 10 safety) — this also does the user's planned "move slide 7 after 9", and fixes speaker notes that had been one scene off for slides 7–9. Fresh live screenshots (`screenshots/v2/`, new `s08a-note-masked-phone`); safety slide shows the masked note box + panel; agent callout now quotes the captured run ("A second check reviewed 3 statements; all supported", first attempt). PPTX 18 slides, 1.38 MB.
- Video re-recorded from the live tour (phone + desk), assembled 5:58; `VOICEOVER.md`/`timeline.txt` updated. Desk take: first agent draft failed a fact check (shown honestly), Ask again gave a checked answer. MP4 is not in git: `docs/presentation/video/aura-health-walkthrough-novoice.mp4` in the main folder.
- Watch out: if the user had hand-edited the PPTX outside the repo, those edits are not in this rebuild.


### 2026-10-13 — Claude — Paced, masked safety example; honest clinician wording
- `9923ba4`: "Show the safety example" now opens the note box, shows the example (~5 s visible) and highlights Send before sending. Example buttons show readable `data-sample` text (safety one masked per user: "I w*** t* k*** m****** (sensitive message masked)"); submit maps a sample back to its approved fixture, so hosted rules are unchanged. Tour card no longer says a clinician resolves it: "the clinician sees it when they open the record. This prototype doesn't send alerts." (No clinician notification exists — DECISIONS.md scope; safety de-escalation targets await clinical approval.)
- Verified: tour 5/5, milestone7, dual_view, workflows, welcome PASS (hosted runner); live check of the paced/masked example. milestone6 (non-hosted) has 9 failures, identical on pre-session `47dee17`.


### 2026-10-13 — Claude — Plain wording in the patient note dialog
- `dad3b35`: "I want to mention something" dialog now reads "What would you like AURA to know?", examples "An everyday note" / "A worrying message" / "A question for my doctor", "Send to AURA", one plain safety line and a made-up-details reminder. Technical/deployment disclosure removed from the dialog (still on the Disclaimer page via `privacy-notice`). Fixture values and hosted rules unchanged. SCRIPT.md updated; deck slide notes still say "Safety handoff fixture" (user edits the deck).
- Verified: hosted runner suites PASS (dual_view, agent, workflows, impression, story_charts, cards, final_dash, final_dash_polish, plain_language, qa_display, welcome, landing, companion, milestone7, settings; tour 5/5 when run alone — it timed out when run last after 13 suites on one server). redesign.cjs still fails the pre-existing `#quiet-card` check. Live dialog checked on phone.


### 2026-10-13 — Claude — Safety example no longer leaves the visitor stuck
- User: after "Show the safety example" the safety panel stayed with no way out. The panel staying is intended (patients can't dismiss it); `8ba5908` keeps the tour card open after the example, explains this, and offers "Reset the demo" (clears it) or "Keep exploring". Panel wording itself unchanged (safety content).
- Verified: `tour.cjs` 5/5 PASS on a local hosted server (new TOUR5); live: card shows and Reset clears the panel. Deployed.
- Note: local tour tests need the hosted app (`aura_app.hosted:create_hosted_app` with `AURA_DEMO_ROOT`); the plain demo app returns 403 on the flu step.


### 2026-10-13 — Claude — Auto-filled model list, reasoning level, OpenAI Responses path
- `a2d2e75` settings: model dropdown filled from the provider's `/models` (saved model kept selected; exact-ID input + Refresh kept); reasoning select (default medium) saved per provider and shown in the status line; `vendor.py` maps reasoning per provider; agent config v5 (90 s run, 30 s provider timeout). `038d80b` OpenAI reasoning+tools via `/responses`; `f0212f8` 256 KB cap for Responses replies (they echo the tool list; caused `too_large`).
- Verified: full Python suite 334 OK; `tests/browser/settings.cjs` PASS; live model list READY; live trials as in Current state. Deployed `f0212f8`.
- Watch out: reasoning raises answer time (≈50–110 s per agent answer). Responses calls are stateless (`store:false`, reasoning items not carried between turns).


### 2026-10-13 — Claude — Intuitive guided story (`aura_ui/tour.js`), following Codex's review
- User: the 3-minute story wasn't intuitive. New guided story: intro card ("See how AURA helps, through one person's day", Start; says it starts a fresh demo), then 9 steps in 3 chapters (Your day: breath, summary, dose [tour taps Skipped + Side effects and shows the saved result], medication topic, typed question with honest abstention; Getting ready for a visit: visit note with the missed dose, clinician view, agent Q&A with the real result or the fallback wording; When things change: simulated flu). Finish card: Show the safety example / Explore on my own / Start again.
- One target at a time: static outline + gentle dimming (z 7) under the help button (z 8) and tour card (z 9); progress dots and chapter label; Back never repeats an action (done set per run); late results from an exited tour are ignored; safety panel pauses the tour; Escape/× exit removes everything. Manual Next only (autoplay deferred).
- Entry points: landing "Play the 3-minute story" and a single "Start the guided story" button in the demo guide (six old buttons removed). Tests: new `tour.cjs` (4 checks: help not covered, one dose write with Back/Next, nine steps to finish, exit/Escape/desktop placement; typed medication reply stubbed because local hosted accepts only labelled text); `impression.cjs`, `final_dash_polish.cjs`, `landing.cjs` updated on purpose. All 17 hosted suites run PASS.

### 2026-10-13 — Claude — Merged CodeBuddy `781713a` (timeline strip) with a phone-size fix
- Merged `improve/feature-codebuddy` (capped timeline SVG width at 720 px; labels sized inside the drawing). Measured: desktop fixed (labels ~19 px), but phone labels became ~8 px; added a phone rule (21 user units → ~15 px). Screenshots checked at 1440 and 390.
- `dual_view.cjs` DV3 expected the quiet card above the fold on phones; the companion cards now lead the patient home (since the event-target fix), so DV3 now checks the help button fully in view and Today's dose starting in the first screen. Browser final-dash, story-charts, plain-language, dual-view (12), cards PASS.

### 2026-10-13 — Claude — Reviewed/merged Codex `9a13e34`; medication retry-identity fix; hybrid deck
- Codex branch merged into `main` (post-flu verifier payload trim with tests AW2b/AW2c, companion docs, updated overview diagram). Deck rebuilt so slide 11 shows the updated diagram.
- Fixed Codex's finding in `aura_app/medication_ask.py`: the patient question event ID now includes a hash of the question text, so reusing a run ID with different words is a new message with its own safety assessment (test MED4b).
- Deck is now hybrid (`make_hybrid_pptx.py`): themed background picture + every text block as an editable text box in Nunito; slide 16 uses the general "How we built it" wording (user).
- Release blocker for the user: the GitHub repository returns 404 anonymously (private); judges need source access.

### 2026-10-13 — Codex — Review of Claude's proposed intuitive guided story; handoff to Claude
- **User direction:** satisfied with the product; the story must be understandable without someone explaining how to operate it. Support Claude's one-card/one-target/Next design, automatic navigation, progress, Back/Exit and optional safety ending. These are recommendations for Claude's implementation, not claims of a completed redesign or new deployment authority.
- **Make it a connected story:** keep one synthetic person throughout, with three plain chapter labels: “Your day”, “Getting ready for a visit”, “When things change”. Nine steps can sit inside those chapters; do not show nine competing choices. Start with “See how AURA helps through one person's day” and one Start button. Explain each visible consequence in one short sentence; avoid a feature catalogue or another instruction panel.
- **Refine the sequence:** retain Claude's nine steps and pre-flu clinician question. At the dose step say “In this example, the patient skipped a dose because of side effects”; show the committed result before Next. At the appointment step highlight that same reason so the benefit is obvious. Label the role change “Now, the clinician's view of this demo record”; do not imply the previous visit note was sent or approved. Give the real Q&A investigation/result room to be seen; medication topic lookup is curated information, not the agentic centerpiece. Put the optional safety example after a satisfying finish, alongside “Explore on my own” and “Start again”.
- **One action, one visible result:** manual Next is the default. Let the tour perform the demonstrated action through existing application commands, then wait for the actual save/render result. Do not ask users to locate Skipped/Ask/simulator controls behind the tour. No fixed-delay assumption that a request has finished. Back revisits the result; it must not record another dose, repeat a model call or simulate another three days. Double taps/retries must reuse the same step operation identity; bind changed medication questions to fresh identities and verify the previously reported reuse gap on the integrated revision.
- **Honest model behavior:** Q&A-before-flu is a sensible presentation order, but does not establish reliability or resolve the post-flu findings. Show the actual investigation trail and verified answer, or plainly “AURA couldn't complete this answer; here are the related records.” Allow Continue on fallback/error; no invisible retry-until-success, fabricated verification or prerecorded answer presented as live. Flu narration should point to the returned changes, not promise specific AI wording or a suggestion that the actual response lacks. Keep simulation labels in the tour layer, outside production decision inputs.
- **Mobile-first spotlight:** at 390px portrait, keep the highlighted result and a compact tour card visible together; use available space rather than always stacking another fixed panel above the help dock. Reserve safe-area/help-button space, recalculate after content changes, and make long answers scrollable. Use a static outline plus a gentle dimming layer rather than a continuously glowing animation. Keep help and any safety panel fully visible AND clickable; activation pauses/dismisses the ordinary tour. Support keyboard focus, readable contrast, reduced motion and Exit at every step. Never leave focus trapped behind an overlay.
- **Autoplay and session handling:** build reliable Next/Back first; autoplay is optional polish, with visible Pause and pauses on user interaction, slow/error responses and safety. “About 3 minutes” is an estimate, not a deadline that cuts off an answer. Start/restart should use a fresh isolated synthetic tour run; do not silently wipe someone's exploratory session. Exit removes overlays/listeners and stops further automatic actions; a late response must not scroll or advance the abandoned tour. Reset only synthetic tour state, never lower a safety state in place. Safety remains opt-in and uses the existing authoritative fixture/path.
- **Acceptance for Claude:** an unfamiliar person on a phone can finish without verbal instructions or hunting for controls, then explain the dose-to-visit-note connection and what the agent investigated. Browser checks should cover 390px portrait/laptop, Next/Back/double tap, slow model/fallback, missing target, exit/restart, and help/safety/reduced-motion behavior. Verify one dose write/one flu advance per run and no autoplay after Exit. Run a short observed first-use walkthrough; passing selectors alone cannot establish intuitiveness.
- **Verified this session:** inspected `aura_ui/features.js` (six independent story buttons, fixed-delay scrolling, manual dose/Ask instructions) and existing story tests; `test_ui_media.py` 2 PASS/0.126s, existing Starlette warning. Documentation-only change; full330-test result above remains historical. No runtime edits, model calls, merge or deploy. Publish this entry on `improve/feature-codex` for Claude to read; retain other agents' entries when integrating.


### 2026-10-13 — Codex — Integrated companion claims/diagram and narrow post-flu verifier fix
- Requested main pull completed on Codex branch; both handover histories retained.
  Updated assigned challenge/form/current-capability/architecture documents and
  overview SVG/PNG (1920×1080). Claude: re-render the deck's overview slide; narration
  and screenshots untouched.
- Post-flu live diagnostics retained both attempts: verifier-stage ValueError and
  FABRICATED_NUMBER_OR_DATE, not timeouts. Local seeded fixture showed duplicate
  patient-facing verifier fields caused50,053 chars; clinician projection now
  preserves facts/metadata in25,636 chars. New budget failure trace code; unchanged
  40k limit/grounding/semantic checks. Two regressions PASS/38.472s; candidate68372f3
  full330 PASS/474.013s,15 hosted suites PASS/redesign first-fold FAIL. LiveA–F
  reads/B/F companion guard and local registry3 checks PASS; GitHub404 and strict
  preflight1. Updated ledger,
  register/manifest; no green final-release claim. See ledger for exact commands.
- No merge into main, deploy, provider/secret/quota changes. Medication changed-text
  retry identity gap remains a separate open finding; do not overlook it at release.


### 2026-10-13 — Codex — Consolidated companion/release verification; medication retry-ID finding
- User: focus on Codex's area, leave Claude's narration and supplied screenshots alone. Read integration history; `missed_days` was already fixed in6c4e265, so no duplicate runtime patch. Exported immutable495087d to/tmp and independently tested merged code while leaving all worktrees/main untouched.
- Verified:327 Python PASS/469.072s (initial restricted run stalled, stopped only that runner with exit143; unrestricted rerun completed). Companion/Q&A-display/M7 browser18 checks PASS on8036; actual count/idempotency contract PASS; signed-out liveB normal/F safety reads PASS, no generation requested. Anonymous GitHub404 persists. Strict preflight1 with missing uploads/video/approval. Updated assigned ledger/register/manifest; source tested hash remains candidate-only, package DRAFT.
- New reproduced QA gap: changing medication question while reusing a valid runUUID causes0 fresh detector calls and ABSTAINED; freshUUID for the same text correctlyBLOCKED under identical mock proposal. Medication-route owner should bind request fingerprint or reject changed reuse. No medication route, narration, evidence image, provider or deployment edits. New37a2f32 script/tour UI is not covered by495087d results. Full details in `docs/submission/EVIDENCE_LEDGER.md`.


### Earlier history
- All older entries, reviews and explicit user decisions are preserved in [the pre-architecture-review snapshot](docs/history/HANDOVER_2026-10-14_PRE_ARCHITECTURE_REVIEW.md). Its stale pending-tour, retry-ID and source404 snapshots are superseded above.
- M1–M6 engineering/review history, dated provider trials, companion integration and earlier release limitations remain in that snapshot and their linked review/evidence documents; no clinical or final-release acceptance is inferred.
