"""Inspectable engineering parameters; none are clinical cutoffs."""

from dataclasses import dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class EngineeringConfig:
    version: str
    rolling_window_days: int
    minimum_points: int
    minimum_window_coverage: float
    minimum_observation_coverage: float
    reestablish_after_days: int
    deviation_spread_multiplier: float
    persistent_fraction: float
    trend_spread_per_day: float
    relative_spread_floor: float
    communication_cooldown_days: int


def parse_config(raw: dict) -> EngineeringConfig:
    config = EngineeringConfig(**raw)
    if not config.version.endswith("not-clinically-validated"):
        raise ValueError("engineering configuration must carry its validation label")
    if min(config.rolling_window_days, config.minimum_points,
           config.reestablish_after_days) <= 0 or config.minimum_points > config.rolling_window_days:
        raise ValueError("invalid window configuration")
    if config.communication_cooldown_days < 0:
        raise ValueError("invalid cooldown")
    for value in (config.minimum_window_coverage, config.minimum_observation_coverage,
                  config.persistent_fraction, config.relative_spread_floor):
        if not 0 < value <= 1:
            raise ValueError("invalid fraction")
    if config.deviation_spread_multiplier <= 0 or config.trend_spread_per_day < 0:
        raise ValueError("invalid drift multiplier")
    return config


def load_config(path: Path | None = None) -> EngineeringConfig:
    return parse_config(json.loads((path or Path(__file__).with_name("engineering_config.json")).read_text()))
