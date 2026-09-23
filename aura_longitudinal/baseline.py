"""Explicit anchor governance and independent rolling/sensing state."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum
from statistics import mean, median

from .config import EngineeringConfig, load_config
from .domain import BaselineTrustState, ObservationPoint, SensingState, SignalKey


class AnchorAction(str, Enum):
    CREATE_PROVISIONAL_ANCHOR = "CREATE_PROVISIONAL_ANCHOR"
    TRUST_ANCHOR = "TRUST_ANCHOR"
    CLINICAL_REVIEW_REANCHOR = "CLINICAL_REVIEW_REANCHOR"


@dataclass(frozen=True)
class AnchorCommand:
    action: AnchorAction
    key: SignalKey
    at: datetime
    reference_points: tuple[ObservationPoint, ...] = ()
    reviewed_by: str | None = None


@dataclass(frozen=True)
class AnchoredBaseline:
    key: SignalKey
    center: float
    robust_spread: float
    reference_start: date
    reference_end: date
    version: int
    created_at: datetime
    reviewed_by: str | None


@dataclass(frozen=True)
class RollingBaseline:
    key: SignalKey
    as_of: date
    mean: float | None
    median: float | None
    robust_spread: float | None
    slope_per_day: float | None
    latest_value: float | None
    coverage_ratio: float
    sample_count: int
    sufficient: bool
    points: tuple[ObservationPoint, ...]


def robust_spread(values: tuple[float, ...]) -> float:
    center = median(values)
    return 1.4826 * median(abs(value - center) for value in values)


def linear_slope(points: tuple[ObservationPoint, ...]) -> float:
    if len(points) < 2:
        return 0.0
    first = points[0].day
    xs = tuple((point.day - first).days for point in points)
    x_bar = mean(xs)
    y_bar = mean(point.value for point in points)
    denominator = sum((x - x_bar) ** 2 for x in xs)
    return (sum((x - x_bar) * (point.value - y_bar) for x, point in zip(xs, points))
            / denominator if denominator else 0.0)


class BaselineManager:
    def __init__(self, config: EngineeringConfig | None = None):
        self.config = config or load_config()
        self._points: dict[SignalKey, dict[date, ObservationPoint]] = {}
        self._anchors: dict[SignalKey, AnchoredBaseline] = {}
        self._trust: dict[SignalKey, BaselineTrustState] = {}
        self._last_good: dict[SignalKey, date] = {}

    def ingest(self, point: ObservationPoint) -> None:
        key = point.key
        existing = self._points.setdefault(key, {}).get(point.day)
        if existing is not None and (existing.coverage * existing.data_quality
                                     > point.coverage * point.data_quality):
            return
        self._points[key][point.day] = point
        if point.coverage < self.config.minimum_observation_coverage or point.data_quality < self.config.minimum_observation_coverage:
            return
        prior = self._last_good.get(key)
        if (prior is not None and (point.day - prior).days > self.config.reestablish_after_days
                and key in self._anchors):
            self._trust[key] = BaselineTrustState.REESTABLISHING
        if prior is None or point.day >= prior:
            self._last_good[key] = point.day

    def ingest_observation(self, observation) -> None:
        for point in observation.points():
            self.ingest(point)

    def sensing_state(self, key: SignalKey, as_of: date) -> SensingState:
        last = max((day for day, point in self._points.get(key, {}).items()
                    if day <= as_of
                    and point.coverage >= self.config.minimum_observation_coverage
                    and point.data_quality >= self.config.minimum_observation_coverage),
                   default=None)
        if last is None or (as_of - last).days > self.config.reestablish_after_days:
            return SensingState.UNOBSERVED
        return SensingState.OBSERVED

    def trust_state(self, key: SignalKey) -> BaselineTrustState:
        return self._trust.get(key, BaselineTrustState.PROVISIONAL)

    def anchor(self, key: SignalKey) -> AnchoredBaseline | None:
        return self._anchors.get(key)

    def apply_anchor_command(self, command: AnchorCommand) -> AnchoredBaseline:
        key = command.key
        current = self._anchors.get(key)
        if command.action == AnchorAction.TRUST_ANCHOR:
            if current is None or not command.reviewed_by:
                raise ValueError("existing anchor and reviewer required")
            self._trust[key] = BaselineTrustState.TRUSTED
            return current  # Trust changes; the reference does not move.
        if command.action == AnchorAction.CREATE_PROVISIONAL_ANCHOR and current is not None:
            raise ValueError("anchor already exists; clinical review required to move it")
        if command.action == AnchorAction.CLINICAL_REVIEW_REANCHOR and (current is None or not command.reviewed_by):
            raise ValueError("existing anchor and reviewer required")
        if command.action not in (AnchorAction.CREATE_PROVISIONAL_ANCHOR,
                                  AnchorAction.CLINICAL_REVIEW_REANCHOR):
            raise ValueError("unsupported anchor command")
        points = tuple(sorted(command.reference_points, key=lambda point: point.day))
        if (len(points) < self.config.minimum_points
                or len({point.day for point in points}) != len(points)
                or any(point.key != key for point in points)):
            raise ValueError("anchor needs enough same-signal reference observations")
        if any(point.coverage < self.config.minimum_observation_coverage
               or point.data_quality < self.config.minimum_observation_coverage for point in points):
            raise ValueError("anchor reference coverage is insufficient")
        values = tuple(point.value for point in points)
        anchor = AnchoredBaseline(key, median(values), robust_spread(values), points[0].day,
                                  points[-1].day, (current.version + 1 if current else 1),
                                  command.at, command.reviewed_by)
        self._anchors[key] = anchor
        self._trust[key] = (BaselineTrustState.PROVISIONAL
                            if command.action == AnchorAction.CREATE_PROVISIONAL_ANCHOR
                            else BaselineTrustState.TRUSTED)
        return anchor

    def rolling(self, key: SignalKey, as_of: date) -> RollingBaseline:
        start = as_of - timedelta(days=self.config.rolling_window_days - 1)
        points = tuple(sorted((p for day, p in self._points.get(key, {}).items()
                               if start <= day <= as_of
                               and p.coverage >= self.config.minimum_observation_coverage
                               and p.data_quality >= self.config.minimum_observation_coverage),
                              key=lambda point: point.day))
        coverage = len(points) / self.config.rolling_window_days
        sufficient = len(points) >= self.config.minimum_points and coverage >= self.config.minimum_window_coverage
        if not sufficient:
            return RollingBaseline(key, as_of, None, None, None, None, None,
                                   coverage, len(points), False, points)
        values = tuple(point.value for point in points)
        return RollingBaseline(key, as_of, mean(values), median(values), robust_spread(values),
                               linear_slope(points), points[-1].value, coverage,
                               len(points), True, points)
