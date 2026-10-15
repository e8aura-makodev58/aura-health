# Gaps, catch-up and calendar — design for review (Claude → Codex)

Status: **PROPOSAL for Codex review, 2026-10-15.** Requested by the user ("build all … deliberate
with Codex … get it right once"). Nothing here is implemented yet. Codex: please answer the
**Questions for Codex** (inline, or in a reply section at the end) and flag anything unsafe or
inconsistent with the backend before Claude builds. User decisions are marked **(user)**.

## 0 · Principles carried over

- Missing is unknown: never "normal", "zero" or "missed". Only an explicit report is a record.
- Patient words are safety-assessed first; the safety state always wins.
- AI may *propose*; deterministic code validates; **the patient confirms** before anything is saved.
- Self-reported past entries are labelled as such everywhere (patient, clinician, agent facts).
- Sharing (`aura_app/sharing.py`) applies to every new clinician-facing surface.
- No nagging, no reminders, no judgement; absence is never a risk signal by itself.

## 1 · Medication catch-up (the user's main interest)

### 1.1 Gentle prompt **(user idea; wording proposed)**
When the newest medication record (any status) is ≥ `catchup_after_days` (proposal: 3) before the
record's latest day, in the normal safety state only, the dose card shows one quiet line:

> Your last medication record was 12 days ago. If you'd like, you can fill in the days since —
> just tell AURA in your own words. **Update my record**

No colour, no warning icon, dismissible for the day. Never shown during a safety episode, never
says "remember to take", never sent as a push.

### 1.2 Catch-up in plain words, then confirm **(user idea)**
1. Patient types, e.g. *"I took it most days except last Friday and yesterday."*
2. The text is **patient free text → safety-assessed first** (same path as notes). Blocked → no
   proposal; the safety panel takes over.
3. A new agent task `medication_backfill` (low reasoning) receives: the note, the record's local
   "today", the patient timezone, the gap window (first and last unrecorded day, max 14 days) and a
   calendar of those days with weekday names. It returns only
   `{"days": [{"date": ISO, "status": "ACKNOWLEDGED"|"MISSED"|"UNKNOWN"}], "unclear": bool}`.
4. Deterministic checks: dates inside the window only, no future dates, each date once, statuses
   from the enum, no reasons invented (a reason is added only if the patient picks one in the
   preview). Anything outside → dropped; malformed → "AURA couldn't work that out; you can tap the
   days instead."
5. **Preview:** a mini calendar of the window with each day pre-filled from the proposal; every day
   is a tap target (taken / missed / not sure). Nothing is saved until **Save these days**.
6. Saved days become ordinary `MEDICATION_EVENT`s with `scheduled_time` = that day at the schedule
   time, `occurred_at` = that day, `received_at` = now, and a new payload flag
   `"reported_later": true` (schema change → validator, hosted rule and tests).
7. If the text indicates stopping, changing or doubling medication ("I stopped taking it"), nothing
   is proposed for those days; AURA shows the existing fixed advice-request line (talk to your
   doctor or pharmacist) and the days stay unknown. The model never gives medication advice.

### 1.3 Tap-only alternative
The same preview is reachable without typing (calendar → a past day → set status), so the AI is a
shortcut, not a requirement.

### Questions for Codex — medication
- **Q1.** Is a new payload field (`reported_later`) better than a separate `source`
  (`synthetic_patient_backfill`) for distinguishing late reports? Which keeps the safety/longitudinal
  engines unchanged?
- **Q2.** Event ordering: events with `occurred_at` in the past but received now — does
  `PatientEventService.process` and the safety engine handle them without re-evaluating history
  unsafely? Should backfilled events bypass `MEDICATION_EVENT_RECEIVED` safety processing, or is
  passing them through harmless?
- **Q3.** Review items: a backfilled MISSED day with a reason currently creates a review item. Keep
  that (likely yes, labelled "reported later")?
- **Q4.** Hosted rule (`aura_app/hosted.py`) only permits a medication event for the record's latest
  day. Proposed: also permit `reported_later: true` events for days inside the last 14 record days
  that have no existing record. Agree, and should it refuse overwriting an existing record?
- **Q5.** Idempotency: one save = a batch of events. Use `process_batch` with per-day idempotency keys
  (`backfill:<date>`) so a re-save cannot duplicate?
- **Q6.** Should "not sure" be saved as `UNKNOWN` (an explicit "patient doesn't remember") or simply
  left unrecorded? Proposal: save `UNKNOWN` only when the patient chooses it.

## 2 · Engagement facts for the clinician (neutral, minimum-shared)
A one-line strip on the clinician view and an agent fact (`get_status`):
*"Last check-in 18 days ago · last medication record 12 days ago (3 reported later) · wearable data
up to 2 days ago."* Deterministic, record-local dates, no colour coding, no risk wording.
- **Q7.** Classify as minimum (coverage metadata) rather than optional? Proposal: minimum.

## 3 · Welcome back (patient)
If the patient's last own input (check-in, dose, note, idea, catch-up) is ≥ 7 record days before the
current session's first input, the home shows once per session, fixed wording:
> Welcome back. Your watch kept recording while you were away, so there's nothing to catch up on
> unless you'd like to.
Plus the medication line from §1.1 if it applies. No AI needed.

## 4 · Re-learning your usual (patient)
When a signal's trust is `REESTABLISHING` or sensing is `UNOBSERVED`, the patient recap adds:
> Your watch data paused for a while, so AURA is relearning your usual for {sleep}. It won't point
> out changes for {that signal} until it has enough days again.
Signal names in plain words; no numbers.
- **Q8.** Is `trust_state`/`sensing_state` already in the evidence projection for every key so the UI
  can read it without engine changes? (Appears so: `current.sensing_state`, `trust_state`.)

## 5 · Calendar (new; patient and clinician) **(user idea)**
### 5.1 View
Month grid (record-local dates; today = record's latest day). Each day cell shows small markers:
- Check-in: dot coloured Good / Okay / Rough (existing palette); none if no check-in.
- Medication: ✓ taken, ✕ missed, ? not sure, hollow marker if **reported later**; blank = no record.
- Wearable coverage: thin bar (full / partial / none) from observation coverage.
- Note or activity mentioned: small pen icon (patient side; clinician only if notes/activity details
  are shared).
- Change markers: a line under days inside an engine finding period (from evidence findings).
A legend explains every marker; blank never means "fine".

### 5.2 Day detail (click a day)
Check-in; medication (with "reported later on {date}"); readings for that day (clinician only if
readings are shared; patient always); notes and activities (patient; clinician if shared); ideas
chosen; active findings covering that day; data gaps. Patient side: "Update this day's medication"
opens the §1.2 preview for that day.

### 5.3 Backend
`GET /patients/{id}/calendar?month=YYYY-MM&viewer=patient|clinician` → per-day aggregates;
`GET /patients/{id}/calendar/{date}?viewer=…` → day detail. Pure read projections over committed
evidence/events/timeline, sharing-filtered for `viewer=clinician`. No AI.
- **Q9.** Build the projection from `EvidenceViewService` + timeline (like CompanionService), or add
  a dedicated read in `service.py`? Concern: one consistent transaction per request.
- **Q10.** Where should "day" boundaries come from for observations (sleep spans midnight)? Proposal:
  use the observation's own `day` field as the engine does.
- **Q11.** Clinician agent: add a `get_day(date)` read tool, or is the calendar UI-only for now?
  Proposal: UI-only now (keeps prompt v12 and tool budgets unchanged).

## 6 · Tests to add
Backfill: window/future/duplicate rejection, unclear text, advice-request text, safety-blocked text,
preview-before-save (nothing persisted until confirm), idempotent re-save, `reported_later` labels in
companion/visit note/clinician/agent facts, hosted rule. Calendar: markers per day incl. unknown vs
missed vs reported later, sharing filter, timezone/day boundaries, day detail. Engagement strip and
welcome-back triggers. Browser: calendar navigation and day detail on phone and laptop.

## 7 · Proposed split
Codex: §1 backend (payload flag, hosted rule, batch save, safety/longitudinal handling) and §5.3
projections. Claude: agent task + checks, UI (dose card line, catch-up dialog + preview, calendar,
welcome back, re-learning line, engagement strip), integration tests, deploy. Order: Codex answers
Q1–Q11 → Codex backend → Claude UI/agent → joint review → deploy.

---

## 8 · Reconciled after Codex and Gemini reviews (2026-10-15, Claude) — pending user approval

Reviews: `BACKLOG_AND_CALENDAR_REVIEW_CODEX.md`, `BACKLOG_AND_CALENDAR_REVIEW_GEMINI.md`.

**Agreed by all three (supersedes §1.2 step 6 and related text):**
1. **No backdated `occurred_at`.** A catch-up is a report made *now*: `occurred_at`/`received_at` =
   report time, the described day lives in `scheduled_time`, plus server-derived late-report metadata
   (Gemini found that "latest record day" is read from the last inserted event, so a backdated event
   would move the demo's "today" backwards). Every reader groups medication by `scheduled_time`'s
   local date.
2. **Normal safety path, never bypassed;** typed catch-up text is patient text, safety-assessed, and
   must not also trigger note reply, ideas or activity extraction.
3. **Server-validated retrospective window** (last 14 record days, within treatment, no future days),
   **fill empty days only** (existing records shown and locked), conflict check inside the save
   transaction, recheck safety/sharing at save, no silent truncation (out-of-window dates are
   disclosed in the preview).
4. **Idempotency:** batch keyed to patient + scheduled day + request, bound to a payload
   fingerprint; exact retry returns the stored result; a changed payload under the same key is
   rejected as a conflict.
5. **UNKNOWN only when the patient picks "Not sure";** untouched days stay unrecorded; empty save
   creates nothing.
6. **Review items** for explicit missed reasons, labelled with the described day and the report day.
7. **Calendar:** one read projector in one transaction; observation `day`, medication scheduled
   day, patient-local dates for check-ins/notes; **sharing filters markers too** (check-in dots
   hidden if daily check-ins are withheld; note/activity icons only if shared; wearable coverage
   bars count as detailed readings); UI-only, no new agent tool; Q&A facts gain late-report labels.
8. **Phone cells show medication and check-in only;** coverage, notes and findings go in day detail;
   no continuous "finding bands" (detection dates don't prove every day in between).
9. **Honest copy:** UI says "Update past medication records" (not "catch up"); welcome text only
   claims recorded data that exists; re-learning text describes the actual per-signal state and
   never promises automatic recovery (e.g. "AURA doesn't currently have a usable reference for
   your sleep").
10. **Prompt trigger counts unresolved days** in the window (not just "days since the newest record").

**Choices for the user:**
- **A · "Most days except Friday and yesterday."** Codex: "most days" does not prove every other
  day was taken. Proposal: the preview pre-fills the other days as *Taken (from "most days")* in a
  distinct style and asks one question — "Were Friday and yesterday the only days you missed?" —
  **Yes** confirms them, **No** leaves them unresolved for tapping. Nothing is saved before that.
- **B · "I stopped taking it" with dates.** Proposal for version one: safety first, the existing
  fixed "talk to your doctor or pharmacist" line, and the days go to tap-only confirmation (no AI
  date inference for stop statements).
- **C · Clinician "Record coverage" strip** (last scheduled day with a medication report, how many
  reported later in the window, last check-in, latest wearable day): part of the shared **minimum**?
  Proposal: yes (it is coverage metadata, not content).
- **D · Thresholds:** prompt after **3** unresolved days; edit window **14** days (engineering
  settings, configurable).
- **E · Work split:** Codex — data contract, validator, hosted rule, batch idempotency/conflicts,
  calendar projector (+ backend tests). Claude — `medication_backfill` agent task and checks, all UI
  (dose-card line, update dialog + preview, calendar + day detail, welcome back, re-learning line,
  coverage strip), integration, deploy. Gemini — browser test suite for the new flows (phone +
  laptop) and an independent review before merge.

---

## 9 · APPROVED (user, 2026-10-15) — contract and assignments

The user approved §8 A–E as proposed and named **Claude the final gate**: Claude reviews, fixes,
merges and deploys everything below. Build against this contract; if something in it is wrong,
write the problem in your handover entry rather than silently changing the contract.

### 9.1 Record-local time (everyone)
"Now" for a record is its **latest event `occurred_at`** (demo records live in early 2026), never
the wall clock. Catch-up saves use `occurred_at` = record-local now, `received_at` = server clock,
and carry the described day in `scheduled_time` (schedule hour, patient timezone).

### 9.2 Backend — **Codex** (branch `improve/feature-codex`)
1. **Payload:** `valid_medication_payload` accepts `"reported_later": true` (only `true`, only set by
   the server on the update path; client-supplied values are rejected elsewhere). Normalised medication
   rows, review items and agent facts carry it (fact text e.g. "Medication-routine record 2026-03-02:
   ACKNOWLEDGED (reported later on 2026-03-11).").
2. **Readers group medication by `scheduled_time` local date** (companion counts, review period,
   visit note, tools). Fix any `rows[-1]["occurred_at"]` "latest day" reads that a catch-up could break.
3. `GET /patients/{id}/medication/update-window` →
   `{"today": ISO, "timezone": str, "schedule_hour": int, "max_days": 14, "unresolved_count": int,
   "days": [{"date": ISO, "weekday": "Mon", "status": "ACKNOWLEDGED"|"MISSED"|"UNKNOWN"|null,
   "reported_later": bool, "locked": bool}]}` (last 14 record days within treatment, oldest first;
   `locked` = already has a record).
4. `POST /patients/{id}/medication/update` with
   `{"request_id": uuid, "days": [{"date": ISO, "status": enum, "reason": optional MISSED_REASONS key}]}`
   → validates inside one transaction (window, empty days only, treatment, safety normal, not held),
   writes one `MEDICATION_EVENT` per day via `process_batch` with idempotency bound to
   patient + day + request + payload fingerprint (exact retry → same result; changed payload →
   `409 UPDATE_CONFLICT`), returns `{"saved": [...dates], "window": <same as 3>}`. Empty `days` → 400.
   Hosted rule allows exactly this path.
5. **Companion:** add `"medication_gap": {"unresolved_days": int, "window_days": 14,
   "last_record_day": ISO|null}` (normal safety state only, else null).
6. **Record coverage:** `GET /patients/{id}/coverage` →
   `{"last_medication_day": ISO|null, "reported_later_in_window": int, "window_days": 14,
   "last_checkin_day": ISO|null, "last_wearable_day": ISO|null}` (minimum-shared) and the same as one
   `get_status` agent fact.
7. **Calendar projector** (one repository transaction, sharing-filtered for `viewer=clinician`):
   `GET /patients/{id}/calendar?month=YYYY-MM&viewer=patient|clinician` →
   `{"month": "YYYY-MM", "today": ISO, "withheld": [..], "days": [{"date": ISO,
   "checkin": "Good"|"Okay"|"Rough"|null, "medication": {"status": enum, "reported_later": bool}|null,
   "coverage": "full"|"partial"|"none"|null, "note": bool|null, "activity": bool|null}]}`
   (null = not available to this viewer or no data; `coverage` null when readings are withheld;
   `checkin` null when daily check-ins are withheld; note/activity null when withheld).
   `GET /patients/{id}/calendar/{date}?viewer=…` → `{"date", "checkin", "medication": {status, reason,
   reported_later, reported_on}|null, "readings": [{"signal","label","value","unit"}]|null,
   "notes": [str]|null, "activities": [{"phrase","labels","minutes"}]|null, "ideas_chosen": [label],
   "findings": [{"signal","direction","since"}], "gaps": [label], "withheld": [..]}`.
   Coverage per signal: "full" if every enabled signal has a covered observation that day, "partial" if
   some, "none" if none (documented engineering rule).
8. Backend unit tests for all of the above (window edges, locked days, conflict/idempotency, record-local
   time, grouping by scheduled day, sharing filters on grid and detail).

### 9.3 Agent task, UI, integration — **Claude** (branch `improve/feature-claude`)
1. `POST /patients/{id}/medication/update/interpret` `{"request_id": uuid, "text": str}`: safety-assesses
   the text as patient free text with source `patient_medication_update` (no note reply, ideas or
   activity tagging for this source), then the `medication_backfill` agent task (low reasoning) →
   checked proposal `{"days": [{"date","status","basis": "explicit"|"from_most_days"}],
   "question": str|null, "out_of_window": [dates], "advice_request": bool}`; BLOCKED when safety stops it.
2. UI (IDs below), welcome back, re-learning line, coverage strip, calendar + day detail (patient and
   clinician), integration tests, final review of all branches, merge and deploy.

### 9.4 Browser tests and review — **Gemini** (branch `improve/feature-gemini`)
`tests/browser/catchup_calendar.cjs` (hosted, phone 390 and laptop 1280) using only these IDs, plus an
independent review of Codex's and Claude's branches before Claude merges. Cover: prompt appears with
unresolved days; typed update → preview with "from most days" styling and the one question; locked
days not editable; save → calendar shows ✓/✕ with reported-later marker; clinician calendar with
Everything vs Minimum only (check-in dots and coverage disappear, medication stays); day detail;
welcome back; no horizontal scroll.

### 9.5 UI element IDs (contract for Gemini's tests)
- Dose card line `#med-update-line`, open button `#med-update-open`.
- Dialog `#med-update-dialog`: text `#med-update-text`, interpret `#med-update-interpret`, tap-only link
  `#med-update-tap`, preview `#med-update-preview` with `.med-day[data-date][data-status][data-basis][data-locked]`
  (status cycles on click), question `#med-update-question` with `#med-update-yes` / `#med-update-no`,
  save `#med-update-save`, result `#med-update-result`.
- Calendar entry links `#calendar-link` (patient nav) and `#clinician-calendar-link`; view `#calendar-view`;
  `#calendar-prev`, `#calendar-next`, `#calendar-month`; grid `#calendar-grid .cal-day[data-date]`
  containing `.cal-med[data-status][data-reported-later]` and `.cal-checkin[data-state]`; detail
  `#calendar-detail`; legend `#calendar-legend`.
- `#welcome-back`, `.relearning-line`, clinician `#record-coverage`.

### 9.6 Order
Codex 9.2 and Claude 9.3 in parallel (Claude mocks 9.2 responses until Codex lands) → Gemini 9.4 →
Claude final review, fixes, full test runs, merge, deploy, live check.
