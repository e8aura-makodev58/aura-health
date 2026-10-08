"""Descriptive comparisons between current, rolling, and governed anchor."""

from dataclasses import dataclass
from enum import Enum

from .baseline import AnchoredBaseline, RollingBaseline
from .config import EngineeringConfig
from .domain import BaselineTrustState, Signal, SignalKey
from .registry import load_registry


class DriftKind(str, Enum):
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    STABLE = "STABLE"
    TRANSIENT_DEVIATION = "TRANSIENT_DEVIATION"
    PERSISTENT_DRIFT = "PERSISTENT_DRIFT"
    ROLLING_ANCHOR_DIVERGENCE = "ROLLING_ANCHOR_DIVERGENCE"


class TrendDirection(str, Enum):
    INCREASING = "INCREASING"
    DECREASING = "DECREASING"
    FLAT = "FLAT"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class DriftAssessment:
    key: SignalKey
    kind: DriftKind
    current_vs_rolling: float | None
    rolling_vs_anchor: float | None
    trend_direction: TrendDirection
    trend_magnitude_per_day: float | None
    coverage: float
    confidence: float
    description: str


def _describe(key: SignalKey, delta: float | None, kind: DriftKind) -> str:
    if kind == DriftKind.INSUFFICIENT_DATA:
        return f"Insufficient covered data to compare {key.signal.value.lower().replace('_', ' ')} with its reference."
    if kind == DriftKind.STABLE:
        return f"No configured descriptive drift was found for {key.signal.value.lower().replace('_', ' ')}."
    direction = "later" if key.signal == Signal.SLEEP_MIDPOINT and delta is not None and delta > 0 else (
        "earlier" if key.signal == Signal.SLEEP_MIDPOINT else (
            "higher" if delta is not None and delta > 0 else "lower"))
    label = key.signal.value.lower().replace("_", " ")
    reference = "anchored reference" if kind != DriftKind.TRANSIENT_DEVIATION else "recent rolling pattern"
    return f"{label.capitalize()} is {direction} relative to the {reference}."


def assess_drift(rolling: RollingBaseline, anchor: AnchoredBaseline | None,
                 config: EngineeringConfig | None = None,
                 trust_state: BaselineTrustState | None = None) -> DriftAssessment:
    config = config or load_registry().config_for(rolling.key.signal)
    if trust_state == BaselineTrustState.REESTABLISHING:
        return DriftAssessment(rolling.key, DriftKind.INSUFFICIENT_DATA, None, None,
                               TrendDirection.UNKNOWN, None, rolling.coverage_ratio,
                               rolling.coverage_ratio,
                               "Reference is being re-established after a sensing gap.")
    if not rolling.points or rolling.points[-1].day != rolling.as_of:
        return DriftAssessment(rolling.key, DriftKind.INSUFFICIENT_DATA, None, None,
                               TrendDirection.UNKNOWN, None, rolling.coverage_ratio,
                               rolling.coverage_ratio,
                               "No current covered observation is available for comparison.")
    if anchor is None or not rolling.sufficient:
        return DriftAssessment(rolling.key, DriftKind.INSUFFICIENT_DATA, None, None,
                               TrendDirection.UNKNOWN, None, rolling.coverage_ratio,
                               rolling.coverage_ratio, _describe(rolling.key, None, DriftKind.INSUFFICIENT_DATA))
    if anchor.key != rolling.key:
        raise ValueError("anchor and rolling signal/source must match")
    current_delta = rolling.latest_value - rolling.median
    anchor_delta = rolling.median - anchor.center
    scale = max(anchor.robust_spread, abs(anchor.center) * config.relative_spread_floor,
                config.absolute_spread_floor, 1e-9)
    deviation = scale * config.deviation_spread_multiplier
    slope = rolling.slope_per_day
    slope_floor = scale * config.trend_spread_per_day
    direction = (TrendDirection.INCREASING if slope > slope_floor else
                 TrendDirection.DECREASING if slope < -slope_floor else TrendDirection.FLAT)
    outlying_fraction = sum(abs(point.value - anchor.center) >= deviation
                            for point in rolling.points) / len(rolling.points)
    diverged = abs(anchor_delta) >= deviation
    moving_away = (anchor_delta > 0 and direction == TrendDirection.INCREASING) or (
        anchor_delta < 0 and direction == TrendDirection.DECREASING)
    if diverged and moving_away and abs(current_delta) < deviation:
        kind = DriftKind.ROLLING_ANCHOR_DIVERGENCE
    elif diverged and outlying_fraction >= config.persistent_fraction:
        kind = DriftKind.PERSISTENT_DRIFT
    elif abs(current_delta) >= deviation:
        kind = DriftKind.TRANSIENT_DEVIATION
    elif diverged:
        kind = DriftKind.ROLLING_ANCHOR_DIVERGENCE
    else:
        kind = DriftKind.STABLE
    delta = current_delta if kind == DriftKind.TRANSIENT_DEVIATION else anchor_delta
    quality = sum(point.data_quality for point in rolling.points) / len(rolling.points)
    return DriftAssessment(rolling.key, kind, current_delta, anchor_delta,
                           direction, abs(slope), rolling.coverage_ratio,
                           min(rolling.coverage_ratio, quality),
                           _describe(rolling.key, delta, kind))
