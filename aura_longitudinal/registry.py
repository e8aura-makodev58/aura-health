"""Versioned sponsor-editable engineering choices, not clinical validation.

Cadence is metadata, never a denominator discount: coverage still counts actual
covered days / calendar window. Sparse opt-in cannot manufacture measurements.
"""

from dataclasses import asdict, dataclass, fields
from hashlib import sha256
import json
from math import isfinite
import os
from pathlib import Path
from types import MappingProxyType

from .config import EngineeringConfig, load_config, parse_config
from .domain import Signal


LEGACY_SIGNALS = frozenset({Signal.SLEEP_MIDPOINT, Signal.SLEEP_DURATION,
                            Signal.ACTIVITY, Signal.RESTING_HEART_RATE})
CADENCES = {"DAILY", "NIGHTLY", "SPARSE_NIGHTLY", "INTERMITTENT"}


@dataclass(frozen=True)
class SignalDefinition:
    name: Signal
    label: str
    unit: str
    cadence_class: str
    expected_measurements_per_week: float
    source_type: str
    evidence_tier: str
    enabled_in_engine: bool
    display: bool
    engineering_overrides: object


class SignalRegistry:
    def __init__(self, raw: dict, base_config: EngineeringConfig | None = None):
        if not isinstance(raw, dict) or set(raw) != {"version", "signals", "communication_overrides"}:
            raise ValueError("invalid signal registry shape")
        if not isinstance(raw["version"], str) or not raw["version"].endswith("not-clinically-validated"):
            raise ValueError("registry must carry its engineering validation label")
        if not isinstance(raw["signals"], list):
            raise ValueError("signal definitions must be a list")
        base = base_config or load_config()
        definitions, configs = {}, {}
        allowed_overrides = set(EngineeringConfig.__dataclass_fields__) - {"version", "communication_cooldown_days"}
        for item in raw["signals"]:
            if not isinstance(item, dict) or set(item) != {field.name for field in fields(SignalDefinition)}:
                raise ValueError("invalid signal definition shape")
            name = Signal(item["name"])
            if name in definitions:
                raise ValueError("duplicate signal definition")
            for key in ("label", "unit", "source_type", "evidence_tier"):
                if not isinstance(item[key], str) or not 1 <= len(item[key]) <= 100:
                    raise ValueError("invalid signal metadata")
            if item["cadence_class"] not in CADENCES or item["evidence_tier"] not in {"E2", "E3_RESEARCH"}:
                raise ValueError("invalid cadence or evidence tier")
            frequency = item["expected_measurements_per_week"]
            if type(frequency) not in {int, float} or not isfinite(frequency) or not 0 < frequency <= 7:
                raise ValueError("invalid descriptive measurement frequency")
            if any(type(item[key]) is not bool for key in ("enabled_in_engine", "display")):
                raise ValueError("registry switches must be booleans")
            overrides = item["engineering_overrides"]
            if not isinstance(overrides, dict) or set(overrides) - allowed_overrides:
                raise ValueError("unsupported per-signal engineering setting")
            for key, value in overrides.items():
                if type(value) not in {int, float} or not isfinite(value):
                    raise ValueError("engineering settings must be finite numbers")
                if type(getattr(base, key)) is int and type(value) is not int:
                    raise ValueError("day and sample counts must be integers")
            configs[name] = parse_config({**asdict(base), **overrides})
            definitions[name] = SignalDefinition(**{**item, "name": name,
                "engineering_overrides": MappingProxyType(dict(overrides))})
        if set(definitions) != set(Signal):
            raise ValueError("registry must define every supported channel exactly once")
        communication = raw["communication_overrides"]
        if (not isinstance(communication, dict) or set(communication) - {"communication_cooldown_days"}
                or any(type(value) is not int for value in communication.values())):
            raise ValueError("invalid communication settings")
        self.communication_config = parse_config({**asdict(base), **communication})
        self.version = raw["version"]
        self.definitions = MappingProxyType(definitions)
        self.configs = MappingProxyType(configs)
        self._raw = json.dumps(raw, sort_keys=True, allow_nan=False)
        self.fingerprint = sha256((self._raw + json.dumps(asdict(base), sort_keys=True)).encode()).hexdigest()

    def definition(self, signal: Signal) -> SignalDefinition:
        return self.definitions[signal]

    def config_for(self, signal: Signal) -> EngineeringConfig:
        return self.configs[signal]

    def public(self) -> dict:
        return {**json.loads(self._raw), "fingerprint": self.fingerprint,
                "effective_engineering_settings": {signal.value: asdict(config)
                    for signal, config in self.configs.items()},
                "effective_communication_settings": asdict(self.communication_config),
                "coverage_rule": "actual covered days / calendar window; no interpolation"}


def load_registry(path: Path | None = None, *, base_config=None) -> SignalRegistry:
    location = path or os.environ.get("AURA_SIGNAL_REGISTRY") or Path(__file__).with_name("signal_registry.json")
    return SignalRegistry(json.loads(Path(location).read_text()), base_config)
