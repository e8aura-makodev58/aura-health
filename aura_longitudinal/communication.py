"""Burden-aware communication selection, separate from observed change."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from aura_safety import Event, SafetyStore
from aura_safety.domain import Result as SafetyResult

from .config import EngineeringConfig, load_config
from .context import ContextualizedDrift, EvidenceEvent, EvidenceKind, HeldDriftRegistry
from .domain import CheckinState, MedicationEvent, MedicationStatus, PatientCheckin, SignalKey
from .drift import DriftKind


class CommunicationOutcome(str, Enum):
    STAY_QUIET = "STAY_QUIET"
    MICRO_CHECKIN = "MICRO_CHECKIN"
    TARGETED_CLARIFICATION = "TARGETED_CLARIFICATION"
    STRUCTURED_ASSESSMENT = "STRUCTURED_ASSESSMENT"
    CLINICIAN_REVIEW_ITEM = "CLINICIAN_REVIEW_ITEM"
    SAFETY_REVIEW_REQUIRED = "SAFETY_REVIEW_REQUIRED"


@dataclass(frozen=True)
class CommunicationDecision:
    outcome: CommunicationOutcome
    inspectable_signals: tuple[SignalKey, ...]
    clinician_review_signals: tuple[SignalKey, ...]
    reason: str
    safety_result: SafetyResult | None = None


def _worsened(previous: PatientCheckin | None, current: PatientCheckin | None) -> bool:
    if previous is None or current is None:
        return False
    rank = {CheckinState.GOOD: 0, CheckinState.OKAY: 1, CheckinState.ROUGH: 2}
    return rank[current.state] > rank[previous.state]


class CommunicationEngine:
    def __init__(self, config: EngineeringConfig | None = None):
        self.config = config or load_config()

    def decide(self, drifts: tuple[ContextualizedDrift, ...], held: HeldDriftRegistry,
               at: datetime, *, previous_checkin: PatientCheckin | None = None,
               current_checkin: PatientCheckin | None = None,
               last_interruption_at: datetime | None = None,
               assessment_requested: bool = False, review_requested: bool = False,
               structured_assessment_changed: bool = False,
               new_longitudinal_signal: SignalKey | None = None,
               medication_event: MedicationEvent | None = None,
               safety_event: Event | None = None, safety_store: SafetyStore | None = None,
               patient_id: str | None = None) -> CommunicationDecision:
        evidence = None
        if safety_event is not None:
            evidence = EvidenceEvent(EvidenceKind.SAFETY_RELEVANT_EVENT, at)
        elif _worsened(previous_checkin, current_checkin):
            evidence = EvidenceEvent(EvidenceKind.WORSE_CHECKIN, at)
        elif structured_assessment_changed:
            evidence = EvidenceEvent(EvidenceKind.STRUCTURED_ASSESSMENT_CHANGE, at)
        elif medication_event is not None and medication_event.status == MedicationStatus.MISSED:
            evidence = EvidenceEvent(EvidenceKind.MEDICATION_ROUTINE_DISRUPTION, at)
        elif new_longitudinal_signal is not None:
            evidence = EvidenceEvent(EvidenceKind.NEW_LONGITUDINAL_SIGNAL, at,
                                     signal=new_longitudinal_signal)
        if evidence is not None:
            for item in held.review_items():
                held.reopen(item.key, evidence)
        inspectable = tuple(dict.fromkeys(item.drift.key for item in drifts))
        review_items = tuple(item.key for item in held.review_items() if item.clinician_review_item)
        if safety_event is not None:
            if safety_store is None or patient_id is None:
                raise ValueError("safety event requires the authoritative safety writer and patient ID")
            result = safety_store.apply(patient_id, safety_event)
            return CommunicationDecision(CommunicationOutcome.SAFETY_REVIEW_REQUIRED,
                                         inspectable, review_items,
                                         "Delegated safety event to aura_safety", result)
        if review_requested:
            return CommunicationDecision(CommunicationOutcome.CLINICIAN_REVIEW_ITEM,
                                         inspectable, review_items, "Review explicitly requested")
        if assessment_requested:
            return CommunicationDecision(CommunicationOutcome.STRUCTURED_ASSESSMENT,
                                         inspectable, review_items, "Structured assessment explicitly requested")
        if _worsened(previous_checkin, current_checkin):
            return CommunicationDecision(CommunicationOutcome.TARGETED_CLARIFICATION,
                                         inspectable, review_items, "Patient check-in became rougher")
        active = tuple(item for item in drifts
                       if item.drift.kind not in (DriftKind.STABLE, DriftKind.INSUFFICIENT_DATA)
                       and not item.attenuated
                       and not (held.get_for_drift(item.drift)
                                and held.get_for_drift(item.drift).suppress_duplicate_notification))
        if not active:
            return CommunicationDecision(CommunicationOutcome.STAY_QUIET,
                                         inspectable, review_items, "No uncovered change warrants an interruption")
        if last_interruption_at is not None and at - last_interruption_at < timedelta(days=self.config.communication_cooldown_days):
            return CommunicationDecision(CommunicationOutcome.STAY_QUIET,
                                         inspectable, review_items, "Engineering interruption cooldown")
        persistent = tuple(item for item in active if item.drift.kind in (
            DriftKind.PERSISTENT_DRIFT, DriftKind.ROLLING_ANCHOR_DIVERGENCE))
        if not persistent:
            return CommunicationDecision(CommunicationOutcome.STAY_QUIET,
                                         inspectable, review_items, "Transient variation remains inspectable")
        outcome = (CommunicationOutcome.TARGETED_CLARIFICATION
                   if any(item.risk_contexts for item in persistent)
                   else CommunicationOutcome.MICRO_CHECKIN)
        return CommunicationDecision(outcome, inspectable, review_items,
                                     "Descriptive persistent change merits one low-burden question")
