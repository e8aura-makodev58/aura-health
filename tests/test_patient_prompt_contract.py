"""Inspect the actual runtime messages and strict rejection paths; no paid calls."""
from copy import deepcopy
import json
import re
import unittest

from aura_agent.providers import ScriptedAgentProvider
from aura_agent.roles import AgentRole, PROMPT_VERSION, instructions
from aura_agent.runtime import run
from aura_agent.tools import RecordTools
from aura_agent.voice import VOICE_EXAMPLES
from tests.test_final_dash import HeadlineProvider, evidence


class RecordingScriptedProvider(ScriptedAgentProvider):
    def __init__(self):
        self.requests = []

    def step(self, messages, tools):
        self.requests.append(deepcopy(messages))
        return super().step(messages, tools)


class PatientPromptContractTests(unittest.TestCase):
    def test_actual_scripted_messages_use_short_target_and_native_tool_protocol(self):
        for role in (AgentRole.PATIENT_INSIGHT, AgentRole.CLINICIAN_BRIEF):
            with self.subTest(role=role):
                provider = RecordingScriptedProvider()
                tools = RecordTools(evidence(), role)
                result = run(role, None, tools, provider, presentation=True)
                self.assertFalse(result['generation_used'])
                self.assertEqual(result['prompt_version'], 'aura-agent-v9')
                first = provider.requests[0]
                prompt = first[0]['content']
                self.assertIn('native tool_calls with JSON object arguments', prompt)
                self.assertIn('exactly the keys headline, fact_ids, question_ids', prompt)
                self.assertIn('arrays of strings', prompt)
                self.assertEqual(json.loads(first[1]['content'])['prompt_version'], PROMPT_VERSION)
                completed = [row for row in provider.requests[-1] if row['role'] == 'tool']
                self.assertTrue(any(row['name'] == 'get_series' for row in completed))
                self.assertTrue(all(isinstance(json.loads(row['content'])['facts'], list) for row in completed))
                if role == AgentRole.PATIENT_INSIGHT:
                    self.assertIn('28 words total and 18 words per sentence', prompt)
                    self.assertNotIn('two or three', prompt)
                    self.assertIn('RECENT_PATTERN', prompt)
                else:
                    self.assertIn('Absolute maximum 20 words', prompt)

    def test_every_patient_example_leaves_room_below_hard_limits(self):
        self.assertEqual(VOICE_EXAMPLES['version'], 'patient-voice-v2')
        self.assertIn('18 words per sentence', instructions(AgentRole.PATIENT_INSIGHT))
        for row in VOICE_EXAMPLES['patient']:
            with self.subTest(remark=row['remark']):
                self.assertLessEqual(len(row['remark'].split()), 28)
                self.assertTrue(all(len(sentence.split()) <= 18 for sentence in re.split(r'[.!?]', row['remark'])))
                self.assertNotRegex(row['remark'], r'\d|\bbedtime\b|because|due to|nothing else')

    def test_verifier_gets_exact_citations_comparison_and_checkin_metadata_without_event_ids(self):
        source = evidence()
        source['checkins'] = [{'event_id':f'demo-B-hidden-check-{day}',
            'at':f'2026-03-{day:02}T10:00:00', 'state':'Rough', 'deferred':False} for day in (10,11,12)]
        tools = RecordTools(source, AgentRole.PATIENT_INSIGHT)

        class RejectingCapture(HeadlineProvider):
            def __init__(self):
                super().__init__(supported=False)
                self.verifier_messages = None

            def step(self, messages, specs):
                if not specs:
                    self.verifier_messages = deepcopy(messages)
                    return super().step(messages, specs)
                completed = [row for row in messages if row['role'] == 'tool']
                if not completed:
                    return {'role':'assistant','content':None,'tool_calls':[
                        {'id':name,'type':'function','function':{'name':name,'arguments':'{}'}}
                        for name in ('get_series','get_decisions')]}
                facts = [fact for row in completed for fact in json.loads(row['content'])['facts']]
                finding = next(fact for fact in facts if fact.get('finding'))
                run_report = next(fact for fact in facts if fact.get('checkin_run'))
                report = next(fact for fact in facts if fact.get('checkin_summary'))
                return {'role':'assistant','content':json.dumps({
                    'headline':'Your resting heart rate was higher than in your recent records. You marked Rough in your check-ins.',
                    'fact_ids':[finding['fact_id'], run_report['fact_id'], report['fact_id']], 'question_ids':[]})}

        provider = RejectingCapture()
        result = run(AgentRole.PATIENT_INSIGHT, None, tools, provider, presentation=True)
        self.assertFalse(result['generation_used'])
        self.assertTrue(any(row.get('code') == 'VERIFIER_REJECTED' for row in result['trace']))
        self.assertIsNotNone(provider.verifier_messages)
        data = json.loads(provider.verifier_messages[1]['content'])
        self.assertEqual(len(data), 1)
        for fact in data[0]['facts']:
            original = tools.delivered[fact['fact_id']]
            self.assertEqual(fact['finding'], original['finding'])
            self.assertEqual(fact['comparison'], original.get('comparison'))
            self.assertEqual(fact['patient'], original['patient'])
            for key in ('checkin_run','checkin_summary'):
                if original.get(key):
                    self.assertEqual(fact[key], {name:value for name,value in original[key].items() if name != 'source_refs'})
        serialized = json.dumps(data)
        self.assertNotIn('source_ref', serialized)
        self.assertNotIn('demo-B', serialized)
        self.assertNotIn('measure-12', serialized)
        self.assertIn('Reject unsupported direction, comparator', provider.verifier_messages[0]['content'])
        self.assertIn('never infer current feelings', provider.verifier_messages[0]['content'])

    def test_malformed_empty_and_wrong_shapes_still_fall_back_without_repair_or_retry(self):
        class InvalidFinal(HeadlineProvider):
            def __init__(self, content):
                super().__init__()
                self.content = content
                self.final_calls = 0

            def step(self, messages, specs):
                if not any(row['role'] == 'tool' for row in messages):
                    return super().step(messages, specs)
                self.final_calls += 1
                return {'role':'assistant','content':self.content}

        for content, code in [('', 'MALFORMED_JSON'), ('```json\n{}\n```', 'MALFORMED_JSON'),
                              ('{"headline":', 'MALFORMED_JSON'),
                              ('{"headline":"Your heart rate changed","fact_ids":"f1","question_ids":[]}', 'HEADLINE_SCHEMA')]:
            with self.subTest(content=content):
                provider = InvalidFinal(content)
                result = run(AgentRole.PATIENT_INSIGHT, None,
                    RecordTools(evidence(), AgentRole.PATIENT_INSIGHT), provider, presentation=True)
                self.assertFalse(result['generation_used'])
                self.assertEqual(provider.final_calls, 1)
                self.assertTrue(any(row.get('code') == code for row in result['trace']))
                self.assertFalse(any(row.get('action') == 'INDEPENDENT_VERIFIER' for row in result['trace']))


if __name__ == '__main__':
    unittest.main()
