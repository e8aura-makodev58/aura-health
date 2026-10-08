"""Explicit anchor governance and independent rolling/sensing state."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum
from statistics import mean, median

from .config import EngineeringConfig, load_config
from .domain import BaselineTrustState, ObservationPoint, SensingState, SignalKey
from .registry import LEGACY_SIGNALS, SignalRegistry, load_registry


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
    def __init__(self, config: EngineeringConfig | None = None, *, registry: SignalRegistry | None = None):
        self.config = config or load_config()
        self.registry = registry or load_registry(base_config=self.config)
        self._points: dict[SignalKey, dict[date, ObservationPoint]] = {}
        self._anchors: dict[SignalKey, AnchoredBaseline] = {}
        self._trust: dict[SignalKey, BaselineTrustState] = {}
        self._last_good: dict[SignalKey, date] = {}

    def ingest(self, point: ObservationPoint) -> None:
        key = point.key
        if not self.registry.definition(key.signal).enabled_in_engine:
            return
        config = self.config_for(key)
        existing = self._points.setdefault(key, {}).get(point.day)
        if existing is not None and (existing.coverage * existing.data_quality
                                     > point.coverage * point.data_quality):
            return
        self._points[key][point.day] = point
        if point.coverage < config.minimum_observation_coverage or point.data_quality < config.minimum_observation_coverage:
            return
        prior = self._last_good.get(key)
        if (prior is not None and (point.day - prior).days > config.reestablish_after_days
                and key in self._anchors):
            self._trust[key] = BaselineTrustState.REESTABLISHING
        if prior is None or point.day >= prior:
            self._last_good[key] = point.day

    def ingest_observation(self, observation) -> None:
        for point in observation.points():
            self.ingest(point)

    def sensing_state(self, key: SignalKey, as_of: date) -> SensingState:
        config = self.config_for(key)
        last = max((day for day, point in self._points.get(key, {}).items()
                    if day <= as_of
                    and point.coverage >= config.minimum_observation_coverage
                    and point.data_quality >= config.minimum_observation_coverage),
                   default=None)
        if last is None or (as_of - last).days > config.reestablish_after_days:
            return SensingState.UNOBSERVED
        return SensingState.OBSERVED

    def trust_state(self, key: SignalKey) -> BaselineTrustState:
        return self._trust.get(key, BaselineTrustState.PROVISIONAL)

    def anchor(self, key: SignalKey) -> AnchoredBaseline | None:
        return self._anchors.get(key)

    def config_for(self, key: SignalKey) -> EngineeringConfig:
        return self.registry.config_for(key.signal)

    def apply_anchor_command(self, command: AnchorCommand) -> AnchoredBaseline:
        key = command.key
        if not self.registry.definition(key.signal).enabled_in_engine:
            raise ValueError("display-only signal cannot receive an engine anchor")
        config = self.config_for(key)
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
        if (len(points) < config.minimum_points
                or len({point.day for point in points}) != len(points)
                or any(point.key != key for point in points)):
            raise ValueError("anchor needs enough same-signal reference observations")
        if any(point.coverage < config.minimum_observation_coverage
               or point.data_quality < config.minimum_observation_coverage for point in points):
            raise ValueError("anchor reference coverage is insufficient")
        # New channels cannot establish a dense-looking reference from a handful
        # of scattered readings. Preserve the four accepted anchor rules exactly.
        if key.signal not in LEGACY_SIGNALS:
            span = max(config.rolling_window_days, (points[-1].day - points[0].day).days + 1)
            if len(points) / span < config.minimum_window_coverage:
                raise ValueError("new-signal anchor reference calendar coverage is insufficient")
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
        config = self.config_for(key)
        start = as_of - timedelta(days=config.rolling_window_days - 1)
        points = tuple(sorted((p for day, p in self._points.get(key, {}).items()
                               if start <= day <= as_of
                               and p.coverage >= config.minimum_observation_coverage
                               and p.data_quality >= config.minimum_observation_coverage),
                              key=lambda point: point.day))
        coverage = len(points) / config.rolling_window_days
        sufficient = len(points) >= config.minimum_points and coverage >= config.minimum_window_coverage
        if not sufficient:
            return RollingBaseline(key, as_of, None, None, None, None, None,
                                   coverage, len(points), False, points)
        values = tuple(point.value for point in points)
        return RollingBaseline(key, as_of, mean(values), median(values), robust_spread(values),
                               linear_slope(points), points[-1].value, coverage,
                               len(points), True, points)
