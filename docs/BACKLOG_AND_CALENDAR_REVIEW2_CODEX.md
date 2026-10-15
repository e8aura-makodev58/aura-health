# Catch-up/calendar backend review — Codex, 2026-10-15

Reviewed immutable `origin/main` **ab1dd093b124582533799de61b3aa64636a9b9cf** (feature code `1dbcd0c`, interpret code `02481e8`) against approved spec §9. This is the backend review requested in Claude's latest handover, not a second implementation. Claude remains the final gate and fix owner; Gemini owns the UI/browser review.

**Result: changes requested.** The ordinary flow works and the existing focused tests pass, but two high-priority defects remain: overlapping saves defeat empty-day/conflict rules, and appointment/review consumers still misdate retrospective entries. Smaller findings concern held-save feedback, timezone provenance and coverage semantics. No production source, main branch, deployment, settings or model calls changed during this review.

## Findings

### R1 · P1 — Validate the window, slot and retry payload inside the batch transaction

**Location:** `aura_app/record_calendar.py:108–142`; `aura_app/service.py:137–150,161–164`; `aura_app/persistence.py:53–57,413–426`.

The transaction ends immediately after reading the window and checking safety. Slot/payload checks use that stale snapshot, and `process_batch` opens a different transaction. SQLite serializes each write transaction, but does not protect the gap between these transactions. There is no scheduled-slot uniqueness constraint.

**Reproduced with deterministic interleaving:** A reads March 10 as empty and prepares Taken; before A enters `process_batch`, B saves Missed for March 10. A then succeeds too: **two normalized medication rows**, statuses `MISSED`, `ACKNOWLEDGED`, for the same described day. Using the **same request ID** makes it worse: B's Missed wins the key, A's Taken is silently replayed by the generic event service, yet A receives `saved: ["2026-03-10"]`. The event-ID fingerprint does not help because generic replay looks up the idempotency key first, without comparing the body.

**Fix:** keep the current safety/window/treatment/slot checks, payload comparison and batch ingestion under one repository transaction; use the existing shared-transaction pattern rather than opening a second connection while holding SQLite's write lock. Protect the slot independently of request identity. Return `409 UPDATE_CONFLICT` for a changed same-key payload, including overlapping requests. A second test should advance the record or activate safety between the original read and write; those checks must also happen against the write transaction's state. Domain safety processing must remain intact.

### R2 · P1 — Retrospective dates and labels disappear from appointment/review consumers

**Location:** `aura_app/service.py:511–520,591–592`; consumers `aura_ui/app.js:305` and `aura_ui/evidence.js:209–222`; normalized medication construction `service.py:264–268`.

Calendar detail and new evidence rows carry the described day, but `review_snapshot().medication_routine_events` still returns only report-time `at`, status and optional reason. Review-item summaries also omit both the described day and late-report label. The appointment UI renders `event.at`, and the clinician medication strip still renders `row.at` rather than the new `day`.

**Reproduced:** save **March 9 Missed / Forgot**, reported March 11. Review snapshot returns `{"at":"2026-03-11T23:00:00+00:00","status":"MISSED","reason":"FORGOT"}`. Its review item says only “Missed dose reported — reason: forgot…” with March 11 `created_at`. A multi-day update therefore appears as several doses all on the report day in existing appointment/clinician surfaces, without “reported later”. The normalized row itself also has no explicit `reported_later` field; current calendar reconstruction joins raw events to recover it.

**Fix:** carry described local day, report day and explicit late provenance through review projections and review-item wording, then update existing appointment/clinician consumers to use them. Keep actual timestamps for audit; do not backdate `occurred_at`. Ensure companion aggregates containing retrospective records expose their provenance as required by the principles/spec, rather than assuming the new calendar label covers all readers. Add a multi-day late-report regression spanning the calendar, visit note, clinician strip and linked review item.

### R3 · P2 — A held batch is returned as successfully saved days

**Location:** `aura_app/record_calendar.py:140–142`.

`save` discards every `ApplicationResult` from `process_batch` and unconditionally returns all requested dates in `saved`. A safety gate can become unavailable during ingestion after the initial normal-state check. The domain service correctly holds the input, but the update endpoint claims the medication record was saved normally.

**Reproduced with a fake gate:** seed a normal patient; make the gate unavailable only for the update. The service returns `saved: ["2026-03-10"]`, while the corresponding event is `longitudinal_deferred=true` and the returned window still has **14 unresolved days**. This is contradictory feedback and leaves retries particularly difficult because the held event already owns its idempotency key.

**Fix:** inspect batch results/current safety and return an explicit blocked/held result rather than a normal saved list. Preserve the committed safety state and required audit/held evidence; do not roll back or bypass safety merely to manufacture a clean save. The UI must show the authoritative safety state and avoid a success claim. Test a gate failure during a multi-day batch and the subsequent same-key retry/recovery behavior.

### R4 · P2 — Agent “reported later on” uses UTC date rather than patient-local date

**Location:** `aura_agent/tools.py:147–151`; evidence producer `aura_app/evidence.py:134–139`.

The described day is correctly localized, but the report label uses `row['at'][:10]`.

**Reproduced:** timezone `Asia/Singapore`, record-local report moment `2026-03-11T23:00:00+00:00`. Calendar detail correctly says `reported_on: "2026-03-12"`; the agent fact says “reported later on **2026-03-11**” for the same record.

**Fix:** project an explicit patient-local `reported_on` once and consume it in agent facts and other displays. Add a midnight-boundary test with UTC storage and a non-UTC patient timezone.

### R5 · P2 — “Full” coverage excludes enabled signals with no observations

**Location:** `aura_app/record_calendar.py:211–221`, used at `calendar():235–247`.

The agreed rule is “every enabled signal has a covered observation that day”. The denominator first drops signals without observations. With enabled A covered and enabled B never observed, the function returns total **1**, covered **1**, producing **full**. Missing B has disappeared from the denominator. Evidence also only instantiates signals represented in committed rows, so removing this one filter alone does not establish the agreed enabled-signal set.

**Fix:** derive the expected signal set from the agreed registry/patient configuration and use it consistently, including never-observed enabled signals. If the intended product rule is actually “all previously observed streams”, explicitly resolve/document that contract change with the final gate. Do not silently describe it as all enabled signals. Sparse display-only channels need not become daily requirements. This is a display projection issue, not a request to alter engine coverage thresholds.

## Smaller contract follow-ups

- **Last medication day outside the edit window:** `medication_gap()` returns the latest locked day *inside* its 14-day window, unlike `/coverage`, which returns the actual latest described day. Reproduced a sole February 10 report with March 11 today: gap `last_record_day=null`, coverage `last_medication_day="2026-02-10"`. Use the actual latest day, or name/document the field as window-specific.
- **Request ID binds individual day payloads, not the complete save:** reusing a request ID with a different previously unrecorded day is accepted as another save. If §8's “changed payload under the same key” means the whole POST body, persist a canonical request fingerprint/result. If per-day identity is intentional, state it explicitly. This ambiguity is separate from R1's confirmed same-day conflict failure.
- **Exact replay is window/safety dependent:** replay lookup follows current window and safety validation, so a previously saved request can cease to replay after the window advances or safety activates. Decide whether the response promises permanent operation replay or only retry within the current editable window; avoid replaying ordinary UI success across an active safety boundary.
- **Finding intervals:** day detail fills every date between `first_seen` and `last_seen` with a finding. Those dates establish detections, not continuous daily evidence. Ensure wording does not imply the engine evaluated that finding on every intervening day (§8.8).
- **Configuration:** 14-day/3-day settings are module constants. This implements the selected defaults, but not the configurable settings described in §8.D. Lower priority than R1/R2 for this demo.

## Verified and limits

- Reviewed event validation, normal safety ingestion, hosted routing, normalized storage, companion/date aggregation, evidence/agent facts, calendar grid/detail and sharing filtering against the immutable commit above. Inspected UI consumers only where needed to establish the impact of backend projection omissions; Gemini still owns UI review.
- New calendar reads reuse one transaction for evidence and consent, and both marker/detail responses filter optional check-ins/readings/notes/activity details. The existing sharing tests exercise this successfully. No new clinician authorization claim: the demo viewer remains self-declared.
- Reproduction harness: [`evidence/calendar-backend-review-probes.py`](evidence/calendar-backend-review-probes.py). It uses only temporary synthetic patients and fake safety gates; deterministic hooks interleave requests at the actual `process_batch` boundary. Run against the **reviewed source**, with its project root on `PYTHONPATH`: `PYTHONPATH=. /path/to/venv/bin/python /path/to/calendar-backend-review-probes.py`. It prints observed outcomes, not a passing regression suite; UUIDs vary. No live-model calls.
- Existing focused suites: `test_record_calendar.py` **6 PASS/222.004s**, `test_medication_update.py` **8 PASS/0.540s**, `test_sharing.py` **6 PASS/9.607s** (20 total). Calendar required an unrestricted rerun after the restricted runner stalled (stopped with143); existing Starlette/httpx warning remains. These tests do not cover the reproduced races, retrospective review rendering, midnight report dates or gate-failure save response. A green result does not close these findings. Full suite, browser and deployed-service checks were not repeated; Claude's full381/browser/live results remain Claude's evidence, not an independent release gate. Harness compile and documentation whitespace checks passed.

**For Claude:** fix R1/R2 first, then the smaller confirmed findings; add the targeted regressions and rerun the new feature suites. Compare with Gemini's independent review before final integration. This review does not change the approved feature scope or authorize Codex to merge/deploy.
