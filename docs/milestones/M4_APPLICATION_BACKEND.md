# M4 — Application Backend and Orchestration

Status: COMPLETE / ACCEPTED. Canonical acceptance evidence: [`MILESTONE4_REVIEW.md`](../../MILESTONE4_REVIEW.md). A1–A20 were verified against that review and repository tests.

## Goal and delivered architecture

Connect accepted domains without API-controller policy. Implemented FastAPI, SQLite development persistence, repository boundaries, idempotent atomic ingestion, timeline/status, deterministic clinician-review snapshot, safety-first integration, and synthetic Cases A–F.

Actual accepted event flow is: patient event → API → application service → transaction/raw event → **safety boundary first for safety-relevant input** → longitudinal processing as applicable → safety-precedent communication result → persistence/audit → API response. Safety-first order corrects the older shorthand that placed longitudinal processing before safety for every event.

## Historical acceptance criteria

- **A1:** controllers contain no longitudinal/safety decisions.
- **A2:** idempotency prevents duplicate domain processing.
- **A3:** ordinary observations cannot move anchored baseline.
- **A4:** governed anchor command can change anchor.
- **A5:** longitudinal output persists in timeline.
- **A6:** context explanation updates held-for-review correctly.
- **A7:** clinician snapshot includes held items.
- **A8:** snapshot does not imply automatic sharing.
- **A9:** safety output overrides ordinary communication.
- **A10:** application never assigns T1–T4.
- **A11:** free text reaches safety before conversational processing.
- **A12:** rollback prevents partial event processing.
- **A13:** sensing/trust survive reload.
- **A14:** safety references survive reload.
- **A15:** Cases A–E retain M3 behavior through application path.
- **A16:** Case F safety handoff works end-to-end.
- **A17:** timeline order is deterministic.
- **A18:** identical persisted state yields identical snapshot.
- **A19:** endpoints expose no relapse probability, diagnosis, or psychiatric risk score.
- **A20:** application restart retains development state.

Case F starts with ordinary longitudinal context; safety-relevant patient input enters `aura_safety`, whose authoritative result overrides ordinary communication and is persisted/audited without a conversational LLM.

## Known limitations and stop condition

SQLite is development-only; authentication/reviewer authorization is not production-ready. Governed REESTABLISHING exit, clinical threshold review, and safety content/resource review remain open. Replay-per-event cost grows with history; routine T0/null safety references may need snapshot filtering. M4 stopped with orchestration, persistence, minimum API, explicit domain boundaries, snapshot, Cases A–F, and A1–A20 passing—without UI, real wearables, LLM, or production deployment.
