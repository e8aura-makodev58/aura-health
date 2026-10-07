# Dual-view implementation — review notes

2026-10-07. User approved the revised scope with **Proceed**. Implemented for
synthetic demonstration; user experience acceptance and Claude review remain pending.

## Experience

- The demo opens **Clinician**, Case B. **Demo guide** selects existing A–F and
  before/after checkpoints. Checkpoints remain distinct seeded patient records.
- Clinician has a read-only workspace: up to three descriptive findings, four aligned
  charts, categorical check-ins/routine records, linked context, retained explanations,
  questions/review preparation and safety provenance. No population ranking or score.
- **Patient** keeps the same selected record. Home has one quiet moment or approved
  question, a persistent **I want to mention something**, appointment preparation,
  **See my full data**, and a collapsed optional check-in/routine action.
- Patient full data uses the **same projection and chart DOM**, without a clinician
  approval gate. Optional details are not a second set of calculations.
- Appointment preparation is factual, deterministic and clearly **temporary / not
  sent**. Selection remains memory-only, not saved approval or sharing.
- The exact synthetic sharing disclosure is visible in Clinician. Toggle changes
  presentation only: no write, authorization, consent, anchor or safety change.

## Evidence contract

`GET /patients/{id}/evidence` calls `EvidenceViewService`, through the existing
repository/patient boundary (including the hosted synthetic allowlist).

The response contains version, patient/treatment, period, committed snapshot count,
per-signal raw observations and stored baseline history, anchor command links,
findings with first/last dates and event IDs, explicit contexts/gap events, categorical
reports, held/review items, evaluated patient questions and safety state/references.
It includes unavailable/deferred snapshot markers and `NOT_SHARED` metadata.

`EventRepository.committed_results()` reads saved `app_events.result_json` in commit
order. The projection never runs a domain engine or model, changes a record, or
fills history from the latest mutable `baselines` row. No DB schema change.
Context dates/explanations and anchor commands come from validated event payloads;
the abbreviated normalized timeline does not contain those complete fields.
Free-text messages, detectors and hidden scenario truth are not exposed as chart data.

## Chart semantics

- Raw points are recorded values with source IDs, coverage and quality metadata.
- Rolling means are **stored** outputs. Last committed snapshot per record-date is
  a drawing convention; insufficient windows are not drawn as a rolling line.
- Dashed **your own reference** is historical anchor data, not a normal range.
  Versions/reference dates/reviewer are inspectable; no backward extension of today's
  anchor. Missing/deferred history is not reconstructed.
- Lines connect only adjacent recorded days; they never bridge a wearable absence.
  Missing days do not become zero, healthy or pathological. An old anchor may remain
  in textual reference details without claiming current sensing or trust.
- Sleep-clock coordinates preserve source-local minutes since sleep-start midnight.
  Exact values show day offsets; axis labels wrap the clock overnight. No timezone
  conversion or new circular baseline analysis is performed.
- Last 8 weeks / All is **display-only**, ending at the selected record date, not
  current wall time. Stored current rolling availability is not selected-period
  coverage, a clinical-quality measure or a health score.
- Context bands appear only on explicitly associated signals. They do not clear
  independent subjective evidence. Check-ins are categorical, never a numeric trend.

## Safety and writes

Existing event, explanation, communication, retry and protected settings paths are
reused. Clinician has no patient-input, dose, anchor, downgrade, dismiss or sharing
control. Enter Patient to exercise existing synthetic commands.
Hosted explanation controls offer only the exact prepared schedule fixture accepted
by the existing server allowlist. Other linked context stays visible as evidence;
the UI does not offer unsupported illness-explanation submissions or judge credibility.

Active safety output/resources remain separate and visible across both views and
navigation. Offline uses the unchanged local fail-closed fallback. Degraded policy
can exist without an episode; history collapsing does not hide policy/resources.
Routine T0/null history is omitted from this presentation, not deleted from storage.
No clinician/emergency service is notified. Live synthetic wording configuration is
unchanged; no paid provider call was made to verify this implementation.

## Verification

Backend: `tests/test_dual_view.py`, EV1–EV14. Covers read-only determinism/no generation,
exact historical values, gap/return, original anchor snapshots and explicit v2
reanchor history, scoped context plus independent evidence, retained explanation,
quiet-with-drift, safety reload/degraded-without-episode, fixture isolation, asset
restriction, raw record fidelity and hosted read allowlist.

Browser: `tests/browser/dual_view.cjs`, DV1–DV12. Covers clinician-first B, zero-write
same-record toggle, minimal home, display-only filtering, D held state, E gap/return,
F safety in both views, clinician offline containment, A–F shared charts and
320/390/1280 widths plus keyboard operation, production hold submission with unchanged
anchors, and truthful hosted context-action availability. Existing UI1–UI15, offline retry,
hosted isolation/reset, settings and eight layout checks remain regression gates;
selectors were updated for collapsed controls, not to remove behavioral requirements.

Commands (existing developer Chromium installation):

```sh
.venv/bin/python -m unittest discover -s tests -q
NODE_PATH=/home/makodev58/rendertest/node_modules LD_LIBRARY_PATH=/home/makodev58/rendertest/libs/usr/lib/x86_64-linux-gnu .venv/bin/python tests/browser/run.py --suite milestone6.cjs --port 8018 --artifacts /tmp/aura-dual-m6-regression
NODE_PATH=/home/makodev58/rendertest/node_modules LD_LIBRARY_PATH=/home/makodev58/rendertest/libs/usr/lib/x86_64-linux-gnu .venv/bin/python tests/browser/run.py --hosted --suite dual_view.cjs milestone7.cjs settings.cjs redesign.cjs --port 8019 --artifacts /tmp/aura-dual-hosted-browser
```

The runner owns fresh temporary synthetic databases and loopback servers. Screenshots
are verification artifacts, not CodeBuddy evidence or clinical validation.
Final run counts and deployment status are recorded in root `HANDOVER.md`.

## Review and limits

No accepted `aura_safety` or `aura_longitudinal` algorithm/configuration changes, no
new schema/dependencies, additional synthetic data, clinical thresholds or detectors.
Clinical parameter/content/resource review, context association/credibility governance,
REESTABLISHING exit, real identity/authorization and sharing remain unresolved.
Historical engine configuration is not separately pinned by existing baseline
snapshots; the UI does not claim configuration-version history it cannot prove.

This is engineering behavior, not proof of usability or clinical efficacy. User and
Claude should review purpose clarity, GP usefulness and ordinary-day patient burden.
The proposed external five-viewer comprehension check has **not** been performed.
Public HTTPS URL remains unverified. Additional data and CodeBuddy remain deferred.
