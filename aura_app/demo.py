"""Explicit synthetic-only M6 demo. Not a real detector or production server.

Scenario names/checkpoints stay in this developer/evaluation plane. The app service
receives only the accepted simulator's observable events and resolved fixtures.
"""

import argparse
from pathlib import Path

from aura_communication.provider import DisabledProvider
from .api import create_app
from .communication import PatientCommunicationService
from .models import EventType
from .persistence import SQLiteRepositoryFactory
from .safety import FixtureSafetyGate, SafetyGateUnavailable
from .service import PatientEventService
from .simulator import run_case


CHECKPOINTS = (
    ("stable", "Stable day", "A", 20, True),
    ("A", "A · Physical illness", "A", 34, True),
    ("B", "B · Slow change", "B", 69, True),
    ("C", "C · Illness + independent change", "C", 40, True),
    ("D-before", "D · Before explanation", "D", 30, False),
    ("D", "D · Explained, held for review", "D", 69, True),
    ("E-gap", "E · Wearable unavailable", "E", 54, True),
    ("E", "E · Wearable returned", "E", 69, True),
    ("F", "F · Safety handoff", "F", 69, True),
)


class DemoFixtureGate:
    """Finite declared fixtures, restricted to demo patients. Unknown input fails closed.

    No arbitrary text is classified as benign. These fixtures are engineering
    demonstrations, not clinically validated detectors or resolved real-world risk.
    """

    def __init__(self, patient_ids):
        self.patient_ids = frozenset(patient_ids)

    def resolve(self, event, source_episode_id, source_sequence):
        if event.patient_id not in self.patient_ids:
            raise SafetyGateUnavailable("not an enrolled synthetic fixture")
        normal = False
        payload = event.payload
        if event.event_type == EventType.PATIENT_CHECKIN:
            normal = set(payload) == {"state"} and payload["state"] in {"Good", "Okay", "Rough"}
        elif event.event_type == EventType.MEDICATION_EVENT:
            normal = set(payload) == {"scheduled_time", "status"} and payload["status"] in {"ACKNOWLEDGED", "MISSED", "UNKNOWN"}
        elif event.event_type == EventType.CONTEXT_EXPLANATION:
            normal = payload.get("explanation") == "new stable work schedule"
        elif event.event_type == EventType.PATIENT_FREE_TEXT:
            normal = payload == {"text": "fixture ordinary message"}
            if payload == {"text": "fixture safety concern"}:
                return FixtureSafetyGate({event.event_id: (("D2", "CLARIFY"),)}).resolve(
                    event, source_episode_id, source_sequence)
        if normal:
            return ()
        raise SafetyGateUnavailable("no reviewed/resolved fixture for this input")


def demo_catalog(seed=7):
    return [{"id": key, "label": label, "patient_id": f"demo-{key}-{seed}",
             "synthetic": True} for key, label, *_ in CHECKPOINTS]


def prepare(db_path, seed=7):
    factory = SQLiteRepositoryFactory(db_path)
    factory.initialize()
    for key, label, case, day, explain in CHECKPOINTS:
        patient_id = f"demo-{key}-{seed}"
        with factory.transaction() as repo:
            exists = repo.patient(patient_id) is not None
        if not exists:
            run_case(case, seed, db_path, through_day=day, patient_id=patient_id,
                     event_prefix=patient_id, include_explanation=explain)
    return factory


def create_demo_app(db_path=None, seed=7):
    import os
    db_path = db_path or os.environ.get("AURA_DEMO_DB", "aura-m6-demo.sqlite3")
    factory = prepare(db_path, seed)
    catalog = demo_catalog(seed)
    service = PatientEventService(factory, safety_gate=DemoFixtureGate(item["patient_id"] for item in catalog))
    # No external provider, even if AURA_COMMUNICATION_ENDPOINT happens to be set.
    app = create_app(service=service, communication_service=PatientCommunicationService(service, provider=DisabledProvider()))

    @app.get("/demo/scenarios")
    def scenarios():
        return {"synthetic_only": True, "scenarios": catalog,
                "notice": "Resolved safety fixtures only. Arbitrary text is held, not classified."}

    return app


def main():
    parser = argparse.ArgumentParser(description="Seed accepted synthetic checkpoint fixtures (no real patient data)")
    parser.add_argument("--db", type=Path, default=Path("aura-m6-demo.sqlite3"))
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    prepare(args.db, args.seed)
    print(f"Synthetic checkpoints ready in {args.db}. Existing patients were preserved.")


if __name__ == "__main__":
    main()
