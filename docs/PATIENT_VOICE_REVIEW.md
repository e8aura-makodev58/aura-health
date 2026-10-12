# Patient voice review checkpoint — 2026-10-12

Updated after Claude's `372e4ad` fallback fixes, using the same seed42 production
application fixtures. Latest capture uses prompt v9 with ScriptedAgentProvider;
these remain rule-based fallbacks, not live model outputs.

Pending user sign-off, not an acceptance claim. These are actual **deterministic
fallbacks** from production `AgentService`, using an ephemeral synthetic SQLite
database and `ScriptedAgentProvider`. No live credentials or model prose are stored.
Accepted demo seed 42; the flu uses the explicit three-day MODERATE plan, notes off.
All five responses: `patient_insight`, COMPLETE, generation_used=false, STEP_BUDGET.

| Fixture | Exact fallback recap | Supporting facts |
|---|---|---|
| B | Your sleep time shifted later than your usual since late February. You've marked 7 of the last 7 days as Rough in your check-ins. | f3, f57 |
| B + flu | Your resting heart rate was higher than in your recent records since mid March. You've marked 4 of the last 7 days as Rough in your check-ins. | f38, f110 |
| Stable day | You've marked 7 of the last 7 days as Good in your check-ins. | f47 |
| Wearable gap | You've marked 7 of the last 7 days as Good in your check-ins. There was a gap in your sleep time readings on 12 Feb. | f51, f11 |
| Check-ins only | You've marked 3 of the last 7 days as Good in your check-ins. | f6 |

The check-in-only patient was created through `PatientEventService`, with resolved
safety fixtures for the three check-in events and zero wearable observations.
Scenario labels stayed in evaluation; domain events contained observable inputs only.

## Review points

- The gap recap now cites the recorded signal-specific gap, without claiming all
  wearable channels stopped or interpreting missingness as health.
- The flu fallback now leads a recent heart-rate change rather than the older sleep
  finding. The comparator remains recent records, not the anchored usual pattern.
- Five matching live v9 outputs are not yet captured. Deployment and one fixed
  reliability trial await authorization; unchanged quotas still apply.
- User voice acceptance, live-sample comparison and final design lock remain pending.
