"""FD: bounded wording and presentation facts; no paid models or domain changes."""
from copy import deepcopy
import json
import unittest

from aura_agent.grounding import validate
from aura_agent.presentation import checked_headline
from aura_agent.roles import AgentRole
from aura_agent.runtime import run
from aura_agent.tools import RecordTools


def evidence():
    signals = []
    for name, label, enabled in [('RESTING_HEART_RATE','Resting heart rate',True),
                                  ('BODY_TEMPERATURE','Thermometer temperature',False)]:
        signals.append({'key':{'signal':name,'source':'synthetic_watch','metric':''},'label':label,
            'unit':'beats/min' if enabled else 'degC','registry':{'enabled_in_engine':enabled,'display':True},
            'current':{'sensing_state':'OBSERVED','trust_state':'TRUSTED'},'gaps':[],'contexts':[],
            'observations':[{'event_id':f'measure-{day}','day':f'2026-03-{day:02}',
                'value':70+day if enabled else 37+day/10,'coverage':1,'data_quality':1,'deferred':False}
                for day in (10,11,12)],
            'findings':[{'event_id':'measure-12','first_seen':'2026-03-10','last_seen':'2026-03-12',
                         'drift':{'kind':'TRANSIENT_DEVIATION','current_vs_rolling':8,'rolling_vs_anchor':1,
                                  'description':'Resting heart rate is higher relative to the recent rolling pattern.'}}] if enabled else []})
    return {'period':{'start':'2026-01-01','end':'2026-03-12'},'current_decision':'STAY_QUIET',
            'signals':signals,'checkins':[],'medication':[],'held':[],
            'analysis_coverage_thresholds':{s['key']['signal']:{'minimum_observation_coverage':.5} for s in signals}}


class HeadlineProvider:
    live = True
    model_id = 'fixture-headline'
    def __init__(self, text='Recorded changes in resting heart rate', supported=True):
        self.text, self.supported = text, supported
    def step(self, messages, specs):
        if not specs:
            return {'content':json.dumps({'verdicts':[{'index':0,'supported':self.supported}]})}
        completed = [m for m in messages if m['role']=='tool']
        if not completed:
            return {'role':'assistant','content':None,'tool_calls':[{'id':'read','type':'function',
                'function':{'name':'get_series','arguments':'{}'}}]}
        fact = next(f for m in completed for f in json.loads(m['content'])['facts'] if f.get('finding'))
        return {'role':'assistant','content':json.dumps({'headline':self.text,'fact_ids':[fact['fact_id']], 'question_ids':[]})}


class FinalDashTests(unittest.TestCase):
    def test_fd1_model_headline_and_server_history_are_separate_and_cited(self):
        source=evidence();before=deepcopy(source);tools=RecordTools(source,AgentRole.CLINICIAN_BRIEF)
        result=run(AgentRole.CLINICIAN_BRIEF,None,tools,HeadlineProvider(),presentation=True)
        self.assertTrue(result['generation_used'],result['trace'])
        self.assertEqual(result['draft']['headline'],'Recorded changes in resting heart rate')
        self.assertTrue(tools.required <= {fid for c in result['draft']['claims'] for fid in c['fact_ids']})
        self.assertTrue(result['headline_fact_ids']);self.assertTrue(result['extracted_fact_ids'])
        self.assertEqual(source,before)
        validate(result['draft'],tools,AgentRole.CLINICIAN_BRIEF)

    def test_fd2_citation_numeric_jargon_cause_and_diagnostic_rejections_remain(self):
        tools=RecordTools(evidence(),AgentRole.CLINICIAN_BRIEF);tools.call('get_series',{})
        fid=next(iter(tools.required))
        for text in ['Resting heart rate was 999 beats/min','Depression is worsening',
                     'Changes due to flu','Activity led to lower sleep','Your anchored midpoint changed']:
            with self.subTest(text=text),self.assertRaises(ValueError):
                checked_headline({'headline':text,'fact_ids':[fid],'question_ids':[]},tools)
        for ids in [['unknown'],[],[fid,fid]]:
            with self.assertRaises(ValueError):checked_headline({'headline':'Recorded changes','fact_ids':ids,'question_ids':[]},tools)

    def test_fd3_semantic_failure_keeps_record_cards_not_generated_headline(self):
        result=run(AgentRole.CLINICIAN_BRIEF,None,RecordTools(evidence(),AgentRole.CLINICIAN_BRIEF),
                   HeadlineProvider(supported=False),presentation=True)
        self.assertFalse(result['generation_used']);self.assertFalse(result['headline_fact_ids'])
        self.assertTrue(result['draft']['claims'])
        self.assertTrue(any(t.get('code')=='VERIFIER_REJECTED' for t in result['trace']))

    def test_fd4_sparse_readings_have_no_reference_direction_or_finding(self):
        source=evidence();source['signals'][1]['observations'][0]['deferred']=True
        source['signals'][1]['observations'][1]['coverage']=.1
        tools=RecordTools(source,AgentRole.CLINICIAN_BRIEF)
        returned=tools.call('get_series',{})
        fact=next(f for f in tools.delivered.values() if f.get('reading'))
        self.assertEqual(fact['reading']['count'],1);self.assertEqual(fact['reading']['latest'],38.2)
        self.assertIsNone(fact['finding']);self.assertNotIn(fact['fact_id'],tools.required)
        self.assertNotIn('reading_source_refs',json.dumps(returned))
        source['signals'][1]['observations']=[]
        self.assertFalse(any(f.get('reading') for f in RecordTools(source,AgentRole.CLINICIAN_BRIEF).facts.values()))


if __name__=='__main__':unittest.main()
