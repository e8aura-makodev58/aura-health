# M6 patient application

Plain HTML/CSS/JavaScript, served by FastAPI at `/`. No build step, remote fonts,
trackers, frontend framework, or new runtime dependency. Only presentation state is
kept in the browser. Domain state lives in the accepted engines and development DB.

## Run

From the repository root after the Python setup in the root README:

```sh
.venv/bin/python -m aura_app.demo --db aura-m6-demo.sqlite3 --seed 7
AURA_DEMO_DB=aura-m6-demo.sqlite3 .venv/bin/python -m uvicorn aura_app.demo:create_demo_app --factory --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/`. **Explore demo** switches between nine persisted
synthetic checkpoints: stable, A, B, C, D-before-explanation, D-held, E-gap,
E-return, F. Initial seeding takes roughly half a minute on the development machine;
restart preserves edits and skips existing patients. Use a new explicit DB path for
a fresh demonstration. If initial seeding was interrupted, use a fresh DB path:
events are atomic but the entire seed is not, and existing profiles are skipped.
No reset/deletion API or Simulation Data Agent is included.

Ordinary API startup also serves the UI, without a demo catalog or safety fixtures:

```sh
.venv/bin/python -m uvicorn aura_app.api:app --host 127.0.0.1 --port 8000
```

Open a development patient by ID in **Explore demo**. Without resolved detector
outputs the public gate holds safety-relevant input; it does not assert safety.
There is no production authentication: use synthetic data only, on loopback.

## Patient flows

- **Today:** optional Good/Okay/Rough check-in, separate optional note, neutral
  acknowledged/missed/unknown medication record, always-available patient entry.
- **Patterns:** server-provided drift/context, signal-specific sensing/trust state,
  governed reference provenance, held observations, and typed recent timeline.
- **Explain:** cite an existing linked benign context and associated signals. D-before
  has the prepared explanation `new stable work schedule`; submitting it exercises
  the real held-for-review command. Arbitrary text is not classified as credible.
- **Review:** structured persisted snapshot. Checkboxes are a temporary local preview,
  never approval, saved selection, sharing, or clinician transmission. Questions are
  safety-gated; unresolved questions are held and excluded from the snapshot.
- **Safety:** committed communication output and separate resources are displayed
  across navigation. No dismiss/downgrade control or frontend tier assignment exists.
- **Offline:** fixed local fail-closed wording plus the embedded, unverified fallback
  resource fixture. Failed submissions stay **in memory only** with their original
  idempotency key; reconnect or **Retry connection** retries them. Reloading loses
  unconfirmed input (with an unload warning). No plaintext browser storage is used.
  This is not durable encrypted offline delivery or an emergency-monitoring service.

The demo's finite adapter supplies resolved fixtures for known structured taps,
the prepared D explanation, `fixture ordinary message`, and `fixture safety concern`.
Unknown text fails closed. These are not real detectors. Synthetic checkpoint dates
remain fixed when interacting and are shown in the page header. Neither latent truth
nor evaluation windows reach decision payloads.

## Privacy and boundaries

Both supplied entry points explicitly disable live models, regardless of gateway
environment variables. Live use is deferred until informed consent is governed.
All current wording/resources require review; no crisis contact is invented.
Resources render outside communication text. REESTABLISHING has no invented exit.

`GET /patients/{id}/view` provides latest committed event ID, reason/context,
reference-linked explanation options, medication record, and privacy metadata through
a read-only application service. Existing event/communication endpoints handle all
writes. Frontend code does not compute drift, move anchors, score mental health, or
assign safety tiers. Routine null-episode references are filtered only in the UI;
the accepted backend snapshot is unchanged.

## Verify

```sh
.venv/bin/python -m unittest discover -s tests -q
```

Optional real Chromium suite (Node + Playwright are **developer tools only**):

```sh
npm install --prefix /tmp/aura-ui-tools playwright@1.62.1
/tmp/aura-ui-tools/node_modules/.bin/playwright install --with-deps chromium
NODE_PATH=/tmp/aura-ui-tools/node_modules .venv/bin/python tests/browser/run.py
```

The runner owns a fresh temporary synthetic DB and loopback server, cleans up its
process, runs UI1–UI15 plus offline retry, and writes results/screenshots under
`/tmp/aura-m6-browser-artifacts`. Override with `--artifacts` or `--port`. It never
uses the persistent demo DB. Browser screenshots are ordinary UI verification,
**not** CodeBuddy evidence.
