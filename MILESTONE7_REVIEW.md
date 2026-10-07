# Milestone 7 — local integration review

Status: **local gates implemented; not complete/accepted**. Public Cloudflare URL is
pending user hostname/token-file configuration and external verification. No M8 work.
Evidence date: 2026-10-07. Synthetic engineering evaluation only, not clinical validation.

## Architecture and changed files

`aura_simulation/{agent,timeline,driver,__main__}.py` separates bounded planning,
seeded numeric generation, hidden evaluation metadata and observable-only application
inputs. `aura_app/{hosted,demo_workspace,benchmark}.py` adds isolated fixture-only
browser workspaces, atomic seed/recoverable reset and timing diagnostics. `demo.py`,
`api.py` and `aura_ui/` wire tooling/reset/fixture question controls and restrict assets.
Docker/Compose/locked demo dependencies configure portable non-root loopback hosting
and optional token-file tunnel. No dependency upgrade was performed.

See [diagram](docs/ARCHITECTURE.md), [deployment](docs/DEPLOYMENT.md),
[scenario runner](aura_simulation/README.md), and [walkthrough](docs/DEMO_SCRIPT.md).

One genuine integration contradiction was found: the application projector never
passed `new_longitudinal_signal` to the accepted communication engine, so unrelated
new longitudinal evidence could not reopen explained records via that boundary.
`aura_app/longitudinal.py` now forwards newly persistent/divergent signals calculated
by the production drift engine. Existing domain reopening rules decide the result.
No `aura_safety/` or `aura_longitudinal/` algorithm or clinical configuration changed.

## Automated gates

All names below are in `tests/test_milestone7.py`; existing P/L/A/G/UI gates are retained.

| ID | Test suffix | Result / scope proven |
|---|---|---|
| DEMO1 | cases_a_to_f_have_hosted_paths | PASS — A–F persist and expose status/review without automatic transmission. |
| DEMO2 | ground_truth_isolation_at_every_input_field | PASS — poisoned hidden fields do not alter observable frames or committed states/actions. |
| DEMO3 | no_live_llm_fallbacks | PASS — all nine wording fixtures work with provider disabled. |
| DEMO4 | invalid_output_and_timeout_fallbacks | PASS — invalid/timeout providers fall back for all nine fixtures. |
| DEMO5 | exact_semantic_replay | PASS — fresh DB reproduces every semantic committed entry. |
| DEMO6 | session_reset_isolated_and_deterministic | PASS — one browser resets exactly without changing another browser's state. |
| DEMO7 | no_real_data_or_signup | PASS — non-fixture intake and patient creation are rejected without new timeline data. |
| DEMO8 | private_assets_and_api_docs_not_served | PASS — only approved static assets are served; CDN API docs are unavailable. |
| DEMO9 | incomplete_seed_not_silently_reopened | PASS — incomplete seed is preserved and rejected. |
| DEMO10 | reset_archives_and_rejects_unknown_profiles | PASS — operator reset archives old DB and rejects non-catalog profiles. |
| DEMO11 | new_signal_reopens_held_without_anchor_change | PASS — new independent persistent signal reopens held records with unchanged anchors. |
| DEMO12 | patient_distress_with_missing_wearable_stays_active | PASS — independent distress triggers communication despite missing physiology; gaps remain null. |
| DEMO13 | figurative_fixture_and_detector_failure_are_not_guessed | PASS — resolved figurative mock stays normal; unavailable detector degrades. |
| DEMO14 | agent_contract_rejects_policy_and_unknown_fields | PASS — planner rejects policy/hidden-truth fields; bounded timeline request validates. |
| DEMO15 | model_adapter_validates_before_numeric_generation | PASS — mocked gateway plans validate before generation; invalid policy output is rejected. |
| DEMO16 | production_domains_do_not_import_simulation_agent | PASS — production domain/application decision modules have no simulation import. |

Full Python command: `.venv/bin/python -m unittest discover -s tests -q`.
**140 tests PASS** (124 existing + 16 M7); existing Starlette/httpx deprecation warning.
Restricted sandbox ASGI test transports may hang after daemon recovery; execute with
the approved local-network permission when necessary.

Real Chromium commands (developer-only Playwright installation; no runtime dependency):

```sh
NODE_PATH=/home/makodev58/rendertest/node_modules LD_LIBRARY_PATH=/home/makodev58/rendertest/libs/usr/lib/x86_64-linux-gnu .venv/bin/python tests/browser/run.py
NODE_PATH=/home/makodev58/rendertest/node_modules LD_LIBRARY_PATH=/home/makodev58/rendertest/libs/usr/lib/x86_64-linux-gnu node tests/browser/milestone7.cjs
```

M6 regressions: **17 PASS**, UI1–UI15 + OFFLINE + MANUAL_RETRY, 320/390/1280 widths,
no page errors. Hosted: **6 PASS** — notice, A–F visible paths, pinned safety precedence,
private reset, no real intake, restricted surface; no page errors. Artifacts are in
`/tmp/aura-m6-browser-artifacts` and `/tmp/aura-m7-browser-artifacts` (ephemeral).
These are UI-test artifacts, not CodeBuddy evidence. Browser checks require loopback
and do not claim public HTTPS testing.

## Scenarios and replay

The nine hosted checkpoints include stable, A, B, C, D-before/D-held, E-gap/E-return,
and F. Existing accepted Cases A–E behavior is rechecked by the prior L/A gates.
Hosted UI confirms all A–F show persisted patterns/timeline/review and no auto-sharing.
F pins safety above ordinary views; no model is involved. Additional fixtures cover
illness + Rough check-ins + missing wearables, explanation followed by independent
RHR change, figurative language with resolved normal input, detector failure,
wording timeout/invalid output, isolation and reset. Older safety tests retain stale
CAS/race/late-result coverage; no new detector sensitivity claim is made.

```sh
.venv/bin/python -m aura_simulation --description 'Case D new signal after explanation' --seed 7 --save /tmp/aura-m7-new-signal.json
.venv/bin/python -m aura_simulation --replay /tmp/aura-m7-new-signal.json
```

Replay matched **150 semantic state/action entries exactly** with seed 7 and saved
policy/longitudinal/wording configuration fingerprint plus fixture resource version.
This uses the same explicit new-signal fixture as DEMO11; ordinary Case D was also
replayed separately with 150 exact semantic entries.
Replay sorts review rows by stable source references and excludes random DB IDs and
wall-clock audit/render latency; it is not byte-identical database replay. Fixed
resolved detector proposals are inputs, not a claim of deterministic detectors.

## Hosting, reset and limits

Local timing diagnostic (single run, not a load test):
`.venv/bin/python -m aura_app.benchmark --save /tmp/aura-m7-benchmark.json`.
Initial seed preparation 30.828 s; ten status requests median 12.840 ms / max
39.137 ms; one check-in ingestion 38.498 ms (short history) / 98.267 ms (long
history); session reset 17.768 ms. No live-model latency was measured. These are
machine-specific synthetic diagnostics, not response-time guarantees.

`AURA_SECURE_COOKIE=false docker compose up -d --build app` built and started the app.
`docker compose ps` shows healthy; loopback `/health` returns
`{"status":"ok","synthetic_only":true,"seed":7}`. Port: `127.0.0.1:8017`.
Cloudflare sidecar is prepared but not started; HTTPS must use Secure cookies and a
reviewed pinned cloudflared image. No other hosted application's deployment changed.

Baseline is persisted and verified; each browser gets a private SQLite clone. Reset
copies the immutable baseline, keeps the old clone until expiry, and does not execute
a patient safety downgrade. Session mappings are in-memory, not authentication.
Restart preserves baseline but starts new browser workspaces. Abrupt-restart orphan
files are retained; cleanup/rate limiting remains a limitation. Engineering budgets:
16 sessions, 3600-second idle TTL, 4 resets/session, 8192-byte body. No production care.

## Assumptions and open issues

- Offline template planner is implemented; live Simulation Data Agent gateway is only
  mocked. No actual model-generated scenarios or live generation are claimed.
- Numeric timelines over 70 days repeat terminal fixture values before explicit changes;
  no population realism or clinically validated signal thresholds are claimed.
- Context associations and synthetic anchor-review references are explicit fixtures.
  Context credibility and reviewer authorization remain ungoverned for real deployment.
- REESTABLISHING has no governed exit. Clinical parameters and all safety content/resources
  require review. Resource fixtures are not verified crisis resources.
- No production auth, clinician transmission, real wearable APIs, diagnosis, relapse
  prediction or medication/taper instructions. Review selection remains temporary preview.
- Public input restriction is a synthetic-demo boundary, not clinical classification.
  Non-demo unknown free text still reaches safety and fails closed.
- History replay/render cost grows with event history. Routine T0/null safety snapshot
  references remain backend data, filtered only by the UI. Offline queue is memory-only;
  no cold-start offline application.
- Public Cloudflare hostname/token-file path, pinned sidecar and external reachability
  are outstanding. CodeBuddy timing remains user-controlled; no evidence is fabricated.

## Verdict

Local integration gates are green; **M7 stop condition is not yet met** because the
required public live link is not configured/verified. Finish that gate and obtain
review before M8. No accepted clinical policy was invented or expanded.
