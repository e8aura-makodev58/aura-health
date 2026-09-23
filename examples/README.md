# Safety simulator

Run the fixture scenario and save its normalized event log:

```sh
python3 -m aura_safety.simulator run examples/safety_scenario.json --save /tmp/aura-safety-trace.json
python3 -m aura_safety.simulator replay /tmp/aura-safety-trace.json
```

The simulator uses the production `SafetyEngine` and serial `SafetyStore`. A scenario can set `initial_state`, `start_at`, `resource_version`, `policy_config`, and `steps`. Omit `initial_state` for NORMAL/NONE. A step can be:

- an `event` with any accepted `kind`; `based_on_sequence: "current"` resolves to the current sequence, while an integer simulates a potentially stale CAS;
- `{"type":"advance","seconds":3600}` or `{"type":"advance","to":"2026-09-23T01:00:00+00:00"}`; then explicitly inject the clock event;
- `{"type":"race","events":[...]}` to specify arrival order at the single writer;
- `{"type":"offline_input","input_id":"held-1","payload":"fixture input"}` followed by `{"type":"reconnect"}`. Reconnected input remains unassessed until a later resolved safety event is injected.

Use `DETECTORS_COMPLETE` with fixture `detector_outputs` for D1–D6. Use `STRUCTURED_RESPONSE_RECEIVED` to hold a structured answer, then a resolved D1 output to assess it. Use `POLICY_FLAG_SET` with `flag_name` and optional `flag_expires_at` to inject an explicit D5 input flag. This harness does not implement detector models or clinical tier mappings. The built-in resource is labelled as an unverified development fixture and contains no crisis contact information.
