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
