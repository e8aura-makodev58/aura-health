"""I1/I5/I6 arrival: real scoped records, no paid models or new policy."""
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from fastapi.testclient import TestClient
from aura_app.assessment import AssessmentService
from aura_app.agent import AgentService
from aura_app.api import create_app
from aura_app.demo import create_demo_app
from aura_app.models import AppError
from aura_app.persistence import SQLiteRepositoryFactory
from aura_app.service import PatientEventService
from tests.test_agent import MockAgent


class ImpressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=TemporaryDirectory();cls.baseline=Path(cls.root.name)/'base.sqlite3'
        cls.seed=create_demo_app(cls.baseline)

    @classmethod
    def tearDownClass(cls):cls.root.cleanup()

    def setUp(self):
        self.temp=TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'copy.sqlite3';shutil.copyfile(self.baseline,self.path)
        self.repo=SQLiteRepositoryFactory(self.path)
        self.events=PatientEventService(self.repo,safety_gate=self.seed.state.service.safety_gate)
        self.provider=MockAgent();self.agent=AgentService(self.events,provider=self.provider,synthetic_only=True)
        self.arrival=AssessmentService(self.agent)

    def test_i1_immediate_arrival_has_dated_numeric_findings_without_provider(self):
        result=self.arrival.get('demo-B-7','clinician_brief');draft=result['preview']['draft']
        self.assertTrue(draft['headline']);self.assertGreaterEqual(len(draft['claims']),2)
        self.assertTrue(all(c['findings'] for c in draft['claims'][:2]))
        self.assertTrue(all('deviation' in c['text'] for c in draft['claims'][:2]))
        self.assertEqual(self.provider.calls,0)
        with self.repo.transaction() as repo:self.assertIsNone(repo.agent_run('demo-B-7',result['run_id']))

    def test_i1_arrival_retry_uses_durable_cache_without_second_generation(self):
        first=self.arrival.get('demo-B-7','clinician_brief')
        generated=self.agent.execute('demo-B-7','clinician_brief',run_id=first['run_id'])
        calls=self.provider.calls
        cached=self.arrival.get('demo-B-7','clinician_brief')
        self.assertEqual(cached['cached'],generated)
        retry=self.agent.execute('demo-B-7','clinician_brief',run_id=first['run_id'])
        self.assertTrue(retry['idempotent_replay']);self.assertEqual(calls,self.provider.calls)

    def test_i1_guard_blocks_offline_and_unsafe_cache(self):
        initial=self.arrival.get('demo-B-7','clinician_brief')
        self.agent.execute('demo-B-7','clinician_brief',run_id=initial['run_id'])
        calls=self.provider.calls
        offline=self.arrival.get('demo-B-7','clinician_brief',client_offline=True)
        self.assertFalse(offline['generation_allowed']);self.assertIsNone(offline['cached']);self.assertFalse(offline['preview']['draft']['claims'])
        with self.repo.transaction() as repo:
            state=repo.safety_state('demo-B-7');repo.save_safety_state('demo-B-7',{**state,'degraded':True,'degraded_causes':['DETECTOR_TIMEOUT']})
        blocked=self.arrival.get('demo-B-7','clinician_brief')
        self.assertFalse(blocked['generation_allowed']);self.assertIsNone(blocked['cached']);self.assertEqual(calls,self.provider.calls)
        with self.assertRaises(AppError):self.agent.execute('demo-B-7','clinician_brief',run_id=initial['run_id'])
        self.assertEqual(calls,self.provider.calls)

    def test_i1_provider_revision_and_stale_arrival_are_guarded_before_call(self):
        prior=self.arrival.get('demo-B-7','clinician_brief');self.provider.model_id='changed-provider-version'
        current=self.arrival.get('demo-B-7','clinician_brief');self.assertNotEqual(prior['run_id'],current['run_id'])
        with self.assertRaises(AppError):self.agent.execute('demo-B-7','clinician_brief',run_id=prior['run_id'])
        self.assertEqual(self.provider.calls,0)

    def test_i1_api_uses_same_arrival_contract_and_accepts_server_run_id(self):
        with TestClient(create_app(service=self.events,agent_service=self.agent)) as client:
            arrival=client.get('/patients/demo-B-7/assessment/clinician_brief').json()
            response=client.post('/patients/demo-B-7/agent/clinician_brief',json={'run_id':arrival['run_id']})
            self.assertEqual(response.status_code,200,response.text)
            self.assertEqual(client.get('/patients/demo-B-7/assessment/record_qa').status_code,400)

    def test_i6_patient_fallback_plain_short_cited_and_quiet_when_empty(self):
        draft=self.arrival.get('demo-B-7','patient_insight')['preview']['draft']
        self.assertLessEqual(len(draft['claims']),2);self.assertTrue(draft['claims'])
        self.assertEqual([c['findings'][0]['signal'] for c in draft['claims']],['SLEEP_MIDPOINT','ACTIVITY'])
        for c in draft['claims']:
            self.assertTrue(c['fact_ids']);self.assertNotRegex(c['text'].lower(),r'baseline|drift|anchor')
        self.assertFalse(self.arrival.get('demo-stable-7','patient_insight')['preview']['draft']['claims'])

    def test_i1_all_required_history_remains_behind_display_cap(self):
        result=self.arrival.get('demo-D-7','clinician_brief')['preview']
        tools,_=self.agent.record_tools('demo-D-7',__import__('aura_agent.roles',fromlist=['AgentRole']).AgentRole.CLINICIAN_BRIEF,56)
        cited={fid for c in result['draft']['claims'] for fid in c['fact_ids']}
        self.assertTrue(tools.required<=cited)

    def test_i1_arrival_mid_read_change_discards_preview_and_cached_prose(self):
        original=self.agent.record_tools
        def change(*args):
            result=original(*args)
            with self.repo.transaction() as repo:
                state=repo.safety_state('demo-B-7');repo.save_safety_state('demo-B-7',{**state,'degraded':True,'degraded_causes':['DETECTOR_TIMEOUT']})
            return result
        self.agent.record_tools=change
        result=self.arrival.get('demo-B-7','clinician_brief')
        self.assertEqual(result['preview']['status'],'STALE');self.assertFalse(result['generation_allowed'])
        self.assertIsNone(result['cached']);self.assertFalse(result['preview']['draft']['claims']);self.assertEqual(self.provider.calls,0)

    def test_i1_strict_offline_and_live_non_demo_boundary(self):
        with self.assertRaises(AppError):self.arrival.get('demo-B-7','clinician_brief',client_offline='false')
        non_demo=AssessmentService(AgentService(self.events,provider=self.provider))
        result=non_demo.get('demo-B-7','clinician_brief')
        self.assertFalse(result['generation_allowed']);self.assertEqual(result['preview']['reason'],'LIVE_SYNTHETIC_ONLY')

if __name__=='__main__':unittest.main()
