# Milestone 6 — Patient application review

Status: IMPLEMENTED / REVIEW PENDING. Date: 2026-10-03.

## 1. Delivered scope

Responsive, no-build-step patient web app: calm home, Good/Okay/Rough check-in,
optional safety-gated note, medication records, personal observations/provenance,
explicit explanation/held-for-review, wearable gap/return, structured review preview,
and a separate pinned safety panel. Synthetic Cases A–F are available in the UI.

No accepted safety/longitudinal algorithm, schema, clinical parameter, detector,
live-model configuration, wearable API, production authentication, automatic sharing,
deployment, or Simulation Data Agent was added. No CodeBuddy tool/evidence is claimed.

## 2. Architecture and files

```text
aura_ui/index.html + styles.css + app.js       presentation/input only
    → aura_app.api                          transport + same-origin static files
    → PatientEventService                   existing atomic/idempotent writes
    → aura_safety / aura_longitudinal        unchanged accepted decisions
    → PatientCommunicationService           existing bounded/static wording
    → SQLite repositories/audit             existing development persistence

PatientViewService                          read-only latest-event/provenance links
aura_app.demo                               explicitly synthetic checkpoint server
    → accepted simulator → production app/domain engines
```

New files: `aura_ui/{index.html,styles.css,app.js,README.md}`,
`aura_app/{patient_view.py,demo.py}`, `tests/test_milestone6.py`,
`tests/browser/{milestone6.cjs,run.py}`, and this packet.

Changed: `aura_app/api.py` (read view, static assets, local-only provider default,
no-store/same-origin response headers), `service.py` and `communication.py` (public
`requires_safety_gate` name; routing unchanged), `simulator.py` (optional checkpoint,
namespace and explanation omission; existing defaults unchanged), root README,
communication README, roadmap/M6 spec, and root HANDOVER.

API additions: `GET /`, `GET /assets/{path}`, `GET /patients/{id}/view`;
explicit demo factory only: `GET /demo/scenarios`. Existing command endpoints are
reused for writes. Controllers and frontend contain no drift/tier/anchor policy.

## 3. Test results

Python: `.venv/bin/python -m unittest discover -s tests -q` — **124 PASS**
(106 existing + 18 M6). Existing Starlette/httpx deprecation remains non-blocking.
Browser: UI1–UI15 plus OFFLINE and MANUAL_RETRY — **17 PASS** in real headless
Chromium. All four views have no horizontal overflow at 320/390/1280 pixels;
native dialog focus/Escape and keyboard focus styling were checked. No browser
page errors. `node --check` and `git diff --check` pass.

Each row below has a Python test in `tests/test_milestone6.py` and the corresponding
real-browser entry in `tests/browser/milestone6.cjs`.

| ID | Result | Python test name | Proven |
|---|---|---|---|
| UI1 | PASS | `test_ui1_stable_home_has_no_risk_score` | Stable backend state renders a quiet home without score/alert content. |
| UI2 | PASS | `test_ui2_checkin_reaches_existing_api` | A tap creates an existing check-in event and persists its timeline record. |
| UI3 | PASS | `test_ui3_optional_note_is_safety_gated` | Unscripted text reaches the safety gate, is held/degraded, and cannot enter normal conversation. |
| UI4 | PASS | `test_ui4_explanation_uses_existing_governed_path` | The D explanation command creates two held observations without moving anchors. |
| UI5 | PASS | `test_ui5_held_observation_retained_and_visible` | Held descriptions/explanation remain inspectable with reference-retention wording. |
| UI6 | PASS | `test_ui6_gap_is_unobserved_not_pathological` | The gap has UNOBSERVED state and an empty rolling sample, not a fabricated value. |
| UI7 | PASS | `test_ui7_reestablishing_shows_uncertainty` | Return displays REESTABLISHING as uncertainty and discloses the absent exit rule. |
| UI8 | PASS | `test_ui8_medication_records_without_dose_controls` | Routine acknowledgement persists through the accepted API without dose/taper controls. |
| UI9 | PASS | `test_ui9_safety_precedence_survives_ordinary_checkin` | A later Good tap/navigation cannot dismiss the authoritative F safety output/resources. |
| UI10 | PASS | `test_ui10_review_preview_does_not_share` | Review selection is a temporary preview; persisted snapshot remains NOT_SHARED. |
| UI11 | PASS | `test_ui11_why_asked_uses_latest_backend_provenance` | Why-asked uses recorded description, source, anchor version/window and latest event reference. |
| UI12 | PASS | `test_ui12_patient_can_initiate_while_quiet` | A patient can start an approved ordinary fixture interaction without a passive prompt. |
| UI13 | PASS | `test_ui13_no_diagnosis_probability_outputs` | Screens/contracts expose no diagnosis, relapse probability, internal T1–T4 score, or psychiatric percentage. |
| UI14 | PASS | `test_ui14_cases_a_to_f_available_without_truth_in_domain_events` | All A–F views use persisted production outputs without evaluation-truth payloads. |
| UI15 | PASS | `test_ui15_responsive_accessible_core_contract` | Semantic dialogs/navigation and responsive layouts work at phone/desktop widths. |

Supplemental Python checks: resource fixture matches the accepted bundle; unknown
fixture input is rejected; environment variables cannot enable a live model in the
supplied patient API. Browser OFFLINE proves automatic reconnect; MANUAL_RETRY proves
retry after request failure uses the same idempotency key and produces one raw event.
The browser also checks that a submitted script-like note is never executed.

## 4. Cases and visible behavior

Seed 7. Checkpoints are ordinary observable event prefixes from the accepted
deterministic synthetic generator; full A–F application regression tests still pass.
The labels/cutoff/explanation timing below are demo metadata, not engine inputs.

| Checkpoint | Day | Backend decision | Visible result | Result |
|---|---:|---|---|---|
| Stable | 20 | STAY_QUIET | Calm home, optional patient entry; OBSERVED/TRUSTED. | PASS |
| A · illness | 34 | STAY_QUIET | Physiological changes/context remain inspectable; no unsupported mental-health conclusion. | PASS |
| B · slow drift | 69 | STAY_QUIET (cooldown) | Accumulated anchored drift remains visible despite rolling adaptation; historical review changes retained. Quietness does not erase drift. | PASS |
| C · illness + independent change | 40 | TARGETED_CLARIFICATION | Relevant illness context coexists with independent change/check-in evidence and a small approved prompt. | PASS |
| D · before explanation | 30 | STAY_QUIET | Explicit linked context is available; patient command creates held state. | PASS |
| D · held | 69 | STAY_QUIET | Two held observations and review items, unchanged anchor, suppressed repeated prompt. | PASS |
| E · gap | 54 | STAY_QUIET | UNOBSERVED/TRUSTED; rolling mean/median absent, zero samples; no pathological interpretation. | PASS |
| E · return | 69 | STAY_QUIET | OBSERVED/REESTABLISHING; no automatic trust-restoration claim. | PASS |
| F · safety | 69 | SAFETY_REVIEW_REQUIRED | Authoritative CLARIFY fixture, static review-pending content and separate resources persist across screens/taps. | PASS |

The engine alone decides interruption. The UI does not add prompts merely because
a pattern card exists. Voluntary provenance inspection does not create an alert.
These results demonstrate engineering behavior, not clinical efficacy.

## 5. Privacy, safety and offline behavior

- Both supplied API/demo factories now explicitly use `DisabledProvider`, even if
  gateway environment variables exist. This closes the M5 review's privacy concern
  for these patient entry points. Live use awaits informed-consent governance.
  Explicit developer injection remains supported for synthetic evaluation; provider
  metadata/disclosure distinguishes it from the local-only default.
- No real detector exists. Demo fixture resolution is finite and restricted to
  enrolled synthetic patients: known structured taps, the prepared explanation,
  and two labelled message fixtures. Unknown text fails closed. No general benign
  text classification or context-credibility inference was introduced.
- A safety surface comes from the accepted output boundary's pinned-resource field,
  not a UI-assigned tier. It cannot be dismissed or downgraded. Offline presentation
  retains any already-displayed safety message alongside fixed fail-closed wording.
- The existing unverified Singapore resource placeholder is also embedded locally.
  Stale/unverified notice remains visible; no contact information was invented.
- Failed submissions retain their exact envelope in memory and retry idempotently.
  No plaintext local/session storage, durable protected queue, service worker, or
  cold-start offline/PWA support is claimed. Reload loses unconfirmed input with a
  warning. Already-loaded app resources remain usable without a network call.
- Review checkboxes are temporary preview only. No approval/share/send endpoint
  was introduced. Null-episode routine safety references are filtered in the UI only.

## 6. Reproduce

```sh
.venv/bin/python -m aura_app.demo --db aura-m6-demo.sqlite3 --seed 7
AURA_DEMO_DB=aura-m6-demo.sqlite3 .venv/bin/python -m uvicorn aura_app.demo:create_demo_app --factory --host 127.0.0.1 --port 8000
# Open http://127.0.0.1:8000/ and Explore demo.
.venv/bin/python -m unittest discover -s tests -q
```

Portable browser setup/runner is in `aura_ui/README.md`. Actual verification reused
already-installed developer Playwright/Chromium and shared libraries:

```sh
LD_LIBRARY_PATH=/home/makodev58/rendertest/libs/usr/lib/x86_64-linux-gnu \
NODE_PATH=/home/makodev58/rendertest/node_modules \
.venv/bin/python tests/browser/run.py
```

The runner owns a fresh temporary DB/server and stops it afterward. Browser result
JSON and mobile/desktop screenshots are under `/tmp/aura-m6-browser-artifacts` on
this development machine (not committed, not CodeBuddy evidence).

## 7. Assumptions and genuine open issues

- SQLite remains development/demo-only; no production auth/reviewer authorization.
- Synthetic timestamps remain at the displayed checkpoint during interactions;
  received-at/server time is still authoritative in the safety engine.
- Context associations/credibility remain explicit, not inferred from free text.
- No governed exit from REESTABLISHING; no clinical thresholds were invented.
- Safety questions/guidance/resources and engineering parameters need review.
- Live model disclosure/consent is not implemented; supplied entry points remain
  disabled. No clinical safety detector is implemented.
- Review approval/transmission and durable encrypted offline input are future work.
- Multi-client freshness/push updates, cold-start offline support, long-history
  replay/render scaling, and demo reset/deployment hardening belong to later work;
  this is not continuous safety monitoring.
- Initial checkpoint seeding is event-atomic, not whole-seed atomic. An interrupted
  seed can leave a partial patient, which the current restart skips. Use a fresh DB
  path if initial seeding was interrupted; completion/resume belongs to M7 hardening.
- Backend snapshot still contains routine null-episode references; patient UI filters
  them. Future sharing must define relevance/governance before transmission.

No blocking engine integration contradiction was found. The first browser run caught
a stale test-server fixture and a 320px flex-width error; both were corrected and
verified against a fresh server. Medication transport uses the already accepted
uppercase `MedicationStatus` values; readable tap labels remain neutral.

## 8. Verdict

M6 engineering stop condition met; ready for Claude/user review. Accepted domain
algorithms remain unchanged. M7 has not started. Do not enable live models, real
patient use or automatic clinician sharing on the strength of these synthetic tests.
