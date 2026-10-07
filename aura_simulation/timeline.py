"""Fixed-seed numeric fixtures; no production policy, latent-truth reasoning or ML."""

from copy import deepcopy
from datetime import date, datetime, timedelta

from aura_longitudinal.synthetic import generate_case
from .agent import ScenarioPlan


def generate(plan: ScenarioPlan):
    timeline = deepcopy(generate_case(plan.case if plan.case != "F" else "A", plan.seed))
    start = date.fromisoformat(timeline["start_date"])
    rows = []
    for index in range(plan.days):
        # Longer-than-70-day extension deliberately repeats the last accepted daily
        # fixture values at new dates. Not a realism/population-validation claim.
        source = deepcopy(timeline["days"][min(index,69)])
        target = start + timedelta(days=index)
        shift = target - date.fromisoformat(source["date"])
        source.update(index=index, date=target.isoformat())
        if source["sleep_start"]:
            source["sleep_start"] = (datetime.fromisoformat(source["sleep_start"]) + shift).isoformat()
        for change in plan.changes:
            if change["start_day"] <= index <= change["end_day"] and source["sleep_start"]:
                delta = change["delta"] + (index-change["start_day"]) * change["delta_per_day"]
                if change["signal"] == "SLEEP_MIDPOINT":
                    source["sleep_start"] = (datetime.fromisoformat(source["sleep_start"]) + timedelta(minutes=delta)).isoformat()
                elif change["signal"] == "SLEEP_DURATION":
                    source["duration_hours"] += delta
                    if source["duration_hours"] <= 0:
                        raise ValueError("Synthetic sleep interval must remain positive")
                elif change["signal"] == "ACTIVITY":
                    source["activity_steps"] = max(0, source["activity_steps"] + delta)
                else:
                    source["resting_hr"] += delta
        for checkin in plan.checkins:
            if checkin["start_day"] <= index <= checkin["end_day"]:
                source["checkin"] = checkin["state"]
        if any(gap["start_day"] <= index <= gap["end_day"] for gap in plan.gaps):
            source.update(sleep_start=None,duration_hours=None,activity_steps=None,resting_hr=None,coverage=0)
        rows.append(source)
    timeline["days"] = rows
    timeline["plan"] = plan.data()
    timeline["evaluation"] = {"scenario_id":timeline.pop("case"), "latent_truth":timeline.pop("truth"),
                              "expected_outcome":"engineering evaluation only"}
    return timeline
