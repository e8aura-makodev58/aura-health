import json
import re
import unittest

from aura_agent.grounding import validate
from aura_agent.presentation import checked_headline
from aura_agent.roles import AgentRole, instructions
from aura_agent.templates import fallback
from aura_agent.tools import RecordTools
from aura_agent.voice import VOICE_EXAMPLES, jargon
from tests.test_final_dash import evidence, HeadlineProvider
from aura_agent.runtime import run


class PatientVoiceTests(unittest.TestCase):
    def tools(self, patient=True):
        role = AgentRole.PATIENT_INSIGHT if patient else AgentRole.CLINICIAN_BRIEF
        tools = RecordTools(evidence(), role)
        tools.call('get_series',{})
        return tools

    def test_friendly_facts_preserve_raw_and_exact_metadata(self):
        tools = self.tools()
        fact = next(f for f in tools.facts.values() if f.get('finding'))
        self.assertIn('First recorded',fact['raw_text'])
        self.assertEqual(fact['finding']['since'],'2026-03-10')
        self.assertIn('since early March',fact['patient']['text'])
        self.assertNotIn('bedtime',fact['patient']['text'])
        self.assertEqual(fact['patient']['source_label'],'Your measurements')
        model_facts = tools.call('get_series',{})['facts']
        self.assertTrue(all('raw_text' not in f for f in model_facts))
        numeric = next(f for f in model_facts if f.get('magnitude'))
        self.assertIn(numeric['patient']['magnitude_phrase'],numeric['text'])

    def test_fallback_is_plain_and_cited(self):
        tools = self.tools()
        draft = fallback(tools,AgentRole.PATIENT_INSIGHT)
        validate(draft,tools,AgentRole.PATIENT_INSIGHT)
        for text in [draft['headline'],*(c['text'] for c in draft['claims'])]:
            self.assertFalse(jargon(text,True),text)
            self.assertNotRegex(text,r'\d{4}-\d{2}-\d{2}|demo-|<|!')
        self.assertLessEqual(len(draft['headline'].split()),35)
        self.assertTrue(all(len(s.split()) <= 25 for s in re.split(r'[.!?]',draft['headline'])))

    def test_checkins_and_specific_gap_have_supported_fallback_without_findings(self):
        for kind in ('checkins','gap'):
            source=evidence()
            source['signals'][0]['findings']=[]
            if kind == 'checkins':
                source['checkins']=[{'event_id':'check-12','at':'2026-03-12T10:00:00','state':'Rough','deferred':False}]
            else:
                source['signals'][0]['gaps']=[{'event_id':'gap-12','at':'2026-03-12T10:00:00','type':'SENSING_GAP'}]
            tools=RecordTools(source,AgentRole.PATIENT_INSIGHT)
            for name in tools.groups: tools.call(name,{})
            draft=fallback(tools,AgentRole.PATIENT_INSIGHT)
            self.assertTrue(draft['claims'])
            self.assertIn('check-ins' if kind=='checkins' else 'heart rate readings',draft['headline'])
            self.assertNotIn('watch hasn',draft['headline'])
            validate(draft,tools,AgentRole.PATIENT_INSIGHT)

    def test_patient_length_change_does_not_change_clinician_budget(self):
        tools = self.tools()
        fid = next(f['fact_id'] for f in tools.delivered.values() if f.get('finding'))
        text = 'Your resting heart rate was higher than usual in your recent entries. Your resting heart rate was higher than usual in your recent entries.'
        raw = {'headline':text,'fact_ids':[fid],'question_ids':[]}
        checked_headline(raw,tools,AgentRole.PATIENT_INSIGHT)
        with self.assertRaisesRegex(ValueError,'HEADLINE_BUDGET'):
            checked_headline(raw,tools,AgentRole.CLINICIAN_BRIEF)

    def test_examples_cannot_be_copied_or_invent_feelings_actions_and_stability(self):
        self.assertEqual(len(VOICE_EXAMPLES['patient']),7)
        self.assertIn('Style examples',instructions(AgentRole.PATIENT_INSIGHT))
        for text in ('Your heart rate changed since <PERIOD>.','Your heart rate was 9999.',
                     'Your bedtime changed.','Nothing else has changed.',
                     'You feel worse.','You should call your doctor.','Your sleep was shorter.'):
            with self.subTest(text=text):
                tools = self.tools()
                fid = next(f['fact_id'] for f in tools.delivered.values() if f.get('finding'))
                with self.assertRaises(ValueError):
                    checked_headline({'headline':text,'fact_ids':[fid],'question_ids':[]},tools,AgentRole.PATIENT_INSIGHT)

    def test_independent_verifier_still_rejects_direction_reversal(self):
        result = run(AgentRole.PATIENT_INSIGHT,None,self.tools(),
            HeadlineProvider('Your resting heart rate was lower than usual.',supported=False),presentation=True)
        self.assertFalse(result['generation_used'])
        self.assertTrue(any(t.get('code') == 'VERIFIER_REJECTED' for t in result['trace']))

    def test_clinician_projection_retains_numbers_dates_and_raw_facts(self):
        patient = self.tools()
        clinician = self.tools(False)
        self.assertEqual(list(patient.facts),list(clinician.facts))
        for fid,fact in clinician.facts.items():
            self.assertEqual(fact['raw_text'],patient.facts[fid]['raw_text'])
            self.assertEqual(re.findall(r'\d+(?:\.\d+)?',fact['text']),re.findall(r'\d+(?:\.\d+)?',fact['raw_text']))


if __name__ == '__main__':
    unittest.main()
