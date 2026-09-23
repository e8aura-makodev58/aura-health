"""Application adapter: replay typed inputs through the accepted longitudinal engine."""

from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from typing import Any

from aura_longitudinal.baseline import AnchorAction, AnchorCommand, BaselineManager
from aura_longitudinal.communication import CommunicationEngine, CommunicationOutcome
from aura_longitudinal.context import EvidenceEvent, EvidenceKind, HeldDriftRegistry, apply_context
from aura_longitudinal.domain import (
    ActivityObservation, CheckinState, ContextCategory, ContextEvent, MedicationEvent,
    MedicationStatus, ObservationPoint, PatientCheckin, RestingHeartRateObservation,
    Signal, SignalKey, SleepObservation,
)
from aura_longitudinal.drift import assess_drift

from .models import EventType, INTERRUPTIONS


def key_dict(key: SignalKey) -> dict:
    return {"signal": key.signal.value, "source": key.source, "metric": key.metric}


def key_name(key: SignalKey) -> str:
    return key.signal.value + (":" + key.metric if key.metric else "") + "@" + key.source


def key_from(raw: dict) -> SignalKey:
    return SignalKey(Signal(raw["signal"]), raw["source"], raw.get("metric"))


def points_from_payload(payload: dict) -> tuple[ObservationPoint, ...]:
    points = []
    for raw in payload.get("observations", []):
        kind = raw["kind"]
        if kind == "sleep":
            start = datetime.fromisoformat(raw["sleep_start"])
            end = datetime.fromisoformat(raw["sleep_end"])
            observation = SleepObservation(date.fromisoformat(raw["date"]), start, end,
                                           end - start, float(raw["coverage"]),
                                           float(raw.get("data_quality", raw["coverage"])), raw["source"])
        elif kind == "activity":
            observation = ActivityObservation(date.fromisoformat(raw["date"]),
                                              tuple(sorted((name, float(value)) for name, value in raw["metrics"].items())),
                                              float(raw["coverage"]), raw["source"])
        elif kind == "resting_hr":
            observation = RestingHeartRateObservation(date.fromisoformat(raw["date"]),
                                                      float(raw["value"]), float(raw["coverage"]), raw["source"])
        else:
            raise ValueError("unsupported observation kind")
        points.extend(observation.points())
    if not points:
        raise ValueError("wearable event requires an observation")
    return tuple(points)


def context_from(event: dict) -> ContextEvent:
    raw = event["payload"]
    return ContextEvent(datetime.fromisoformat(raw["start"]),
                        datetime.fromisoformat(raw["end"]) if raw.get("end") else None,
                        ContextCategory(raw["category"]),
                        tuple(Signal(value) for value in raw["affected_signals"]),
                        raw["source"], raw.get("explanation"))


def drift_dict(item) -> dict:
    drift = item.drift
    return {
        "key": key_dict(drift.key), "kind": drift.kind.value,
        "current_vs_rolling": drift.current_vs_rolling,
        "rolling_vs_anchor": drift.rolling_vs_anchor,
        "trend_direction": drift.trend_direction.value,
        "trend_magnitude_per_day": drift.trend_magnitude_per_day,
        "coverage": drift.coverage, "confidence": drift.confidence,
        "description": drift.description, "attenuated": item.attenuated,
        "benign_contexts": [c.patient_explanation for c in item.benign_contexts],
        "risk_contexts": [c.patient_explanation for c in item.risk_contexts],
    }


@dataclass
class Projection:
    decision: str
    reason: str
    drifts: list[dict]
    baselines: list[dict]
    held: list[dict]
    active_contexts: list[dict]
    checkins: list[dict]
    medication: list[dict]
    explanation_status: str | None = None

    def public(self) -> dict:
        return {"decision": self.decision, "reason": self.reason, "drifts": self.drifts,
                "baselines": self.baselines, "held": self.held,
                "active_contexts": self.active_contexts,
                "explanation_status": self.explanation_status}


class LongitudinalProjector:
    """No drift or communication policy here: orchestration calls production modules."""

    def __init__(self):
        self.manager = BaselineManager()
        self.communicator = CommunicationEngine()
        self.held = HeldDriftRegistry()
        self.points: dict[SignalKey, list[ObservationPoint]] = {}
        self.contexts: list[tuple[str, ContextEvent]] = []
        self.previous_checkin: PatientCheckin | None = None
        self.last_interruption_at: datetime | None = None
        self.checkins: list[dict] = []
        self.medication: list[dict] = []

    def run(self, events: list[dict], safety_relevant_ids: set[str] | None = None) -> Projection:
        if not events:
            raise ValueError("event stream required")
        safety_relevant_ids = safety_relevant_ids or set()
        current = None
        for event in events:
            current = self._step(event, event["event_id"] in safety_relevant_ids)
        return current

    def _step(self, event: dict, safety_relevant: bool) -> Projection:
        kind = EventType(event["event_type"])
        at = datetime.fromisoformat(event["occurred_at"])
        day = at.date()
        raw = event["payload"]
        current_checkin = None
        medication_event = None
        explanation_status = None
        if kind == EventType.WEARABLE_OBSERVATION:
            for point in points_from_payload(raw):
                self.manager.ingest(point)
                self.points.setdefault(point.key, []).append(point)
        elif kind == EventType.PATIENT_CHECKIN:
            current_checkin = PatientCheckin(at, CheckinState(raw["state"]),
                                             tuple(sorted(raw.get("structured_answers", {}).items())),
                                             tuple(raw.get("context_tags", [])))
            self.checkins.append({"at": event["occurred_at"], "state": current_checkin.state.value})
        elif kind == EventType.MEDICATION_EVENT:
            medication_event = MedicationEvent(datetime.fromisoformat(raw["scheduled_time"]),
                                               at, MedicationStatus(raw["status"]), event["source"])
            self.medication.append({"at": event["occurred_at"], "status": medication_event.status.value})
        elif kind == EventType.CONTEXT_EVENT:
            self.contexts.append((event["event_id"], context_from(event)))
        elif kind == EventType.ANCHOR_COMMAND:
            key = key_from(raw)
            action = AnchorAction(raw["action"])
            start = date.fromisoformat(raw["reference_start"]) if raw.get("reference_start") else date.min
            end = date.fromisoformat(raw["reference_end"]) if raw.get("reference_end") else day
            refs = tuple(point for point in self.points.get(key, []) if start <= point.day <= end)
            self.manager.apply_anchor_command(AnchorCommand(action, key, at, refs, raw.get("reviewed_by")))

        contextualized = []
        baselines = []
        for key in sorted(self.points, key=key_name):
            rolling = self.manager.rolling(key, day)
            anchor = self.manager.anchor(key)
            drift = assess_drift(rolling, anchor, self.manager.config, self.manager.trust_state(key))
            contextualized.append(apply_context(drift, tuple(c for _, c in self.contexts), at))
            baselines.append({
                **key_dict(key), "anchor": ({"center": anchor.center,
                                              "robust_spread": anchor.robust_spread,
                                              "reference_start": anchor.reference_start.isoformat(),
                                              "reference_end": anchor.reference_end.isoformat(),
                                              "version": anchor.version,
                                              "created_at": anchor.created_at.isoformat(),
                                              "reviewed_by": anchor.reviewed_by} if anchor else None),
                "trust_state": self.manager.trust_state(key).value,
                "sensing_state": self.manager.sensing_state(key, day).value,
                "rolling": {"mean": rolling.mean, "median": rolling.median,
                            "robust_spread": rolling.robust_spread,
                            "slope_per_day": rolling.slope_per_day,
                            "coverage_ratio": rolling.coverage_ratio,
                            "sample_count": rolling.sample_count,
                            "sufficient": rolling.sufficient},
            })
        if kind == EventType.CONTEXT_EXPLANATION:
            context_ref = raw["context_event_id"]
            matching = next((context for ref, context in self.contexts if ref == context_ref), None)
            if matching is None or matching.category != ContextCategory.BENIGN_CONTEXT:
                raise ValueError("explanation requires an existing explicitly linked benign context")
            affected = set(raw["affected_signals"])
            if not affected or not affected <= {signal.value for signal in matching.affected_signals}:
                raise ValueError("explanation signals must be explicitly associated with context")
            eligible = tuple(item for item in contextualized if item.drift.key.signal.value in affected)
            before = len(self.held.review_items())
            self.held.hold_explained(eligible, raw["explanation"], at)
            explanation_status = ("EXPLAINED_HELD_FOR_REVIEW" if len(self.held.review_items()) > before
                                  or any(self.held.get_for_drift(item.drift) for item in eligible)
                                  else "PENDING_DRIFT")
        if safety_relevant:
            for item in self.held.review_items():
                self.held.reopen(item.key, EvidenceEvent(EvidenceKind.SAFETY_RELEVANT_EVENT, at))
        decision = self.communicator.decide(tuple(contextualized), self.held, at,
                                            previous_checkin=self.previous_checkin,
                                            current_checkin=current_checkin,
                                            last_interruption_at=self.last_interruption_at,
                                            structured_assessment_changed=(kind == EventType.STRUCTURED_ASSESSMENT_RESPONSE
                                                                           and bool(raw.get("changed"))),
                                            medication_event=medication_event,
                                            review_requested=(kind == EventType.REVIEW_COMMAND
                                                              and raw.get("action") == "PREPARE_REVIEW"))
        if decision.outcome.value in INTERRUPTIONS:
            self.last_interruption_at = at
        if current_checkin:
            self.previous_checkin = current_checkin
        held = []
        for item in self.held.review_items():
            held.append({"key": key_dict(item.key), "detected_drift": asdict(item.detected_drift),
                         "explanation": item.explanation, "held_at": item.held_at.isoformat(),
                         "status": item.status.value,
                         "reopened_at": item.reopened_at.isoformat() if item.reopened_at else None,
                         "reopened_because": item.reopened_because.value if item.reopened_because else None,
                         "clinician_review_item": item.clinician_review_item})
        # asdict retains Enum values; convert only the fixed fields used by persistence.
        for item in held:
            item["detected_drift"] = {"kind": item["detected_drift"]["kind"].value,
                                      "rolling_vs_anchor": item["detected_drift"]["rolling_vs_anchor"],
                                      "description": item["detected_drift"]["description"]}
            item["direction"] = 1 if (item["detected_drift"]["rolling_vs_anchor"] or 0) > 0 else -1
        active_contexts = [{"event_id": ref, "category": context.category.value,
                            "affected_signals": [signal.value for signal in context.affected_signals],
                            "explanation": context.patient_explanation}
                           for ref, context in self.contexts
                           if context.start <= at and (context.end is None or at <= context.end)]
        return Projection(decision.outcome.value, decision.reason,
                          [drift_dict(item) for item in contextualized], baselines,
                          held, active_contexts, list(self.checkins), list(self.medication), explanation_status)
