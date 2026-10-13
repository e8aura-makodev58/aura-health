# Patient companion features — build spec (13–15 Oct 2026)

Status: APPROVED by the user on 2026-10-13 ("Cancel feature freeze and let's go all in").
Author: Claude. Purpose: close the gaps against the Healthcare track's **Challenge Statement 2,
Scenario 1** (see `docs/submission/CHALLENGE_MAPPING.md`). Three agents build in parallel on
their own branches; this file is the contract between them. Change it only by agreement
recorded in `HANDOVER.md`.

## 0. Product shift

AURA becomes a **patient-facing companion first**: medication, daily dose, health tracking,
coming-up reminders and gentle suggestions on the patient home. The clinician view stays and is
presented as "what the patient chooses to share". Everything already built (baselines, safety,
agent Q&A, appointment prep) stays.

## 1. Safety rules for every new feature (non-negotiable)

1. **No medication advice.** No dose changes, stopping, switching, tapering or "what to do"
   instructions beyond restating the person's own prescription label and approved leaflet text.
   Every medication answer ends with: "If you're unsure, check with your pharmacist or doctor."
2. **Abstain when unsure.** Anything outside the approved content gets exactly:
   **"I'm not able to identify that medication, please check with your pharmacist."** (unknown
   medication) or **"I'm not able to answer that here, please check with your pharmacist or
   doctor."** (unknown topic).
3. **Medication content is curated, never AI-written.** AI may only *match* a question to an
   approved topic; the answer text comes from the approved file. Label all content
   "Development content — needs pharmacist review".
4. **Safety first.** Patient-written text goes through the existing safety gate before anything
   else (same path as patient questions today). Suggestions and medication answers are hidden
   whenever the safety state is not normal or is degraded; the safety panel stays on top.
5. **Suggestions are curated and optional.** Fixed list, chosen by the patient, never about
   medication, never framed as treatment, never shown during a safety interaction.
6. **No relapse prediction, no scores, no streaks.** Adherence is shown as a plain count
   ("taken on 6 of the last 7 days"), never as a grade, and missed doses are never shown as bad.
7. **Synthetic data only.** The demo medication is a synthetic prescription.

## 2. Synthetic demo prescription (fixture)

All demo patients get a synthetic treatment context (replaces "fixture-only; no treatment
instruction"):

| Field | Value |
|---|---|
| `medication_name` | `Sertraline` |
| `medication_schedule` | `50 mg, once each morning` |
| `regimen_start` | 9 months before the record start |
| `stable_since` | 6 months before the record start |
| `review_cadence` | `every 3 months` |
| `next_review` | 13 days after the record's latest date |
| `supply_days` (new) | `28` |
| `last_refill` (new) | 20 days before the record's latest date |

## 3. API contract

### 3.1 `GET /patients/{patient_id}/companion` (new, read-only)

```json
{
  "safety_normal": true,
  "medication": {
    "name": "Sertraline", "schedule": "50 mg, once each morning",
    "known": true,
    "purpose": "…approved text…", "how_to_take": "…approved text…",
    "topics": [{"id": "purpose", "label": "What is it for?"}, {"id": "how_to_take", "label": "How do I take it?"},
               {"id": "missed_dose", "label": "What if I miss a dose?"}, {"id": "side_effects", "label": "Common side effects"},
               {"id": "alcohol", "label": "Alcohol"}],
    "content_status": "Development content — needs pharmacist review"
  },
  "dose_today": {"scheduled_time": "2026-03-11T08:00:00+00:00", "status": null},
  "adherence": {"window_days": 7, "taken_days": 6, "recorded_days": 7,
                "missed_reasons": [{"reason": "SIDE_EFFECTS", "label": "Side effects", "count": 1}]},
  "coming_up": [
    {"kind": "MEDICATION_REVIEW", "date": "2026-03-24", "label": "Medication review with your doctor"},
    {"kind": "REFILL", "date": "2026-03-19", "label": "Refill estimated"},
    {"kind": "APPOINTMENT", "date": "2026-03-24", "label": "Next appointment"}
  ],
  "suggestions": {
    "because": "You've been moving less than your usual since early March.",
    "options": [{"id": "short_walk", "label": "A short walk outside"},
                {"id": "message_someone", "label": "Message someone you trust"},
                {"id": "plan_session", "label": "Plan a session with your therapist or counsellor"}]
  }
}
```

- `medication` is `null` when no treatment context exists; `known: false` when the name is not in
  the approved file (UI then shows the exact abstention line).
- `dose_today.status` is the latest medication event for the record's latest day:
  `ACKNOWLEDGED` | `MISSED` | `UNKNOWN` | `null` (not recorded yet).
- `suggestions` is `null` when `safety_normal` is false or there is no recent descriptive change.
- Dates are ISO; the UI formats them in everyday words.

### 3.2 `POST /patients/{patient_id}/events` with `MEDICATION_EVENT` (extended)

Payload: `{"scheduled_time": iso, "status": "ACKNOWLEDGED"|"MISSED"|"UNKNOWN", "reason"?: R}`
where `reason` is allowed **only** with `MISSED` and R ∈ `FORGOT`, `SIDE_EFFECTS`, `RAN_OUT`,
`FELT_BETTER`, `OTHER`. All safety gates (demo fixture gate, hosted allowlist, layered detector)
accept this exact categorical shape without free text. Missed-dose reasons appear in the
appointment review as items to discuss ("Missed doses in the last 7 days: 2 — reason: side
effects. Worth discussing with your doctor or pharmacist.").

### 3.3 `POST /patients/{patient_id}/medication/ask` (new)

Request: `{"run_id": uuid, "topic_id"?: str, "question"?: str}` (exactly one of the two).
Response: `{"status": "ANSWERED"|"ABSTAINED"|"BLOCKED", "topic_id": str|null, "answer": str,
"source_label": "Approved medication information (development content)", "trace": [...]}`.
- `topic_id` → curated answer directly (no model).
- `question` → patient text goes through the safety gate first (as a patient free-text event);
  if blocked, `BLOCKED` and no answer. Otherwise the model only classifies the question into one
  approved topic id or `none`; `none` → `ABSTAINED` with the exact line. The answer text is always
  the curated text.

## 4. Ownership (who builds what)

| Area | Owner | Files (new or changed) |
|---|---|---|
| Fixture prescription (§2), schema columns `supply_days`, `last_refill`; medication `reason` column and validation; all three safety gates accept §3.2; missed reasons into review snapshot; dose/adherence/coming-up computation; `GET /companion` endpoint and wiring | **Codex** | `aura_app/service.py`, `persistence.py`, `models.py`, `demo.py`, `hosted.py`, `simulator.py`, `aura_detectors/layered.py`, new `aura_app/companion.py`, tests |
| Approved medication content (Sertraline, Escitalopram, Fluoxetine; five topics each) and lookup; `POST /medication/ask` with safety-first routing and topic classifier; curated suggestions and their selection rule (pure function the companion endpoint calls); safety tests | **Claude** | new `aura_agent/medication_info.json`, `aura_agent/medication.py`, `aura_app/medication_ask.py`, `aura_agent/suggestions.json`, `aura_agent/suggestions.py`, `aura_app/api.py` (one route), tests |
| Patient home UI: "Today's dose" (Taken / Not yet / Skipped → reason chips), "My medication" (card + topic chips + ask box + answers + abstention), "Coming up", "A small idea for today"; appointment page shows missed-dose items; works at 390 and 1280 px; plain-language lint passes | **CodeBuddy** | `aura_ui/` only, plus browser tests |
| Story, script, deck, video, integration merges and deploys when the user directs | **Claude** | `docs/presentation/`, `docs/submission/` |

Interfaces between owners:
- Codex's `companion.py` calls `aura_agent.medication.lookup(name, schedule) -> dict | None` and
  `aura_agent.suggestions.select(evidence, safety_normal) -> dict | None`. Both are done on
  `origin/improve/feature-claude` (commit `0d7889a`); fetch and merge or cherry-pick that commit.
- CodeBuddy builds against §3 with mocked responses until the endpoints land; use the field names
  exactly as written.

## 5. Schedule

No fixed deadlines (user, 2026-10-13): each agent works through its tasks and reports **done** in
`HANDOVER.md` (branch, commit, what was verified). As soon as all three have reported done,
integration starts: merge order Codex → Claude → CodeBuddy into `main`, full tests, deploy on the
user's go-ahead, then a short freeze for QA, script, screenshots, deck and recording. The form
deadline (16 Oct) is the only fixed date.

Cut list if behind (in order): medication free-text ask (keep topic chips) → suggestions →
coming-up refill line.

## 6. Done means

- Full Python suite and all browser suites pass on the merged `main`.
- New tests cover: reason only with MISSED; gates accept the exact shape and reject extras;
  abstention text exact; medication answers never come from the model; suggestions hidden when
  safety is not normal; patient question goes to the safety gate first; plain-language lint on the
  new cards.
- Live demo shows all four cards for the demo patient on phone and desktop.
