"""Observations carry measurements and provenance, not clinical conclusions."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, time
from enum import Enum
from math import isfinite


class Signal(str, Enum):
    SLEEP_MIDPOINT = "SLEEP_MIDPOINT"
    SLEEP_DURATION = "SLEEP_DURATION"
    ACTIVITY = "ACTIVITY"
    RESTING_HEART_RATE = "RESTING_HEART_RATE"


class SensingState(str, Enum):
    OBSERVED = "OBSERVED"
    UNOBSERVED = "UNOBSERVED"


class BaselineTrustState(str, Enum):
    PROVISIONAL = "PROVISIONAL"
    TRUSTED = "TRUSTED"
    REESTABLISHING = "REESTABLISHING"


class MedicationStatus(str, Enum):
    ACKNOWLEDGED = "ACKNOWLEDGED"
    MISSED = "MISSED"
    UNKNOWN = "UNKNOWN"


class CheckinState(str, Enum):
    GOOD = "Good"
    OKAY = "Okay"
    ROUGH = "Rough"


class ContextCategory(str, Enum):
    BENIGN_CONTEXT = "BENIGN_CONTEXT"
    RISK_CONTEXT = "RISK_CONTEXT"


def _coverage(value: float, name: str) -> None:
    if not isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f"{name} must be between 0 and 1")


@dataclass(frozen=True)
class SignalKey:
    signal: Signal
    source: str
    metric: str | None = None

    def __post_init__(self):
        if (not self.source or (self.signal == Signal.ACTIVITY) != (self.metric is not None)
                or (self.metric is not None and not self.metric)):
            raise ValueError("source required; activity requires a named metric")


@dataclass(frozen=True)
class ObservationPoint:
    key: SignalKey
    day: date
    value: float
    coverage: float
    data_quality: float

    def __post_init__(self):
        if not isfinite(self.value):
            raise ValueError("observed value must be finite")
        _coverage(self.coverage, "coverage")
        _coverage(self.data_quality, "data quality")


@dataclass(frozen=True)
class SleepObservation:
    window_date: date
    sleep_start: datetime
    sleep_end: datetime
    duration: timedelta
    coverage: float
    data_quality: float
    source: str

    def __post_init__(self):
        if self.sleep_start.tzinfo is None or self.sleep_end.tzinfo is None:
            raise ValueError("sleep times require timezone information")
        if self.window_date != self.sleep_start.date():
            raise ValueError("sleep window date is the local sleep-start date")
        if self.sleep_end <= self.sleep_start or self.duration != self.sleep_end - self.sleep_start:
            raise ValueError("duration must match a positive sleep interval")
        _coverage(self.coverage, "coverage")
        _coverage(self.data_quality, "data quality")
        if not self.source:
            raise ValueError("source required")

    def points(self) -> tuple[ObservationPoint, ObservationPoint]:
        midpoint = self.sleep_start + self.duration / 2
        midnight = datetime.combine(self.window_date, time.min, tzinfo=self.sleep_start.tzinfo)
        minutes = (midpoint - midnight).total_seconds() / 60
        return (
            ObservationPoint(SignalKey(Signal.SLEEP_MIDPOINT, self.source), self.window_date,
                             minutes, self.coverage, self.data_quality),
            ObservationPoint(SignalKey(Signal.SLEEP_DURATION, self.source), self.window_date,
                             self.duration.total_seconds() / 3600, self.coverage, self.data_quality),
        )


@dataclass(frozen=True)
class ActivityObservation:
    day: date
    metrics: tuple[tuple[str, float], ...]
    coverage: float
    source: str

    def __post_init__(self):
        if not self.source or not self.metrics or len({name for name, _ in self.metrics}) != len(self.metrics):
            raise ValueError("source and unique activity metrics required")
        if any(not name or not isfinite(value) or value < 0 for name, value in self.metrics):
            raise ValueError("activity metrics must be named, finite, and nonnegative")
        _coverage(self.coverage, "coverage")

    def points(self) -> tuple[ObservationPoint, ...]:
        return tuple(ObservationPoint(SignalKey(Signal.ACTIVITY, self.source, name),
                                      self.day, value, self.coverage, self.coverage)
                     for name, value in self.metrics)


@dataclass(frozen=True)
class RestingHeartRateObservation:
    day: date
    value: float
    coverage: float
    source: str

    def __post_init__(self):
        if not self.source or not isfinite(self.value) or self.value <= 0:
            raise ValueError("positive finite resting HR and source required")
        _coverage(self.coverage, "coverage")

    def points(self) -> tuple[ObservationPoint, ...]:
        return (ObservationPoint(SignalKey(Signal.RESTING_HEART_RATE, self.source),
                                 self.day, self.value, self.coverage, self.coverage),)


@dataclass(frozen=True)
class MedicationEvent:
    scheduled_time: datetime
    timestamp: datetime
    status: MedicationStatus
    source: str


@dataclass(frozen=True)
class PatientCheckin:
    timestamp: datetime
    state: CheckinState
    structured_answers: tuple[tuple[str, str], ...] = ()
    context_tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class ContextEvent:
    start: datetime
    end: datetime | None
    category: ContextCategory
    affected_signals: tuple[Signal, ...]
    source: str
    patient_explanation: str | None = None

    def __post_init__(self):
        if self.end is not None and self.end < self.start:
            raise ValueError("context window cannot end before it starts")
        if not self.source:
            raise ValueError("context source required")
