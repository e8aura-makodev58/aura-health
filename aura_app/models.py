"""Application records; none encode diagnoses or treatment advice."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class EventType(str, Enum):
    WEARABLE_OBSERVATION = "WEARABLE_OBSERVATION"
    PATIENT_CHECKIN = "PATIENT_CHECKIN"
    MEDICATION_EVENT = "MEDICATION_EVENT"
    CONTEXT_EVENT = "CONTEXT_EVENT"
    CONTEXT_EXPLANATION = "CONTEXT_EXPLANATION"
    STRUCTURED_ASSESSMENT_RESPONSE = "STRUCTURED_ASSESSMENT_RESPONSE"
    PATIENT_FREE_TEXT = "PATIENT_FREE_TEXT"
    ANCHOR_COMMAND = "ANCHOR_COMMAND"
    REVIEW_COMMAND = "REVIEW_COMMAND"


@dataclass(frozen=True)
class PatientProfile:
    patient_id: str
    display_name: str
    age: int
    timezone: str
    onboarding_status: str
    created_at: datetime
    active: bool = True


@dataclass(frozen=True)
class TreatmentContext:
    patient_id: str
    medication_name: str | None = None
    medication_schedule: str | None = None
    regimen_start: str | None = None
    stable_since: str | None = None
    treating_clinician_ref: str | None = None
    review_cadence: str | None = None
    next_review: str | None = None
    treatment_notes: str | None = None


@dataclass(frozen=True)
class WearableSource:
    patient_id: str
    source_id: str
    source_type: str
    connected: bool
    last_seen: datetime | None
    consent_status: str


@dataclass(frozen=True)
class ConsentRecord:
    patient_id: str
    consent_type: str
    granted: bool
    timestamp: datetime
    version: str


@dataclass(frozen=True)
class ContextExplanation:
    patient_id: str
    relevant_drift_ref: str | None
    explanation: str
    affected_signals: tuple[str, ...]
    created_at: datetime
    status: str


@dataclass(frozen=True)
class ClinicianReviewItem:
    patient_id: str
    source_ref: str
    summary: str
    created_at: datetime
    status: str = "OPEN"
    patient_visible: bool = True
    share_status: str = "NOT_SHARED"


@dataclass(frozen=True)
class ApplicationEvent:
    event_id: str
    patient_id: str
    event_type: EventType
    occurred_at: datetime
    received_at: datetime
    source: str
    payload: dict[str, Any]
    correlation_id: str
    idempotency_key: str


@dataclass(frozen=True)
class ApplicationResult:
    event_id: str
    patient_id: str
    communication_decision: str
    safety: dict[str, Any] | None
    longitudinal: dict[str, Any]
    review_item_ids: tuple[str, ...] = ()
    idempotent_replay: bool = False
    conversation_status: str | None = None


class AppError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.status = status


INTERRUPTIONS = frozenset({"MICRO_CHECKIN", "TARGETED_CLARIFICATION", "STRUCTURED_ASSESSMENT"})
