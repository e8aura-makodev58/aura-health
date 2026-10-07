# Development-only scenario planning and replay

The default Simulation Data Agent uses an **offline template planner**, not a live
generative model. An optional `JSONGatewayPlanner` adapter is contract-tested with a
mock transport; no live provider is configured or claimed. It receives synthetic
descriptions only, validates exact fields and bounded size/windows, and rejects invalid
plans rather than asking a model to repair policy. It holds no repository or patient state.

```sh
.venv/bin/python -m aura_simulation --description 'Case C illness with independent worsening check-in and missing wearable' --seed 7 --save /tmp/aura-c.json
.venv/bin/python -m aura_simulation --description 'Case D new signal after explanation' --seed 7 --save /tmp/aura-d.json
.venv/bin/python -m aura_simulation --description 'Case A figurative language' --seed 7
.venv/bin/python -m aura_simulation --description 'Case A detector failure' --seed 7
.venv/bin/python -m aura_simulation --replay /tmp/aura-d.json
# Or supply an exact validated specification:
.venv/bin/python -m aura_simulation --spec /tmp/aura-d.plan.json --save /tmp/aura-d-repeat.json
```

Save creates trace, `.timeline.json`, and `.plan.json` files. Numeric generation uses
the accepted Cases A–F seed generator. Beyond 70 days it repeats the terminal numeric
fixture before applying explicit plan changes; this is a reproducibility convenience,
not realistic population modeling. Cases/check-in changes/gaps/message fixtures are
generation inputs; hidden labels and expected outcomes stay evaluation-only. The driver
constructs observable payloads explicitly and invokes the production application and
domain engines. It never implements alternative product policy.

Replay checks the configuration fingerprint and compares every semantic committed
state/action entry exactly. Random SQL row identifiers, wall-clock audit/render timing
and insertion order of logically equivalent review rows are not replayed; review rows
are compared by stable source references. Resolved detector fixtures are fixed inputs,
not deterministic-detector or clinical-performance claims. Anchor review references are
explicit synthetic commands, not evidence of real authorization. Configuration units
and budgets are engineering values (days 14–365, ≤32 events/family, description ≤2000
characters, gateway output ≤32768 bytes, timeout 5 seconds).
