"""Application-path synthetic fixtures A–F; hidden labels never enter the service."""

import argparse
import calendar
from datetime import date, datetime, time, timedelta, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from aura_longitudinal.synthetic import generate_case

from .models import ApplicationEvent, EventType, INTERRUPTIONS
from .persistence import SQLiteRepositoryFactory
from .safety import FixtureSafetyGate
from .service import PatientEventService


def _at(day: date, hour: int = 12) -> datetime:
    return datetime.combine(day, time(hour, 0), tzinfo=timezone.utc)


def fixture_treatment(start: date, latest: date) -> dict:
    """Explicit synthetic label/history, never an inferred treatment instruction."""
    def earlier(months):
        year, month = divmod(start.year * 12 + start.month - 1 - months, 12)
        return date(year, month + 1, min(start.day, calendar.monthrange(year, month + 1)[1])).isoformat()
    return {"medication_name": "Sertraline", "medication_schedule": "50 mg, once each morning",
            "regimen_start": earlier(9), "stable_since": earlier(6), "review_cadence": "every 3 months",
            "next_review": (latest + timedelta(days=13)).isoformat(), "supply_days": 28,
            "last_refill": (latest - timedelta(days=20)).isoformat()}


def run_case(case: str, seed: int, db_path: str | Path, *, through_day: int = 69,
             patient_id: str | None = None, event_prefix: str | None = None,
             include_explanation: bool = True) -> dict:
    """Optional checkpoints are demo tooling, not inputs to either decision engine."""
    if not 13 <= through_day <= 69:
        raise ValueError("checkpoint must include the reference period")
    timeline = generate_case(case if case in "ABCDE" else "A", seed)
    factory = SQLiteRepositoryFactory(db_path)
    factory.initialize()
    proposals: dict[str, tuple[tuple[str, str], ...]] = {}
    service = PatientEventService(factory, safety_gate=FixtureSafetyGate(proposals))
    patient_id = patient_id or f"synthetic-{case}-{seed}"
    prefix = event_prefix or f"{case}-{seed}"
    service.create_patient(patient_id=patient_id, display_name=f"Synthetic case {case}",
                           age=35, timezone_name="UTC",
                           treatment=fixture_treatment(date.fromisoformat(timeline["start_date"]),
                                                       date.fromisoformat(timeline["days"][through_day]["date"])),
                           consents=[{"consent_type": "WEARABLE", "granted": True, "version": "fixture-v1"}],
                           wearable_sources=[{"source_id": "synthetic_wearable", "source_type": "FIXTURE"}],
                           created_at=_at(date.fromisoformat(timeline["start_date"])))
    results = []
    day_decisions: dict[int, list[str]] = {}
    contexts_by_day: dict[int, list[dict]] = {}
    for index, context in enumerate(timeline["contexts"]):
        contexts_by_day.setdefault(context["start_day"], []).append({**context, "fixture_context_index": index})

    def submit(index: int, kind: EventType, payload: dict, suffix: str,
               *, tier: str | None = "NORMAL", hour: int = 12):
        day = date.fromisoformat(timeline["days"][index]["date"])
        event_id = f"{prefix}-{index}-{suffix}"
        if tier is not None:
            proposals[event_id] = () if tier == "NORMAL" else (("D2", tier),)
        event = ApplicationEvent(event_id, patient_id, kind, _at(day, hour), _at(day, hour),
                                 "synthetic_wearable" if kind == EventType.WEARABLE_OBSERVATION else "synthetic_patient",
                                 payload, event_id, event_id)
        result = service.command_anchor(event) if kind == EventType.ANCHOR_COMMAND else service.process(event)
        if index >= 14:
            day_decisions.setdefault(index, []).append(result.communication_decision)
        results.append({"day": index, "event_id": event_id, "event_type": kind.value,
                        "decision": result.communication_decision,
                        "safety": result.safety["state"] if result.safety else None})
        return result

    for raw in timeline["days"]:
        index = raw["index"]
        if index > through_day:
            break
        day = date.fromisoformat(raw["date"])
        for context in contexts_by_day.get(index, []):
            start = date.fromisoformat(timeline["start_date"]) + timedelta(days=context["start_day"])
            end = date.fromisoformat(timeline["start_date"]) + timedelta(days=context["end_day"] + 1)
            submit(index, EventType.CONTEXT_EVENT,
                   {"start": _at(start, 0).isoformat(), "end": _at(end, 0).isoformat(),
                    "category": context["category"], "affected_signals": context["affected_signals"],
                    "source": context["source"], "explanation": context["explanation"]},
                   f"context-{context['fixture_context_index']}", hour=0)
        if raw["sleep_start"] is not None:
            start = datetime.fromisoformat(raw["sleep_start"])
            end = start + timedelta(hours=raw["duration_hours"])
            observations = [
                {"kind": "sleep", "date": raw["date"], "sleep_start": start.isoformat(),
                 "sleep_end": end.isoformat(), "coverage": raw["coverage"],
                 "source": "synthetic_wearable"},
                {"kind": "activity", "date": raw["date"], "metrics": {"steps": raw["activity_steps"]},
                 "coverage": raw["coverage"], "source": "synthetic_wearable"},
                {"kind": "resting_hr", "date": raw["date"], "value": raw["resting_hr"],
                 "coverage": raw["coverage"], "source": "synthetic_wearable"},
            ]
            submit(index, EventType.WEARABLE_OBSERVATION, {"observations": observations}, "wearable", tier=None)
        if index == 13:
            for signal, metric in (("SLEEP_MIDPOINT", None), ("SLEEP_DURATION", None),
                                   ("ACTIVITY", "steps"), ("RESTING_HEART_RATE", None)):
                payload = {"signal": signal, "source": "synthetic_wearable", "metric": metric,
                           "reference_start": timeline["days"][0]["date"],
                           "reference_end": raw["date"]}
                submit(index, EventType.ANCHOR_COMMAND,
                       {**payload, "action": "CREATE_PROVISIONAL_ANCHOR"}, f"anchor-{signal}", tier=None)
                submit(index, EventType.ANCHOR_COMMAND,
                       {**payload, "action": "TRUST_ANCHOR", "reviewed_by": "synthetic-review-event-only"},
                       f"trust-{signal}", tier=None)
        if case == "D" and index == 30 and include_explanation:
            context_id = f"{prefix}-30-context-0"
            submit(index, EventType.CONTEXT_EXPLANATION,
                   {"context_event_id": context_id, "explanation": "new stable work schedule",
                    "affected_signals": ["SLEEP_MIDPOINT", "ACTIVITY"]}, "explanation")
        submit(index, EventType.PATIENT_CHECKIN, {"state": raw["checkin"]}, "checkin")

    if case == "F" and through_day == 69:
        result = submit(69, EventType.PATIENT_FREE_TEXT, {"text": "fixture safety concern"},
                        "safety-text", tier="CLARIFY", hour=18)
        assert result.communication_decision == "SAFETY_REVIEW_REQUIRED"
    status = service.status(patient_id)
    snapshot = service.review_snapshot(patient_id)
    app_timeline = service.timeline(patient_id)
    interruptions = sum(any(decision in INTERRUPTIONS for decision in decisions)
                        for decisions in day_decisions.values())
    return {"case": case, "seed": seed, "patient_id": patient_id,
            "patient_interruptions": interruptions,
            "latest_decision": results[-1]["decision"],
            "signals": status["signals"], "held": status["held_for_review"],
            "review_items": len(snapshot["unresolved_items"]),
            "safety": status["safety"], "timeline_entries": len(app_timeline),
            "decisions": results,
            "not_shared": snapshot["share_status"] == "NOT_SHARED" and not snapshot["automatically_sent"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run synthetic A–F through application service")
    parser.add_argument("--case", choices=(*"ABCDEF", "ALL"), default="ALL")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--db-dir", type=Path)
    parser.add_argument("--save", type=Path)
    args = parser.parse_args(argv)
    cases = tuple("ABCDEF") if args.case == "ALL" else (args.case,)
    if args.db_dir:
        args.db_dir.mkdir(parents=True, exist_ok=True)
        results = {case: run_case(case, args.seed, args.db_dir / f"case-{case}.sqlite3") for case in cases}
    else:
        with TemporaryDirectory() as temporary:
            results = {case: run_case(case, args.seed, Path(temporary) / f"case-{case}.sqlite3") for case in cases}
    output = {case: {key: value for key, value in record.items() if key not in {"signals", "held", "decisions"}}
              for case, record in results.items()}
    print(json.dumps(output, indent=2))
    if args.save:
        args.save.write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
    main()
