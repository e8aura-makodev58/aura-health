"""Run synthetic timelines through production longitudinal modules and comparators."""

from datetime import date, datetime, time, timedelta, timezone
from statistics import mean, median

from .baseline import AnchorAction, AnchorCommand, BaselineManager
from .communication import CommunicationEngine, CommunicationOutcome
from .comparators import (
    NAIVE_1_FIXED_THRESHOLD, NAIVE_2_ROLLING_ONLY, ComparatorConfig,
    fixed_threshold_alerts, key_name, rolling_only_alerts,
)
from .config import EngineeringConfig
from .context import HeldDriftRegistry, apply_context
from .domain import (
    ActivityObservation, CheckinState, ContextCategory, ContextEvent,
    PatientCheckin, RestingHeartRateObservation, Signal, SignalKey,
    SleepObservation,
)
from .drift import DriftKind, assess_drift


AURA = "AURA"
METHODS = (AURA, NAIVE_1_FIXED_THRESHOLD, NAIVE_2_ROLLING_ONLY)
INTERRUPTIONS = {CommunicationOutcome.MICRO_CHECKIN,
                 CommunicationOutcome.TARGETED_CLARIFICATION,
                 CommunicationOutcome.STRUCTURED_ASSESSMENT}


def _time(day: date) -> datetime:
    return datetime.combine(day, time.min, tzinfo=timezone.utc)


def _observations(raw: dict):
    if raw["sleep_start"] is None:
        return ()
    day = date.fromisoformat(raw["date"])
    sleep_start = datetime.fromisoformat(raw["sleep_start"])
    duration = timedelta(hours=raw["duration_hours"])
    return (
        SleepObservation(day, sleep_start, sleep_start + duration, duration,
                         raw["coverage"], raw["coverage"], "synthetic_wearable"),
        ActivityObservation(day, (("steps", raw["activity_steps"]),),
                            raw["coverage"], "synthetic_wearable"),
        RestingHeartRateObservation(day, raw["resting_hr"], raw["coverage"],
                                    "synthetic_wearable"),
    )


def _contexts(timeline: dict) -> tuple[ContextEvent, ...]:
    start = date.fromisoformat(timeline["start_date"])
    return tuple(ContextEvent(
        _time(start + timedelta(days=raw["start_day"])),
        _time(start + timedelta(days=raw["end_day"] + 1)) - timedelta(microseconds=1),
        ContextCategory(raw["category"]),
        tuple(Signal(signal) for signal in raw["affected_signals"]),
        raw["source"], raw["explanation"],
    ) for raw in timeline["contexts"])


def _useful(day_index: int, truth: dict) -> bool:
    return any(start <= day_index <= end for start, end in truth["useful_notification_ranges"])


def _metric_record(method: str, events: list[dict], timeline: dict,
                   detected_day: int | None, review_count: int) -> dict:
    truth = timeline["truth"]
    start = truth["persistent_start_day"]
    interruptions = sum(event["decisions"][method]["interrupt"] for event in events)
    unnecessary = sum(event["decisions"][method]["interrupt"] and not _useful(event["index"], truth)
                      for event in events)
    explained_from = truth["explained_from_day"]
    duplicates = sum(event["decisions"][method]["interrupt"] and explained_from is not None
                     and event["index"] >= explained_from for event in events)
    quiet = sum(not event["decisions"][method]["interrupt"] for event in events)
    coverage = sum(day["coverage"] for day in timeline["days"]) / len(timeline["days"])
    return {
        "patient_interruptions": interruptions,
        "unnecessary_notifications": unnecessary,
        "persistent_drift_detection_latency_days": (
            max(0, detected_day - start) if start is not None and detected_day is not None else None),
        "missed_persistent_drift": int(start is not None and detected_day is None),
        "duplicate_notifications_for_explained_drift": duplicates,
        "data_coverage": round(coverage, 4),
        "stay_quiet_proportion": round(quiet / len(events), 4),
        "clinician_review_items": review_count,
    }


def run_timeline(timeline: dict, engineering: EngineeringConfig,
                 comparator: ComparatorConfig) -> dict:
    manager = BaselineManager(engineering)
    communicator = CommunicationEngine(engineering)
    held = HeldDriftRegistry()
    contexts = _contexts(timeline)
    reference_points: dict[SignalKey, list] = {}
    comparator_history: dict[SignalKey, list[tuple[int, float]]] = {}
    fixed_reference: dict[SignalKey, float] = {}
    last_interruption: dict[str, datetime | None] = {method: None for method in METHODS}
    detected_day: dict[str, int | None] = {method: None for method in METHODS}
    trace = []
    previous_checkin = None
    for raw in timeline["days"]:
        index = raw["index"]
        day = date.fromisoformat(raw["date"])
        at = _time(day)
        current = PatientCheckin(at, CheckinState(raw["checkin"]))
        observations = _observations(raw)
        current_points = tuple(point for observation in observations for point in observation.points())
        current_values = {point.key: point.value for point in current_points}
        for point in current_points:
            manager.ingest(point)
            if index < 14:
                reference_points.setdefault(point.key, []).append(point)
        if index == 13:
            for key, points in reference_points.items():
                manager.apply_anchor_command(AnchorCommand(
                    AnchorAction.CREATE_PROVISIONAL_ANCHOR, key, at, tuple(points)))
                manager.apply_anchor_command(AnchorCommand(
                    AnchorAction.TRUST_ANCHOR, key, at,
                    reviewed_by="synthetic-review-event-only"))
                fixed_reference[key] = median(point.value for point in points)
        if index < 14:
            for key, value in current_values.items():
                comparator_history.setdefault(key, []).append((index, value))
            previous_checkin = current
            continue

        contextualized = []
        signals = {}
        for key in reference_points:
            rolling = manager.rolling(key, day)
            drift = assess_drift(rolling, manager.anchor(key), engineering,
                                 manager.trust_state(key))
            context = apply_context(drift, contexts, at)
            contextualized.append(context)
            signals[key_name(key)] = {
                "kind": drift.kind.value,
                "current_vs_rolling": drift.current_vs_rolling,
                "rolling_vs_anchor": drift.rolling_vs_anchor,
                "trend_direction": drift.trend_direction.value,
                "coverage": drift.coverage,
                "confidence": drift.confidence,
                "attenuated": context.attenuated,
                "sensing_state": manager.sensing_state(key, day).value,
                "baseline_trust_state": manager.trust_state(key).value,
                "anchor_center": manager.anchor(key).center,
                "description": drift.description,
            }
        explanation_day = timeline["truth"]["explained_from_day"]
        if explanation_day is not None and index >= explanation_day:
            held.hold_explained(tuple(contextualized),
                                "synthetic patient explanation: new stable work schedule", at)

        aura = communicator.decide(tuple(contextualized), held, at,
                                   previous_checkin=previous_checkin,
                                   current_checkin=current,
                                   last_interruption_at=last_interruption[AURA])
        aura_interrupt = aura.outcome in INTERRUPTIONS
        if aura_interrupt:
            last_interruption[AURA] = at
        fixed_alerts = fixed_threshold_alerts(current_values, fixed_reference, comparator)
        rolling_alerts = rolling_only_alerts(current_values, comparator_history,
                                             index, engineering, comparator)
        decisions = {AURA: {"outcome": aura.outcome.value,
                            "interrupt": aura_interrupt,
                            "signals": [key_name(key) for key in aura.inspectable_signals]},
                     NAIVE_1_FIXED_THRESHOLD: {}, NAIVE_2_ROLLING_ONLY: {}}
        for method, alerts in ((NAIVE_1_FIXED_THRESHOLD, fixed_alerts),
                               (NAIVE_2_ROLLING_ONLY, rolling_alerts)):
            previous = last_interruption[method]
            allowed = previous is None or at - previous >= timedelta(days=engineering.communication_cooldown_days)
            interrupt = bool(alerts) and allowed
            if interrupt:
                last_interruption[method] = at
            decisions[method] = {"outcome": "ALERT" if interrupt else "STAY_QUIET",
                                 "interrupt": interrupt,
                                 "signals": [key_name(key) for key in alerts]}
        persistent_start = timeline["truth"]["persistent_start_day"]
        if persistent_start is not None and index >= persistent_start:
            if detected_day[AURA] is None and any(item.drift.kind in (
                DriftKind.PERSISTENT_DRIFT, DriftKind.ROLLING_ANCHOR_DIVERGENCE
            ) and key_name(item.drift.key) in timeline["truth"]["persistent_signals"]
                and (timeline["case"] == "D" or not item.attenuated)
                  for item in contextualized):
                detected_day[AURA] = index
            for method, alerts in ((NAIVE_1_FIXED_THRESHOLD, fixed_alerts),
                                   (NAIVE_2_ROLLING_ONLY, rolling_alerts)):
                if detected_day[method] is None and any(
                    key_name(key) in timeline["truth"]["persistent_signals"] for key in alerts
                ):
                    detected_day[method] = index
        trace.append({"index": index, "date": raw["date"], "checkin": raw["checkin"],
                      "signals": signals, "decisions": decisions,
                      "held_review_items": [key_name(item.key) for item in held.review_items()],
                      "held_statuses": {key_name(item.key): item.status.value
                                        for item in held.review_items()},
                      "active_contexts": [context.patient_explanation for context in contexts
                                          if context.start <= at <= context.end]})
        for key, value in current_values.items():
            comparator_history.setdefault(key, []).append((index, value))
        previous_checkin = current

    metrics = {method: _metric_record(method, trace, timeline, detected_day[method],
                                      len(held.review_items()) if method == AURA else 0)
               for method in METHODS}
    return {"case": timeline["case"], "seed": timeline["seed"],
            "trace": trace, "metrics": metrics,
            "reference_centers": {key_name(key): anchor.center
                                  for key, anchor in ((key, manager.anchor(key))
                                                      for key in reference_points)}}


def aggregate(results: dict[str, dict]) -> dict[str, dict]:
    summary = {}
    for method in METHODS:
        rows = [result["metrics"][method] for result in results.values()]
        latencies = [row["persistent_drift_detection_latency_days"] for row in rows
                     if row["persistent_drift_detection_latency_days"] is not None]
        summary[method] = {
            "patient_interruptions": sum(row["patient_interruptions"] for row in rows),
            "unnecessary_notifications": sum(row["unnecessary_notifications"] for row in rows),
            "persistent_drift_detection_latency_days": round(mean(latencies), 2) if latencies else None,
            "missed_persistent_drift": sum(row["missed_persistent_drift"] for row in rows),
            "duplicate_notifications_for_explained_drift": sum(
                row["duplicate_notifications_for_explained_drift"] for row in rows),
            "data_coverage": round(mean(row["data_coverage"] for row in rows), 4),
            "stay_quiet_proportion": round(mean(row["stay_quiet_proportion"] for row in rows), 4),
            "clinician_review_items": sum(row["clinician_review_items"] for row in rows),
        }
    return summary
