"""Seeded synthetic observations and predeclared engineering scenario labels."""

from datetime import date, datetime, timedelta, timezone
import random

from .domain import Signal


START = date(2026, 1, 1)
CASE_NAMES = {
    "A": "physical_illness_false_alarm",
    "B": "slow_drift",
    "C": "illness_plus_independent_change",
    "D": "explained_benign_lifestyle_shift",
    "E": "wearable_gap_and_return",
}


def generate_case(case: str, seed: int) -> dict:
    if case not in CASE_NAMES:
        raise ValueError("case must be A, B, C, D, or E")
    rng = random.Random(seed * 101 + "ABCDE".index(case))
    days = []
    for index in range(70):
        day = START + timedelta(days=index)
        sleep_shift = 0.0
        duration_change = 0.0
        activity_change = 0.0
        heart_change = 0.0
        checkin = "Good"
        if case == "A" and 28 <= index <= 34:
            sleep_shift, duration_change, activity_change, heart_change = 60, -1.5, -2200, 8
        if case == "B" and index >= 21:
            sleep_shift = min(200, 6 * (index - 20))
            activity_change = -min(2100, 60 * (index - 20))
            checkin = "Rough" if index >= 50 else "Okay" if index >= 35 else "Good"
        if case == "C":
            if 28 <= index <= 34:
                duration_change, activity_change, heart_change = -1.5, -2200, 8
            if index >= 28:
                sleep_shift = 185
                activity_change -= 1500
                checkin = "Rough" if index >= 40 else "Okay"
        if case == "D" and index >= 21:
            sleep_shift, activity_change = 190, -1200
        missing = case == "E" and 28 <= index <= 54
        if missing:
            sleep_start = None
            duration_hours = None
            steps = None
            heart_rate = None
        else:
            jitter = rng.gauss(0, 4)
            start = datetime(day.year, day.month, day.day, 20, 15,
                             tzinfo=timezone.utc) + timedelta(minutes=sleep_shift + jitter)
            sleep_start = start.isoformat()
            duration_hours = round(8 + duration_change + rng.gauss(0, 0.08), 4)
            steps = round(max(0, 7000 + activity_change + rng.gauss(0, 120)), 2)
            heart_rate = round(62 + heart_change + rng.gauss(0, 0.6), 2)
        days.append({"index": index, "date": day.isoformat(),
                     "sleep_start": sleep_start, "duration_hours": duration_hours,
                     "activity_steps": steps, "resting_hr": heart_rate,
                     "checkin": checkin, "coverage": 0.0 if missing else 1.0})

    contexts = []
    if case in ("A", "C"):
        affected = [signal.value for signal in (
            Signal.RESTING_HEART_RATE, Signal.SLEEP_DURATION, Signal.ACTIVITY)]
        if case == "A":
            affected.append(Signal.SLEEP_MIDPOINT.value)
        contexts.append({"start_day": 28, "end_day": 42,
                         "category": "BENIGN_CONTEXT", "affected_signals": affected,
                         "source": "synthetic_patient", "explanation": "acute physical illness and recovery"})
    if case == "D":
        contexts.append({"start_day": 30, "end_day": 69,
                         "category": "BENIGN_CONTEXT",
                         "affected_signals": [Signal.SLEEP_MIDPOINT.value, Signal.ACTIVITY.value],
                         "source": "synthetic_patient", "explanation": "new stable work schedule"})
    # These labels are set before running any policy; they are engineering
    # scenario truth, not a patient diagnosis or clinical outcome.
    truth = {
        "persistent_start_day": {"A": None, "B": 35, "C": 35, "D": 29, "E": None}[case],
        "persistent_signals": {
            "A": [], "B": [Signal.SLEEP_MIDPOINT.value, "ACTIVITY:steps"],
            "C": [Signal.SLEEP_MIDPOINT.value, "ACTIVITY:steps"],
            "D": [Signal.SLEEP_MIDPOINT.value, "ACTIVITY:steps"], "E": [],
        }[case],
        "useful_notification_ranges": {"A": [], "B": [[35, 69]],
                                        "C": [[28, 69]], "D": [[21, 29]],
                                        "E": []}[case],
        "explained_from_day": 30 if case == "D" else None,
    }
    return {"case": case, "name": CASE_NAMES[case], "seed": seed,
            "start_date": START.isoformat(), "days": days,
            "contexts": contexts, "truth": truth,
            "data_label": "synthetic engineering fixture; not clinical ground truth"}
