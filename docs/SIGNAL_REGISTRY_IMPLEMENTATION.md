# Signal registry — implementation and review

2026-10-08. Implements the telemetry foundation of DECISIONS §41 and
`PATIENT_SIMULATOR_AGENT_PLAN.md` §3, **not the full patient simulator**.

## Sponsor configuration

`aura_longitudinal/signal_registry.json` declares each channel's name, label,
unit, source class, cadence, descriptive readings/week, evidence tier, display
switch, engine switch and per-signal engineering overrides. The existing
`engineering_config.json` supplies inherited defaults; a separate
`communication_overrides.communication_cooldown_days` controls communication.

All settings are **ENGINEERING DEFAULT / CLINICAL REVIEW REQUIRED**. Neither
the evidence-tier labels nor passing tests establish clinical suitability.
Clinical/regulatory assessment belongs to the sponsor; technical boundaries
(finite measurements, missingness, explicit anchors, deterministic policy)
remain enforced in code.

| Channels | Engine default | Cadence |
|---|---|---|
| Sleep midpoint/duration, activity, resting HR | Enabled; original defaults unchanged | Daily |
| HRV RMSSD, nocturnal respiratory rate, skin-temperature deviation | Enabled, E3_RESEARCH | Nightly |
| SpO2 | Display only | Potentially sparse nightly |
| Systolic/diastolic BP | Display only | Intermittent; descriptive 2.5/week |
| Thermometer temperature, weight | Display only | Intermittent |

The optional `AURA_SIGNAL_REGISTRY=/absolute/path/sponsor-registry.json`
selects another complete registry. The service captures it on startup;
changes require restart and versioning. In Docker, an operator-owned file
can be placed in persistent `/data`, then selected with the Compose
environment setting. No publicly writable configuration endpoint was added.
`GET /signals` exposes effective non-secret settings and their fingerprint.
The public hosted route does not allocate a session or permit changes.

Per-signal overrides support rolling-window days, minimum samples, calendar
coverage, measurement quality/coverage, gap duration, spread multiplier,
persistent fraction, trend threshold, relative spread floor and absolute
spread floor. Communication cooldown is global rather than ambiguously
signal-specific. Invalid/unknown settings prevent startup instead of silently
substituting defaults. There is no automatic REESTABLISHING exit.

### Two integration corrections

1. A zero-centered temperature-deviation reference needs a scale floor that
   does not depend on its center. `absolute_spread_floor` is an additive config
   field, default **0** for the existing four channels. Skin deviation uses
   **0.1 °C**, a provisional engineering placeholder, not an illness threshold.
2. New-channel anchor creation checks actual calendar coverage as well as the
   existing sample/quality checks. It cannot turn ten weekly readings over
   seventy days into a dense reference. Existing four-channel anchor rules
   are unchanged. No cadence-based interpolation or denominator discount exists.

## Ingestion and evidence

Existing sleep/activity/resting-HR observation formats remain unchanged.
New scalar measurements use the ordinary `WEARABLE_OBSERVATION` envelope:

```json
{"observations":[{"kind":"scalar","signal":"BODY_TEMPERATURE",
  "date":"2026-01-01","value":39.2,"coverage":1,"data_quality":1,
  "source":"synthetic_thermometer","unit":"degC"}]}
```

This is a **synthetic example**, not a diagnostic threshold. Unit must match
the registry exactly; no implicit unit conversion occurs. BP components are
distinct named measurements. A repeated same-day reading is retained in the
event/observation ledger, but the accepted baseline manager's daily selection
never counts it as another covered day. No high-frequency BP analysis is claimed.

All supplied measurements are persisted transactionally. Display-only channels
never enter drift/communication/held-reopening calculations or receive new
engine anchors. They remain source-linked evidence for charts and read-only
agent tools. Research labels and cadence travel with the evidence projection.
Hidden evaluation fields in the new scalar shape are rejected. No scenario
truth is added to domain inputs; no safety-policy changes were made.

Engine-enabled channels use the same rolling/anchor/drift/context/communication
algorithms with their registered parameters. A missing calendar day remains
missing. BP at two or three readings/week and weekly weight fail the default
50% rolling coverage threshold even after engine opt-in; output remains
INSUFFICIENT_DATA. The sponsor may explicitly revise coverage/window settings,
but enabling a flag alone does not relax them.

The hosted demo **still rejects arbitrary observation intake**. The existing
allowlist is not bypassed to make this foundation appear interactive. Structured
demo entry and the simulator's validated ingestion path remain next work.
Manual scalar inputs currently use the existing wearable-event envelope and
therefore its WEARABLE consent requirement; a source-appropriate manual-entry
consent path must be defined with the upcoming intake UI rather than silently
waiving consent here.

## Configuration history

Committed application projections record registry version and fingerprint.
Read-only agent run signatures include the registry fingerprint; old drafts
cannot be replayed as current after a registry change, even if no event was added.
The service pins one configuration per process. Existing committed results and
anchors are not overwritten just by restarting or disabling a channel; historical
reference plots remain historical. Disabled channels do not become current
decision evidence, and new anchor commands for them are rejected.

On a later input, the existing application replay adapter re-evaluates eligible
history using the loaded registry. Operators must retain the matching registry
and base engineering config for exact historical replay. This implementation
does **not** provide a configuration-version archive or retrospective migration
workflow. Raising anchor requirements can reject replay of a previously created
reference; failure rolls back the new event rather than silently recreating it.
Unit changes require explicit data migration, not editing a label. Versioning,
reviewer authorization and production settings management remain future work.

## Verification / remaining work

`tests/test_signal_registry.py`: SR1–SR16 cover legacy defaults, research flags,
sparse opt-in, sparse anchors, repeated-day coverage, display-only isolation,
atomic invalid-input rejection, per-signal settings, zero-centered scale,
configuration validation/fingerprints, API/restart, disabled history, anchor
preservation, display flags and source-matched new-channel agent claims.

Existing L1–L14 and A–F regressions remain the acceptance evidence for the original
channels. No new clinical validation or live-model sweep is claimed.

Next: approved agent readability/verifier/tools work, Disclaimer page and public
provider/model line, structured intake and layered free-text gate, then the
demo-only life director/seeded generator, flu effects and demo controls. The
three-day flu simulation, simulator-run ledger and live director are **not yet
implemented** by this step. Safety resources, question wording and sponsor
configuration UI also remain separate work; this registry does not imply those
controls already exist.

Verified: SR1–SR16 **16 PASS**; full suite **211 PASS**; existing hosted browser
dual view **12 PASS**, agent **5 PASS**, settings PASS at 320/390/1280; additional
development `registry.cjs` **3 PASS** checks exact scalar ingestion, research/
display-only charts and 390/1280 layout without page errors. These checks make
no provider calls. Commands:

```sh
.venv/bin/python -m unittest discover -s tests -q
.venv/bin/python -m unittest tests.test_signal_registry -q
# With the already-installed Playwright environment (see aura_ui/README.md):
.venv/bin/python tests/browser/run.py --hosted --suite dual_view.cjs agent.cjs settings.cjs --port 8020 --artifacts /tmp/aura-registry-browser
.venv/bin/python tests/browser/run.py --suite registry.cjs --port 8021 --artifacts /tmp/aura-registry-new-browser
```
