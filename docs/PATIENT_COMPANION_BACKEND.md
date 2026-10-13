# Patient companion backend — Codex delivery

2026-10-13. Implements the Codex rows in Claude's approved
`docs/PATIENT_COMPANION_SPEC.md` §4 (introduced on `origin/main` at `8cbb478`).
Worktree `/home/makodev58/aura-health-codex`, branch `improve/feature-codex`.
Integration/production deployment remains user-directed.

## API and data

`GET /patients/{patient_id}/companion` is a read-only projection with the agreed
`safety_normal`, `medication`, `dose_today`, `adherence`, `coming_up`, and
`suggestions` fields. The route only calls `CompanionService`; it contains no
domain policy or calculation. Repository interfaces remain the storage boundary.

`MEDICATION_EVENT` accepts only:

```json
{
  "scheduled_time": "2026-03-11T08:00:00+00:00",
  "status": "MISSED",
  "reason": "SIDE_EFFECTS"
}
```

`reason` is optional and allowed only with `MISSED`: `FORGOT`, `SIDE_EFFECTS`,
`RAN_OUT`, `FELT_BETTER`, `OTHER`. Null/free-text/extra fields and unzoned dates
are rejected before persistence or detection. Existing reason-less categorical
events still work. The demo fixture gate, hosted allowlist and layered adapter
share this shape validator; valid categories do not require an LLM call.
All events continue through the accepted safety controller; a categorical report
does not clear an existing safety interaction.

Migration is additive and repeatable: `treatment_context.supply_days INTEGER`,
`treatment_context.last_refill TEXT`, `medication_events.reason TEXT`. Existing
rows remain intact and new columns initially null. Named-column inserts work
with both upgraded and newly initialized databases. Medication rows are read
through the new `ObservationRepository.medication_events` method.

Reasons are retained in normalized records, typed timeline entries and
`review_snapshot.medication_routine_events`. Each assessed reason report can
create one patient-visible, Not-shared review item linked to its source event.
Idempotent retries do not repeat processing or review-item creation. Held reports
are excluded until safety recovery; released reports then receive review items.
The existing event transaction includes all new records and rolls them back
on unexpected processing failure.

## Daily projection and engineering defaults

- Seven-calendar-day window, ending on the latest recorded day in the patient's
  timezone. The synthetic timeline may be months behind the real server clock.
- Latest report per scheduled local day, comparing absolute report timestamps;
  ties use repository commit order. Multiple taps do not become extra taken days.
- `UNKNOWN` remains unknown; absent days are not recorded. `taken_days` counts
  patient acknowledgements, not independently verified ingestion. No score/streak.
- This projection supports the explicitly once-daily, single-medication fixture.
  Multi-medication/multi-dose routine modelling is not supplied by these counts.
- The synthetic morning label is displayed at08:00 when no report supplies a
  schedule. `CompanionConfig.synthetic_morning_hour` is an engineering display
  parameter, not a dosing instruction. Arbitrary prescription prose is not parsed
  into a time. `window_days` is likewise an inspectable engineering parameter.
- Refill estimate = recorded last-refill date + recorded supply days. Review
  date comes from `next_review`. Entries are sorted by date/kind. There is no
  push notification, automatic prescription change or inferred medication plan.

**Contract interpretation for review:** the example has `APPOINTMENT` as well as
`MEDICATION_REVIEW`, but no booked-appointment field exists. This implementation
emits the stored review date as `MEDICATION_REVIEW`, without inventing a booking.

## Fixtures and independent-branch integration

All new synthetic catalog profiles receive Sertraline / "50 mg, once each morning",
regimen start9 calendar months before record start, stable since6 months before,
review cadence every3 months, next review13 days after the fixture's latest day,
supply28 days, last refill20 days before that day. These are fixture facts.
Dates use calendar-month arithmetic, including month-end clamping.

Existing verified demo databases receive schema additions and replacement of
only the exact legacy medication placeholder. Ordinary observations, anchors,
timelines and custom treatment contexts are preserved. Review/refill dates do
not drift forward automatically on every new observation.

Claude owns `aura_agent.medication.lookup(name, schedule)` and
`aura_agent.suggestions.select(evidence, safety_normal)`. The companion service
uses those interfaces without copying content or selection rules. Before those
modules are merged into this branch, missing content produces the exact unknown-
medication abstention and no suggestions; no clinical text is invented as a stub.
Once integrated, the same service uses the real modules automatically. Injectable
callbacks support isolated contract tests.

A cross-worktree smoke check read Claude's actual lookup and selector modules
without merging or changing them: synthetic CaseB returned the known prescription,
curated standard footer and activity-linked options. No model calls were used.

Safety permission is checked via the existing `aura_agent.guard.blocked_reason`.
Non-normal, invalid, degraded or held state yields `safety_normal=false`,
`medication=null`, `suggestions=null`, and invokes neither content callback.
The evidence projection and permission check share one repository transaction;
GET does not replay domains, mutate anchors, change safety or append audit events.
Pinned safety rendering remains independent.

## Verification and integration checklist

`tests/test_companion.py` covers PC1–PC17: exact validation; three adapters;
idempotency/review linkage; daily counts and missingness; stored reminder dates;
safety/held suppression and recovery; read-only API/reload; rollback; timezone
and tie handling; exact abstention; absent treatment; additive legacy migration;
all synthetic prescriptions and preservation on fixture upgrades.

Results on2026-10-13: full320 Python tests PASS/426.774s; final companion17
PASS/36.695s after timestamp-tie handling and expanded fixture-date assertions.
Five hosted browser suites31 assertions PASS. Cross-worktree lookup/select smoke
PASS. Existing Starlette/httpx deprecation warning remains.

Run:

```sh
.venv/bin/python -m unittest tests.test_companion -q
.venv/bin/python -m unittest discover -s tests -q
NODE_PATH=/home/makodev58/rendertest/node_modules \
LD_LIBRARY_PATH=/home/makodev58/rendertest/libs/usr/lib/x86_64-linux-gnu \
.venv/bin/python tests/browser/run.py --hosted --port 8036 \
  --suite milestone7.cjs workflows.cjs agent.cjs plain_language.cjs dual_view.cjs
```

Keep Claude's medication route/content and CodeBuddy's UI separate until the
designated merge. Both branches edit `aura_app/api.py`; preserve both service
imports/routes when resolving any conflict. Full merged-build browser validation
and new-card phone/desktop checks remain integration work, not claimed here.

The old `milestone6.cjs` suite assumes unrestricted local sign-up, so hosted mode
is inappropriate for it. An attempted hosted run also exposed stale raw-wording
assertions (`reference is unchanged`, `No automatic exit rule`, exact raw drift
description); the latter failure leaves a dialog open and causes later clicks to
time out. The corresponding UI code predates this backend patch. These are
recorded for the frontend/test owner, without modifying their files.
