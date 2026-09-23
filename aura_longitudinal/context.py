"""Signal-scoped context and inspectable explained/held drift records."""

from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum

from .domain import ContextCategory, ContextEvent, SignalKey
from .drift import DriftAssessment, DriftKind


@dataclass(frozen=True)
class ContextualizedDrift:
    drift: DriftAssessment
    attenuated: bool
    benign_contexts: tuple[ContextEvent, ...]
    risk_contexts: tuple[ContextEvent, ...]


def apply_context(drift: DriftAssessment, contexts: tuple[ContextEvent, ...],
                  at: datetime) -> ContextualizedDrift:
    active = tuple(context for context in contexts
                   if context.start <= at and (context.end is None or at <= context.end)
                   and drift.key.signal in context.affected_signals)
    benign = tuple(context for context in active if context.category == ContextCategory.BENIGN_CONTEXT)
    risk = tuple(context for context in active if context.category == ContextCategory.RISK_CONTEXT)
    # Attenuation changes communication priority only. The observed drift is retained.
    return ContextualizedDrift(drift, bool(benign), benign, risk)


class HeldStatus(str, Enum):
    EXPLAINED_HELD_FOR_REVIEW = "EXPLAINED_HELD_FOR_REVIEW"
    REOPENED = "REOPENED"


class EvidenceKind(str, Enum):
    WORSE_CHECKIN = "WORSE_CHECKIN"
    NEW_LONGITUDINAL_SIGNAL = "NEW_LONGITUDINAL_SIGNAL"
    STRUCTURED_ASSESSMENT_CHANGE = "STRUCTURED_ASSESSMENT_CHANGE"
    MEDICATION_ROUTINE_DISRUPTION = "MEDICATION_ROUTINE_DISRUPTION"
    SAFETY_RELEVANT_EVENT = "SAFETY_RELEVANT_EVENT"


@dataclass(frozen=True)
class EvidenceEvent:
    kind: EvidenceKind
    at: datetime
    meaningful: bool = True
    signal: SignalKey | None = None


@dataclass(frozen=True)
class HeldDrift:
    key: SignalKey
    detected_drift: DriftAssessment
    explanation: str
    held_at: datetime
    status: HeldStatus = HeldStatus.EXPLAINED_HELD_FOR_REVIEW
    reopened_at: datetime | None = None
    reopened_because: EvidenceKind | None = None

    @property
    def suppress_duplicate_notification(self) -> bool:
        return self.status == HeldStatus.EXPLAINED_HELD_FOR_REVIEW

    @property
    def inspectable(self) -> bool:
        return True

    @property
    def clinician_review_item(self) -> bool:
        return True


class HeldDriftRegistry:
    def __init__(self):
        self._items: dict[tuple[SignalKey, int], HeldDrift] = {}

    @staticmethod
    def _identity(drift: DriftAssessment) -> tuple[SignalKey, int]:
        delta = drift.rolling_vs_anchor or 0
        return drift.key, (1 if delta > 0 else -1 if delta < 0 else 0)

    def hold(self, drift: DriftAssessment, explanation: str, at: datetime) -> HeldDrift:
        if drift.kind not in (DriftKind.PERSISTENT_DRIFT, DriftKind.ROLLING_ANCHOR_DIVERGENCE):
            raise ValueError("only persistent drift can be held for review")
        if not explanation.strip():
            raise ValueError("explanation required")
        identity = self._identity(drift)
        existing = self._items.get(identity)
        if existing and existing.suppress_duplicate_notification:
            return existing
        item = HeldDrift(drift.key, drift, explanation, at)
        self._items[identity] = item
        return item

    def hold_explained(self, drifts: tuple[ContextualizedDrift, ...],
                       explanation: str, at: datetime) -> tuple[HeldDrift, ...]:
        return tuple(self.hold(item.drift, explanation, at) for item in drifts
                     if item.attenuated and item.drift.kind in (
                         DriftKind.PERSISTENT_DRIFT, DriftKind.ROLLING_ANCHOR_DIVERGENCE))

    def get(self, key: SignalKey) -> HeldDrift | None:
        matches = tuple(item for (item_key, _), item in self._items.items() if item_key == key)
        return max(matches, key=lambda item: item.held_at, default=None)

    def get_for_drift(self, drift: DriftAssessment) -> HeldDrift | None:
        return self._items.get(self._identity(drift))

    def reopen(self, key: SignalKey, evidence: EvidenceEvent) -> HeldDrift | None:
        matching = tuple(identity for identity in self._items if identity[0] == key)
        if not matching or not evidence.meaningful:
            return self.get(key)
        if evidence.kind == EvidenceKind.NEW_LONGITUDINAL_SIGNAL and evidence.signal is None:
            raise ValueError("new signal evidence needs a signal key")
        for identity in matching:
            item = self._items[identity]
            if item.suppress_duplicate_notification:
                self._items[identity] = replace(item, status=HeldStatus.REOPENED,
                                                reopened_at=evidence.at,
                                                reopened_because=evidence.kind)
        return self.get(key)

    def review_items(self) -> tuple[HeldDrift, ...]:
        return tuple(self._items.values())
