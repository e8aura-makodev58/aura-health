"""DEMO-series integration gates; synthetic-only, not clinical/model validation."""

from copy import deepcopy
import inspect
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient
import httpx

from aura_app.api import create_app
from aura_app.demo import prepare
from aura_app.demo_workspace import verify, reset_snapshot
from aura_app.hosted import HostedDemo
from aura_app.persistence import SQLiteRepositoryFactory
from aura_app.service import PatientEventService
from aura_simulation.agent import SimulationDataAgent, JSONGatewayPlanner, validate_plan
from aura_simulation.timeline import generate
from aura_simulation.driver import observable_events, drive
from aura_communication.evaluation import run_fixtures


class MilestoneSeven(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = TemporaryDirectory()
        cls.root = Path(cls.temporary.name)
        cls.host = HostedDemo(cls.root / "host", secure_cookie=False)
        cls.client = TestClient(cls.host)
        cls.timeline = generate(SimulationDataAgent().plan("Case D new signal after explanation"))
        cls.frames = observable_events(cls.timeline)
        cls.record = drive(cls.frames,cls.root/"trace.sqlite3")

    @classmethod
    def tearDownClass(cls):
        cls.client.close(); cls.temporary.cleanup()

    def ingest(self, client, patient, kind, payload):
        value = str(uuid4())
        return client.post(f"/patients/{patient}/events",json={"event_id":value,"event_type":kind,
            "occurred_at":"2026-01-21T12:00:00+00:00","source":"patient","payload":payload,
            "correlation_id":value,"idempotency_key":value})

    def test_demo1_cases_a_to_f_have_hosted_paths(self):
        scenarios = self.client.get("/demo/scenarios").json()
        self.assertTrue(scenarios["hosted"])
        for case in "ABCDEF":
            patient=f"demo-{case}-7"
            self.assertEqual(self.client.get(f"/patients/{patient}/status").status_code,200)
            self.assertFalse(self.client.get(f"/patients/{patient}/review-snapshot").json()["automatically_sent"])

    def test_demo2_ground_truth_isolation_at_every_input_field(self):
        dirty = deepcopy(self.timeline)
        hidden = {"scenario_id":"poison","latent_truth":{"deterioration":True},
                  "expected_outcome":"IMMEDIATE","useful_interruption_windows":[[0,365]],"synthetic_labels":["risk"]}
        dirty.update(hidden); dirty["evaluation"]=hidden
        for row in dirty["days"]:
            row.update(hidden)
        for context in dirty["contexts"]:
            context.update(hidden)
        self.assertEqual(observable_events(dirty),self.frames)
        replay=drive(observable_events(dirty),self.root/"isolated.sqlite3")
        self.assertEqual(self.record,replay)
        for frame in self.frames:
            self.assertFalse(set(hidden) & set(frame["payload"]))

    def test_demo3_no_live_llm_fallbacks(self):
        self.assertTrue(all(row["passed"] for row in run_fixtures(behavior="disabled")))

    def test_demo4_invalid_output_and_timeout_fallbacks(self):
        for behavior in ("invalid","timeout"):
            self.assertTrue(all(row["passed"] for row in run_fixtures(behavior=behavior)))

    def test_demo5_exact_semantic_replay(self):
        result=drive(self.frames,self.root/"replay.sqlite3")
        self.assertEqual(result,self.record)

    def test_demo6_session_reset_isolated_and_deterministic(self):
        with TestClient(self.host) as first, TestClient(self.host) as second:
            first.get("/demo/scenarios")
            second.get("/demo/scenarios")
            before=first.get("/patients/demo-stable-7/status").json()
            second_before=second.get("/patients/demo-stable-7/status").json()
            self.assertEqual(self.ingest(first,"demo-stable-7","PATIENT_CHECKIN",{"state":"Rough"}).status_code,200)
            self.assertEqual(second.get("/patients/demo-stable-7/status").json(),second_before)
            self.assertEqual(first.post("/demo/reset",json={"confirm":"RESET_SYNTHETIC_SESSION"}).status_code,200)
            self.assertEqual(first.get("/patients/demo-stable-7/status").json(),before)

    def test_demo7_no_signup_and_unassessed_synthetic_text_is_held(self):
        self.assertEqual(self.client.post("/patients",json={"patient_id":"real","display_name":"do not store","age":35}).status_code,403)
        before=self.client.get("/patients/demo-stable-7/timeline").json()
        response=self.ingest(self.client,"demo-stable-7","PATIENT_FREE_TEXT",{"text":"Synthetic unassessed note"})
        self.assertEqual(response.status_code,200)
        self.assertTrue(response.json()['longitudinal']['deferred'])
        self.assertTrue(response.json()['safety']['state']['degraded'])

    def test_demo8_private_assets_and_api_docs_not_served(self):
        for path in ("/assets/README.md","/assets/index.html","/docs","/redoc","/openapi.json"):
            self.assertEqual(self.client.get(path).status_code,404,path)
        self.assertEqual(self.client.get("/assets/app.js").status_code,200)

    def test_demo9_incomplete_seed_not_silently_reopened(self):
        db=self.root/"partial.sqlite3"; factory=SQLiteRepositoryFactory(db); factory.initialize()
        PatientEventService(factory).create_patient(patient_id="demo-stable-7",display_name="Partial",age=35,timezone_name="UTC")
        with self.assertRaises(ValueError): prepare(db)
        with factory.transaction() as repo: self.assertIsNotNone(repo.patient("demo-stable-7"))

    def test_demo10_reset_archives_and_rejects_unknown_profiles(self):
        db=self.root/"operator.sqlite3"; shutil.copyfile(self.host.baseline,db)
        archive=reset_snapshot(db,self.host.baseline)
        self.assertTrue(archive.is_file()); verify(db,exclusive=True)
        PatientEventService(SQLiteRepositoryFactory(db)).create_patient(patient_id="unknown",display_name="Do not erase",age=35,timezone_name="UTC")
        with self.assertRaises(ValueError): reset_snapshot(db,self.host.baseline)

    def test_demo11_new_signal_reopens_held_without_anchor_change(self):
        held_at=next(row for row in self.record["trace"] if row["longitudinal"]["held"])
        final=self.record["trace"][-1]
        self.assertTrue(all(item["status"]=="REOPENED" for item in final["longitudinal"]["held"]))
        self.assertEqual([b["anchor"] for b in held_at["longitudinal"]["baselines"]],
                         [b["anchor"] for b in final["longitudinal"]["baselines"]])

    def test_demo12_patient_distress_with_missing_wearable_stays_active(self):
        timeline=generate(SimulationDataAgent().plan("Case C illness plus worsening check-in and missing wearable"))
        result=drive(observable_events(timeline),self.root/"mixed.sqlite3")
        self.assertTrue(any(row["communication_decision"] in {"MICRO_CHECKIN","TARGETED_CLARIFICATION"} for row in result["trace"]))
        gap=next(row for row in result["trace"] if all(b["sensing_state"]=="UNOBSERVED" for b in row["longitudinal"]["baselines"]) and row["longitudinal"]["baselines"])
        self.assertTrue(all(b["rolling"]["mean"] is None for b in gap["longitudinal"]["baselines"]))

    def test_demo13_figurative_fixture_and_detector_failure_are_not_guessed(self):
        for phrase, degraded in (("Case A figurative language",False),("Case A detector failure",True)):
            plan=SimulationDataAgent().plan(phrase)
            result=drive(observable_events(generate(plan)),self.root/("timeout.sqlite3" if degraded else "figurative.sqlite3"))
            self.assertEqual(result["trace"][-1]["safety"]["state"]["degraded"],degraded)
        # These are explicit resolved mocks, not detector sensitivity/specificity claims.

    def test_demo14_agent_contract_rejects_policy_and_unknown_fields(self):
        for extra in ({"safety_tier":"URGENT"},{"latent_truth":True},{"diagnosis":"depression"}):
            with self.assertRaises(ValueError): validate_plan({"case":"A",**extra})
        agent=SimulationDataAgent()
        self.assertEqual(agent.plan("Case B 90-day slow drift").days,90)

    def test_demo15_model_adapter_validates_before_numeric_generation(self):
        transport=httpx.MockTransport(lambda request:httpx.Response(200,json={"case":"B","seed":7,"days":70}))
        planner=JSONGatewayPlanner("https://fixture.invalid","synthetic-fixture",transport=transport)
        plan=SimulationDataAgent(planner).plan("Synthetic slow drift")
        self.assertEqual(plan.case,"B")
        bad=httpx.MockTransport(lambda request:httpx.Response(200,json={"case":"B","interaction_mode":"URGENT"}))
        with self.assertRaises(ValueError): SimulationDataAgent(JSONGatewayPlanner("https://fixture.invalid","fixture",transport=bad)).plan("Synthetic only")

    def test_demo16_production_domains_do_not_import_simulation_agent(self):
        root=Path(__file__).resolve().parents[1]
        for folder in ("aura_safety","aura_longitudinal"):
            for file in (root/folder).glob("*.py"):
                self.assertNotIn("aura_simulation",file.read_text())
        for file in ("service.py","communication.py","longitudinal.py"):
            self.assertNotIn("aura_simulation",(root/"aura_app"/file).read_text())


if __name__ == "__main__": unittest.main()
