"""State and event vocabulary from safety-machine v1.2."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum, IntEnum


class Mode(IntEnum):
    NORMAL = 0
    CLARIFY = 1
    ELEVATED = 2
    URGENT = 3
    IMMEDIATE = 4


class Status(str, Enum):
    NONE = "NONE"
    OPEN = "OPEN"
    RECHECK_REQUIRED = "RECHECK_REQUIRED"
    DROPOUT = "DROPOUT"
    CLOSED = "CLOSED"


class DropoutReason(str, Enum):
    DURING_URGENT = "DURING_URGENT"
    DURING_IMMEDIATE = "DURING_IMMEDIATE"
    RECHECK_NOT_COMPLETED = "RECHECK_NOT_COMPLETED"


class FlagName(str, Enum):
    RECHECK_PASSED = "RECHECK_PASSED"
    T2_FOLLOWUP_INCOMPLETE = "T2_FOLLOWUP_INCOMPLETE"
    PRIOR_UNRESOLVED_HIGH_TIER = "PRIOR_UNRESOLVED_HIGH_TIER"
    RECHECK_OVERDUE = "RECHECK_OVERDUE"
    REPEATED_ROUGH_CHECKINS = "REPEATED_ROUGH_CHECKINS"
    RECENT_SAFETY_DROPOUT = "RECENT_SAFETY_DROPOUT"
    RAPID_PHQ_CHANGE = "RAPID_PHQ_CHANGE"
    RECENT_HIGH_TIER_EPISODE = "RECENT_HIGH_TIER_EPISODE"
    RECONTACT_COUNT = "RECONTACT_COUNT"


class EventKind(str, Enum):
    FREE_TEXT_RECEIVED = "FREE_TEXT_RECEIVED"
    STRUCTURED_RESPONSE_RECEIVED = "STRUCTURED_RESPONSE_RECEIVED"
    CHECKIN_TAP_RECEIVED = "CHECKIN_TAP_RECEIVED"
    MEDICATION_EVENT_RECEIVED = "MEDICATION_EVENT_RECEIVED"
    PATIENT_RETURNED = "PATIENT_RETURNED"
    DETECTORS_COMPLETE = "DETECTORS_COMPLETE"
    DETECTOR_TIMEOUT = "DETECTOR_TIMEOUT"
    DETECTOR_ERROR = "DETECTOR_ERROR"
    POLICY_ERROR = "POLICY_ERROR"
    STATE_INTEGRITY_ERROR = "STATE_INTEGRITY_ERROR"
    OUTPUT_VALIDATION_FAILED = "OUTPUT_VALIDATION_FAILED"
    CLIENT_RECONNECTED = "CLIENT_RECONNECTED"
    LATE_DETECTOR_RESULT = "LATE_DETECTOR_RESULT"
    RECONTACT_DUE = "RECONTACT_DUE"
    RECHECK_DUE = "RECHECK_DUE"
    FOLLOWUP_WINDOW_EXPIRED = "FOLLOWUP_WINDOW_EXPIRED"
    EPISODE_ARCHIVE_DUE = "EPISODE_ARCHIVE_DUE"
    RESOURCE_REFRESH_DUE = "RESOURCE_REFRESH_DUE"
    FLAG_EXPIRY_DUE = "FLAG_EXPIRY_DUE"
    LIVE_RESOURCES_AVAILABLE = "LIVE_RESOURCES_AVAILABLE"
    LIVE_RESOURCES_UNAVAILABLE = "LIVE_RESOURCES_UNAVAILABLE"
    RESOURCE_INTEGRITY_FAILED = "RESOURCE_INTEGRITY_FAILED"
    CLARIFICATION_CLEARED = "CLARIFICATION_CLEARED"
    ELEVATION_RESOLVED = "ELEVATION_RESOLVED"
    URGENT_DEESCALATION_APPROVED = "URGENT_DEESCALATION_APPROVED"
    IMMEDIATE_DEESCALATION_APPROVED = "IMMEDIATE_DEESCALATION_APPROVED"
    DROPOUT_REENTRY = "DROPOUT_REENTRY"
    RECHECK_PASSED = "RECHECK_PASSED"
    RECHECK_FAILED = "RECHECK_FAILED"
    EPISODE_CLOSE_APPROVED = "EPISODE_CLOSE_APPROVED"
    POLICY_FLAG_SET = "POLICY_FLAG_SET"


class Outcome(str, Enum):
    TRANSITION = "TRANSITION"
    NO_STATE_CHANGE = "NO_STATE_CHANGE"
    REJECT_EVENT = "REJECT_EVENT"
    SET_DEGRADED = "SET_DEGRADED"
    DEFER_EVENT = "DEFER_EVENT"


@dataclass(frozen=True)
class PolicyFlag:
    name: FlagName
    source_episode_id: str | None
    set_at: datetime
    expires_at: datetime | None = None
    metadata: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class SafetyState:
    interaction_mode: Mode = Mode.NORMAL
    episode_status: Status = Status.NONE
    episode_peak_tier: Mode = Mode.NORMAL
    flags: tuple[PolicyFlag, ...] = ()
    dropout_reason: DropoutReason | None = None
    degraded: bool = False
    degraded_causes: frozenset[str] = frozenset()
    sequence: int = 0
    episode_id: str | None = None


@dataclass(frozen=True)
class DetectorOutput:
    detector_id: str
    proposed_tier: Mode
    input_id: str
    source_episode_id: str | None
    source_sequence: int


@dataclass(frozen=True)
class Event:
    kind: EventKind
    occurred_at: datetime
    based_on_sequence: int | None = None
    proposed_tier: Mode = Mode.NORMAL
    detector_outputs: tuple[DetectorOutput, ...] = ()
    episode_id: str | None = None
    source_episode_id: str | None = None
    flag_name: FlagName | None = None
    unresolved_higher_result: bool = False
    input_id: str | None = None
    flag_expires_at: datetime | None = None
    structured_answer: str | None = None
    resource_version: str | None = None


@dataclass(frozen=True)
class Result:
    outcome: Outcome
    state: SafetyState
    action: str | None = None
    reason: str | None = None
    source_episode_id: str | None = None
    previous_episode_id: str | None = None
    archived_episode: SafetyState | None = None


def state_valid(state: SafetyState) -> bool:
    if not isinstance(state, SafetyState):
        return False
    if not isinstance(state.interaction_mode, Mode) or not isinstance(state.episode_peak_tier, Mode):
        return False
    if not isinstance(state.episode_status, Status) or type(state.sequence) is not int or state.sequence < 0:
        return False
    if type(state.degraded) is not bool or not isinstance(state.degraded_causes, frozenset):
        return False
    if bool(state.degraded_causes) != state.degraded or any(not isinstance(c, str) for c in state.degraded_causes):
        return False
    if not isinstance(state.flags, tuple) or any(not isinstance(f, PolicyFlag) or not isinstance(f.name, FlagName) or not isinstance(f.set_at, datetime) or (f.expires_at is not None and not isinstance(f.expires_at, datetime)) for f in state.flags):
        return False
    if state.dropout_reason is not None and not isinstance(state.dropout_reason, DropoutReason):
        return False
    if state.episode_status == Status.NONE:
        return state.interaction_mode == Mode.NORMAL and state.episode_peak_tier == Mode.NORMAL and state.episode_id is None and state.dropout_reason is None
    if not isinstance(state.episode_id, str) or not state.episode_id:
        return False
    if state.episode_peak_tier < state.interaction_mode:
        return False
    if state.episode_status == Status.OPEN:
        return state.interaction_mode >= Mode.CLARIFY and state.dropout_reason is None
    if state.episode_status == Status.RECHECK_REQUIRED:
        return state.episode_peak_tier >= Mode.URGENT and state.dropout_reason is None
    if state.episode_status == Status.DROPOUT:
        if state.episode_peak_tier < Mode.URGENT or state.dropout_reason is None:
            return False
        if state.dropout_reason == DropoutReason.DURING_URGENT:
            return state.interaction_mode == Mode.URGENT
        if state.dropout_reason == DropoutReason.DURING_IMMEDIATE:
            return state.interaction_mode == Mode.IMMEDIATE
        return True
    if state.episode_status == Status.CLOSED:
        return state.interaction_mode == Mode.NORMAL and state.episode_peak_tier >= Mode.CLARIFY and state.dropout_reason is None
    return False
