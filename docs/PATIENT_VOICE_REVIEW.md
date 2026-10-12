# Patient voice review checkpoint — 2026-10-12

Pending user sign-off, not an acceptance claim. These are actual **deterministic
fallbacks** from production `AgentService`, using an ephemeral synthetic SQLite
database and `ScriptedAgentProvider`. No live credentials or model prose are stored.
Accepted demo seed 42; the flu uses the explicit three-day MODERATE plan, notes off.
All five responses: `patient_insight`, COMPLETE, generation_used=false, STEP_BUDGET.

| Fixture | Exact fallback recap | Supporting facts |
|---|---|---|
| B | Your sleep time shifted later than your usual since late February. You've marked 7 of the last 7 days as Rough in your check-ins. | f3, f57 |
| B + flu | Your sleep time shifted later than your usual since late February. You've marked 4 of the last 7 days as Rough in your check-ins. | f3, f110 |
| Stable day | You've marked 7 of the last 7 days as Good in your check-ins. | f47 |
| Wearable gap | You've marked 7 of the last 7 days as Good in your check-ins. | f51 |
| Check-ins only | You've marked 3 of the last 7 days as Good in your check-ins. | f6 |

The check-in-only patient was created through `PatientEventService`, with resolved
safety fixtures for the three check-in events and zero wearable observations.
Scenario labels stayed in evaluation; domain events contained observable inputs only.

## Review points

- The gap recap cites real check-ins but does not describe the gap. Missingness remains
  available in sensing state and source data; whether the recap should foreground it
  remains a presentation review item.
- The flu fallback keeps the older sleep finding rather than foregrounding the newest
  physiological readings. It is factual, but is not a comprehensive summary.
- Five matching live outputs are not yet captured. Reliability testing takes precedence
  over concurrent paid sampling so its unchanged shared quotas remain meaningful.
- User voice acceptance, live-sample comparison and final design lock remain pending.
