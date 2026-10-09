"""Resolved-output safety gate adapter; no detector or tier logic is implemented here."""

from dataclasses import dataclass
from typing import Protocol

from aura_safety.domain import DetectorOutput

from .models import ApplicationEvent


class SafetyGateUnavailable(Exception):
    def __init__(self, message, *, outputs=(), failure_code='UNAVAILABLE'):
        super().__init__(message)
        self.outputs = outputs
        self.failure_code = failure_code


class ResolvedSafetyGate(Protocol):
    def resolve(self, event: ApplicationEvent, source_episode_id: str | None,
                source_sequence: int) -> tuple[DetectorOutput, ...]: ...


class UnconfiguredSafetyGate:
    """The public development API cannot assert that unexamined text is safe."""

    def resolve(self, event, source_episode_id, source_sequence):
        raise SafetyGateUnavailable("resolved safety detector output is not configured")


@dataclass
class FixtureSafetyGate:
    """Explicit developer/test fixture. Values are detector proposals, never policy results."""

    proposals: dict[str, tuple[tuple[str, str], ...]]

    def resolve(self, event, source_episode_id, source_sequence):
        from aura_safety.domain import Mode
        if event.event_id not in self.proposals:
            raise SafetyGateUnavailable("no resolved fixture for this input")
        return tuple(DetectorOutput(detector_id, Mode[tier], event.event_id,
                                    source_episode_id, source_sequence)
                     for detector_id, tier in self.proposals[event.event_id])
