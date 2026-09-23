# Longitudinal engineering simulator

Run one or all synthetic cases, then verify exact replay:

```sh
python3 -m aura_longitudinal.simulator run --case ALL --seed 7 \
  --save-timeline /tmp/aura-longitudinal-timeline.json \
  --save-trace /tmp/aura-longitudinal-trace.json
python3 -m aura_longitudinal.simulator replay /tmp/aura-longitudinal-trace.json
```

`--case` accepts `A`, `B`, `C`, `D`, `E`, or `ALL`. The trace contains the seed, configuration, generated input timeline, daily observations/decisions, and metrics. Replay regenerates the timeline from the seed and runs the saved timeline through the same production `BaselineManager`, `assess_drift`, `apply_context`, `HeldDriftRegistry`, and `CommunicationEngine`. It compares every decision and metric with the saved trace.

These are synthetic engineering cases. Their labels and useful-interruption windows are set in `synthetic.py` before evaluation. They are not clinical ground truth.

## Comparator rules

Both comparators and AURA use the same configured interruption cooldown. Comparator constants are externalized in `comparator_config.json` and are engineering values, not clinical cutoffs.

- `NAIVE_1_FIXED_THRESHOLD` alerts when a current value differs from the first 14 days' median by a fixed, signal-specific absolute amount. It has no rolling adaptation or context handling.
- `NAIVE_2_ROLLING_ONLY` alerts when a current value differs from the preceding 14-day median by at least the larger of a signal-specific floor and two robust spreads. It has no anchored reference or context handling.
- AURA uses the production anchored/rolling drift, context, held-for-review, and communication modules. The simulator does not copy their policy logic.

## Metric definitions

- **Patient interruptions:** days with an AURA micro-check-in, targeted clarification, or structured assessment, or a comparator alert.
- **Unnecessary notifications:** interruptions outside each case's predeclared useful-interruption window. This is an engineering label, not a clinical judgment.
- **Persistent-drift detection latency:** days from the predeclared onset to first detection of a predeclared changed signal. AURA's Case C detection must be unattenuated; Case D counts descriptive detection even after the benign explanation. `null` means no labelled persistent drift or no detection; the missed count distinguishes these.
- **Missed persistent drift:** labelled case with no matching signal detected by the end of its timeline.
- **Duplicate notifications for explained drift:** interruptions on or after Case D's explanation day.
- **Data coverage:** fraction of days with synthetic wearable observations. All four supported signal values share coverage in these fixtures.
- **STAY_QUIET proportion:** evaluated days without a patient interruption. The first 14 days establish a synthetic reference and are excluded.
- **Clinician-review items:** inspectable held-drift items. No clinician is contacted.

The simulator assumes the explicit synthetic reviewer event accepts the initial anchor. A new covered observation after the wearable gap sets `REESTABLISHING`; the reference is not treated as fully current until a later governed action. Context-to-signal links and the Case D explanation are supplied explicitly by synthetic fixtures. No simulator output diagnoses depression or predicts relapse.
