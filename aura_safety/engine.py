"""Pure transition reducer and a serialized in-memory writer."""

from dataclasses import replace
from datetime import timedelta
from threading import RLock

from .config import PolicyConfig, load_config
from .domain import (
    DropoutReason, Event, EventKind, FlagName, Mode, Outcome, PolicyFlag,
    Result, SafetyState, Status, state_valid,
)


POLICY_VERSION = "1.2"
BLOCKING_CAUSES = frozenset({"POLICY_ERROR", "STATE_INTEGRITY_ERROR"})
CAS_EDGES = frozenset({
    EventKind.CLARIFICATION_CLEARED, EventKind.ELEVATION_RESOLVED,
    EventKind.URGENT_DEESCALATION_APPROVED, EventKind.IMMEDIATE_DEESCALATION_APPROVED,
    EventKind.DROPOUT_REENTRY, EventKind.EPISODE_CLOSE_APPROVED,
})
NAMED_DEESCALATIONS = CAS_EDGES | {EventKind.RECHECK_FAILED}


def _table():
    """Explicit total dispatch matrix. A row is (status, mode, event) -> handler.

    The default REJECT row makes unsupported combinations explicit. Events which
    are harmless but irrelevant get the named no-change handler below.
    """
    table = {(status, mode, kind): "reject" for status in Status for mode in Mode for kind in EventKind}
    for status in Status:
        for mode in Mode:
            for kind in (EventKind.FREE_TEXT_RECEIVED, EventKind.STRUCTURED_RESPONSE_RECEIVED,
                         EventKind.CHECKIN_TAP_RECEIVED, EventKind.MEDICATION_EVENT_RECEIVED,
                         EventKind.CLIENT_RECONNECTED, EventKind.RESOURCE_REFRESH_DUE):
                table[status, mode, kind] = "hold_input"
            for kind in (EventKind.DETECTOR_TIMEOUT, EventKind.DETECTOR_ERROR,
                         EventKind.POLICY_ERROR, EventKind.STATE_INTEGRITY_ERROR,
                         EventKind.RESOURCE_INTEGRITY_FAILED):
                table[status, mode, kind] = "degrade"
            table[status, mode, EventKind.LIVE_RESOURCES_AVAILABLE] = "resource_available"
            table[status, mode, EventKind.LIVE_RESOURCES_UNAVAILABLE] = "resource_fallback"
            table[status, mode, EventKind.OUTPUT_VALIDATION_FAILED] = "output_fallback"
            table[status, mode, EventKind.DETECTORS_COMPLETE] = "evidence"
            table[status, mode, EventKind.LATE_DETECTOR_RESULT] = "evidence"
            table[status, mode, EventKind.FLAG_EXPIRY_DUE] = "expire_flag"
            table[status, mode, EventKind.POLICY_FLAG_SET] = "set_flag"
    table[Status.NONE, Mode.NORMAL, EventKind.EPISODE_ARCHIVE_DUE] = "no_change"
    table[Status.OPEN, Mode.CLARIFY, EventKind.CLARIFICATION_CLEARED] = "close_simple"
    table[Status.OPEN, Mode.ELEVATED, EventKind.ELEVATION_RESOLVED] = "close_simple"
    for mode in (Mode.ELEVATED, Mode.URGENT, Mode.IMMEDIATE):
        table[Status.OPEN, mode, EventKind.RECONTACT_DUE] = "recontact"
    table[Status.OPEN, Mode.ELEVATED, EventKind.FOLLOWUP_WINDOW_EXPIRED] = "t2_timeout"
    table[Status.OPEN, Mode.URGENT, EventKind.URGENT_DEESCALATION_APPROVED] = "deescalate"
    table[Status.OPEN, Mode.IMMEDIATE, EventKind.IMMEDIATE_DEESCALATION_APPROVED] = "deescalate"
    table[Status.OPEN, Mode.URGENT, EventKind.FOLLOWUP_WINDOW_EXPIRED] = "high_dropout"
    table[Status.OPEN, Mode.IMMEDIATE, EventKind.FOLLOWUP_WINDOW_EXPIRED] = "high_dropout"
    for mode in Mode:
        table[Status.RECHECK_REQUIRED, mode, EventKind.RECHECK_DUE] = "recheck_due"
        table[Status.RECHECK_REQUIRED, mode, EventKind.RECHECK_PASSED] = "recheck_passed"
        table[Status.RECHECK_REQUIRED, mode, EventKind.RECHECK_FAILED] = "recheck_failed"
        table[Status.RECHECK_REQUIRED, mode, EventKind.EPISODE_CLOSE_APPROVED] = "close_recheck"
        table[Status.RECHECK_REQUIRED, mode, EventKind.FOLLOWUP_WINDOW_EXPIRED] = "recheck_dropout"
        table[Status.DROPOUT, mode, EventKind.PATIENT_RETURNED] = "propose_reentry"
        table[Status.DROPOUT, mode, EventKind.DROPOUT_REENTRY] = "reentry"
    table[Status.CLOSED, Mode.NORMAL, EventKind.EPISODE_ARCHIVE_DUE] = "archive"
    return table


TRANSITION_TABLE = _table()


class SafetyEngine:
    def __init__(self, config: PolicyConfig | None = None):
        self.config = config or load_config()

    def apply(self, state: SafetyState, event: Event) -> Result:
        if not state_valid(state):
            # Invalid stored data is never guessed into a valid tuple.
            if isinstance(state, SafetyState):
                state = replace(state, degraded=True,
                                degraded_causes=state.degraded_causes | {"STATE_INTEGRITY_ERROR"})
            return Result(Outcome.SET_DEGRADED, state, reason="invalid state tuple")
        if not isinstance(event, Event) or not isinstance(event.kind, EventKind):
            return Result(Outcome.REJECT_EVENT, state, reason="invalid event")
        if event.kind in CAS_EDGES and event.based_on_sequence != state.sequence:
            return Result(Outcome.REJECT_EVENT, state, reason="stale or missing CAS sequence")
        if state.degraded and state.degraded_causes & BLOCKING_CAUSES:
            if event.kind in (EventKind.POLICY_ERROR, EventKind.STATE_INTEGRITY_ERROR):
                return Result(Outcome.NO_STATE_CHANGE, state)
            return Result(Outcome.DEFER_EVENT, state, reason="policy or integrity degraded")
        handler = TRANSITION_TABLE[(state.episode_status, state.interaction_mode, event.kind)]
        if state.degraded and handler in {"hold_input", "close_simple", "deescalate", "reentry", "close_recheck", "set_flag"}:
            return Result(Outcome.DEFER_EVENT, state, reason="degraded input held")
        return getattr(self, f"_{handler}")(state, event)

    @staticmethod
    def _commit(state, **changes):
        next_state = replace(state, sequence=state.sequence + 1, **changes)
        if not state_valid(next_state):
            raise AssertionError("transition produced invalid state")
        return Result(Outcome.TRANSITION, next_state)

    @staticmethod
    def _reject(state, event):
        return Result(Outcome.REJECT_EVENT, state)

    @staticmethod
    def _no_change(state, event):
        return Result(Outcome.NO_STATE_CHANGE, state)

    @staticmethod
    def _hold_input(state, event):
        return Result(Outcome.NO_STATE_CHANGE, state, action="HOLD_FOR_SAFETY_GATE")

    def _recontact(self, state, event):
        prior = next((f for f in state.flags if f.name == FlagName.RECONTACT_COUNT
                      and f.source_episode_id == state.episode_id
                      and dict(f.metadata).get("phase") == state.interaction_mode.name), None)
        count = int(dict(prior.metadata)["count"]) if prior else 0
        if count >= self.config.max_recontacts_per_phase:
            return Result(Outcome.NO_STATE_CHANGE, state, action="RECONTACT_LIMIT_REACHED")
        flag = PolicyFlag(FlagName.RECONTACT_COUNT, state.episode_id, event.occurred_at,
                          metadata=(("phase", state.interaction_mode.name), ("count", str(count + 1))))
        flags = tuple(f for f in state.flags if f is not prior) + (flag,)
        return replace(self._commit(state, flags=flags), action="SEND_BOUNDED_RECONTACT")

    @staticmethod
    def _recheck_due(state, event):
        return Result(Outcome.NO_STATE_CHANGE, state, action="REQUEST_RECHECK")

    @staticmethod
    def _propose_reentry(state, event):
        return Result(Outcome.NO_STATE_CHANGE, state, action="PROPOSE_DROPOUT_REENTRY")

    @staticmethod
    def _degrade(state, event):
        cause = event.kind.value
        if cause in state.degraded_causes:
            return Result(Outcome.NO_STATE_CHANGE, state)
        result = SafetyEngine._commit(state, degraded=True,
                                      degraded_causes=state.degraded_causes | {cause})
        return replace(result, outcome=Outcome.SET_DEGRADED)

    @staticmethod
    def _resource_available(state, event):
        causes = state.degraded_causes - {"LIVE_RESOURCES_UNAVAILABLE"}
        if causes == state.degraded_causes:
            return Result(Outcome.NO_STATE_CHANGE, state)
        return SafetyEngine._commit(state, degraded=bool(causes), degraded_causes=causes)

    @staticmethod
    def _resource_fallback(state, event):
        return Result(Outcome.NO_STATE_CHANGE, state, action="USE_BUILT_IN_RESOURCES")

    @staticmethod
    def _output_fallback(state, event):
        if state.interaction_mode == Mode.URGENT:
            return Result(Outcome.NO_STATE_CHANGE, state, action="USE_STATIC_URGENT_TEMPLATE")
        return Result(Outcome.REJECT_EVENT, state)

    def _evidence(self, state, event):
        if not isinstance(event.proposed_tier, Mode):
            return Result(Outcome.REJECT_EVENT, state, reason="invalid proposed tier")
        outputs = event.detector_outputs
        if any(not isinstance(o.proposed_tier, Mode) or o.detector_id not in {"D1", "D2", "D3", "D4", "D5", "D6"}
               or (o.detector_id == "D6" and o.proposed_tier > Mode.CLARIFY) for o in outputs):
            return Result(Outcome.REJECT_EVENT, state, reason="invalid detector output")
        if outputs and event.proposed_tier > max(o.proposed_tier for o in outputs):
            return Result(Outcome.REJECT_EVENT, state, reason="aggregate proposal exceeds detector outputs")
        tier = max((event.proposed_tier, *(o.proposed_tier for o in outputs)))
        recovered = (event.kind == EventKind.DETECTORS_COMPLETE
                     and state.degraded_causes <= {"DETECTOR_TIMEOUT", "DETECTOR_ERROR"})
        if state.degraded and not recovered and (any(o.detector_id != "D1" for o in outputs) or (tier > Mode.NORMAL and not outputs)):
            return Result(Outcome.DEFER_EVENT, state, reason="only D1 evidence allowed while detector degraded")
        if event.kind == EventKind.LATE_DETECTOR_RESULT and event.source_episode_id is None:
            return Result(Outcome.REJECT_EVENT, state, reason="late result requires source episode")
        recovery_changes = {"degraded": False, "degraded_causes": frozenset()} if recovered and state.degraded else {}
        if tier <= state.interaction_mode:
            result = self._commit(state, **recovery_changes) if recovery_changes else Result(Outcome.NO_STATE_CHANGE, state)
            return replace(result, source_episode_id=event.source_episode_id)
        if state.episode_status in (Status.NONE, Status.CLOSED):
            if not event.episode_id:
                return Result(Outcome.REJECT_EVENT, state, reason="new episode ID required")
            if event.episode_id == state.episode_id:
                return Result(Outcome.REJECT_EVENT, state, reason="new episode must have a distinct ID")
            previous_id = state.episode_id if state.episode_status == Status.CLOSED else None
            flags = tuple(f for f in state.flags if f.source_episode_id is None
                          or f.name == FlagName.RECENT_HIGH_TIER_EPISODE)
            if previous_id and state.episode_peak_tier >= Mode.URGENT:
                days = int(self.config.recent_high_tier_ttl[1:-1])
                flags += (PolicyFlag(FlagName.RECENT_HIGH_TIER_EPISODE, previous_id,
                                     event.occurred_at, event.occurred_at + timedelta(days=days),
                                     (("prior_peak", state.episode_peak_tier.name),)),)
            result = self._commit(state, interaction_mode=tier, episode_peak_tier=tier,
                                  episode_status=Status.OPEN, episode_id=event.episode_id,
                                  flags=flags, dropout_reason=None, **recovery_changes)
            result = replace(result, previous_episode_id=previous_id,
                             archived_episode=state if previous_id else None)
        else:
            changes = dict(interaction_mode=tier, episode_peak_tier=max(state.episode_peak_tier, tier))
            if state.episode_status == Status.RECHECK_REQUIRED:
                if tier >= Mode.URGENT:
                    changes["episode_status"] = Status.OPEN
                changes["flags"] = tuple(f for f in state.flags if f.name != FlagName.RECHECK_PASSED)
            elif state.episode_status == Status.DROPOUT and state.dropout_reason == DropoutReason.DURING_URGENT and tier == Mode.IMMEDIATE:
                changes["dropout_reason"] = DropoutReason.DURING_IMMEDIATE
            changes.update(recovery_changes)
            result = self._commit(state, **changes)
        return replace(result, source_episode_id=event.source_episode_id)

    @staticmethod
    def _close_simple(state, event):
        if state.degraded:
            return Result(Outcome.DEFER_EVENT, state)
        return SafetyEngine._commit(state, interaction_mode=Mode.NORMAL, episode_status=Status.CLOSED)

    def _deescalate(self, state, event):
        target = (self.config.urgent_deescalation_target if event.kind == EventKind.URGENT_DEESCALATION_APPROVED
                  else self.config.immediate_deescalation_target)
        if target is None:
            return Result(Outcome.REJECT_EVENT, state, reason="de-escalation target pending clinical configuration")
        return self._commit(state, interaction_mode=target, episode_status=Status.RECHECK_REQUIRED)

    def _t2_timeout(self, state, event):
        if self.config.t2_timeout_action != "HOLD_ELEVATED_WITH_FLAG":
            return Result(Outcome.REJECT_EVENT, state, reason="unsupported T2 action")
        if any(f.name == FlagName.T2_FOLLOWUP_INCOMPLETE and f.source_episode_id == state.episode_id for f in state.flags):
            return Result(Outcome.NO_STATE_CHANGE, state)
        flag = PolicyFlag(FlagName.T2_FOLLOWUP_INCOMPLETE, state.episode_id, event.occurred_at)
        return self._commit(state, flags=state.flags + (flag,))

    @staticmethod
    def _high_dropout(state, event):
        reason = DropoutReason.DURING_URGENT if state.interaction_mode == Mode.URGENT else DropoutReason.DURING_IMMEDIATE
        return SafetyEngine._commit(state, episode_status=Status.DROPOUT, dropout_reason=reason)

    @staticmethod
    def _recheck_dropout(state, event):
        return SafetyEngine._commit(state, episode_status=Status.DROPOUT,
                                    dropout_reason=DropoutReason.RECHECK_NOT_COMPLETED)

    def _reentry(self, state, event):
        target = self.config.dropout_reentry_target_by_peak[state.episode_peak_tier]
        return self._commit(state, interaction_mode=target, episode_status=Status.RECHECK_REQUIRED,
                            dropout_reason=None)

    @staticmethod
    def _recheck_passed(state, event):
        if any(f.name == FlagName.RECHECK_PASSED and f.source_episode_id == state.episode_id for f in state.flags):
            return Result(Outcome.NO_STATE_CHANGE, state)
        return SafetyEngine._commit(state, flags=state.flags + (PolicyFlag(FlagName.RECHECK_PASSED, state.episode_id, event.occurred_at),))

    def _recheck_failed(self, state, event):
        target = self.config.recheck_failed_target_by_peak[state.episode_peak_tier]
        if target < state.interaction_mode and event.based_on_sequence != state.sequence:
            return Result(Outcome.REJECT_EVENT, state, reason="stale or missing CAS sequence")
        flags = tuple(f for f in state.flags if f.name != FlagName.RECHECK_PASSED)
        return self._commit(state, interaction_mode=target, episode_status=Status.OPEN, flags=flags)

    @staticmethod
    def _close_recheck(state, event):
        if event.unresolved_higher_result or not any(f.name == FlagName.RECHECK_PASSED and f.source_episode_id == state.episode_id for f in state.flags):
            return Result(Outcome.REJECT_EVENT, state, reason="re-check closure preconditions missing")
        return SafetyEngine._commit(state, interaction_mode=Mode.NORMAL, episode_status=Status.CLOSED)

    @staticmethod
    def _expire_flag(state, event):
        if event.flag_name is None:
            return Result(Outcome.REJECT_EVENT, state, reason="flag name required")
        flags = tuple(f for f in state.flags if not (f.name == event.flag_name and f.expires_at is not None and f.expires_at <= event.occurred_at))
        if flags == state.flags:
            return Result(Outcome.NO_STATE_CHANGE, state)
        return SafetyEngine._commit(state, flags=flags)

    def _archive(self, state, event):
        flags = tuple(f for f in state.flags if f.source_episode_id is None
                      or f.name == FlagName.RECENT_HIGH_TIER_EPISODE)
        if state.episode_peak_tier >= Mode.URGENT:
            days = int(self.config.recent_high_tier_ttl[1:-1])
            flags += (PolicyFlag(FlagName.RECENT_HIGH_TIER_EPISODE, state.episode_id,
                                 event.occurred_at, event.occurred_at + timedelta(days=days),
                                 (("prior_peak", state.episode_peak_tier.name),)),)
        result = self._commit(state, interaction_mode=Mode.NORMAL, episode_status=Status.NONE,
                              episode_peak_tier=Mode.NORMAL, episode_id=None, flags=flags)
        return replace(result, archived_episode=state)

    @staticmethod
    def _set_flag(state, event):
        if event.flag_name is None or not isinstance(event.flag_name, FlagName):
            return Result(Outcome.REJECT_EVENT, state, reason="valid flag name required")
        flag = PolicyFlag(event.flag_name, state.episode_id, event.occurred_at,
                          event.flag_expires_at)
        flags = tuple(f for f in state.flags if not (f.name == flag.name and f.source_episode_id == flag.source_episode_id))
        return SafetyEngine._commit(state, flags=flags + (flag,))


class SafetyStore:
    """One logical writer per patient in this process; persistence is a later milestone."""

    def __init__(self, engine: SafetyEngine | None = None):
        self.engine = engine or SafetyEngine()
        self._states: dict[str, SafetyState] = {}
        self._locks: dict[str, RLock] = {}
        self._registry_lock = RLock()
        self.audit: list[dict] = []
        self.event_log: list[dict] = []
        self._quarantined: set[str] = set()
        self.closed_snapshots: dict[tuple[str, str], SafetyState] = {}
        self.archived_episodes: dict[tuple[str, str], SafetyState] = {}

    def initialize(self, patient_id: str, state: SafetyState) -> None:
        if not state_valid(state):
            raise ValueError("initial state is invalid")
        with self._registry_lock:
            if patient_id in self._states:
                raise ValueError("patient safety context already initialized")
            self._states[patient_id] = state
            self._locks[patient_id] = RLock()
            if state.episode_status == Status.CLOSED:
                self.closed_snapshots[(patient_id, state.episode_id)] = state

    def apply(self, patient_id: str, event: Event) -> Result:
        with self._registry_lock:
            lock = self._locks.setdefault(patient_id, RLock())
        with lock:
            before = self._states.get(patient_id, SafetyState())
            if patient_id in self._quarantined:
                result = Result(Outcome.DEFER_EVENT, before, reason="fail-closed quarantine")
                self.event_log.append({"patient_id": patient_id, "event": event.kind.value,
                                       "source_episode_id": event.source_episode_id,
                                       "outcome": result.outcome.value, "sequence": before.sequence})
                return result
            result = self.engine.apply(before, event)
            self.event_log.append({"patient_id": patient_id, "event": event.kind.value,
                                   "source_episode_id": result.source_episode_id or event.source_episode_id,
                                   "outcome": result.outcome.value, "sequence": result.state.sequence,
                                   "input_id": event.input_id,
                                   "detector_outputs": event.detector_outputs})
            if result.outcome == Outcome.SET_DEGRADED and (result.state == before or not state_valid(result.state)):
                self._quarantined.add(patient_id)
                self.audit.append({
                    "patient_id": patient_id, "episode_id": before.episode_id,
                    "previous_state": before, "event": event, "resulting_state": None,
                    "outcome": Outcome.SET_DEGRADED, "reason": result.reason,
                    "sequence": before.sequence, "policy_version": POLICY_VERSION,
                    "policy_config_version": self.engine.config.version,
                    "clock_timestamp": event.occurred_at, "degraded_causes": result.state.degraded_causes,
                })
            if result.state != before and state_valid(result.state):
                if result.archived_episode is not None:
                    episode_id = result.archived_episode.episode_id
                    key = (patient_id, episode_id)
                    self.archived_episodes[key] = self.closed_snapshots.get(key, result.archived_episode)
                self._states[patient_id] = result.state
                if result.state.episode_status == Status.CLOSED and before.episode_status != Status.CLOSED:
                    self.closed_snapshots[(patient_id, result.state.episode_id)] = result.state
                self.audit.append({
                    "patient_id": patient_id, "episode_id": result.state.episode_id,
                    "source_episode_id": result.source_episode_id, "previous_state": before,
                    "previous_episode_id": result.previous_episode_id,
                    "event": event, "flags": result.state.flags,
                    "detector_outputs": event.detector_outputs, "proposed_tier": event.proposed_tier,
                    "resulting_state": result.state, "sequence": result.state.sequence,
                    "policy_version": POLICY_VERSION, "policy_config_version": self.engine.config.version,
                    "clock_timestamp": event.occurred_at, "resource_version": event.resource_version,
                    "transition_type": "named_downgrade" if result.state.interaction_mode < before.interaction_mode else "upgrade_or_other",
                    "cas_base_sequence": event.based_on_sequence, "degraded_causes": result.state.degraded_causes,
                    "dropout_reason": result.state.dropout_reason,
                    "closure_reason": event.kind.value if result.state.episode_status == Status.CLOSED else None,
                })
            return result

    def get(self, patient_id: str) -> SafetyState:
        with self._registry_lock:
            return self._states.get(patient_id, SafetyState())

    def is_fail_closed(self, patient_id: str) -> bool:
        with self._registry_lock:
            return patient_id in self._quarantined or self._states.get(patient_id, SafetyState()).degraded
