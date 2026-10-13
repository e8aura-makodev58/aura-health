"""Patient-companion application contracts; no live provider or clinical tuning."""

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo
from uuid import uuid4

from fastapi.testclient import TestClient
from aura_app.api import create_app
from aura_app.companion import CompanionService, routine_days
from aura_app.demo import DemoFixtureGate, demo_catalog, prepare
from aura_app.hosted import SyntheticOnlyService
from aura_app.models import AppError, ApplicationEvent, EventType, MISSED_REASONS, valid_medication_payload
from aura_app.persistence import SCHEMA, SQLiteRepositoryFactory
from aura_app.safety import FixtureSafetyGate, SafetyGateUnavailable
from aura_app.service import PatientEventService
from aura_app.simulator import fixture_treatment
from aura_detectors.layered import LayeredSafetyGate


BASE = datetime(2026, 3, 11, 12, tzinfo=timezone.utc)


class ClearGate:
    def __init__(self): self.calls = 0
    def resolve(self, *args):
        self.calls += 1
        return ()


class CompanionTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.factory = SQLiteRepositoryFactory(Path(temp.name) / "companion.sqlite3")
        self.factory.initialize()
        self.gate = ClearGate()
        self.service = PatientEventService(self.factory, safety_gate=self.gate)
        self.pid = "demo-B-7"
        self.service.create_patient(patient_id=self.pid, display_name="Synthetic", age=35, timezone_name="UTC",
            treatment=fixture_treatment(date(2026, 1, 1), BASE.date()), created_at=BASE)
        self.lookup = Mock(return_value={"name": "Sertraline", "known": True, "purpose": "Curated fixture",
            "how_to_take": "Recorded prescription fixture", "topics": [], "content_status": "Development content — needs pharmacist review"})
        self.select = Mock(return_value=None)
        self.companion = CompanionService(self.service, lookup=self.lookup, select=self.select)

    def event(self, identifier="med", day=0, status="MISSED", reason="SIDE_EFFECTS"):
        at = BASE + timedelta(days=day)
        payload = {"scheduled_time": at.replace(hour=8).isoformat(), "status": status}
        if reason is not None: payload["reason"] = reason
        return ApplicationEvent(identifier, self.pid, EventType.MEDICATION_EVENT, at, at,
                                "synthetic_patient", payload, identifier, identifier)

    def test_pc1_exact_reason_shape_rejected_before_persistence_or_detector(self):
        valid = self.event()
        invalid = [replace(valid, payload={**valid.payload, "status": status}) for status in ("ACKNOWLEDGED", "UNKNOWN")]
        invalid += [replace(valid, payload={**valid.payload, "reason": reason}) for reason in (None, "because I felt unwell", [], True)]
        invalid += [replace(valid, payload={**valid.payload, "text": "extra"}),
                    replace(valid, payload={**valid.payload, "scheduled_time": "2026-03-11T08:00:00"}),
                    replace(valid, payload={**valid.payload, "status": []})]
        for event in invalid:
            with self.subTest(payload=event.payload), self.assertRaises(AppError):
                self.service.process(event)
        self.assertEqual(self.gate.calls, 0)
        with self.factory.transaction() as repo:
            self.assertEqual(repo.events(self.pid), [])
            self.assertEqual(repo.medication_events(self.pid), [])

    def test_pc2_demo_and_layered_gates_accept_each_reason_without_model(self):
        fixture = DemoFixtureGate([self.pid])
        provider = Mock()
        layered = LayeredSafetyGate(provider)
        for reason in MISSED_REASONS:
            event = self.event(reason=reason)
            self.assertTrue(valid_medication_payload(event.payload))
            self.assertEqual(fixture.resolve(event, None, 0), ())
            self.assertEqual(layered.resolve(event, None, 0), ())
        self.assertEqual(provider.mock_calls, [])
        for gate in (fixture, layered):
            for field in ("arbitrary", "text", "question"):
                with self.assertRaises(SafetyGateUnavailable):
                    gate.resolve(replace(self.event(), payload={**self.event().payload, field: "text"}), None, 0)
        self.assertEqual(provider.mock_calls, [])

    def test_pc3_hosted_gate_accepts_today_morning_reason_and_rejects_extras(self):
        self.service.process(self.event("base", status="UNKNOWN", reason=None))
        hosted = SyntheticOnlyService(self.factory)
        result = hosted.process(self.event(str(uuid4())))
        self.assertFalse(result.safety["state"]["degraded"])
        for event in (replace(self.event("bad"), payload={**self.event().payload, "extra": "text"}),
                      self.event("tomorrow", day=1)):
            with self.assertRaises(AppError): hosted.process(event)

    def test_pc4_reason_persists_and_duplicate_creates_one_review_item(self):
        event = self.event()
        first = self.service.process(event)
        second = self.service.process(replace(event, event_id="retry"))
        self.assertTrue(second.idempotent_replay)
        self.assertEqual(self.gate.calls, 1)
        self.assertEqual(len(first.review_item_ids), 1)
        with self.factory.transaction() as repo:
            self.assertEqual(len(repo.medication_events(self.pid)), 1)
            self.assertEqual(repo.medication_events(self.pid)[0]["reason"], "SIDE_EFFECTS")
            self.assertEqual(len(repo.review_items(self.pid)), 1)
        snapshot = self.service.review_snapshot(self.pid)
        self.assertEqual(snapshot["medication_routine_events"][0]["reason"], "SIDE_EFFECTS")
        self.assertIn("reason: side effects", snapshot["unresolved_items"][0]["summary"])
        self.assertFalse(snapshot["automatically_sent"])

    def test_pc5_latest_report_per_day_not_number_of_taps(self):
        for day in range(-6, 1):
            self.service.process(self.event(f"day{day}", day=day, status="ACKNOWLEDGED", reason=None))
        self.service.process(self.event("skip", status="MISSED", reason="FORGOT"))
        result = self.companion.get(self.pid)
        self.assertEqual(result["adherence"], {"window_days": 7, "taken_days": 6, "recorded_days": 7, "missed_days": 1,
            "missed_reasons": [{"reason": "FORGOT", "label": "Forgot", "count": 1}]})
        self.assertEqual(result["dose_today"]["status"], "MISSED")
        self.assertEqual(result["dose_today"]["scheduled_time"], BASE.replace(hour=8).isoformat())
        self.lookup.assert_called_with("Sertraline", "50 mg, once each morning")
        self.select.assert_called_once()

    def test_pc6_missing_and_unknown_stay_unrecorded_or_unknown(self):
        blank = self.companion.get(self.pid)
        self.assertIsNone(blank["dose_today"]["status"])
        self.assertEqual(blank["adherence"]["recorded_days"], 0)
        self.service.process(self.event(status="UNKNOWN", reason=None))
        result = self.companion.get(self.pid)
        self.assertEqual(result["dose_today"]["status"], "UNKNOWN")
        self.assertEqual(result["adherence"]["recorded_days"], 1)
        self.assertEqual(result["adherence"]["taken_days"], 0)

    def test_pc7_stored_dates_produce_estimate_not_booked_appointment(self):
        result = self.companion.get(self.pid)
        self.assertEqual(result["coming_up"], [
            {"kind": "REFILL", "date": "2026-03-19", "label": "Refill estimated"},
            {"kind": "MEDICATION_REVIEW", "date": "2026-03-24", "label": "Medication review with your doctor"}])
        self.assertNotIn("APPOINTMENT", [row["kind"] for row in result["coming_up"]])

    def test_pc8_safety_interaction_hides_content_and_never_calls_selectors(self):
        event = ApplicationEvent("concern", self.pid, EventType.PATIENT_FREE_TEXT, BASE, BASE,
                                 "synthetic", {"text": "fixture safety concern"}, "c", "concern")
        self.service.safety_gate = FixtureSafetyGate({"concern": (("D2", "CLARIFY"),)})
        self.service.process(event)
        result = self.companion.get(self.pid)
        self.assertFalse(result["safety_normal"])
        self.assertIsNone(result["medication"])
        self.assertIsNone(result["suggestions"])
        self.lookup.assert_not_called(); self.select.assert_not_called()

    def test_pc9_deferred_report_excluded_then_review_item_created_on_recovery(self):
        self.service.safety_gate = FixtureSafetyGate({})
        held = self.service.process(self.event("held"))
        self.assertTrue(held.longitudinal["deferred"])
        result = self.companion.get(self.pid)
        self.assertFalse(result["safety_normal"])
        self.assertEqual(result["adherence"]["recorded_days"], 0)
        self.assertEqual(self.service.review_snapshot(self.pid)["unresolved_items"], [])
        self.service.safety_gate = self.gate
        event = ApplicationEvent("recover", self.pid, EventType.PATIENT_CHECKIN, BASE, BASE,
                                 "synthetic", {"state": "Good"}, "recover", "recover")
        self.service.process(event)
        self.assertTrue(self.companion.get(self.pid)["safety_normal"])
        self.assertEqual(len(self.service.review_snapshot(self.pid)["unresolved_items"]), 1)

    def test_pc10_new_endpoint_is_read_only_and_reload_deterministic(self):
        self.service.process(self.event())
        before = self.service.timeline(self.pid)
        with TestClient(create_app(service=self.service)) as client:
            first = client.get(f"/patients/{self.pid}/companion")
            self.assertEqual(first.status_code, 200)
            self.assertEqual(first.json(), client.get(f"/patients/{self.pid}/companion").json())
            self.assertEqual(client.get("/patients/missing/companion").status_code, 404)
        reloaded = PatientEventService(SQLiteRepositoryFactory(self.factory.path))
        self.assertEqual(first.json(), CompanionService(reloaded).get(self.pid))
        self.assertEqual(before, self.service.timeline(self.pid))

    def test_pc11_medication_reason_failure_rolls_back_all_records(self):
        with patch.object(self.service, "_sync_review_items", side_effect=RuntimeError("fixture failed")):
            with self.assertRaises(AppError): self.service.process(self.event())
        with self.factory.transaction() as repo:
            self.assertEqual(repo.events(self.pid), [])
            self.assertEqual(repo.medication_events(self.pid), [])
            self.assertEqual(repo.review_items(self.pid), [])
            self.assertEqual(repo.audit(self.pid), [])

    def test_pc12_local_day_and_absolute_timestamp_choose_latest_report(self):
        # Both scheduled timestamps are March11 in Singapore; lexical timestamp
        # order would select the wrong report across offsets.
        rows = [{"scheduled_time": "2026-03-11T00:00:00+00:00", "timestamp": "2026-03-11T12:00:00+08:00", "status": "MISSED"},
                {"scheduled_time": "2026-03-11T08:00:00+08:00", "timestamp": "2026-03-11T05:00:00+00:00", "status": "UNKNOWN"}]
        selected = routine_days(rows, BASE.date(), ZoneInfo("Asia/Singapore"), 7)
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[BASE.date()]["status"], "UNKNOWN")
        first = self.event("tie-first", status="ACKNOWLEDGED", reason=None)
        first = replace(first, occurred_at=BASE.astimezone(ZoneInfo("Asia/Singapore")))
        self.service.process(first)
        self.service.process(self.event("tie-second", status="UNKNOWN", reason=None))
        self.assertEqual(self.companion.get(self.pid)["dose_today"]["status"], "UNKNOWN")

    def test_pc13_unknown_medication_has_exact_abstention(self):
        with self.factory.transaction() as repo:
            repo.save_treatment({"patient_id": self.pid, "medication_name": "Unidentified fixture"})
        result = CompanionService(self.service).get(self.pid)
        self.assertFalse(result["medication"]["known"])
        self.assertEqual(result["medication"]["abstain"], "I'm not able to identify that medication, please check with your pharmacist.")
        self.assertIsNone(result["medication"]["purpose"])
        self.assertIsNone(result["dose_today"]["scheduled_time"])

    def test_pc14_no_treatment_produces_no_medication_or_reminders(self):
        with self.factory.transaction() as repo: repo.save_treatment({"patient_id": self.pid})
        result = self.companion.get(self.pid)
        self.assertIsNone(result["medication"])
        self.assertEqual(result["coming_up"], [])
        self.lookup.assert_not_called()

    def test_pc15_schema_migration_preserves_existing_data_and_is_repeatable(self):
        temp = TemporaryDirectory(); self.addCleanup(temp.cleanup)
        path = Path(temp.name) / "legacy.sqlite3"
        legacy = SCHEMA.replace(", supply_days INTEGER, last_refill TEXT", "").replace(", source TEXT NOT NULL, reason TEXT", ", source TEXT NOT NULL")
        with sqlite3.connect(path) as conn:
            conn.executescript(legacy)
            conn.execute("INSERT INTO patients VALUES ('old','Existing',35,'UTC','PROTOTYPE',?,1)", (BASE.isoformat(),))
            conn.execute("INSERT INTO treatment_context VALUES ('old','Recorded medicine','Recorded label',NULL,NULL,NULL,NULL,NULL,NULL)")
        factory = SQLiteRepositoryFactory(path)
        factory.initialize(); factory.initialize()
        with factory.transaction() as repo:
            treatment = repo.patient("old")["treatment"]
            self.assertEqual(treatment["medication_name"], "Recorded medicine")
            self.assertIsNone(treatment["supply_days"])
            self.assertIsNone(treatment["last_refill"])
            repo.save_treatment({"patient_id": "old", **treatment, "supply_days": 28, "last_refill": "2026-02-19"})
        with factory.transaction() as repo: self.assertEqual(repo.patient("old")["treatment"]["supply_days"], 28)


class CompanionFixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = TemporaryDirectory()
        cls.path = Path(cls.temp.name) / "fixtures.sqlite3"
        cls.factory = prepare(cls.path)

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def test_pc16_all_catalog_profiles_have_explicit_fixture_prescription(self):
        with self.factory.transaction() as repo:
            for row in demo_catalog():
                treatment = repo.patient(row["patient_id"])["treatment"]
                self.assertEqual(treatment["medication_name"], "Sertraline")
                self.assertEqual(treatment["medication_schedule"], "50 mg, once each morning")
                self.assertEqual(treatment["supply_days"], 28)
                self.assertEqual(treatment["review_cadence"], "every 3 months")
                self.assertEqual(treatment["regimen_start"], "2025-04-01")
                self.assertEqual(treatment["stable_since"], "2025-07-01")
                latest = max(datetime.fromisoformat(event["occurred_at"]) for event in repo.events(row["patient_id"])).date()
                self.assertEqual(treatment["next_review"], (latest + timedelta(days=13)).isoformat())
                self.assertEqual(treatment["last_refill"], (latest - timedelta(days=20)).isoformat())
        clamped = fixture_treatment(date(2026, 3, 31), BASE.date())
        self.assertEqual(clamped["regimen_start"], "2025-06-30")
        self.assertEqual(clamped["stable_since"], "2025-09-30")

    def test_pc17_existing_demo_upgrade_preserves_events_anchors_and_custom_context(self):
        with self.factory.transaction() as repo:
            before = repo.events("demo-B-7"), repo.baselines("demo-B-7")
            repo.save_treatment({"patient_id": "demo-B-7", "medication_name": "fixture-only; no treatment instruction"})
            repo.save_treatment({"patient_id": "demo-stable-7", "medication_name": "Custom recorded context"})
        prepare(self.path)
        with self.factory.transaction() as repo:
            self.assertEqual(before, (repo.events("demo-B-7"), repo.baselines("demo-B-7")))
            self.assertEqual(repo.patient("demo-B-7")["treatment"]["medication_name"], "Sertraline")
            self.assertEqual(repo.patient("demo-stable-7")["treatment"]["medication_name"], "Custom recorded context")
