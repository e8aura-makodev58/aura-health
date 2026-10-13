"""Approved §39–41 workflows; synthetic fixtures and mocked models only."""
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from uuid import uuid4
from unittest.mock import patch
from fastapi.testclient import TestClient

from aura_agent.roles import AgentRole
from aura_agent.runtime import run
from aura_agent.tools import RecordTools
from aura_app.agent import AgentService
from aura_app.api import create_app
from aura_app.demo import create_demo_app, DemoFixtureGate
from aura_app.evidence import EvidenceViewService
from aura_app.models import AppError, ApplicationEvent, EventType
from aura_app.persistence import SQLiteRepositoryFactory
from aura_app.service import PatientEventService
from aura_app.safety import SafetyGateUnavailable
from aura_app.workflows import WorkflowService, measurements
from aura_detectors.layered import LayeredSafetyGate
from aura_simulation.life import LifePlan, generate, load_effects
from tests.test_agent import MockAgent

class TaskModel:
    live=True;model_id='synthetic-task-mock-v1'
    def __init__(self, concern='none', fail=False):self.concern=concern;self.fail=fail;self.requests=[]
    def step(self,messages,tools):
        self.requests.append(messages)
        if self.fail:raise TimeoutError()
        instruction=messages[0]['content'];data=json.loads(messages[1]['content'])
        if 'concern' in instruction:raw={'concern':self.concern}
        elif 'date_column' in instruction:raw={'date_column':'date','columns':[{'column':'hr','signal':'RESTING_HEART_RATE','unit':'beats/min'}]}
        elif 'contextual category' in instruction:raw={'category':'BENIGN_CONTEXT','affected_signals':['SLEEP_MIDPOINT']}
        else:raw={'days':data['days'],'events':[{'type':'FLU','start_day':1,'duration_days':data['days'],'severity':'MODERATE'}],'feedback':[]}
        return {'content':json.dumps(raw)}

class ApprovedWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures=TemporaryDirectory();cls.baseline=Path(cls.fixtures.name)/'base.sqlite3';create_demo_app(cls.baseline)
    @classmethod
    def tearDownClass(cls):cls.fixtures.cleanup()
    def setUp(self):
        self.temp=TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.db=Path(self.temp.name)/'test.sqlite3';shutil.copyfile(self.baseline,self.db)
        self.repo=SQLiteRepositoryFactory(self.db);self.repo.initialize();self.model=TaskModel()
        gate=LayeredSafetyGate(self.model,fixtures=DemoFixtureGate(['demo-B-7','demo-D-7','demo-stable-7']))
        self.service=PatientEventService(self.repo,safety_gate=gate);self.flow=WorkflowService(self.service,self.model,synthetic_only=True);self.patient='demo-B-7'
    def event(self,text):
        with self.repo.transaction() as repo:at=datetime.fromisoformat(repo.events(self.patient)[-1]['occurred_at'])
        id=str(uuid4());return ApplicationEvent(id,self.patient,EventType.PATIENT_FREE_TEXT,at,datetime.now(timezone.utc),'synthetic_patient_ui',{'text':text},id,id)
    def count(self):
        with self.repo.transaction() as repo:return len(repo.events(self.patient))
    def test_aw1_multiple_tools_and_independent_verifier(self):
        class Parallel(MockAgent):
            def step(self,messages,specs):
                if specs and not any(m['role']=='tool' for m in messages):
                    return {'tool_calls':[{'id':str(i),'function':{'name':name,'arguments':'{}'}} for i,name in enumerate(self.plan)]}
                return super().step(messages,specs)
        tools=RecordTools(EvidenceViewService(self.service).get(self.patient),AgentRole.CLINICIAN_BRIEF)
        result=run(AgentRole.CLINICIAN_BRIEF,None,tools,Parallel());self.assertTrue(result['generation_used']);self.assertTrue(any(t['action']=='INDEPENDENT_VERIFIER' for t in result['trace'] if 'action' in t))
    def test_aw2_verifier_rejects_fluent_unsupported_fact(self):
        def corrupt(raw):raw['claims'][0]['text']='The patient changed jobs in Paris.';return raw
        tools=RecordTools(EvidenceViewService(self.service).get(self.patient),AgentRole.CLINICIAN_BRIEF)
        result=run(AgentRole.CLINICIAN_BRIEF,None,tools,MockAgent(corrupt=corrupt));self.assertFalse(result['generation_used']);self.assertNotIn('Paris',json.dumps(result['draft']))
    def test_aw3_parameterized_analysis_calendar_gaps_and_window_bounds(self):
        tools=RecordTools(EvidenceViewService(self.service).get(self.patient),AgentRole.RECORD_QA,window_days=30)
        end=tools.end[:10];from datetime import timedelta,date
        start=(date.fromisoformat(end)-timedelta(days=6)).isoformat()
        result=tools.call('summarize_gaps',{'key_id':'k1','start':start,'end':end});self.assertEqual(result['facts'][0]['analysis']['calendar_days'],7)
        with self.assertRaises(ValueError):tools.call('day_of_week',{'key_id':'k1','start':'1999-01-01','end':end})
    def test_aw4_free_question_safety_precedes_record_model(self):
        self.model.concern='possible';provider=MockAgent();agent=AgentService(self.service,provider=provider,synthetic_only=True)
        result=agent.execute(self.patient,'record_qa',run_id='qa',question='I feel very uncertain today.')
        self.assertEqual(result['status'],'BLOCKED');self.assertEqual(provider.calls,0);self.assertEqual(len(self.model.requests),1)
    def test_aw4b_clinician_question_is_not_patient_testimony(self):
        provider=MockAgent();agent=AgentService(self.service,provider=provider,synthetic_only=True);count=self.count()
        result=agent.execute(self.patient,'record_qa',run_id='qa-clinician',question='When did sleep timing change?',asker='clinician')
        self.assertEqual(result['status'],'COMPLETE');self.assertGreater(provider.calls,0)
        self.assertEqual(self.count(),count);self.assertEqual(self.model.requests,[])
        self.assertEqual(result['asker'],'clinician');self.assertEqual(result['clinician_question'],'When did sleep timing change?')
        with self.repo.transaction() as repo:
            self.assertFalse(any(row['payload'].get('text')=='When did sleep timing change?' for row in repo.events(self.patient)))
    def test_aw4c_clinician_route_refuses_personal_statements_without_storing(self):
        provider=MockAgent();agent=AgentService(self.service,provider=provider,synthetic_only=True);count=self.count()
        with self.assertRaises(AppError) as raised:
            agent.execute(self.patient,'record_qa',run_id='qa-statement',question='I want to die.',asker='clinician')
        self.assertEqual(raised.exception.code,'QUESTION_NOT_INVESTIGATED');self.assertEqual(provider.calls,0)
        self.assertEqual(self.count(),count);self.assertEqual(self.model.requests,[])
        with self.assertRaises(AppError):agent.execute(self.patient,'record_qa',run_id='qa-bad',question='x',asker='nurse')
    def test_aw4d_free_question_fallback_lists_related_facts_not_status(self):
        from aura_agent.templates import fallback
        tools=RecordTools(EvidenceViewService(self.service).get(self.patient),AgentRole.RECORD_QA)
        for name in tools.groups:tools.call(name,{})
        draft=fallback(tools,AgentRole.RECORD_QA,'Did activity drop before sleep timing changed?')
        texts=[claim['text'] for claim in draft['claims']]
        self.assertEqual(draft['headline'],'Related facts from the record')
        self.assertTrue(any(text.startswith('Activity') for text in texts))
        self.assertFalse(any('sensing' in text or 'Recorded period ends' in text for text in texts))
    def test_aw4e_fallback_selects_routine_facts_and_whole_words(self):
        from aura_agent.templates import fallback
        with self.repo.transaction() as repo:at=datetime.fromisoformat(repo.events(self.patient)[-1]['occurred_at'])
        id=str(uuid4());self.service.process(ApplicationEvent(id,self.patient,EventType.MEDICATION_EVENT,at,datetime.now(timezone.utc),'synthetic_patient_ui',{'status':'MISSED','scheduled_time':at.isoformat()},id,id))
        tools=RecordTools(EvidenceViewService(self.service).get(self.patient),AgentRole.RECORD_QA)
        for name in tools.groups:tools.call(name,{})
        texts=[c['text'] for c in fallback(tools,AgentRole.RECORD_QA,'Were any medication doses missed?')['claims']]
        self.assertTrue(texts and all(text.startswith('Medication-routine record') for text in texts))
        from aura_agent.templates import _mentions
        self.assertFalse(_mentions('was the patient proactive?','active'));self.assertTrue(_mentions('any missed doses?','dose'))
        self.assertEqual(fallback(tools,AgentRole.RECORD_QA,'Any temperature changes?')['claims'],[])
    def test_aw5_rules_or_semantic_cannot_lower_current_mode(self):
        result=self.service.process(self.event('I want to die.'))
        self.assertEqual(result.safety['state']['interaction_mode'],'ELEVATED')
        later=self.service.process(self.event('Everything is ordinary today.'));self.assertEqual(later.safety['state']['interaction_mode'],'ELEVATED')
    def test_aw6_semantic_failure_preserves_rules_and_holds(self):
        self.model.fail=True;result=self.service.process(self.event('I cannot keep myself safe.'))
        self.assertEqual(result.safety['state']['interaction_mode'],'IMMEDIATE');self.assertTrue(result.safety['state']['degraded']);self.assertTrue(result.longitudinal['deferred'])
    def test_aw7_manual_idempotency_missing_fields_and_anchor_preservation(self):
        with self.repo.transaction() as repo:before=[b['anchor'] for b in repo.baselines(self.patient)];day=repo.events(self.patient)[-1]['occurred_at'][:10]
        result=self.flow.manual(self.patient,run_id='manual',day=day,values={'BODY_TEMPERATURE':38.1});count=self.count()
        self.assertTrue(self.flow.manual(self.patient,run_id='manual',day=day,values={'BODY_TEMPERATURE':38.1})['idempotent_replay']);self.assertEqual(self.count(),count)
        with self.repo.transaction() as repo:self.assertEqual(before,[b['anchor'] for b in repo.baselines(self.patient)])
        self.assertEqual(len(result['event_ids']),1)
    def test_aw8_import_proposal_never_writes_before_confirmation(self):
        count=self.count();proposal=self.flow.import_proposal(self.patient,run_id='proposal',format='csv',content='date,hr\n2026-03-11,66')
        self.assertEqual(count,self.count());self.assertFalse(proposal['confirmed'])
        result=self.flow.confirm_import(self.patient,run_id='confirm',proposal_id='proposal',mapping=proposal['mapping'],confirm='IMPORT_SYNTHETIC_DATA');self.assertTrue(result['confirmed']);self.assertEqual(self.count(),count+1)
    def test_aw9_import_bad_later_row_rolls_back_entire_batch(self):
        count=self.count();proposal=self.flow.import_proposal(self.patient,run_id='proposal',format='csv',content='date,hr\n2026-03-10,66\n2026-03-11,-3')
        with self.assertRaises(AppError):self.flow.confirm_import(self.patient,run_id='confirm',proposal_id='proposal',mapping=proposal['mapping'],confirm='IMPORT_SYNTHETIC_DATA')
        self.assertEqual(count,self.count())
    def test_aw10_stale_mapping_and_units_rejected(self):
        proposal=self.flow.import_proposal(self.patient,run_id='proposal',format='csv',content='date,hr\n2026-03-11,66')
        self.service.process(self.event('fixture ordinary message'))
        with self.assertRaises(AppError):self.flow.confirm_import(self.patient,run_id='confirm',proposal_id='proposal',mapping=proposal['mapping'],confirm='IMPORT_SYNTHETIC_DATA')
        mapping=proposal['mapping'];mapping['columns'][0]['unit']='wrong'
        with self.assertRaises(AppError):self.flow.confirm_import(self.patient,run_id='bad',proposal_id='proposal',mapping=mapping,confirm='IMPORT_SYNTHETIC_DATA')
    def test_aw11_confirmed_context_uses_held_logic_and_preserves_anchor(self):
        self.patient='demo-D-7'
        with self.repo.transaction() as repo:before=[b['anchor'] for b in repo.baselines(self.patient)]
        proposal=self.flow.propose_context(self.patient,run_id='cp',text='A permanent benign schedule change explains my later sleep.')
        count=self.count();result=self.flow.confirm_context(self.patient,run_id='cc',proposal_id='cp',category='BENIGN_CONTEXT',affected_signals=['SLEEP_MIDPOINT'],confirm='KEEP_EXPLICIT_CONTEXT')
        self.assertEqual(self.count(),count+2)
        with self.repo.transaction() as repo:self.assertEqual(before,[b['anchor'] for b in repo.baselines(self.patient)]);self.assertTrue(repo.held(self.patient))
        self.assertEqual(result['results'][-1]['longitudinal']['explanation_status'],'EXPLAINED_HELD_FOR_REVIEW')
    def test_aw12_risk_context_cannot_be_confirmed_benign(self):
        self.flow.propose_context(self.patient,run_id='cp',text='Work stress explains this change.')
        with self.assertRaises(AppError):self.flow.confirm_context(self.patient,run_id='cc',proposal_id='cp',category='BENIGN_CONTEXT',affected_signals=['SLEEP_MIDPOINT'],confirm='KEEP_EXPLICIT_CONTEXT')
    def test_aw13_life_agent_runs_replays_and_preserves_original_anchors(self):
        self.patient='demo-stable-7'
        with self.repo.transaction() as repo:before={b['signal']:b['anchor'] for b in repo.baselines(self.patient)}
        result=self.flow.advance(self.patient,run_id='flu',days=3,notes=False,request='flu');self.assertEqual(result['status'],'VALIDATED_MODEL_PLAN')
        self.assertTrue(self.flow.replay(self.patient,'flu')['matched']);self.assertTrue(self.flow.advance(self.patient,run_id='flu',days=3,notes=False,request='flu')['idempotent_replay'])
        with self.repo.transaction() as repo:
            after={b['signal']:b for b in repo.baselines(self.patient)}
            for signal,anchor in before.items():self.assertEqual(anchor,after[signal]['anchor'])
            self.assertTrue(after['HRV']['anchor']);self.assertTrue(any(o['signal']=='BODY_TEMPERATURE' for o in repo.observations(self.patient)))
            committed=[r['payload'] for r in repo.events(self.patient) if r['source']=='SIMULATOR']
        self.assertNotIn('FLU',json.dumps(committed));self.assertNotIn('expected_outcome',json.dumps(committed))
    def test_flu_clinician_model_budget_keeps_temperature_readings_and_ui_sources(self):
        self.flow.advance(self.patient,run_id='flu-reading-budget',days=3,notes=False,request='flu')
        tools=RecordTools(EvidenceViewService(self.service).get(self.patient),AgentRole.CLINICIAN_BRIEF)
        original=next(f for f in tools.facts.values() if f.get('reading') and f['signal']=='BODY_TEMPERATURE')
        self.assertEqual(original['reading']['count'],3)
        # Raw/UI duplicate text must not consume a budget for model-only facts.
        for fact in tools.facts.values():
            fact['raw_text'] += ' UI-only technical disclosure'*200
        payload=tools.call('get_series',{})
        temperature=next(f for f in payload['facts'] if f.get('reading') and f['signal']=='BODY_TEMPERATURE')
        self.assertEqual(temperature['reading'],original['reading'])
        self.assertLessEqual(len(json.dumps(payload['facts'])),24000)
        self.assertTrue(all('raw_text' not in f and 'patient' not in f for f in payload['facts']))
        retained=tools.delivered[temperature['fact_id']]
        self.assertEqual(retained['reading_source_refs'],original['reading_source_refs'])
        self.assertIn('UI-only technical disclosure',retained['raw_text'])

    def test_aw14_numeric_replay_sparse_cadence_and_no_drug_effect(self):
        effects=load_effects();profile=effects['profile'];base={'days':14,'events':[]}
        one=generate(LifePlan.model_validate(base),seed=42,patient_id='test',start='2026-04-01',profile=profile)
        self.assertEqual(one,generate(LifePlan.model_validate(base),seed=42,patient_id='test',start='2026-04-01',profile=profile))
        self.assertEqual(sum('WEIGHT' in r['values'] for r in one),2);self.assertEqual(sum('BLOOD_PRESSURE_SYSTOLIC' in r['values'] for r in one),6)
        med=generate(LifePlan(days=14,events=[{'type':'MISSED_MEDICATION','start_day':1,'duration_days':3,'severity':'STRONG'}]),seed=42,patient_id='test',start='2026-04-01',profile=profile)
        self.assertEqual([r['values'] for r in one],[r['values'] for r in med])
    def test_aw15_wearable_gap_omits_values_not_zero(self):
        plan=LifePlan(days=7,events=[{'type':'WEARABLE_OFF','start_day':1,'duration_days':5,'severity':'MODERATE'}])
        rows=generate(plan,seed=7,patient_id='test',start='2026-04-01',profile=load_effects()['profile']);self.assertNotIn('RESTING_HEART_RATE',rows[0]['values']);self.assertIn('RESTING_HEART_RATE',rows[-1]['values'])
    def test_aw16_invalid_plan_and_production_boundary(self):
        with self.assertRaises(ValueError):LifePlan.model_validate({'days':3,'events':[],'proposed_tier':'URGENT'})
        with self.assertRaises(AppError):WorkflowService(self.service,self.model).advance(self.patient,run_id='not-demo')
        with self.assertRaises(ValueError):measurements('2026-03-11',{'SLEEP_MIDPOINT':1650},self.service.signal_registry)
    def test_aw17_trace_append_only_and_reload(self):
        self.flow.import_proposal(self.patient,run_id='persist',format='csv',content='date,hr\n2026-03-11,66')
        reopened=WorkflowService(PatientEventService(SQLiteRepositoryFactory(self.db)),self.model,synthetic_only=True)
        self.assertEqual(reopened.trace(self.patient,'persist')['kind'],'IMPORT_PROPOSAL')
        with self.assertRaises(sqlite3.IntegrityError):
            with self.repo.transaction() as repo:repo.conn.execute("UPDATE workflow_runs SET kind='bad'")
    def test_aw18_api_commands_are_thin_and_cross_patient_protected(self):
        app=create_app(service=self.service,agent_service=AgentService(self.service,provider=self.model,synthetic_only=True),synthetic_only=True)
        with TestClient(app) as client:
            response=client.post('/patients/demo-B-7/workflows/manual',json={'run_id':str(uuid4()),'data':{'day':'2026-03-11','values':{'BODY_TEMPERATURE':38.1}}});self.assertEqual(response.status_code,200)
            run_id=response.json()['run_id'];self.assertEqual(client.get('/patients/demo-C-7/workflow-runs/'+run_id).status_code,404)
    def test_aw19_director_failure_has_honest_bounded_fallback(self):
        from aura_simulation.life import direct
        plan,reason=direct(TaskModel(fail=True),7,'flu',{});self.assertEqual(reason,'OFFLINE_KEYWORD_PLAN');self.assertEqual(plan.events[0].type,'FLU')
    def test_aw20_findings_polarity_and_new_words(self):
        from aura_agent.grounding import validate
        tools=RecordTools(EvidenceViewService(self.service).get(self.patient),AgentRole.RECORD_QA);tools.call('get_series',{})
        fid=next(f for f in tools.delivered if tools.delivered[f].get('finding'));fact=tools.delivered[fid]
        raw={'claims':[{'text':'There is a noticeable shift in the recorded sleep schedule.','fact_ids':[fid],'findings':[{'fact_id':fid,**fact['finding']}]}],'question_ids':[]}
        self.assertTrue(validate(raw,tools,AgentRole.RECORD_QA));raw['claims'][0]['findings'][0]['direction']='invented'
        with self.assertRaises(ValueError):validate(raw,tools,AgentRole.RECORD_QA)

    def test_aw21_json_tasks_explicitly_request_json_mode(self):
        from aura_agent.tasks import structured_task
        model=TaskModel();self.assertEqual(structured_task(model,'detect',{'quoted_input':'Synthetic ordinary note'})['concern'],'none')
        self.assertIn('JSON',model.requests[0][0]['content'])

    def test_aw22_empty_vendor_read_arguments_and_role_contract(self):
        class Empty(MockAgent):
            def step(self,messages,specs):
                reply=super().step(messages,specs)
                for call in reply.get('tool_calls',[]):call['function']['arguments']=''
                if specs:
                    schema=json.loads(messages[0]['content'].split('Return JSON only with this schema: ')[1].split('\nQuestion IDs')[0])
                    self.asserted_limit=schema['properties']['claims']['maxItems']
                return reply
        model=Empty();tools=RecordTools(EvidenceViewService(self.service).get(self.patient),AgentRole.PATIENT_INSIGHT)
        result=run(AgentRole.PATIENT_INSIGHT,None,tools,model)
        self.assertTrue(result['generation_used']);self.assertEqual(model.asserted_limit,2)

    def test_aw23_feedback_toggle_and_persisted_simulation_budget(self):
        from aura_app.workflows import load_effects as workflow_effects
        effects=workflow_effects();effects['max_session_runs']=1
        with patch('aura_app.workflows.load_effects',return_value=effects):
            result=self.flow.advance(self.patient,run_id='feedback-off',days=1,notes=False,request='flu')
            with self.repo.transaction() as repo:
                committed=[r for r in repo.events(self.patient) if r['event_id'] in result['event_ids']]
            self.assertFalse(any(r['event_type'] in {'PATIENT_CHECKIN','MEDICATION_EVENT','PATIENT_FREE_TEXT'} for r in committed))
            self.assertTrue(self.flow.replay(self.patient,'feedback-off')['committed_events_match'])
            with self.assertRaises(AppError) as error:self.flow.advance(self.patient,run_id='another',days=1,notes=False)
            self.assertEqual(error.exception.code,'SIMULATION_BUDGET')

    def test_aw24_recovery_survives_advance_boundary(self):
        first=self.flow.advance(self.patient,run_id='flu-tail',days=3,notes=False,plan={'days':3,'events':[{'type':'FLU','start_day':1,'duration_days':3,'severity':'MODERATE'}]})
        second=self.flow.advance(self.patient,run_id='recovery',days=3,notes=False,plan={'days':3,'events':[]})
        self.assertEqual(len(second['carry_events']),1)
        values=[r['values']['BODY_TEMPERATURE'] for r in second['generated']]
        self.assertGreater(first['generated'][-1]['values']['BODY_TEMPERATURE'],values[0]);self.assertGreater(values[0],values[-1])
        self.assertLess(abs(values[-1]-second['profile']['BODY_TEMPERATURE']),.11)
        self.assertTrue(self.flow.replay(self.patient,'recovery')['matched'])

    def test_aw25_verifier_receives_structured_direction_not_text_alone(self):
        class Inspect(MockAgent):
            def step(self,messages,specs):
                if not specs:self.checks=json.loads(messages[1]['content'])
                return super().step(messages,specs)
        provider=Inspect();tools=RecordTools(EvidenceViewService(self.service).get(self.patient),AgentRole.CLINICIAN_BRIEF)
        result=run(AgentRole.CLINICIAN_BRIEF,None,tools,provider)
        self.assertTrue(result['generation_used'])
        facts=[fact for check in provider.checks for fact in check['facts']]
        self.assertTrue(any(fact['finding'] and fact['finding']['direction'] for fact in facts))

    def test_aw26_partial_verifier_drops_claim_without_losing_required_history(self):
        class Partial(MockAgent):
            def step(self,messages,specs):
                if not specs:
                    checks=json.loads(messages[1]['content'])
                    return {'content':json.dumps({'verdicts':[{'index':i,'supported':i!=0} for i in range(len(checks))]})}
                return super().step(messages,specs)
        tools=RecordTools(EvidenceViewService(self.service).get(self.patient),AgentRole.CLINICIAN_BRIEF)
        result=run(AgentRole.CLINICIAN_BRIEF,None,tools,Partial())
        self.assertTrue(result['generation_used']);self.assertEqual(result['reason'],'VALIDATED_PARTIAL_MODEL_DRAFT')
        used={fid for claim in result['draft']['claims'] for fid in claim['fact_ids']}
        self.assertTrue(tools.required<=used);self.assertTrue(result['extracted_fact_ids'])
        self.assertEqual(result['trace'][-2]['rejected_indices'],[0])

    def test_aw27_empty_recap_cannot_claim_no_change_without_reads(self):
        class Empty:
            live=True;model_id='empty-mock'
            def step(self,messages,specs):return {'content':json.dumps({'claims':[],'question_ids':[],'headline':''})}
        tools=RecordTools(EvidenceViewService(self.service).get(self.patient),AgentRole.PATIENT_INSIGHT)
        result=run(AgentRole.PATIENT_INSIGHT,None,tools,Empty())
        self.assertFalse(result['generation_used']);self.assertTrue(result['draft']['claims'])
        self.assertTrue(any(t.get('action')=='READ_REQUIRED' for t in result['trace']))

    def test_aw28_premature_brief_must_read_findings_and_retained_explanations(self):
        class Premature:
            live=True;model_id='premature-brief-mock'
            def __init__(self):self.calls=0
            def step(self,messages,specs):
                self.calls+=1
                if not specs:
                    checks=json.loads(messages[1]['content'])
                    return {'content':json.dumps({'verdicts':[{'index':i,'supported':True} for i in range(len(checks))]})}
                last=messages[-1]
                if last['role']=='user' and last.get('content','').startswith('Server contract: retrieve '):
                    name=last['content'].split('retrieve ')[1].split(' ')[0]
                    return {'tool_calls':[{'id':f'required-{self.calls}','function':{'name':name,'arguments':'{}'}}]}
                reads=[message for message in messages if message['role']=='tool']
                if {message['name'] for message in reads} != {'get_series','get_review_snapshot'}:
                    return {'content':json.dumps({'claims':[],'question_ids':[],'headline':''})}
                payloads=[json.loads(message['content']) for message in reads]
                facts=[fact for payload in payloads for fact in payload['facts']]
                retained={fid for payload in payloads for fid in payload['retained_fact_ids']}
                selected=[fact for fact in facts if fact['fact_id'] in retained]
                return {'content':json.dumps({'claims':[{'text':fact['text'],'fact_ids':[fact['fact_id']],
                    'findings':[{'fact_id':fact['fact_id'],**fact['finding']}] if fact.get('finding') else []}
                    for fact in selected],'question_ids':[],'headline':'Recorded changes'})}
        evidence=EvidenceViewService(self.service).get('demo-D-7')
        tools=RecordTools(evidence,AgentRole.CLINICIAN_BRIEF)
        result=run(AgentRole.CLINICIAN_BRIEF,None,tools,Premature())
        self.assertTrue(result['generation_used'],result['reason'])
        self.assertEqual([t['tool'] for t in result['trace'] if t.get('action')=='READ_REQUIRED'],['get_series','get_review_snapshot'])
        self.assertTrue(tools.required<={fid for claim in result['draft']['claims'] for fid in claim['fact_ids']})
        from aura_agent.runtime import AgentConfig
        provider=Premature()
        limited=run(AgentRole.CLINICIAN_BRIEF,None,RecordTools(evidence,AgentRole.CLINICIAN_BRIEF),provider,AgentConfig(max_steps=1))
        self.assertFalse(limited['generation_used']);self.assertEqual(limited['reason'],'STEP_BUDGET');self.assertEqual(provider.calls,1)
        self.assertTrue(limited['draft']['claims'])

if __name__=='__main__':unittest.main()
