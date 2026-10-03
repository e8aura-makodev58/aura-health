# aura-health

## Project planning

**aura-health** is a wearable-first, patient-controlled companion for adults on stable antidepressant maintenance treatment (hackathon challenge: *AI Healthier Every Day*). It is a synthetic-data research prototype, not a diagnostic or clinical service.

- [Agent handover](HANDOVER.md) — current state, next steps, and update instructions for agents working on this repo.
- [Roadmap](docs/ROADMAP.md), [decisions](docs/DECISIONS.md), [milestone specs](docs/milestones/), and [demo script](docs/DEMO_SCRIPT.md) — canonical plan (M1–M8).
- [aura-health framework v1.0](aura_health_framework_v1.0.md) — canonical product, safety, and governance framework.
- [Deterministic safety policy v1.2](aura_deterministic_safety_policy_state_machine_v1.2.md) — safety state machine specification.
- [Milestone 3 review](MILESTONE3_REVIEW.md), [Milestone 4 review](MILESTONE4_REVIEW.md), [Milestone 5 review](MILESTONE5_REVIEW.md), and [Milestone 6 review](MILESTONE6_REVIEW.md) — milestone evidence and review packets.
- [Brainstorm checkpoint](PROJECT_NOTES.md) — early decisions and reference leads.
- Superseded: [Care Plan Bridge framework](PRODUCT_FRAMEWORK.md), [revision](PRODUCT_FRAMEWORK_V2.md), and [critique](FRAMEWORK_CRITIQUE.md) — dropped direction, kept for background.

## Milestone 4 prototype API

The accepted safety and longitudinal engines remain separate; [application architecture and transaction notes](aura_app/README.md) describe their integration. This is a synthetic-data development API, not a clinical service.

```sh
UV_CACHE_DIR=/tmp/aura-uv-cache uv venv .venv
UV_CACHE_DIR=/tmp/aura-uv-cache uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python -m aura_app.persistence --db aura-m4-development.sqlite3
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m uvicorn aura_app.api:app --host 127.0.0.1 --port 8000
```

Run the synthetic A–F cases through the application service (not the comparator policy), optionally retaining each development DB and a trace:

```sh
.venv/bin/python -m aura_app.simulator --case ALL --seed 7 --db-dir /tmp/aura-app-cases --save /tmp/aura-app-cases.json
```

Example API calls after starting the server:

```sh
curl -X POST http://127.0.0.1:8000/patients -H 'Content-Type: application/json' -d '{"patient_id":"demo","display_name":"Demo alias","age":35,"timezone":"UTC","consents":[{"consent_type":"WEARABLE","granted":true}]}'
curl -X POST http://127.0.0.1:8000/patients/demo/events -H 'Content-Type: application/json' -d '{"event_id":"demo-watch-1","event_type":"WEARABLE_OBSERVATION","occurred_at":"2026-01-01T12:00:00+00:00","source":"fixture","idempotency_key":"demo-watch-1","payload":{"observations":[{"kind":"activity","date":"2026-01-01","metrics":{"steps":7000},"coverage":1.0,"source":"fixture-watch"}]}}'
curl http://127.0.0.1:8000/patients/demo/timeline
curl http://127.0.0.1:8000/patients/demo/status
curl http://127.0.0.1:8000/patients/demo/review-snapshot
```

Anchor changes use only `/patients/{id}/anchors/provisional`, `/trust`, and `/reanchor` command endpoints. Context explanations use `/patients/{id}/context-explanations` and must cite a specific benign-context event and associated signals. The public API has no configured safety detector: free text and other safety-relevant inputs are held fail-closed until a resolved safety-gate adapter is supplied.

## Milestone 6 patient app

Responsive, calm patient web application at `/`: check-in, medication routine,
personal patterns/provenance, explicit explanations, review preview, and pinned
safety resources. No frontend domain policy or live model. Use synthetic data only.

```sh
.venv/bin/python -m aura_app.demo --db aura-m6-demo.sqlite3
AURA_DEMO_DB=aura-m6-demo.sqlite3 .venv/bin/python -m uvicorn aura_app.demo:create_demo_app --factory --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/`; **Explore demo** shows Cases A–F and gap/return,
before/after explanation checkpoints. Existing demo patients survive restart.
[Patient-app instructions](aura_ui/README.md) cover fixtures, privacy, memory-only
offline retry, and the optional real-browser acceptance runner. No CodeBuddy tool
was used; its later SOW/rebuild remains user-controlled.

## Milestone 5 communication

The [bounded communication service](aura_communication/README.md) reads committed
application decisions and safety references, validates optional model output against
approved wording candidates, and persists the message and generation audit. The
default provider is disabled; fixed fallbacks work without a model/network. T3/T4,
degraded, offline, and unassessed-input paths do not call a model. No live model or
real detector is configured by these examples.

```sh
.venv/bin/python -m aura_communication.evaluation --save /tmp/aura-m5-evaluation.json
.venv/bin/python -m aura_communication.evaluation --behavior disabled
curl -X POST http://127.0.0.1:8000/patients/demo/events/demo-watch-1/communication \
  -H 'Content-Type: application/json' -d '{}'
```

Use `{"purpose":"EXPLAIN_OBSERVATION"}` for a voluntary explanation of an existing
descriptive observation. The API accepts an existing event ID and purpose, never
raw text, safety state, or arbitrary generation instructions on this route. Provider
configuration, JSON gateway contract, test commands, persistence, and engineering
limits are documented in `aura_communication/README.md`.
