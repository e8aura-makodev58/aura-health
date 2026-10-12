"""FD: bounded wording and presentation facts; no paid models or domain changes."""
from copy import deepcopy
from pathlib import Path
import json
import unittest

from aura_agent.grounding import validate
from aura_agent.presentation import checked_headline, checked_synthesis, record_presentation
from aura_agent.roles import AgentRole
from aura_agent.runtime import run, AgentConfig
from aura_agent.templates import fallback
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
    def presentation_tools(self, source):
        tools=RecordTools(source,AgentRole.CLINICIAN_BRIEF)
        for name in tools.groups:tools.call(name,{})
        return tools

    def test_fd5_common_overlap_cites_channels_and_patient_run(self):
        source=evidence()
        source['checkins']=[{'event_id':f'check-{d}','at':f'2026-03-{d:02}T10:00:00',
                            'state':'Rough','deferred':False} for d in (10,11,12)]
        tools=self.presentation_tools(source)
        result=record_presentation(tools,AgentConfig())
        synthesis=result['synthesis'];self.assertIsNotNone(synthesis)
        self.assertIn('Resting heart rate and Check-ins',synthesis['text'])
        self.assertEqual(len(synthesis['fact_ids']),2)
        self.assertEqual(synthesis['group']['start'],'2026-03-10')
        self.assertEqual(result['checkins']['checkin_summary']['count'],3)
        self.assertIsNone(record_presentation(tools,AgentConfig(co_occurrence_days=4))['synthesis'])
        interrupted=deepcopy(source)
        interrupted['signals'][0]['gaps']=[{'event_id':'gap','type':'SENSING_GAP','at':'2026-03-11'}]
        self.assertIsNone(record_presentation(self.presentation_tools(interrupted),AgentConfig())['synthesis'])
        for text in ['Changes because of check-ins','Changes due to check-ins','Changes led to check-ins',
                     'Rough on 999 days','Good check-ins','The anchored changes were recorded']:
            with self.subTest(text=text),self.assertRaises(ValueError):
                checked_synthesis({'text':text,'fact_ids':synthesis['fact_ids']},tools,synthesis['group'])
        with self.assertRaises(ValueError):
            checked_synthesis({'text':'Recorded over the same period','fact_ids':synthesis['fact_ids'][:1]},tools,synthesis['group'])

    def test_fd6_held_missing_and_changed_answers_break_runs_no_interpolation(self):
        source=evidence()
        source['checkins']=[{'event_id':f'check-{d}','at':f'2026-03-{d:02}T10:00:00',
                            'state':'Rough','deferred':d==11} for d in (10,11,12)]
        tools=self.presentation_tools(source);result=record_presentation(tools,AgentConfig())
        self.assertIsNone(result['synthesis'])
        self.assertEqual(result['checkins']['checkin_summary']['recorded_days'],2)
        self.assertEqual(result['checkins']['checkin_summary']['run_days'],1)
        self.assertNotIn('check-11',json.dumps(result))

    def test_fd7_questions_vary_with_associated_context_and_recorded_gaps(self):
        source=evidence();self.assertEqual(record_presentation(self.presentation_tools(source),AgentConfig())['question_ids'],['context'])
        source['signals'][0]['contexts']=[{'event_id':'ctx','category':'BENIGN_CONTEXT','start':'2026-03-10','end':'2026-03-12'}]
        self.assertEqual(record_presentation(self.presentation_tools(source),AgentConfig())['question_ids'],['visit'])
        source['signals'][0]['gaps']=[{'event_id':'gap','type':'SENSING_GAP','at':'2026-03-11'}]
        self.assertEqual(record_presentation(self.presentation_tools(source),AgentConfig())['question_ids'],['recording'])
        source['signals'][0]['contexts'][0]['end']='2026-03-09'
        self.assertEqual(record_presentation(self.presentation_tools(source),AgentConfig())['question_ids'],['context','recording'])

    def test_fd8_checkin_source_ids_remain_outside_model_facts(self):
        source=evidence();source['checkins']=[{'event_id':'hidden-scenario-Rough-truth',
            'at':'2026-03-12T10:00:00','state':'Rough','deferred':False}]
        tools=RecordTools(source,AgentRole.CLINICIAN_BRIEF)
        returned=tools.call('get_decisions',{})
        self.assertNotIn('hidden-scenario',json.dumps(returned))
        self.assertNotIn('source_refs',json.dumps(returned))
        self.assertIn('hidden-scenario',json.dumps(list(tools.delivered.values())))

    def test_fd9_synthesis_covers_all_overlapping_channels_and_excludes_chained_spans(self):
        source=evidence();base=source['signals'][0]
        for signal,label in [('SLEEP_MIDPOINT','Sleep timing'),('ACTIVITY','Activity'),
                             ('HRV','HRV'),('RESPIRATORY_RATE','Respiratory rate'),
                             ('SKIN_TEMPERATURE_DEVIATION','Skin temperature')]:
            row=deepcopy(base);row['key']['signal']=signal;row['label']=label
            source['signals'].append(row)
        source['checkins']=[{'event_id':f'check-{d}','at':f'2026-03-{d:02}T10:00:00',
                            'state':'Rough','deferred':False} for d in (10,11,12)]
        result=record_presentation(self.presentation_tools(source),AgentConfig())
        self.assertEqual(len(result['synthesis']['fact_ids']),7)
        for label in ['Sleep timing','Activity','HRV','Respiratory rate','Skin temperature','Check-ins']:
            self.assertIn(label,result['synthesis']['text'])
        source['signals'][-1]['findings'][0].update(first_seen='2026-03-01',last_seen='2026-03-09')
        result=record_presentation(self.presentation_tools(source),AgentConfig())
        self.assertNotIn('Skin temperature',result['synthesis']['text'])

    def test_fd10_actual_registry_labels_produce_jargon_free_validated_synthesis(self):
        source=evidence();base=source['signals'][0]
        registry=json.loads((Path(__file__).resolve().parents[1]/'aura_longitudinal'/'signal_registry.json').read_text())
        definitions=registry['signals']
        for definition in definitions:
            if not definition['enabled_in_engine'] or definition['name']=='RESTING_HEART_RATE':continue
            row=deepcopy(base);row['key']['signal']=definition['name'];row['label']=definition['label']
            source['signals'].append(row)
        self.assertIn('Skin-temperature deviation',[row['label'] for row in source['signals']])
        tools=self.presentation_tools(source)
        result=record_presentation(tools,AgentConfig())
        synthesis=result['synthesis']
        self.assertIn('Skin temperature',synthesis['text'])
        self.assertNotIn('deviation',synthesis['text'].lower())
        checked_synthesis({'text':synthesis['text'],'fact_ids':synthesis['fact_ids']},tools,synthesis['group'])

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

    def test_patient_natural_sentence_retains_citations_and_independent_verifier(self):
        tools=RecordTools(evidence(),AgentRole.PATIENT_INSIGHT)
        sentence='Your resting heart rate was higher than usual in your recent entries.'
        provider=HeadlineProvider(sentence)
        original_step=provider.step
        prompts=[]
        def capture(messages,specs):
            if specs:prompts.append(messages[0]['content'])
            return original_step(messages,specs)
        provider.step=capture
        result=run(AgentRole.PATIENT_INSIGHT,None,tools,provider,presentation=True)
        self.assertTrue(result['generation_used'],result['trace'])
        self.assertEqual(result['draft']['headline'],sentence)
        self.assertTrue(result['headline_fact_ids'])
        self.assertTrue(result['extracted_fact_ids'])
        self.assertIn('Choose one or two supported facts',prompts[0])
        self.assertIn('Read get_decisions',prompts[0])
        self.assertTrue(any(t.get('action')=='INDEPENDENT_VERIFIER' for t in result['trace']))
        validate(result['draft'],tools,AgentRole.PATIENT_INSIGHT)

    def test_patient_technical_lists_perspective_and_advice_are_rejected(self):
        cases=[('Your RMSSD and HRV changed.','HEADLINE_JARGON'),
               ('Your physiology and respiratory rate changed.','HEADLINE_JARGON'),
               ('Recorded changes in resting heart rate','PATIENT_HEADLINE_STYLE'),
               ('Sleep later, activity lower','PATIENT_HEADLINE_STYLE'),
               ('Your heart rate: higher than usual','PATIENT_HEADLINE_STYLE'),
               ('I noticed your heart rate was higher.','PATIENT_HEADLINE_PERSPECTIVE'),
               ('Your heart rate was higher; contact your doctor.','PATIENT_HEADLINE_STYLE'),
               ('You should contact your doctor.','PROHIBITED_CLAIM'),
               ('Take a break.','PROHIBITED_CLAIM'),
               ('Rest more.','PROHIBITED_CLAIM'),
               ('There is nothing to worry about.','PROHIBITED_CLAIM'),
               ('Everything is fine.','PROHIBITED_CLAIM'),
               ('Your breathing was faster than usual.','UNSUPPORTED_SIGNAL'),
               ('Your sleep time was later than usual.','UNSUPPORTED_SIGNAL'),
               ('You were moving less than usual.','UNSUPPORTED_SIGNAL'),
               ('Your resting heart rate was 999.','FABRICATED_NUMBER_OR_DATE'),
               ('You reported Rough days.','UNSUPPORTED_CATEGORY'),
               ('Your heart rate changed because of flu.','PROHIBITED_CLAIM'),
               ('Depression is worsening.','PROHIBITED_CLAIM'),
               ('Your heart rate '+ 'was '*26,'HEADLINE_BUDGET')]
        for text,code in cases:
            with self.subTest(text=text):
                result=run(AgentRole.PATIENT_INSIGHT,None,
                    RecordTools(evidence(),AgentRole.PATIENT_INSIGHT),HeadlineProvider(text),presentation=True)
                self.assertFalse(result['generation_used'])
                self.assertFalse(result['headline_fact_ids'])
                self.assertTrue(result['draft']['claims'])
                self.assertTrue(any(t.get('code')==code for t in result['trace']),result['trace'])
        # Patient copy constraints do not narrow the clinician contract.
        result=run(AgentRole.CLINICIAN_BRIEF,None,RecordTools(evidence(),AgentRole.CLINICIAN_BRIEF),
                   HeadlineProvider(),presentation=True)
        self.assertTrue(result['generation_used'],result['trace'])

    def test_patient_semantic_rejection_restores_useful_plain_record_recap(self):
        result=run(AgentRole.PATIENT_INSIGHT,None,RecordTools(evidence(),AgentRole.PATIENT_INSIGHT),
            HeadlineProvider('Your resting heart rate was lower than usual.',supported=False),presentation=True)
        self.assertFalse(result['generation_used'])
        self.assertFalse(result['headline_fact_ids'])
        self.assertRegex(result['draft']['headline'],r'Your resting heart rate was .*higher')
        self.assertTrue(any(t.get('code')=='VERIFIER_REJECTED' for t in result['trace']))

    def test_patient_extraction_names_research_channels_in_ordinary_words(self):
        source=evidence()
        for signal,label in [('HRV','HRV (RMSSD)'),('RESPIRATORY_RATE','Respiratory rate'),
                             ('SKIN_TEMPERATURE_DEVIATION','Skin-temperature deviation')]:
            with self.subTest(signal=signal):
                row=deepcopy(source['signals'][0]);row['key']['signal']=signal;row['label']=label
                only=deepcopy(source);only['signals']=[row]
                tools=RecordTools(only,AgentRole.PATIENT_INSIGHT);tools.call('get_series',{})
                draft=fallback(tools,AgentRole.PATIENT_INSIGHT)
                self.assertNotRegex(draft['headline'].lower(),r'rmssd|\bhrv\b|respiratory|deviation')
                self.assertLessEqual(len(draft['headline'].split()),35)
                self.assertEqual(draft['claims'][0]['findings'][0]['signal'],signal)
                validate(draft,tools,AgentRole.PATIENT_INSIGHT)

    def test_patient_recaps_preserve_recent_vs_personal_comparator(self):
        for kind,reference in [('TRANSIENT_DEVIATION','in your recent records'),
                               ('PERSISTENT_DRIFT','your usual')]:
            with self.subTest(kind=kind):
                source=evidence();source['signals'][0]['findings'][0]['drift']['kind']=kind
                tools=RecordTools(source,AgentRole.PATIENT_INSIGHT);tools.call('get_series',{})
                draft=fallback(tools,AgentRole.PATIENT_INSIGHT)
                self.assertIn('than '+reference,draft['headline'])
                self.assertIn('than '+reference,draft['claims'][0]['text'])

    def test_patient_report_categories_are_cited_and_semantic_overreach_falls_back(self):
        source=evidence();source['checkins']=[{'event_id':'check-12',
            'at':'2026-03-12T10:00:00','state':'Rough','deferred':False}]
        class ReportProvider(HeadlineProvider):
            def step(self,messages,specs):
                if not specs:return super().step(messages,specs)
                completed=[m for m in messages if m['role']=='tool']
                if not completed:
                    return {'role':'assistant','content':None,'tool_calls':[
                        {'id':name,'type':'function','function':{'name':name,'arguments':'{}'}}
                        for name in ('get_series','get_decisions')]}
                facts=[fact for m in completed for fact in json.loads(m['content'])['facts']]
                finding=next(f for f in facts if f.get('finding'))
                report=next(f for f in facts if f.get('patient',{}).get('source_label') == 'Your check-ins')
                return {'role':'assistant','content':json.dumps({'headline':self.text,
                    'fact_ids':[finding['fact_id'],report['fact_id']],'question_ids':[]})}
        good=run(AgentRole.PATIENT_INSIGHT,None,RecordTools(source,AgentRole.PATIENT_INSIGHT),
            ReportProvider('Your heart rate was higher in recent records, and you reported Rough days.'),presentation=True)
        self.assertTrue(good['generation_used'],good['trace'])
        self.assertEqual(len(good['headline_fact_ids']),2)
        wrong=run(AgentRole.PATIENT_INSIGHT,None,RecordTools(source,AgentRole.PATIENT_INSIGHT),
            ReportProvider('You reported Good days.'),presentation=True)
        self.assertFalse(wrong['generation_used'])
        self.assertTrue(any(t.get('code')=='UNSUPPORTED_CATEGORY' for t in wrong['trace']))
        overreach=run(AgentRole.PATIENT_INSIGHT,None,RecordTools(source,AgentRole.PATIENT_INSIGHT),
            ReportProvider('You feel worse now.',supported=False),presentation=True)
        self.assertFalse(overreach['generation_used'])
        self.assertTrue(any(t.get('code')=='PATIENT_HEADLINE_STYLE' for t in overreach['trace']))


if __name__=='__main__':unittest.main()
