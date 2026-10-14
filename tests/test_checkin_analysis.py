"""Derived Q&A facts: deterministic arithmetic, coverage, grounding and tool loop."""
from datetime import datetime, timedelta, timezone
import json
import unittest

from aura_agent.roles import AgentRole
from aura_agent.tools import RecordTools
from aura_agent.grounding import validate
from aura_agent.runtime import run, AgentConfig


def evidence():
    end = datetime(2026, 3, 11, 12, tzinfo=timezone.utc)
    return {'patient': {'timezone': 'Asia/Singapore'}, 'period': {'start': '2026-02-10T12:00:00+00:00', 'end': end.isoformat()},
            'signals': [], 'current_decision': 'STAY_QUIET', 'held': [], 'medication': [],
            'checkins': [{'event_id': f'private-scenario-{i}', 'at': (end-timedelta(days=29-i)).isoformat(),
                          'state': 'Rough' if i >= 10 else 'Okay', 'deferred': False} for i in range(30)]}


ARGS = {'start': None, 'end': None, 'last_days': 30, 'state': 'Rough', 'denominator': 'recorded_days'}


def draft(fact, text=None):
    return {'headline': '', 'question_ids': [], 'claims': [{'text': text or fact['text'],
            'fact_ids': [fact['fact_id']], 'findings': [], 'section': 'routine'}]}


class CheckinAnalysisTests(unittest.TestCase):
    def calculate(self, ev=None, **args):
        tools = RecordTools(ev or evidence(), AgentRole.RECORD_QA)
        result = tools.call('summarize_checkins', {**ARGS, **args})
        return tools, result['facts'][0]

    def test_twenty_of_thirty_and_source_aliases(self):
        tools, fact = self.calculate()
        self.assertEqual(fact['analysis']['percentage'], '66.7')
        self.assertEqual(fact['analysis']['start'], '2026-02-10')
        self.assertEqual(fact['analysis']['missing_days'], 0)
        self.assertTrue(all(ref.startswith('ref:') for ref in fact['source_refs']))
        self.assertEqual(len(tools.delivered[fact['fact_id']]['source_refs']), 30)
        self.assertEqual(validate(draft(fact), tools, AgentRole.RECORD_QA)['claims'][0]['text'], fact['text'])

    def test_missing_days_denominators_and_held(self):
        ev = evidence(); ev['checkins'] = ev['checkins'][5:]
        _, fact = self.calculate(ev)
        self.assertEqual(fact['analysis']['percentage'], '80.0')
        self.assertEqual(fact['analysis']['missing_days'], 5)
        _, calendar = self.calculate(ev, denominator='calendar_days')
        self.assertEqual(calendar['analysis']['percentage'], '66.7')
        ev['checkins'][-1]['deferred'] = True
        _, held = self.calculate(ev)
        self.assertEqual(held['analysis']['numerator'], 19)
        self.assertEqual(held['analysis']['recorded_days'], 24)

    def test_no_records_is_unavailable_and_zero_is_distinct(self):
        ev = evidence(); ev['checkins'] = []
        tools, empty = self.calculate(ev)
        self.assertIsNone(empty['analysis']['percentage'])
        self.assertEqual(empty['analysis']['missing_days'], 30)
        validate(draft(empty), tools, AgentRole.RECORD_QA)
        _, zero = self.calculate(state='Good')
        self.assertEqual(zero['analysis']['percentage'], '0.0')

    def test_latest_report_per_local_day_and_timestamp_tie(self):
        ev = evidence()
        ev['checkins'] += [{'event_id': 'later', 'at': '2026-03-11T15:00:00+00:00', 'state': 'Good', 'deferred': False},
                           {'event_id': 'tie', 'at': '2026-03-11T15:00:00+00:00', 'state': 'Okay', 'deferred': False}]
        _, fact = self.calculate(ev)
        self.assertEqual(fact['analysis']['numerator'], 19)
        self.assertEqual(fact['analysis']['recorded_days'], 30)
        ev['period']['end'] = '2026-03-11T18:00:00+00:00'  # March 12 locally
        _, fact = self.calculate(ev, last_days=1)
        self.assertEqual(fact['analysis']['end'], '2026-03-12')
        self.assertEqual(fact['analysis']['recorded_days'], 0)

    def test_explicit_periods_and_invalid_arguments(self):
        _, prior = self.calculate(start='2026-02-10', end='2026-02-19', last_days=None)
        self.assertEqual(prior['analysis']['percentage'], '0.0')
        for args in ({'last_days': True}, {'last_days': 57}, {'state': 'Depressed'},
                     {'start': '2026-02-10'}, {'denominator': 'healthy_days'},
                     {'start': '2026-03-12', 'end': '2026-03-13', 'last_days': None}):
            with self.subTest(args=args), self.assertRaises(ValueError):
                self.calculate(**args)

    def test_percentage_permission_is_scoped_and_denominator_cannot_disappear(self):
        tools, fact = self.calculate()
        for text in ('66.7% risk.', '66.7% of days were Rough.', fact['text'].replace('66.7', '66.8')):
            with self.subTest(text=text), self.assertRaises(ValueError):
                validate(draft(fact, text), tools, AgentRole.RECORD_QA)
        with self.assertRaises(ValueError):
            validate(draft(fact), tools, AgentRole.PATIENT_INSIGHT)
        patient = RecordTools(evidence(), AgentRole.PATIENT_INSIGHT)
        with self.assertRaises(ValueError):
            patient.call('summarize_checkins', ARGS)

    def test_replay_is_identical(self):
        self.assertEqual(self.calculate()[1], self.calculate()[1])

    def test_failed_provider_keeps_existing_extraction_fallback(self):
        tools = RecordTools(evidence(), AgentRole.RECORD_QA)
        empty = tools.call('summarize_checkins', {})
        self.assertEqual(empty['error'], 'WINDOW_REQUIRED')
        self.assertEqual(empty['facts'], [])
        class Down:
            live = True
            model_id = 'mock-down'
            def step(self, *args):
                raise TimeoutError()
        result = run(AgentRole.RECORD_QA, 'Rough check-ins?', RecordTools(evidence(), AgentRole.RECORD_QA), Down())
        self.assertFalse(result['generation_used'])
        self.assertEqual(result['reason'], 'MODEL_TIMEOUT')

    def test_unanswered_calculation_gets_one_bounded_repair(self):
        class Incomplete:
            live = True
            model_id = 'mock-incomplete'
            calls = 0
            def step(self, messages, specs):
                self.calls += 1
                if self.calls == 1:
                    return {'tool_calls': [{'id': 'c1', 'type': 'function', 'function': {'name': 'summarize_checkins', 'arguments': json.dumps(ARGS)}}]}
                result = next(json.loads(m['content']) for m in messages if m['role'] == 'tool')
                return {'content': json.dumps(draft(result['facts'][0], '20 days were recorded as Rough.'))}
        provider = Incomplete()
        result = run(AgentRole.RECORD_QA, 'Rough percentage?', RecordTools(evidence(), AgentRole.RECORD_QA), provider)
        self.assertFalse(result['generation_used'])
        self.assertEqual(provider.calls, 3)
        self.assertTrue(any(row.get('code') == 'CALCULATION_ANSWER_INCOMPLETE' for row in result['trace']))

    def test_tool_loop_answers_calculation_and_verifier_sees_method(self):
        class Provider:
            live = True
            model_id = 'mock-calculation'
            def step(self, messages, specs):
                if not specs:
                    checks = json.loads(messages[1]['content'])
                    self.checked = checks
                    return {'content': json.dumps({'verdicts': [{'index': i, 'supported': True} for i in range(len(checks))]})}
                results = [json.loads(m['content']) for m in messages if m['role'] == 'tool']
                if not results:
                    return {'tool_calls': [{'id': 'c1', 'type': 'function', 'function': {'name': 'summarize_checkins', 'arguments': json.dumps(ARGS)}}]}
                return {'content': json.dumps(draft(results[0]['facts'][0]))}
        provider = Provider()
        result = run(AgentRole.RECORD_QA, 'What percentage of the past 30 days was Rough?',
                     RecordTools(evidence(), AgentRole.RECORD_QA), provider, AgentConfig())
        self.assertIn('66.7%', str(result))
        self.assertTrue(result['generation_used'])
        self.assertEqual(provider.checked[0]['facts'][0]['analysis']['denominator'], 30)


if __name__ == '__main__':
    unittest.main()
