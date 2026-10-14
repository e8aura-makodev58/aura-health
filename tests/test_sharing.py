"""Patient consent decides what clinician-serving runs and views can read. Synthetic case B, fakes only."""
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
import re
import unittest

from aura_app.agent import AgentService
from aura_app.evidence import EvidenceViewService
from aura_app.models import AppError, ApplicationEvent, EventType
from aura_app.persistence import SQLiteRepositoryFactory
from aura_app.safety import FixtureSafetyGate
from aura_app.service import PatientEventService
from aura_app.sharing import SharingService, clinician_view, filter_evidence
from aura_app.simulator import run_case

NOTE = "I enjoyed walking with my dog today"


class SharingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = TemporaryDirectory()
        cls.db = Path(cls.temp.name) / "b.sqlite3"
        record = run_case("B", 7, cls.db)
        cls.pid = record.get("patient_id", "synthetic-B-7") if isinstance(record, dict) else "synthetic-B-7"

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.gate = FixtureSafetyGate({})
        self.events = PatientEventService(SQLiteRepositoryFactory(self.db), safety_gate=self.gate)
        rows = self.events.timeline(self.pid)
        self.end = datetime.fromisoformat(max(row["occurred_at"] for row in rows))
        note_id = f"note-{self._testMethodName}"
        self.gate.proposals[note_id] = ()
        self.events.process(ApplicationEvent(note_id, self.pid, EventType.PATIENT_FREE_TEXT, self.end, self.end,
                                             "synthetic_patient", {"text": NOTE}, note_id, note_id))
        self.sharing = SharingService(self.events)
        self.sharing.set(self.pid, {"notes": True, "readings": True, "checkin_history": True, "activity_details": True})
        self.agent = AgentService(self.events, synthetic_only=True)

    def texts(self, role, asker="patient"):
        tools, _ = self.agent.record_tools(self.pid, role, 56, asker=asker)
        return [fact["text"] for fact in tools.facts.values()]

    def test_sh1_demo_default_is_everything_and_choices_are_recorded(self):
        fresh = SharingService(self.events, default_all=True)
        self.assertEqual(fresh.withheld(self.pid), frozenset())
        fresh.set(self.pid, {"notes": False})
        self.assertEqual(fresh.withheld(self.pid), frozenset({"notes"}))
        consent = [row for row in self.events.timeline(self.pid) if row["record_type"] == "SHARING_CONSENT"]
        self.assertEqual(consent[-1]["detail"]["changed"], {"notes": False})
        with self.assertRaises(AppError):
            fresh.set(self.pid, {"safety": False})

    def test_sh2_notes_withheld_from_clinician_runs_only(self):
        self.sharing.set(self.pid, {"notes": False})
        clinician = self.texts("record_qa", asker="clinician")
        self.assertFalse(any(NOTE in text for text in clinician))
        self.assertTrue(any("Not shared with the clinician by the patient: the patient's notes" in text for text in clinician))
        self.assertTrue(any(NOTE in text for text in self.texts("record_qa", asker="patient")))
        self.assertTrue(any(NOTE in text for text in self.texts("visit_prep")))

    def test_sh3_minimum_keeps_findings_and_summaries_but_not_details(self):
        everything = self.texts("clinician_brief")
        self.sharing.set(self.pid, {"notes": False, "readings": False, "checkin_history": False, "activity_details": False})
        minimum = self.texts("clinician_brief")
        daily = re.compile(r"^[^:,]+ recorded \d{4}-\d{2}-\d{2}: ")
        self.assertTrue(any(daily.match(text) for text in everything))         # daily readings were there
        self.assertFalse(any(daily.match(text) for text in minimum))           # and are withheld now
        self.assertTrue(any("Patient check-in 20" in text for text in everything))
        self.assertFalse(any("Patient check-in 20" in text for text in minimum))
        self.assertTrue(any("First recorded" in text for text in minimum))                  # engine findings kept
        self.assertTrue(any("Patient-reported check-ins:" in text for text in minimum))     # summaries kept
        self.assertTrue(len(minimum) < len(everything))

    def test_sh4_filtered_evidence_for_the_clinician_view(self):
        evidence = EvidenceViewService(self.events).get(self.pid)
        view = filter_evidence(evidence, frozenset({"readings", "checkin_history", "notes"}))
        self.assertTrue(all(signal["observations"] == [] for signal in view["signals"]))
        self.assertEqual(view["checkins"], [])
        self.assertTrue(all(signal["findings"] == original["findings"] for signal, original in zip(view["signals"], evidence["signals"])))
        self.assertTrue(any(signal["observations"] for signal in evidence["signals"]))      # patient's own view untouched

    def test_sh5_changing_consent_invalidates_cached_clinician_answers(self):
        with self.events.repositories.transaction() as repo:
            before = self.agent._approval(repo, self.pid, False)[0]
        self.sharing.set(self.pid, {"notes": False})
        with self.events.repositories.transaction() as repo:
            after = self.agent._approval(repo, self.pid, False)[0]
        self.assertNotEqual(before, after)

    def test_sh6_who_counts_as_the_clinician(self):
        self.assertTrue(clinician_view("clinician_brief", "patient"))
        self.assertTrue(clinician_view("record_qa", "clinician"))
        self.assertFalse(clinician_view("record_qa", "patient"))
        self.assertFalse(clinician_view("visit_prep", "patient"))


if __name__ == "__main__":
    unittest.main()
