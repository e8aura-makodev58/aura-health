"""Client-offline fail-closed contract with an in-memory simulator fixture."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from .domain import SafetyState
from .output import OutputPlan, output_plan
from .resources import ResourceRegistry


@dataclass(frozen=True)
class HeldInput:
    input_id: str
    original_timestamp: datetime
    payload: str


class ProtectedInputStore(Protocol):
    def put(self, item: HeldInput) -> None: ...
    def drain(self) -> tuple[HeldInput, ...]: ...


class InMemoryInputFixture:
    """Simulator only; a real client must provide protected durable storage."""

    def __init__(self):
        self.items: list[HeldInput] = []

    def put(self, item: HeldInput) -> None:
        if any(existing.input_id == item.input_id for existing in self.items):
            raise ValueError("duplicate input ID")
        self.items.append(item)

    def drain(self) -> tuple[HeldInput, ...]:
        items = tuple(self.items)
        self.items.clear()
        return items


class OfflineSafetyGate:
    def __init__(self, registry: ResourceRegistry, storage: ProtectedInputStore):
        self.registry = registry
        self.storage = storage

    def hold(self, state: SafetyState, item: HeldInput) -> OutputPlan:
        self.storage.put(item)
        return output_plan(state, self.registry, item.original_timestamp, client_offline=True)

    def reconnect(self) -> tuple[HeldInput, ...]:
        # Returned items still require server safety evaluation before assessment.
        return self.storage.drain()
