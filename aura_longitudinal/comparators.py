"""Transparent naive engineering comparators, separate from AURA policy."""

from dataclasses import dataclass
import json
from pathlib import Path
from statistics import median

from .baseline import robust_spread
from .config import EngineeringConfig
from .domain import SignalKey


NAIVE_1_FIXED_THRESHOLD = "NAIVE_1_FIXED_THRESHOLD"
NAIVE_2_ROLLING_ONLY = "NAIVE_2_ROLLING_ONLY"


def key_name(key: SignalKey) -> str:
    return key.signal.value + (f":{key.metric}" if key.metric else "")


@dataclass(frozen=True)
class ComparatorConfig:
    version: str
    fixed_absolute_delta: dict[str, float]
    rolling_absolute_floor: dict[str, float]
    rolling_robust_spread_multiplier: float


def parse_comparator_config(raw: dict) -> ComparatorConfig:
    config = ComparatorConfig(**raw)
    if not config.version.endswith("not-clinically-validated"):
        raise ValueError("comparator configuration needs engineering label")
    if config.rolling_robust_spread_multiplier <= 0 or any(
        value <= 0 for mapping in (config.fixed_absolute_delta, config.rolling_absolute_floor)
        for value in mapping.values()
    ):
        raise ValueError("comparator thresholds must be positive")
    return config


def load_comparator_config(path: Path | None = None) -> ComparatorConfig:
    raw = json.loads((path or Path(__file__).with_name("comparator_config.json")).read_text())
    return parse_comparator_config(raw)


def fixed_threshold_alerts(current: dict[SignalKey, float],
                           reference: dict[SignalKey, float],
                           config: ComparatorConfig) -> tuple[SignalKey, ...]:
    """Fixed absolute change from the same initial reference window; no context."""
    return tuple(key for key, value in current.items()
                 if key in reference and key_name(key) in config.fixed_absolute_delta
                 and abs(value - reference[key]) >= config.fixed_absolute_delta[key_name(key)])


def rolling_only_alerts(current: dict[SignalKey, float],
                        history: dict[SignalKey, list[tuple[int, float]]],
                        day_index: int, engineering: EngineeringConfig,
                        config: ComparatorConfig) -> tuple[SignalKey, ...]:
    """Compare current value with preceding rolling window; no anchor/context."""
    alerts = []
    for key, value in current.items():
        name = key_name(key)
        if name not in config.rolling_absolute_floor:
            continue
        previous = tuple(value for index, value in history.get(key, [])
                         if day_index - engineering.rolling_window_days <= index < day_index)
        if (len(previous) < engineering.minimum_points or
                len(previous) / engineering.rolling_window_days < engineering.minimum_window_coverage):
            continue
        threshold = max(config.rolling_absolute_floor[name],
                        config.rolling_robust_spread_multiplier * robust_spread(previous))
        if abs(value - median(previous)) >= threshold:
            alerts.append(key)
    return tuple(alerts)
