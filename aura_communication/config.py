"""Engineering limits for optional wording, not clinical thresholds."""

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path


@dataclass(frozen=True)
class CommunicationConfig:
    version: str = "m5-engineering-v1"
    prompt_version: str = "bounded-choice-v1"
    content_version: str = "development-wording-v1"
    max_response_length: int = 420
    max_context_chars: int = 600
    max_facts: int = 2
    provider_timeout_seconds: float = 5.0
    max_provider_response_bytes: int = 16384

    def __post_init__(self):
        if not all(isinstance(value, str) and value for value in
                   (self.version, self.prompt_version, self.content_version)):
            raise ValueError("versions must be nonempty")
        if any(type(value) is not int or value < 1 for value in
               (self.max_response_length, self.max_context_chars, self.max_facts,
                self.max_provider_response_bytes)):
            raise ValueError("limits must be positive integers")
        if not isfinite(self.provider_timeout_seconds) or self.provider_timeout_seconds <= 0:
            raise ValueError("provider timeout must be finite and positive")

    @property
    def fingerprint(self) -> str:
        return sha256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()


def load_config(path: str | Path | None = None) -> CommunicationConfig:
    path = Path(path) if path else Path(__file__).with_name("engineering_config.json")
    return CommunicationConfig(**json.loads(path.read_text()))
