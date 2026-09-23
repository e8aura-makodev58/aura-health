"""Canonical JSON records for simulator traces and policy replay."""

from datetime import datetime

from .domain import (
    DetectorOutput, DropoutReason, Event, EventKind, FlagName, Mode,
    PolicyFlag, SafetyState, Status,
)


def _dt(value):
    return datetime.fromisoformat(value) if value is not None else None


def flag_to_dict(flag: PolicyFlag) -> dict:
    return {
        "name": flag.name.value, "source_episode_id": flag.source_episode_id,
        "set_at": flag.set_at.isoformat(),
        "expires_at": flag.expires_at.isoformat() if flag.expires_at else None,
        "metadata": dict(flag.metadata),
    }


def flag_from_dict(raw: dict) -> PolicyFlag:
    return PolicyFlag(FlagName(raw["name"]), raw.get("source_episode_id"),
                      _dt(raw["set_at"]), _dt(raw.get("expires_at")),
                      tuple(sorted(raw.get("metadata", {}).items())))


def state_to_dict(state: SafetyState) -> dict:
    return {
        "interaction_mode": state.interaction_mode.name,
        "episode_status": state.episode_status.value,
        "episode_peak_tier": state.episode_peak_tier.name,
        "flags": [flag_to_dict(f) for f in state.flags],
        "dropout_reason": state.dropout_reason.value if state.dropout_reason else None,
        "degraded": state.degraded,
        "degraded_causes": sorted(state.degraded_causes),
        "sequence": state.sequence, "episode_id": state.episode_id,
    }


def state_from_dict(raw: dict) -> SafetyState:
    return SafetyState(
        interaction_mode=Mode[raw.get("interaction_mode", "NORMAL")],
        episode_status=Status(raw.get("episode_status", "NONE")),
        episode_peak_tier=Mode[raw.get("episode_peak_tier", "NORMAL")],
        flags=tuple(flag_from_dict(f) for f in raw.get("flags", [])),
        dropout_reason=DropoutReason(raw["dropout_reason"]) if raw.get("dropout_reason") else None,
        degraded=raw.get("degraded", False),
        degraded_causes=frozenset(raw.get("degraded_causes", [])),
        sequence=raw.get("sequence", 0), episode_id=raw.get("episode_id"),
    )


def output_to_dict(output: DetectorOutput) -> dict:
    return {
        "detector_id": output.detector_id, "proposed_tier": output.proposed_tier.name,
        "input_id": output.input_id, "source_episode_id": output.source_episode_id,
        "source_sequence": output.source_sequence,
    }


def output_from_dict(raw: dict) -> DetectorOutput:
    return DetectorOutput(raw["detector_id"], Mode[raw["proposed_tier"]],
                          raw["input_id"], raw.get("source_episode_id"),
                          raw["source_sequence"])


def event_to_dict(event: Event) -> dict:
    return {
        "kind": event.kind.value, "occurred_at": event.occurred_at.isoformat(),
        "based_on_sequence": event.based_on_sequence,
        "proposed_tier": event.proposed_tier.name,
        "detector_outputs": [output_to_dict(o) for o in event.detector_outputs],
        "episode_id": event.episode_id, "source_episode_id": event.source_episode_id,
        "flag_name": event.flag_name.value if event.flag_name else None,
        "flag_expires_at": event.flag_expires_at.isoformat() if event.flag_expires_at else None,
        "unresolved_higher_result": event.unresolved_higher_result,
        "input_id": event.input_id, "structured_answer": event.structured_answer,
        "resource_version": event.resource_version,
    }


def event_from_dict(raw: dict, now: datetime | None = None, resource_version: str | None = None) -> Event:
    timestamp = _dt(raw.get("occurred_at")) or now
    if timestamp is None:
        raise ValueError("event timestamp required")
    return Event(
        kind=EventKind(raw["kind"]), occurred_at=timestamp,
        based_on_sequence=raw.get("based_on_sequence"),
        proposed_tier=Mode[raw.get("proposed_tier", "NORMAL")],
        detector_outputs=tuple(output_from_dict(o) for o in raw.get("detector_outputs", [])),
        episode_id=raw.get("episode_id"), source_episode_id=raw.get("source_episode_id"),
        flag_name=FlagName(raw["flag_name"]) if raw.get("flag_name") else None,
        flag_expires_at=_dt(raw.get("flag_expires_at")),
        unresolved_higher_result=raw.get("unresolved_higher_result", False),
        input_id=raw.get("input_id"), structured_answer=raw.get("structured_answer"),
        resource_version=raw.get("resource_version", resource_version),
    )
