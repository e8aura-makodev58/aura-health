"""Developer CLI for deterministic safety scenarios and exact policy replay."""

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from pathlib import Path

from .codec import event_from_dict, event_to_dict, state_from_dict, state_to_dict
from .config import config_dict, load_config, parse_config
from .domain import EventKind, state_valid
from .engine import SafetyEngine, SafetyStore
from .offline import HeldInput, InMemoryInputFixture, OfflineSafetyGate
from .resources import ResourceRegistry


@dataclass
class InjectableClock:
    now: datetime

    def advance_to(self, timestamp: datetime) -> None:
        if timestamp < self.now:
            raise ValueError("clock cannot move backward")
        self.now = timestamp

    def advance(self, seconds: float) -> None:
        if seconds < 0:
            raise ValueError("clock cannot move backward")
        self.now += timedelta(seconds=seconds)


def run_scenario(scenario: dict) -> dict:
    config = parse_config(scenario["policy_config"]) if "policy_config" in scenario else load_config()
    initial = state_from_dict(scenario.get("initial_state", {}))
    if not state_valid(initial):
        raise ValueError("initial safety state invalid")
    patient_id = scenario.get("patient_id", "simulated-patient")
    start = datetime.fromisoformat(scenario.get("start_at", "2026-09-23T00:00:00+00:00"))
    clock = InjectableClock(start)
    resource_version = scenario.get("resource_version", "fixture-unverified-v1")
    store = SafetyStore(SafetyEngine(config))
    store.initialize(patient_id, initial)
    registry = ResourceRegistry()
    offline_store = InMemoryInputFixture()
    offline_gate = OfflineSafetyGate(registry, offline_store)
    normalized_steps: list[dict] = []
    trace: list[dict] = []

    def apply_event(raw: dict):
        event_raw = dict(raw)
        if event_raw.get("based_on_sequence") == "current":
            event_raw["based_on_sequence"] = store.get(patient_id).sequence
        event = event_from_dict(event_raw, clock.now, resource_version)
        before = store.get(patient_id)
        result = store.apply(patient_id, event)
        normalized_steps.append({"type": "event", "event": event_to_dict(event)})
        trace.append({
            "type": "event", "event": event_to_dict(event),
            "before": state_to_dict(before), "outcome": result.outcome.value,
            "after": state_to_dict(result.state), "action": result.action,
            "reason": result.reason, "source_episode_id": result.source_episode_id,
            "previous_episode_id": result.previous_episode_id,
            "archived_episode_id": result.archived_episode.episode_id if result.archived_episode else None,
        })

    for step in scenario.get("steps", []):
        step_type = step.get("type", "event")
        if step_type == "event":
            apply_event(step.get("event", step))
        elif step_type == "advance":
            if "to" in step:
                clock.advance_to(datetime.fromisoformat(step["to"]))
            else:
                clock.advance(step["seconds"])
            normalized_steps.append({"type": "advance", "to": clock.now.isoformat()})
            trace.append({"type": "advance", "now": clock.now.isoformat()})
        elif step_type == "race":
            # Given arrival order is the single writer's commit order.
            for event_raw in step["events"]:
                apply_event(event_raw)
        elif step_type == "offline_input":
            timestamp = datetime.fromisoformat(step["original_timestamp"]) if "original_timestamp" in step else clock.now
            item = HeldInput(step["input_id"], timestamp, step.get("payload", "fixture input"))
            plan = offline_gate.hold(store.get(patient_id), item)
            normalized_steps.append({"type": "offline_input", "input_id": item.input_id,
                                     "original_timestamp": item.original_timestamp.isoformat(), "payload": item.payload})
            trace.append({"type": "offline_input", "input_id": item.input_id,
                          "assessed": plan.input_assessed, "may_generate": plan.may_generate,
                          "resource_version": plan.pinned_resources.bundle.version})
        elif step_type == "reconnect":
            if step.get("emit_event", True):
                apply_event({"kind": EventKind.CLIENT_RECONNECTED.value})
            pending = offline_gate.reconnect()
            normalized_steps.append({"type": "reconnect", "emit_event": False,
                                     "pending_ids": [x.input_id for x in pending]})
            trace.append({"type": "reconnect", "pending_ids": [x.input_id for x in pending],
                          "assessed": False})
        else:
            raise ValueError(f"unknown simulator step: {step_type}")

    return {
        "schema_version": 1, "patient_id": patient_id,
        "initial_state": state_to_dict(initial), "start_at": start.isoformat(),
        "policy_config": config_dict(config), "resource_version": resource_version,
        "normalized_steps": normalized_steps, "trace": trace,
        "final_state": state_to_dict(store.get(patient_id)),
        "archived_episodes": {episode_id: state_to_dict(value)
                              for (owner, episode_id), value in store.archived_episodes.items()
                              if owner == patient_id},
    }


def replay(record: dict) -> dict:
    scenario = {
        "patient_id": record["patient_id"], "initial_state": record["initial_state"],
        "start_at": record["start_at"], "policy_config": record["policy_config"],
        "resource_version": record["resource_version"],
        "steps": record["normalized_steps"],
    }
    repeated = run_scenario(scenario)
    for key in ("trace", "final_state", "archived_episodes"):
        if repeated[key] != record[key]:
            raise AssertionError(f"replay diverged: {key}")
    return repeated


def main(argv=None):
    parser = argparse.ArgumentParser(description="AURA deterministic safety-state simulator")
    sub = parser.add_subparsers(dest="command", required=True)
    run_parser = sub.add_parser("run", help="run a JSON scenario")
    run_parser.add_argument("scenario", type=Path)
    run_parser.add_argument("--save", type=Path, help="save normalized replay record")
    replay_parser = sub.add_parser("replay", help="verify a saved replay record")
    replay_parser.add_argument("record", type=Path)
    args = parser.parse_args(argv)
    if args.command == "run":
        record = run_scenario(json.loads(args.scenario.read_text()))
        for index, item in enumerate(record["trace"], 1):
            if item["type"] == "event":
                after = item["after"]
                print(f"{index:03d} {item['event']['kind']}: {item['outcome']} -> "
                      f"{after['interaction_mode']}/{after['episode_status']} "
                      f"peak={after['episode_peak_tier']} seq={after['sequence']} "
                      f"episode={after['episode_id']} action={item['action']}")
            else:
                print(f"{index:03d} {item['type']}: {item}")
        if args.save:
            args.save.write_text(json.dumps(record, indent=2) + "\n")
            print(f"Saved replay record: {args.save}")
    else:
        record = json.loads(args.record.read_text())
        replay(record)
        print(f"Replay matched {len(record['trace'])} trace entries")


if __name__ == "__main__":
    main()
