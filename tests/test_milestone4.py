"""A1–A20: application integration over the accepted engines and synthetic fixtures."""

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
import inspect
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from fastapi.testclient import TestClient

from aura_app.api import create_app
from aura_app.models import AppError, ApplicationEvent, EventType
from aura_app.persistence import SQLiteRepositoryFactory
from aura_app.safety import FixtureSafetyGate
from aura_app.service import PatientEventService
from aura_app.simulator import run_case


def at(day: int) -> datetime:
    return datetime(2026, 1, 1, 12, tzinfo=timezone.utc) + timedelta(days=day)


class MilestoneFour(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = TemporaryDirectory()
        cls.root = Path(cls.temporary.name)
        cls.records = {case: run_case(case, 7, cls.root / f"{case}.sqlite3") for case in "ABCDEF"}

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def service(self, case="A", gate=None):
        return PatientEventService(SQLiteRepositoryFactory(self.root / f"{case}.sqlite3"), safety_gate=gate)

    def test_a1_api_controllers_have_no_domain_decision_logic(self):
        source = inspect.getsource(__import__("aura_app.api", fromlist=["create_app"]))
        self.assertNotIn("aura_longitudinal", source)
        self.assertNotIn("aura_safety", source)
        self.assertNotIn("assess_drift", source)
        self.assertNotIn("SafetyEngine", source)

    def test_a2_duplicate_idempotency_prevents_domain_processing(self):
        patient_id = self.records["A"]["patient_id"]
        event = ApplicationEvent("duplicate-probe", patient_id, EventType.PATIENT_CHECKIN,
                                 at(80), at(80), "patient", {"state": "Good"}, "corr", "duplicate-key")
        gate = FixtureSafetyGate({"duplicate-probe": ()})
        first = self.service("A", gate).process(event)
        before = len(self.service("A").timeline(patient_id))
        replay = self.service("A", FixtureSafetyGate({})).process(replace(event, event_id="second-id"))
        self.assertTrue(replay.idempotent_replay)
        self.assertEqual(first.communication_decision, replay.communication_decision)
        self.assertEqual(before, len(self.service("A").timeline(patient_id)))

    def test_a3_observation_cannot_mutate_anchor(self):
        record = self.records["B"]
        service = self.service("B")
        centers = {(b["signal"], b["metric"]): b["anchor"]["center"] for b in service.status(record["patient_id"])["signals"]}
        event = ApplicationEvent("new-observation", record["patient_id"], EventType.WEARABLE_OBSERVATION,
                                 at(80), at(80), "wearable", {"observations": [
                                     {"kind": "activity", "date": at(80).date().isoformat(),
                                      "metrics": {"steps": 2000}, "coverage": 1.0, "source": "synthetic_wearable"}]},
                                 "corr", "new-observation")
        service.process(event)
        after = {(b["signal"], b["metric"]): b["anchor"]["center"] for b in service.status(record["patient_id"])["signals"]}
        self.assertEqual(centers, after)

    def test_a4_named_command_reanchors_through_governed_path(self):
        db = self.root / "A4.sqlite3"
        factory = SQLiteRepositoryFactory(db)
        factory.initialize()
        service = PatientEventService(factory)
        service.create_patient(patient_id="anchor-test", display_name="Anchor fixture", age=35,
                               timezone_name="UTC", consents=[{"consent_type": "WEARABLE", "granted": True}])
        for index in range(10):
            value = 100 if index < 5 else 200
            event = ApplicationEvent(f"obs-{index}", "anchor-test", EventType.WEARABLE_OBSERVATION,
                                     at(index), at(index), "fixture", {"observations": [{"kind": "activity",
                                         "date": at(index).date().isoformat(), "metrics": {"steps": value},
                                         "coverage": 1.0, "source": "watch"}]}, "c", f"obs-{index}")
            service.process(event)
        key = {"signal": "ACTIVITY", "source": "watch", "metric": "steps"}
        first = ApplicationEvent("anchor-first", "anchor-test", EventType.ANCHOR_COMMAND,
                                 at(10), at(10), "reviewer", {**key, "action": "CREATE_PROVISIONAL_ANCHOR",
                                   "reference_start": at(0).date().isoformat(),
                                   "reference_end": at(4).date().isoformat()}, "c", "anchor-first")
        with self.assertRaises(AppError):
            service.process(first)
        service.command_anchor(first)
        before = service.status("anchor-test")["signals"][0]["anchor"]["center"]
        second = replace(first, event_id="anchor-second", idempotency_key="anchor-second", occurred_at=at(11),
                         received_at=at(11), payload={**key, "action": "CLINICAL_REVIEW_REANCHOR",
                         "reference_start": at(5).date().isoformat(),
                         "reference_end": at(9).date().isoformat(), "reviewed_by": "synthetic-reviewer"})
        service.command_anchor(second)
        after = service.status("anchor-test")["signals"][0]["anchor"]["center"]
        self.assertEqual((before, after), (100, 200))

    def test_a5_longitudinal_output_persists_in_timeline(self):
        timeline = self.service("B").timeline(self.records["B"]["patient_id"])
        self.assertTrue(any(row["record_type"] == "LONGITUDINAL_DRIFT" and
                            row["detail"]["kind"] in {"PERSISTENT_DRIFT", "ROLLING_ANCHOR_DIVERGENCE"}
                            for row in timeline))

    def test_a6_explanation_creates_held_state(self):
        held = self.service("D").status(self.records["D"]["patient_id"])["held_for_review"]
        self.assertEqual(len(held), 2)
        self.assertTrue(all(row["status"] == "EXPLAINED_HELD_FOR_REVIEW" for row in held))

    def test_a7_review_snapshot_includes_held(self):
        snapshot = self.service("D").review_snapshot(self.records["D"]["patient_id"])
        self.assertEqual(len(snapshot["explained_held_for_review"]), 2)
        self.assertEqual(len(snapshot["unresolved_items"]), 2)

    def test_a8_review_snapshot_never_implies_sharing(self):
        snapshot = self.service("D").review_snapshot(self.records["D"]["patient_id"])
        self.assertFalse(snapshot["automatically_sent"])
        self.assertEqual(snapshot["share_status"], "NOT_SHARED")
        self.assertTrue(all(item["share_status"] == "NOT_SHARED" for item in snapshot["unresolved_items"]))

    def test_a9_safety_precedence_over_quiet(self):
        case = self.records["F"]
        self.assertEqual(case["decisions"][-1]["decision"], "SAFETY_REVIEW_REQUIRED")
        self.assertEqual(case["safety"]["interaction_mode"], "CLARIFY")

    def test_a10_application_does_not_assign_safety_tiers(self):
        source = inspect.getsource(__import__("aura_app.service", fromlist=["PatientEventService"]))
        self.assertNotIn("Mode.CLARIFY", source)
        self.assertNotIn("Mode.ELEVATED", source)
        self.assertNotIn("Mode.URGENT", source)
        self.assertNotIn("Mode.IMMEDIATE", source)
        self.assertIn("self.safety_engine.apply", source)

    def test_a11_free_text_reaches_gate_before_conversation(self):
        class RecordingGate:
            called = False
            def resolve(self, event, source_episode_id, source_sequence):
                self.called = True
                return ()
        gate = RecordingGate()
        service = self.service("A", gate)
        event = ApplicationEvent("free-text-probe", self.records["A"]["patient_id"], EventType.PATIENT_FREE_TEXT,
                                 at(81), at(81), "patient", {"text": "A neutral fixture sentence."},
                                 "corr", "free-text-probe")
        result = service.process(event)
        self.assertTrue(gate.called)
        self.assertEqual(result.conversation_status, "NORMAL_CONVERSATION_ALLOWED")

    def test_a12_transaction_rolls_back_partial_event(self):
        service = self.service("C", FixtureSafetyGate({"bad-explanation": ()}))
        patient_id = self.records["C"]["patient_id"]
        before = len(service.timeline(patient_id))
        event = ApplicationEvent("bad-explanation", patient_id, EventType.CONTEXT_EXPLANATION,
                                 at(82), at(82), "patient", {"context_event_id": "missing",
                                 "explanation": "fixture", "affected_signals": ["ACTIVITY"]},
                                 "corr", "bad-explanation")
        with self.assertRaises(AppError):
            service.process(event)
        with SQLiteRepositoryFactory(self.root / "C.sqlite3").transaction() as repo:
            self.assertFalse(any(row["event_id"] == event.event_id for row in repo.events(patient_id)))
        self.assertEqual(before, len(service.timeline(patient_id)))

    def test_a13_sensing_and_trust_survive_reload(self):
        status = self.service("E").status(self.records["E"]["patient_id"])
        self.assertTrue(all(row["sensing_state"] == "OBSERVED" and
                            row["trust_state"] == "REESTABLISHING" for row in status["signals"]))

    def test_a14_safety_episode_reference_survives_reload(self):
        patient_id = self.records["F"]["patient_id"]
        service = self.service("F")
        self.assertEqual(service.status(patient_id)["safety"]["interaction_mode"], "CLARIFY")
        self.assertTrue(service.review_snapshot(patient_id)["safety_episode_references"])

    def test_a15_cases_a_to_e_retain_accepted_behavior(self):
        self.assertEqual([self.records[c]["patient_interruptions"] for c in "ABCDE"], [0, 6, 6, 1, 0])
        self.assertEqual(self.records["D"]["review_items"], 2)
        self.assertEqual(self.records["E"]["signals"][0]["trust_state"], "REESTABLISHING")
        b = self.records["B"]["signals"]
        self.assertTrue(all(row["anchor"] is not None for row in b))

    def test_a16_case_f_safety_handoff(self):
        record = self.records["F"]
        self.assertEqual(record["latest_decision"], "SAFETY_REVIEW_REQUIRED")
        self.assertEqual(record["safety"]["episode_status"], "OPEN")
        self.assertTrue(any(row["safety"] and row["safety"]["interaction_mode"] == "CLARIFY"
                            for row in record["decisions"]))

    def test_a17_timeline_order_is_deterministic(self):
        service = self.service("D")
        patient_id = self.records["D"]["patient_id"]
        rows = service.timeline(patient_id)
        self.assertEqual(rows, service.timeline(patient_id))
        self.assertEqual([(row["occurred_at"], row["entry_id"]) for row in rows],
                         sorted((row["occurred_at"], row["entry_id"]) for row in rows))

    def test_a18_review_snapshot_is_deterministic(self):
        service = self.service("D")
        patient_id = self.records["D"]["patient_id"]
        self.assertEqual(service.review_snapshot(patient_id), service.review_snapshot(patient_id))

    def test_a19_no_endpoint_exposes_diagnostic_or_risk_score(self):
        app = create_app(service=self.service("B"))
        client = TestClient(app)
        patient_id = self.records["B"]["patient_id"]
        for route in ("status", "review-snapshot", "timeline"):
            response = client.get(f"/patients/{patient_id}/{route}")
            self.assertEqual(response.status_code, 200)
            self.assertFalse(any(f'"{field}"' in response.text for field in
                                 ("relapse_probability", "depression_score", "diagnosis", "psychiatric_risk_percentage")))

    def test_a20_api_restart_preserves_development_state(self):
        db = self.root / "B.sqlite3"
        patient_id = self.records["B"]["patient_id"]
        first = TestClient(create_app(db_path=db)).get(f"/patients/{patient_id}/status")
        second = TestClient(create_app(db_path=db)).get(f"/patients/{patient_id}/status")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json(), second.json())

    def test_http_create_ingest_and_fail_closed_free_text(self):
        db = self.root / "http.sqlite3"
        client = TestClient(create_app(db_path=db))
        created = client.post("/patients", json={"patient_id": "http-patient", "display_name": "HTTP fixture",
                                                 "age": 40, "timezone": "UTC",
                                                 "consents": [{"consent_type": "WEARABLE", "granted": True}]})
        self.assertEqual(created.status_code, 200)
        wearable = client.post("/patients/http-patient/events", json={
            "event_id": "http-watch", "event_type": "WEARABLE_OBSERVATION", "occurred_at": at(0).isoformat(),
            "source": "fixture", "idempotency_key": "http-watch",
            "payload": {"observations": [{"kind": "activity", "date": at(0).date().isoformat(),
                                          "metrics": {"steps": 7000}, "coverage": 1.0, "source": "watch"}]}})
        self.assertEqual(wearable.status_code, 200)
        self.assertEqual(client.get("/patients/http-patient/status").status_code, 200)
        free_text = client.post("/patients/http-patient/events", json={
            "event_id": "http-text", "event_type": "PATIENT_FREE_TEXT", "occurred_at": at(1).isoformat(),
            "source": "patient", "idempotency_key": "http-text", "payload": {"text": "fixture"}})
        self.assertEqual(free_text.status_code, 200)
        self.assertTrue(free_text.json()["safety"]["state"]["degraded"])
        self.assertEqual(free_text.json()["communication_decision"], "SAFETY_REVIEW_REQUIRED")
        self.assertEqual(free_text.json()["conversation_status"], "SAFETY_HANDOFF_OR_HELD")
        self.assertTrue(free_text.json()["longitudinal"]["deferred"])

    def test_held_input_waits_for_safety_recovery(self):
        db = self.root / "recovery.sqlite3"
        factory = SQLiteRepositoryFactory(db)
        factory.initialize()
        first = PatientEventService(factory)
        first.create_patient(patient_id="recovery", display_name="Recovery fixture", age=35,
                             timezone_name="UTC")
        held = ApplicationEvent("held-checkin", "recovery", EventType.PATIENT_CHECKIN,
                                at(0), at(0), "patient", {"state": "Rough"}, "c", "held-checkin")
        result = first.process(held)
        self.assertTrue(result.longitudinal["deferred"])
        self.assertEqual(first.review_snapshot("recovery")["patient_checkin_trend"], [])
        gate = FixtureSafetyGate({"held-checkin": (), "recovery-checkin": ()})
        recovered = PatientEventService(factory, safety_gate=gate)
        current = replace(held, event_id="recovery-checkin", idempotency_key="recovery-checkin",
                          occurred_at=at(1), received_at=at(1), payload={"state": "Good"})
        outcome = recovered.process(current)
        self.assertFalse(outcome.safety["state"]["degraded"])
        self.assertEqual(len(recovered.review_snapshot("recovery")["patient_checkin_trend"]), 2)
        self.assertTrue(any(row["record_type"] == "HELD_INPUT_RELEASED"
                            for row in recovered.timeline("recovery")))


if __name__ == "__main__":
    unittest.main()
