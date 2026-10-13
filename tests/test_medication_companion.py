"""Patient companion: curated medication answers, abstention, safety-first questions, suggestions."""
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest

from fastapi.testclient import TestClient

from aura_agent import medication
from aura_agent.suggestions import select
from aura_app.api import create_app
from aura_app.demo import create_demo_app, DemoFixtureGate
from aura_app.evidence import EvidenceViewService
from aura_app.medication_ask import MedicationAskService
from aura_app.persistence import SQLiteRepositoryFactory
from aura_app.service import PatientEventService
from aura_detectors.layered import LayeredSafetyGate
from tests.test_approved_workflows import TaskModel


class TopicModel:
    """Live-looking provider for the topic classifier only."""
    live = True; model_id = "topic-mock"
    def __init__(self, reply): self.reply = reply; self.calls = 0
    def step(self, messages, tools):
        self.calls += 1
        return {"content": json.dumps(self.reply)}


class MedicationCompanionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = TemporaryDirectory(); cls.baseline = Path(cls.fixtures.name) / "base.sqlite3"
        create_demo_app(cls.baseline)

    @classmethod
    def tearDownClass(cls):
        cls.fixtures.cleanup()

    def setUp(self):
        self.temp = TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        db = Path(self.temp.name) / "test.sqlite3"; shutil.copyfile(self.baseline, db)
        self.repo = SQLiteRepositoryFactory(db); self.repo.initialize(); self.detector = TaskModel()
        gate = LayeredSafetyGate(self.detector, fixtures=DemoFixtureGate(["demo-B-7"]))
        self.service = PatientEventService(self.repo, safety_gate=gate); self.patient = "demo-B-7"
        self.prescribe("Sertraline", "50 mg, once each morning")

    def prescribe(self, name, schedule):
        with self.repo.transaction() as repo:
            repo.conn.execute("UPDATE treatment_context SET medication_name=?, medication_schedule=? WHERE patient_id=?",
                              (name, schedule, self.patient))

    def ask(self, provider=None, **request):
        return MedicationAskService(self.service, provider or TaskModel()).ask(self.patient, run_id="run-1", **request)

    def count(self):
        with self.repo.transaction() as repo:
            return len(repo.events(self.patient))

    def test_med1_topic_answers_are_curated_text_with_footer_and_no_model(self):
        provider = TopicModel({"topic": "alcohol"})
        result = self.ask(provider, topic_id="how_to_take")
        self.assertEqual(result["status"], "ANSWERED")
        self.assertIn("Your prescription label says: 50 mg, once each morning.", result["answer"])
        self.assertTrue(result["answer"].endswith("If you're unsure, check with your pharmacist or doctor."))
        self.assertEqual(provider.calls, 0)
        self.assertEqual(result["source_label"], "Approved medication information (development content)")

    def test_med2_exact_abstention_lines(self):
        self.assertEqual(self.ask(question="Can I take ibuprofen with it?")["answer"],
                         "I'm not able to identify that medication, please check with your pharmacist.")
        self.assertEqual(self.ask(question="Should I increase my dose?")["answer"], medication.ADVICE_REQUEST)
        self.assertEqual(self.ask(question="Is my zodiac sign relevant?")["answer"],
                         "I'm not able to answer that here, please check with your pharmacist or doctor.")
        self.prescribe("Mirtazapine", "15 mg at night")
        result = self.ask(topic_id="purpose")
        self.assertEqual((result["status"], result["answer"]),
                         ("ABSTAINED", "I'm not able to identify that medication, please check with your pharmacist."))

    def test_med3_typed_question_is_safety_assessed_first(self):
        before = self.count()
        result = self.ask(question="What if I miss a dose?")
        self.assertEqual(result["status"], "ANSWERED"); self.assertEqual(result["topic_id"], "missed_dose")
        self.assertEqual(self.count(), before + 1)
        self.assertTrue(any("concern" in request[0]["content"] for request in self.detector.requests))
        self.assertEqual(result["trace"][0], {"step": "safety_check", "result": "assessed"})

    def test_med4_safety_concern_blocks_any_answer(self):
        self.detector.concern = "possible"
        result = MedicationAskService(self.service, TaskModel()).ask(self.patient, run_id="run-2", question="I feel very uncertain today")
        self.assertEqual((result["status"], result["answer"]), ("BLOCKED", ""))
        # Once safety is not normal, even a chosen topic is withheld.
        self.assertEqual(self.ask(topic_id="purpose")["status"], "BLOCKED")

    def test_med4b_reused_run_id_with_new_text_is_assessed_again(self):
        service = MedicationAskService(self.service, TaskModel())
        first = service.ask(self.patient, run_id="same-run", question="What if I miss a dose?")
        self.assertEqual(first["status"], "ANSWERED")
        before = len(self.detector.requests)
        self.detector.concern = "possible"
        second = service.ask(self.patient, run_id="same-run", question="I feel very uncertain today")
        self.assertGreater(len(self.detector.requests), before)
        self.assertEqual((second["status"], second["answer"]), ("BLOCKED", ""))
    def test_med5_model_only_chooses_a_topic_never_the_answer(self):
        result = self.ask(TopicModel({"topic": "alcohol"}), question="Is a glass with dinner ok?")
        self.assertEqual(result["topic_id"], "alcohol")
        self.assertEqual(result["answer"], medication.answer("Sertraline", "alcohol"))
        rogue = self.ask(TopicModel({"topic": "Take 100 mg tonight"}), question="Something unusual?")
        self.assertEqual(rogue["status"], "ABSTAINED"); self.assertNotIn("100 mg", rogue["answer"])
        extra = self.ask(TopicModel({"topic": "purpose", "answer": "made up"}), question="Something unusual?")
        self.assertEqual(extra["status"], "ABSTAINED")

    def test_med6_suggestions_curated_and_hidden_when_safety_not_normal(self):
        evidence = EvidenceViewService(self.service).get(self.patient)
        chosen = select(evidence, True)
        self.assertEqual(chosen["because"], "You've been moving less than your usual since early March.")
        self.assertEqual(chosen["options"][0]["id"], "short_walk")
        self.assertEqual(len(chosen["options"]), 3)
        self.assertIsNone(select(evidence, False))
        catalog = json.loads((Path(medication.__file__).parent / "suggestions.json").read_text())
        labels = [row["label"].lower() for row in catalog["general"]] + [row["option"]["label"].lower() for row in catalog["by_change"].values()]
        self.assertFalse(any(word in label for label in labels for word in ("medication", "dose", "tablet", "pill")))

    def test_med7_route_validation(self):
        with TestClient(create_app(service=self.service)) as client:
            run = "00000000-0000-4000-8000-000000000001"
            ok = client.post(f"/patients/{self.patient}/medication/ask", json={"run_id": run, "topic_id": "purpose"})
            self.assertEqual(ok.status_code, 200); self.assertEqual(ok.json()["status"], "ANSWERED")
            both = client.post(f"/patients/{self.patient}/medication/ask", json={"run_id": run, "topic_id": "purpose", "question": "x"})
            self.assertEqual(both.status_code, 400)
            unknown = client.post(f"/patients/{self.patient}/medication/ask", json={"run_id": run, "topic_id": "dosing_plan"})
            self.assertEqual(unknown.status_code, 400)


if __name__ == "__main__":
    unittest.main()
