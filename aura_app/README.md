# Milestone 4 application layer

`PatientEventService` owns the event transaction. The FastAPI routes only parse transport data and call the service. Repository protocols in `repositories.py` separate application code from the SQLite development adapter. Accepted `aura_safety` and `aura_longitudinal` algorithms are imported unchanged.

## Transaction and restart model

Each new event uses SQLite `BEGIN IMMEDIATE`, serializing writers to one patient safety context and atomically committing the event envelope, typed normalized rows, safety state/reference/audit, longitudinal projection, review items, timeline, application audit, and stored response. An exception rolls the whole unit back. A repeated `(patient_id, idempotency_key)` returns the stored response without rerunning either domain. The global event ID is unique.

The longitudinal adapter reconstructs its working state from persisted ordered application events and explicit anchor commands for each transaction; no in-memory baseline cache is authoritative after restart. The final sensing/trust/rolling snapshots and held records are also persisted in typed tables for status and review reads. This is intentionally a development-scale replay strategy, not an optimized production materialization scheme.

Safety input is held as a typed event if resolved safety output is unavailable. Its safety state becomes degraded, ordinary conversation is blocked, and longitudinal effects are deferred. When a later safety-input transaction has a working resolver, previously held inputs are re-evaluated first and released in the same transaction; release is recorded in the timeline and linked safety audit. Server receipt time is used for safety transitions, while original occurrence time remains provenance. No detector logic or conversational LLM is supplied by the API. The developer simulator injects resolved fixture proposals; the default API safety gate fails closed for safety-relevant input.

The schema has dedicated patients, consent, wearable-source, event-envelope, observation, check-in, medication, context, explanation, baseline, held-drift, review-item, safety-state/reference/audit, timeline, and application-audit tables. Event payload JSON retains the original typed transport payload, while normalized signal/context/status fields remain queryable. The schema is initialized deterministically with `CREATE TABLE IF NOT EXISTS`. This is a local prototype database, not production storage, authentication, or a migration system.

## Development limits

- The API has no production authentication. `reviewed_by` is a fixture/reference field, not verified clinician authorization. Anchor changes are limited to named command endpoints and service methods, but deployment must add authorization and reviewer governance.
- Explanations must explicitly reference an existing benign context and associated signals. The application never infers credibility from free text. Clinical governance of category/association remains pending.
- The built-in safety resource is deliberately labelled unverified; no crisis contact is invented.
- Review snapshots are deterministic structured data, never automatically shared. The text and synthetic fixtures do not establish clinical efficacy.
- SQLite replay cost grows with the event history. A production repository/materialization design, migrations, and cross-service transaction/outbox policy remain future work.
