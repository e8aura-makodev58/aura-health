# Milestone 3 review packet

## 1. TEST RESULTS

`python3 -m unittest discover -s tests -v` passed 47 tests in the saved Milestone 3 run. The longitudinal requirements were checked individually:

| Property | Result | Test name / file | What it proves |
|---|---|---|---|
| L1 | PASS | `test_l1_anchor_moves_only_on_named_event` — `tests/test_longitudinal_part1.py` | Incoming observations, rolling updates, and trust approval leave the anchor value unchanged; an explicit clinical-review reanchor changes it. |
| L2 | PASS | `test_l2_rolling_updates_without_anchor_change` — `tests/test_longitudinal_part1.py` | New observations change the rolling median while the anchored reference remains unchanged. |
| L3 | PASS | `test_l3_missingness_remains_unknown` — `tests/test_longitudinal_part1.py` | Absent, low-coverage, and future observations do not become a zero value or an inferred healthy/pathological state. |
| L4 | PASS | `test_l4_sensing_and_trust_are_orthogonal` — `tests/test_longitudinal_part1.py` | Observed/provisional, observed/trusted, and unobserved/trusted combinations remain independent. |
| L5 | PASS | `test_l5_slow_drift_detected_against_anchor` — `tests/test_longitudinal_part1.py` | A gradual change can be classified from rolling-versus-anchor divergence after the rolling window adapts. |
| L6 | PASS | `test_l6_benign_context_is_signal_scoped` — `tests/test_longitudinal_part1.py` | A benign context attenuates only its named signal; a risk context does not attenuate it. |
| L7 | PASS | `test_l7_benign_context_cannot_clear_subjective_change` — `tests/test_longitudinal_part1.py` | An attenuated HR drift does not suppress a worsening patient check-in. |
| L8 | PASS | `test_l8_hold_does_not_move_anchor` — `tests/test_longitudinal_part1.py` | An explained, held drift stays inspectable and reviewable without changing the anchor. |
| L9 | PASS | `test_l9_held_drift_suppresses_duplicates` — `tests/test_longitudinal_part1.py` | The same held drift suppresses repeat interruption while an opposite-direction drift remains eligible. |
| L10 | PASS | `test_l10_relevant_evidence_reopens_hold` — `tests/test_longitudinal_part1.py` | Worsened check-ins, new signals, structured changes, medication disruption, and safety-relevant events can reopen a hold. |
| L11 | PASS | `test_l11_return_after_gap_reestablishes` — `tests/test_longitudinal_part1.py` | A covered observation after a long gap restores sensing while changing trust to `REESTABLISHING` without moving the anchor. |
| L12 | PASS | `test_l12_stable_state_stays_quiet` — `tests/test_longitudinal_part1.py` | Stable observations can produce `STAY_QUIET` while remaining inspectable. |
| L13 | PASS | `test_l13_safety_is_delegated_to_aura_safety` — `tests/test_longitudinal_part1.py` | A safety event is passed to the authoritative safety writer; the longitudinal layer does not assign T1–T4. |
| L14 | PASS | `test_l14_same_seed_config_timeline_and_events_replay_exactly` — `tests/test_longitudinal_part2.py` | Identical seed, configuration, timeline, and events reproduce every case result; changed seeds differ and trace tampering is detected. |

## 2. CASE A–E RESULTS

Each synthetic case has 70 days: 14 reference days and 56 evaluated days. The simulator explicitly creates a provisional per-signal anchor and submits a synthetic reviewer command to mark it trusted. Anchors remain unchanged thereafter. The four signal keys are sleep midpoint, sleep duration, activity steps, and resting HR; their final sensing/trust combinations match within each case because the fixture gives them shared coverage.

### CASE A — physical illness

- **Setup:** Days 28–34 add about 8 bpm resting HR, 1.5 hours less sleep, 2,200 fewer steps, and later sleep timing. Check-ins remain `Good`.
- **Anchor / rolling:** The trusted anchor stays fixed. Rolling sleep duration, activity, and HR show temporary deviations and return near their references; the final drift labels are `STABLE`.
- **Context / observed drift:** A patient-supplied benign illness/recovery context spans days 28–42 and explicitly covers those physiological signals. On day 30, sleep duration, activity, and HR are detected as `TRANSIENT_DEVIATION`, each attenuated for communication without erasing the observation.
- **Communication / interruptions:** `STAY_QUIET` on all 56 evaluated days; **0** patient interruptions.
- **Final state / expected behavior:** `OBSERVED + TRUSTED` for all four signals. **PASS** — physical change is visible without an unsupported mental-health conclusion or an unnecessary AURA interruption.

### CASE B — slow drift

- **Setup:** From day 21, sleep timing moves progressively later (capped near 200 minutes), steps gradually decline (capped near 2,100 fewer), and check-ins move from `Good` to `Okay` on day 35 and `Rough` on day 50.
- **Anchor / rolling:** The trusted anchor stays fixed while the 14-day rolling window follows recent values. Activity reaches `ROLLING_ANCHOR_DIVERGENCE` on day 38; by the end, sleep midpoint and activity are `PERSISTENT_DRIFT` despite smaller current-versus-rolling differences.
- **Context / observed drift:** No benign context is supplied; later sleep timing, lower activity, and rougher check-ins remain available independently.
- **Communication / interruptions:** 2 `TARGETED_CLARIFICATION` and 4 `MICRO_CHECKIN` decisions; **6** patient interruptions, with 50 of 56 days `STAY_QUIET`.
- **Final state / expected behavior:** `OBSERVED + TRUSTED`. **PASS** — rolling-versus-anchor exposes accumulated descriptive change; AURA's labelled-drift detection latency is 3 days.

### CASE C — illness + independent deterioration

- **Setup:** Days 28–34 contain the same acute illness effects, while a later sleep midpoint and activity decline continue independently. Check-ins become `Okay` on day 28 and `Rough` on day 40.
- **Anchor / rolling:** The trusted anchor stays fixed. Rolling values initially reflect acute illness; sleep midpoint reaches unattenuated `ROLLING_ANCHOR_DIVERGENCE` on day 40 and later persistent drift. Activity remains shifted after the illness context ends.
- **Context / observed drift:** The benign illness context explicitly covers resting HR, sleep duration, and activity through day 42, but not sleep midpoint or subjective check-ins. On day 40, HR-related interpretation is attenuated while sleep-midpoint divergence and the `Rough` check-in remain active.
- **Communication / interruptions:** 2 `TARGETED_CLARIFICATION` and 4 `MICRO_CHECKIN` decisions; **6** patient interruptions.
- **Final state / expected behavior:** `OBSERVED + TRUSTED`. **PASS** — illness does not clear independent longitudinal or subjective evidence. The labelled, unattenuated drift latency is 5 days.

### CASE D — explained benign long-term drift

- **Setup:** From day 21, a persistent work-schedule shift moves sleep midpoint about 190 minutes later and reduces steps about 1,200 per day. Check-ins remain `Good`. A synthetic patient explanation starts on day 30.
- **Anchor / rolling:** The trusted anchor **did not move**. Rolling sleep midpoint and activity shift; both remain `PERSISTENT_DRIFT` at the end relative to the anchor.
- **Context / observed drift:** The benign new-schedule context explicitly covers sleep midpoint and activity. Both entered `EXPLAINED_HELD_FOR_REVIEW` on day 30; their detected drifts and explanation remain inspectable.
- **Communication / interruptions:** One `MICRO_CHECKIN` before the explanation; **1** total patient interruption. **0** duplicate notifications after day 30; 55 of 56 days `STAY_QUIET`.
- **Final state / expected behavior:** `OBSERVED + TRUSTED`. **PASS** — anchor unchanged, hold entered, duplicates suppressed, and **2 clinician-review items** remain visible. No clinician was contacted.

### CASE E — wearable gap / return

- **Setup:** Wearable observations exist through day 27, are absent on days 28–54, and resume on day 55. Check-ins remain `Good`.
- **Anchor / rolling:** The prior trusted anchor remains stored and unchanged. Rolling comparisons become `INSUFFICIENT_DATA` when current observations are absent; after return, comparison with the old anchor remains gated by `REESTABLISHING`.
- **Context / observed drift:** No context or pathological interpretation is assigned to missingness. Missing values are **not converted to zero, normal, or pathological**. Sensing becomes `UNOBSERVED` once the 14-day recency window expires (shown on day 45), then `OBSERVED` when data returns.
- **Communication / interruptions:** `STAY_QUIET` on all 56 evaluated days; **0** patient interruptions.
- **Final state / expected behavior:** `OBSERVED + REESTABLISHING` for all four signals. **PASS** — the returning wearable is not treated as a fully current trusted reference. There is **no automatic exit rule**: only explicit `TRUST_ANCHOR` or `CLINICAL_REVIEW_REANCHOR` commands can restore `TRUSTED`, and post-gap approval criteria for choosing either command are not defined.

## 3. COMPARATOR TABLE

Seed 7 results below are synthetic engineering comparisons, **not clinical efficacy findings**. `—` means latency does not apply or no detection occurred; the missed count distinguishes a miss. Aggregate latency averages detected labelled cases only. Coverage is shared across methods because they receive the same synthetic timeline.

| Case | Method | Interruptions | Unnecessary | Latency (days) | Missed drift | Explained duplicates | STAY_QUIET | Review items | Coverage |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A | AURA | 0 | 0 | — | 0 | 0 | 100% | 0 | 100% |
| A | NAIVE_1_FIXED_THRESHOLD | 1 | 1 | — | 0 | 0 | 98.21% | 0 | 100% |
| A | NAIVE_2_ROLLING_ONLY | 2 | 2 | — | 0 | 0 | 96.43% | 0 | 100% |
| B | AURA | 6 | 0 | 3 | 0 | 0 | 89.29% | 0 | 100% |
| B | NAIVE_1_FIXED_THRESHOLD | 5 | 0 | 1 | 0 | 0 | 91.07% | 0 | 100% |
| B | NAIVE_2_ROLLING_ONLY | 2 | 1 | 10 | 0 | 0 | 96.43% | 0 | 100% |
| C | AURA | 6 | 0 | 5 | 0 | 0 | 89.29% | 0 | 100% |
| C | NAIVE_1_FIXED_THRESHOLD | 6 | 0 | 0 | 0 | 0 | 89.29% | 0 | 100% |
| C | NAIVE_2_ROLLING_ONLY | 2 | 0 | 17 | 0 | 0 | 96.43% | 0 | 100% |
| D | AURA | 1 | 0 | 0 | 0 | 0 | 98.21% | 2 | 100% |
| D | NAIVE_1_FIXED_THRESHOLD | 7 | 5 | 0 | 0 | 5 | 87.50% | 0 | 100% |
| D | NAIVE_2_ROLLING_ONLY | 1 | 0 | — | 1 | 0 | 98.21% | 0 | 100% |
| E | AURA | 0 | 0 | — | 0 | 0 | 100% | 0 | 61.43% |
| E | NAIVE_1_FIXED_THRESHOLD | 0 | 0 | — | 0 | 0 | 100% | 0 | 61.43% |
| E | NAIVE_2_ROLLING_ONLY | 0 | 0 | — | 0 | 0 | 100% | 0 | 61.43% |
| **Aggregate** | **AURA** | **13** | **0** | **2.67** | **0** | **0** | **95.36%** | **2** | **92.29%** |
| **Aggregate** | **NAIVE_1_FIXED_THRESHOLD** | **19** | **6** | **0.33** | **0** | **5** | **93.21%** | **0** | **92.29%** |
| **Aggregate** | **NAIVE_2_ROLLING_ONLY** | **7** | **3** | **13.5** | **1** | **0** | **97.50%** | **0** | **92.29%** |

Unnecessary notifications are counted outside predeclared case-specific useful-interruption windows. `NAIVE_1_FIXED_THRESHOLD` uses fixed absolute differences from the same initial 14-day reference; `NAIVE_2_ROLLING_ONLY` uses the preceding rolling median and robust spread. All three methods share the configured 7-day interruption cooldown.

## 4. CONFIGURATION

The two JSON configurations are `aura_longitudinal/engineering_config.json` (`m3-engineering-v1-not-clinically-validated`) and `aura_longitudinal/comparator_config.json` (`m3-naive-engineering-v1-not-clinically-validated`). Values below are engineering controls, not validated clinical thresholds. Event-supplied controls and fixed rules are identified so they are not mistaken for JSON settings.

| Area | Parameter or control currently affecting behavior | Label |
|---|---|---|
| Anchor creation | `minimum_points=5` distinct same-signal reference days | ENGINEERING DEFAULT |
| Anchor creation / sensing | `minimum_observation_coverage=0.5` for both coverage and data quality | ENGINEERING DEFAULT |
| Anchor governance | Explicit `CREATE_PROVISIONAL_ANCHOR`, `TRUST_ANCHOR`, or `CLINICAL_REVIEW_REANCHOR`; reviewer and reference points are event-supplied, with no automatic anchor movement | CLINICAL REVIEW REQUIRED |
| Rolling baseline / persistence window | `rolling_window_days=14` | ENGINEERING DEFAULT |
| Rolling coverage | `minimum_window_coverage=0.5`, together with `minimum_points=5` | ENGINEERING DEFAULT |
| Drift deviation | `deviation_spread_multiplier=2.0` times the anchored robust-spread scale | ENGINEERING DEFAULT |
| Drift scale | `relative_spread_floor=0.05` of anchor center when robust spread is small | ENGINEERING DEFAULT |
| Trend | `trend_spread_per_day=0.1` times the scale for directional slope | ENGINEERING DEFAULT |
| Persistence | `persistent_fraction=0.6` of covered observations outside the configured deviation; assessed in the 14-day window | ENGINEERING DEFAULT |
| Context attenuation | Event-supplied `BENIGN_CONTEXT`/`RISK_CONTEXT`, active time window, and `affected_signals`; there is no numeric attenuation threshold or automatic context-to-signal mapping | CLINICAL REVIEW REQUIRED |
| Held for review | Event-supplied explanation and affected persistent drift; the record keeps the anchor and detected drift, and suppresses the same direction of drift | CLINICAL REVIEW REQUIRED |
| Hold reopening | Fixed evidence kinds: worse check-in, meaningful new longitudinal signal, structured-assessment change, missed-medication event, or safety-relevant event; `meaningful` is event-supplied and defaults to `true` | CLINICAL REVIEW REQUIRED |
| Wearable gap | `reestablish_after_days=14` since the last adequately covered observation | ENGINEERING DEFAULT |
| `REESTABLISHING` behavior | Current comparison is `INSUFFICIENT_DATA`; no automatic exit criterion exists, and trust changes only on explicit anchor commands | CLINICAL REVIEW REQUIRED |
| Communication burden | `communication_cooldown_days=7` for AURA and both comparators | ENGINEERING DEFAULT |
| Communication rules | Worse check-in → targeted clarification; uncovered persistent drift → micro-check-in (targeted if risk context); transient/held/insufficient data → quiet; assessment/review outcomes require explicit requests | CLINICAL REVIEW REQUIRED |
| Naive fixed comparator | Absolute deltas: sleep midpoint 90 minutes; sleep duration 1 hour; activity 1,000 steps; resting HR 6 bpm | ENGINEERING DEFAULT |
| Naive rolling comparator | Absolute floors: sleep midpoint 30 minutes; duration 0.4 hour; activity 300 steps; resting HR 2 bpm; `rolling_robust_spread_multiplier=2.0` | ENGINEERING DEFAULT |

The benign-context rule is a product invariant: attenuation can affect only explicitly associated signals and cannot erase observations, check-ins, medication disruption, or safety evidence. It is not a configurable way to clear patient state.

## 5. REPLAY

Exact simulator commands used for the saved seed-7 output:

```sh
python3 -m aura_longitudinal.simulator run --case ALL --seed 7 --save-timeline /tmp/aura-longitudinal-timeline.json --save-trace /tmp/aura-longitudinal-trace.json
python3 -m aura_longitudinal.simulator replay /tmp/aura-longitudinal-trace.json
```

The timeline contains 350 synthetic days (70 per case); the decision trace contains **280 entries** (56 evaluated days per case). Replay matched all five regenerated timelines, all 280 decision entries, and the metrics exactly. Seed: **7**. Configurations: `m3-engineering-v1-not-clinically-validated` and `m3-naive-engineering-v1-not-clinically-validated`, with the values in §4. L14 also checks a changed seed and rejects a tampered saved result.

## 6. ASSUMPTIONS

- **Explicit synthetic anchor-review event:** The simulator submits a fixture reviewer command after 14 reference days. Production `BaselineManager` requires an explicit command but contains no synthetic reviewer identity or automatic approval.
- **Shared wearable coverage:** Synthetic sleep, activity, and HR disappear and return together in Case E. Production observations and sensing are keyed by signal/source, so shared missingness is not required by production logic.
- **Predeclared hidden scenario labels:** Onset days, changed signals, useful-interruption windows, and Case D's explanation day are fixed in `synthetic.py` before evaluation. The production baseline, drift, context, held-record, and communication modules do **not** receive these labels. `evaluation.py` uses them for metric scoring; it also uses Case D's `explained_from_day` to decide when to call the production `hold_explained` API. That simulator-only orchestration affects the Case D result and is not a production explanation trigger.
- **Explicitly linked contextual signals:** The synthetic timeline names the signals each illness or schedule event may explain. Production `apply_context` consumes those explicit links and does not infer them from sensor data or diagnose their cause; the association mechanism itself needs governance.

## 7. OPEN ISSUES

- **Governed exit from `REESTABLISHING`:** There is no automatic exit or specified post-gap evidence criterion. `TRUST_ANCHOR` can restore `TRUSTED` without moving the old anchor; `CLINICAL_REVIEW_REANCHOR` can establish a reviewed new one. Criteria for choosing and approving these paths remain undefined.
- **Clinical review of parameters and communication:** Anchor sufficiency, gap duration, drift/persistence settings, interruption cooldown, check-in escalation, and when to request structured assessment have engineering behavior but no clinical validation. The comparator constants are evaluation fixtures, not care thresholds.
- **Manual context association and explanation credibility:** `affected_signals` and benign/risk category are supplied rather than inferred. No governed rule yet determines whether a particular explanation credibly attenuates a particular signal.
- **Simulator-ground-truth dependency:** Onset/signals/useful windows determine evaluation metrics, and Case D's hidden explanation day triggers the simulator call to hold drift. The production modules do not see hidden labels; a real event-driven explanation trigger has not been specified.
- **Communication-choice ambiguity:** The current rules treat a worse check-in as targeted clarification without applying the persistent-drift cooldown, while persistent drift can prompt repeat micro-check-ins after that cooldown. The appropriate repetition limits and criteria for automatic targeted clarification versus structured assessment remain open.

## 8. VERDICT

**Milestone 3 stop condition met for the synthetic engineering prototype:** Cases A–E run, L1–L14 pass, both comparator result sets are available, and the saved trace replays exactly. The open issues above prevent treating these results as clinical validation or a deployment policy. No Milestone 4 work was begun.
