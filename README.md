# aura-health

## Project planning

- [Agent handover](HANDOVER.md) — current state, next steps, and update instructions for agents working on this repo.
- [Care Plan Bridge revised framework](PRODUCT_FRAMEWORK_V2.md) — current product direction and narrowed hackathon MVP.
- [Original framework](PRODUCT_FRAMEWORK.md) and [Claude's critique](FRAMEWORK_CRITIQUE.md) — background and review trail.
- [Brainstorm checkpoint](PROJECT_NOTES.md) — decisions and reference leads from the discussion.
- [Framework critique](FRAMEWORK_CRITIQUE.md) — review of the Care Plan Bridge framework against the brief, the judging rubric, and the submission deadline.

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

Anchor changes use only `/patients/{id}/anchors/provisional`, `/trust`, and `/reanchor` command endpoints. Context explanations use `/patients/{id}/context-explanations` and must cite a specific benign-context event and associated signals. The public API has no configured safety detector: free text and other safety-relevant inputs are held fail-closed until a resolved safety-gate adapter is supplied. No LLM or patient UI is included.
