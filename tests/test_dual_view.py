"""Read-only evidence contract over accepted synthetic A–F inputs; no new policy."""

import inspect
from datetime import datetime, timezone
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from aura_app.demo import create_demo_app
from aura_app.evidence import EvidenceViewService
from aura_app.persistence import SQLiteRepositoryFactory
from aura_app.models import ApplicationEvent, AppError, EventType


class DualViewEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = TemporaryDirectory()
        cls.db = Path(cls.temp.name) / "evidence.sqlite3"
        cls.app = create_demo_app(cls.db)
        cls.client = TestClient(cls.app)
        cls.service = cls.app.state.service

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        cls.temp.cleanup()

    def evidence(self, case):
        response = self.client.get(f"/patients/demo-{case}-7/evidence")
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_ev1_read_projection_is_deterministic_without_writes_or_generation(self):
        with self.service.repositories.transaction() as repo:
            before = list(repo.conn.iterdump())
        with patch.object(self.app.state.communication_service, "render", side_effect=AssertionError("no generation on read")):
            first = self.evidence("B")
            self.assertEqual(first, self.evidence("B"))
        with self.service.repositories.transaction() as repo:
            self.assertEqual(before, list(repo.conn.iterdump()))

    def test_ev2_history_exactly_matches_original_committed_values(self):
        for case in "ABCDEF":
            evidence = self.evidence(case)
            with self.service.repositories.transaction() as repo:
                snapshots = repo.committed_results(f"demo-{case}-7")
            indexed = {row["event_id"]: row for row in snapshots}
            for signal in evidence["signals"]:
                for point in signal["history"]:
                    result = indexed[point["event_id"]]["result"]["longitudinal"]
                    match = next(row for row in result["baselines"]
                                 if row["signal"] == signal["key"]["signal"]
                                 and row["source"] == signal["key"]["source"]
                                 and (row["metric"] or "") == signal["key"]["metric"])
                    for field in ("rolling", "anchor", "sensing_state", "trust_state"):
                        self.assertEqual(point[field], match[field])

    def test_ev3_gap_keeps_null_values_and_return_keeps_uncertainty(self):
        for signal in self.evidence("E-gap")["signals"]:
            self.assertEqual(signal["current"]["sensing_state"], "UNOBSERVED")
            self.assertIsNone(signal["current"]["rolling"]["mean"])
            self.assertTrue(any(row["type"] == "SENSING_GAP" for row in signal["gaps"]))
            self.assertLess(signal["observations"][-1]["day"], signal["history"][-1]["at"][:10])
        for signal in self.evidence("E")["signals"]:
            self.assertEqual(signal["current"]["trust_state"], "REESTABLISHING")
            self.assertEqual(signal["current"]["sensing_state"], "OBSERVED")

    def test_ev4_anchor_versions_are_historical_not_backfilled(self):
        evidence = self.evidence("B")
        for signal in evidence["signals"]:
            self.assertIsNone(signal["history"][0]["anchor"])
            self.assertTrue(signal["current"]["anchor"])
            commands = signal["anchor_commands"]
            self.assertEqual([row["action"] for row in commands], ["CREATE_PROVISIONAL_ANCHOR", "TRUST_ANCHOR"])
            self.assertTrue(all(row["anchor"]["version"] == 1 for row in signal["history"] if row["anchor"]))

    def test_ev5_context_is_linked_only_to_explicitly_associated_signals(self):
        evidence = self.evidence("C")
        for signal in evidence["signals"]:
            for context in signal["contexts"]:
                self.assertIn(signal["key"]["signal"], context["affected_signals"])
                self.assertTrue(context["start"])
                self.assertTrue(context["explanation"])
        timing = next(row for row in evidence["signals"] if row["key"]["signal"] == "SLEEP_MIDPOINT")
        self.assertTrue(any(not row["drift"]["attenuated"] for row in timing["findings"]))
        self.assertIn("Rough", {row["state"] for row in evidence["checkins"]})

    def test_ev6_held_observation_and_review_item_survive(self):
        evidence = self.evidence("D")
        self.assertEqual(len(evidence["held"]), 2)
        self.assertTrue(all(row["status"] == "EXPLAINED_HELD_FOR_REVIEW" for row in evidence["held"]))
        self.assertTrue(all(row["record"]["explanation"] == "new stable work schedule" for row in evidence["held"]))
        self.assertGreaterEqual(len(evidence["review_items"]), 2)
        self.assertTrue(all(signal["current"]["anchor"]["version"] == 1 for signal in evidence["signals"]))
        self.assertEqual(evidence["share_status"], "NOT_SHARED")
        self.assertFalse(evidence["automatically_sent"])

    def test_ev7_case_b_retained_change_coexists_with_quiet(self):
        evidence = self.evidence("B")
        self.assertEqual(evidence["current_decision"], "STAY_QUIET")
        self.assertTrue(any(row["drift"]["kind"] in {"PERSISTENT_DRIFT", "ROLLING_ANCHOR_DIVERGENCE"}
                            for signal in evidence["signals"] for row in signal["findings"]))

    def test_ev8_safety_provenance_survives_reload(self):
        evidence = self.evidence("F")
        self.assertEqual(evidence["current_decision"], "SAFETY_REVIEW_REQUIRED")
        self.assertTrue(evidence["safety"]["state"]["episode_id"])
        factory = SQLiteRepositoryFactory(self.db)
        from aura_app.service import PatientEventService
        reopened = EvidenceViewService(PatientEventService(factory)).get("demo-F-7")
        self.assertEqual(evidence, reopened)
        for reference in reopened["safety"]["references"]:
            self.assertTrue(reference["event_id"])
            self.assertEqual(reference["sequence"], reference["state"]["sequence"])

    def test_ev9_degraded_without_episode_is_visible_and_not_backfilled(self):
        self.client.post("/patients", json={"patient_id":"held-evidence", "display_name":"Synthetic", "age":35})
        response = self.client.post("/patients/held-evidence/events", json={
            "event_type":"PATIENT_FREE_TEXT", "occurred_at":"2026-01-01T12:00:00+00:00",
            "source":"patient", "payload":{"text":"unresolved synthetic input"}, "idempotency_key":"held"})
        self.assertEqual(response.status_code, 200)
        evidence = self.client.get("/patients/held-evidence/evidence").json()
        self.assertTrue(evidence["safety"]["state"]["degraded"])
        self.assertIsNone(evidence["safety"]["state"]["episode_id"])
        self.assertEqual(len(evidence["safety"]["references"]), 1)
        self.assertEqual(evidence["unavailable_snapshots"][0]["reason"], "DEFERRED")
        self.assertFalse(evidence["signals"])

    def test_ev10_no_hidden_truth_or_patient_text_in_evidence_contract(self):
        forbidden = {"latent_truth", "expected_outcome", "scenario_id", "useful_notification_ranges", "text"}
        def check(value):
            if isinstance(value, dict):
                self.assertFalse(forbidden & value.keys())
                for child in value.values(): check(child)
            elif isinstance(value, list):
                for child in value: check(child)
        for case in "ABCDEF": check(self.evidence(case))
        self.assertNotIn("LongitudinalProjector", inspect.getsource(EvidenceViewService))
        self.assertNotIn("SafetyEngine", inspect.getsource(EvidenceViewService))

    def test_ev11_no_missing_patient_or_asset_access_expansion(self):
        self.assertEqual(self.client.get("/patients/missing/evidence").status_code, 404)
        self.assertEqual(self.client.get("/assets/evidence.js").status_code, 200)
        self.assertEqual(self.client.get("/assets/README.md").status_code, 404)

    def test_ev12_raw_records_and_sources_not_flattened_or_recomputed(self):
        evidence = self.evidence("B")
        with self.service.repositories.transaction() as repo:
            stored = repo.observations("demo-B-7")
        for signal in evidence["signals"]:
            for row in signal["observations"]:
                original = next(item for item in stored if item["event_id"] == row["event_id"]
                                and item["signal"] == signal["key"]["signal"]
                                and item["source"] == signal["key"]["source"])
                for field in ("value", "day", "coverage", "data_quality"):
                    self.assertEqual(row[field], original[field])

    def test_ev13_reanchor_keeps_original_reference_versions(self):
        # Isolated copy: exercise an already-accepted governed command, not new policy.
        copy = Path(self.temp.name) / "reanchor.sqlite3"
        shutil.copyfile(self.db, copy)
        from aura_app.service import PatientEventService
        service = PatientEventService(SQLiteRepositoryFactory(copy))
        view = EvidenceViewService(service)
        before = view.get("demo-B-7")
        at = datetime(2026, 3, 12, 12, tzinfo=timezone.utc)
        service.command_anchor(ApplicationEvent("review-copy", "demo-B-7", EventType.ANCHOR_COMMAND,
            at, at, "governed_command", {"action":"CLINICAL_REVIEW_REANCHOR",
                "signal":"ACTIVITY", "source":"synthetic_wearable", "metric":"steps",
                "reference_start":"2026-02-25", "reference_end":"2026-03-11",
                "reviewed_by":"synthetic-reviewer"}, "review-copy", "review-copy"))
        after = view.get("demo-B-7")
        previous = next(row for row in before["signals"] if row["key"]["signal"] == "ACTIVITY")
        revised = next(row for row in after["signals"] if row["key"]["signal"] == "ACTIVITY")
        self.assertEqual(revised["current"]["anchor"]["version"], 2)
        self.assertEqual(previous["history"], revised["history"][:-1])
        self.assertEqual(revised["history"][-1]["anchor"]["reviewed_by"], "synthetic-reviewer")

    def test_ev14_hosted_patient_allowlist_also_guards_evidence_reads(self):
        from aura_app.hosted import SyntheticOnlyService
        view = EvidenceViewService(SyntheticOnlyService(self.service.repositories))
        with self.assertRaises(AppError) as error:
            view.get("outside-catalog")
        self.assertEqual(error.exception.code, "SYNTHETIC_ONLY")


if __name__ == "__main__":
    unittest.main()
