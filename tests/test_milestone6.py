"""UI1–UI15 transport/contract checks; real browser companions live in tests/browser/."""

from datetime import datetime, timezone
import inspect
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from aura_app.api import create_app
from aura_app.demo import create_demo_app, DemoFixtureGate
from aura_app.models import ApplicationEvent, EventType
from aura_app.safety import SafetyGateUnavailable
from aura_safety.resources import fixture_bundle


class MilestoneSix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = TemporaryDirectory()
        cls.db = Path(cls.temporary.name) / "ui.sqlite3"
        cls.app = create_demo_app(cls.db)
        cls.client = TestClient(cls.app)
        cls.html = cls.client.get("/").text
        cls.js = cls.client.get("/assets/app.js").text
        cls.css = cls.client.get("/assets/styles.css").text

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        cls.temporary.cleanup()

    def status(self, key):
        return self.client.get(f"/patients/demo-{key}-7/status").json()

    def ingest(self, key, kind, payload):
        event_id = str(uuid4())
        at = self.client.get(f"/patients/demo-{key}-7/view").json()["latest_occurred_at"]
        body = {"event_id": event_id, "event_type": kind, "occurred_at": at,
                "source": "patient", "payload": payload, "correlation_id": event_id,
                "idempotency_key": event_id}
        response = self.client.post(f"/patients/demo-{key}-7/events", json=body)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_ui1_stable_home_has_no_risk_score(self):
        self.assertEqual(self.status("stable")["latest_communication_decision"], "STAY_QUIET")
        self.assertIn("No question from AURA right now.", self.html)
        self.assertNotIn("risk_score", self.js)

    def test_ui2_checkin_reaches_existing_api(self):
        result = self.ingest("stable", "PATIENT_CHECKIN", {"state": "Good"})
        self.assertFalse(result["longitudinal"]["deferred"])
        timeline = self.client.get("/patients/demo-stable-7/timeline").json()
        self.assertTrue(any(row["event_id"] == result["event_id"] and row["record_type"] == "PATIENT_CHECKIN" for row in timeline))

    def test_ui3_optional_note_is_safety_gated(self):
        # Separate patient: the demo gate cannot treat arbitrary text as a resolved fixture.
        self.client.post("/patients", json={"patient_id":"unscripted", "display_name":"Synthetic", "age":35})
        at = datetime.now(timezone.utc).isoformat()
        response = self.client.post("/patients/unscripted/events", json={
            "event_type":"PATIENT_FREE_TEXT", "occurred_at":at, "source":"patient",
            "payload":{"text":"arbitrary optional note"}, "idempotency_key":"note"})
        result = response.json()
        self.assertEqual(result["communication_decision"], "SAFETY_REVIEW_REQUIRED")
        self.assertTrue(result["safety"]["state"]["degraded"])
        self.assertTrue(result["longitudinal"]["deferred"])

    def test_ui4_explanation_uses_existing_governed_path(self):
        before = self.status("D-before")
        option = self.client.get("/patients/demo-D-before-7/view").json()["explanation_options"][0]
        response = self.client.post("/patients/demo-D-before-7/context-explanations", json={
            "occurred_at":"2026-01-31T12:00:00+00:00", "context_event_id":option["context_event_id"],
            "affected_signals":option["affected_signals"], "explanation":"new stable work schedule",
            "idempotency_key":"ui-explanation"})
        self.assertEqual(response.status_code, 200, response.text)
        after = self.status("D-before")
        self.assertEqual(len(after["held_for_review"]), 2)
        self.assertEqual([s["anchor"] for s in before["signals"]], [s["anchor"] for s in after["signals"]])

    def test_ui5_held_observation_retained_and_visible(self):
        for row in self.status("D")["held_for_review"]:
            self.assertEqual(row["status"], "EXPLAINED_HELD_FOR_REVIEW")
            self.assertTrue(row["record"]["detected_drift"]["description"])
        self.assertIn("The anchored reference is unchanged.", self.js)

    def test_ui6_gap_is_unobserved_not_pathological(self):
        signals = self.status("E-gap")["signals"]
        self.assertTrue(all(s["sensing_state"] == "UNOBSERVED" for s in signals))
        self.assertTrue(all(s["rolling"]["mean"] is None and s["rolling"]["sample_count"] == 0 for s in signals))
        self.assertIn("No current value is inferred from the gap.", self.js)

    def test_ui7_reestablishing_shows_uncertainty(self):
        self.assertTrue(all(s["trust_state"] == "REESTABLISHING" for s in self.status("E")["signals"]))
        self.assertIn("No automatic exit rule is configured.", self.js)

    def test_ui8_medication_records_without_dose_controls(self):
        result = self.ingest("stable", "MEDICATION_EVENT", {"scheduled_time":"2026-01-21T12:00:00+00:00", "status":"ACKNOWLEDGED"})
        self.assertFalse(result["longitudinal"]["deferred"])
        self.assertNotIn('name="dose"', self.html)
        self.assertNotIn('name="taper"', self.html)

    def test_ui9_safety_precedence_survives_ordinary_checkin(self):
        result = self.ingest("F", "PATIENT_CHECKIN", {"state":"Good"})
        self.assertEqual(result["communication_decision"], "SAFETY_REVIEW_REQUIRED")
        reply = self.client.post(f"/patients/demo-F-7/events/{result['event_id']}/communication", json={}).json()
        self.assertTrue(reply["pinned_resources"])
        self.assertFalse(reply["generation_used"])

    def test_ui10_review_preview_does_not_share(self):
        snapshot = self.client.get("/patients/demo-D-7/review-snapshot").json()
        self.assertFalse(snapshot["automatically_sent"])
        self.assertEqual(snapshot["share_status"], "NOT_SHARED")
        self.assertIn("temporary preview", self.html)

    def test_ui11_why_asked_uses_latest_backend_provenance(self):
        view = self.client.get("/patients/demo-C-7/view").json()
        output = self.client.post(f"/patients/demo-C-7/events/{view['latest_event_id']}/communication", json={"purpose":"EXPLAIN_OBSERVATION"}).json()
        self.assertNotEqual(output["static_template_id"], "SUPERSEDED_EVENT")
        self.assertIn("baseline.anchor.version", self.js)
        self.assertIn("drift.description", self.js)

    def test_ui12_patient_can_initiate_while_quiet(self):
        self.assertIn('id="talk"', self.html)
        result = self.ingest("A", "PATIENT_FREE_TEXT", {"text":"fixture ordinary message"})
        self.assertEqual(result["conversation_status"], "NORMAL_CONVERSATION_ALLOWED")

    def test_ui13_no_diagnosis_probability_outputs(self):
        for forbidden in ("relapse_probability", "depression_score", "psychiatric_risk_percentage"):
            self.assertNotIn(forbidden, self.js)
            self.assertNotIn(forbidden, self.html)

    def test_ui14_cases_a_to_f_available_without_truth_in_domain_events(self):
        scenarios = self.client.get("/demo/scenarios").json()["scenarios"]
        self.assertTrue(set("ABCDEF").issubset({s["id"] for s in scenarios}))
        with self.app.state.service.repositories.transaction() as repo:
            for scenario in scenarios:
                for event in repo.events(scenario["patient_id"]):
                    self.assertFalse({"truth", "scenario_id", "expected_outcome", "useful_notification_ranges"} & set(event["payload"]))

    def test_ui15_responsive_accessible_core_contract(self):
        self.assertIn('name="viewport"', self.html)
        self.assertIn('aria-label="Main navigation"', self.html)
        self.assertIn('aria-labelledby="dialog-heading"', self.html)
        self.assertIn("focus-visible", self.css)
        self.assertIn("min-width:960px", self.css)

    def test_offline_bundle_matches_accepted_fixture(self):
        bundle = fixture_bundle()
        self.assertIn(bundle.version, self.js)
        self.assertIn(bundle.resources[0].label, self.js)
        self.assertIn("memory only", self.js)
        self.assertNotIn("localStorage", self.js)

    def test_fixture_gate_rejects_unknown_text_and_extra_checkin_fields(self):
        gate = DemoFixtureGate(["fixture"])
        at = datetime.now(timezone.utc)
        for kind, payload in ((EventType.PATIENT_FREE_TEXT, {"text":"unknown"}),
                              (EventType.PATIENT_CHECKIN, {"state":"Good", "text":"unchecked"})):
            with self.assertRaises(SafetyGateUnavailable):
                gate.resolve(ApplicationEvent("test", "fixture", kind, at, at, "patient", payload, "test", "test"), None, 0)

    def test_patient_api_does_not_enable_live_provider_from_environment(self):
        with patch.dict("os.environ", {"AURA_COMMUNICATION_ENDPOINT":"https://fixture.invalid", "AURA_COMMUNICATION_MODEL":"fixture"}):
            app = create_app(db_path=Path(self.temporary.name) / "local-only.sqlite3")
            self.assertEqual(app.state.communication_service.provider.model_id, "disabled")
        self.assertNotIn("assess_drift", self.js)
        self.assertNotIn("SafetyEngine", self.js)
        self.assertNotIn("TRUST_ANCHOR", self.js)


if __name__ == "__main__":
    unittest.main()
