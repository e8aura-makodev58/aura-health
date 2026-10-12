"""Patient fallback ordering and gap wording. Deterministic, no model."""
from copy import deepcopy
import unittest

from aura_agent.roles import AgentRole
from aura_agent.templates import fallback
from aura_agent.tools import RecordTools
from tests.test_final_dash import evidence


def with_older_sleep_drift(source):
    source = deepcopy(source)
    source['signals'].insert(0, {
        'key': {'signal': 'SLEEP_MIDPOINT', 'source': 'synthetic_watch', 'metric': ''}, 'label': 'Sleep timing',
        'unit': 'minutes', 'registry': {'enabled_in_engine': True, 'display': True},
        'current': {'sensing_state': 'OBSERVED', 'trust_state': 'TRUSTED'}, 'gaps': [], 'contexts': [],
        'observations': [{'event_id': f'sleep-{d}', 'day': f'2026-03-{d:02}', 'value': 1700 + d, 'coverage': 1,
                          'data_quality': 1, 'deferred': False} for d in (10, 11, 12)],
        'findings': [{'event_id': 'sleep-12', 'first_seen': '2026-02-20', 'last_seen': '2026-03-12',
                      'drift': {'kind': 'PERSISTENT_DRIFT', 'current_vs_rolling': 5, 'rolling_vs_anchor': 190,
                                'description': 'Sleep midpoint is later relative to the anchored reference.'}}]})
    return source


def patient_tools(source):
    tools = RecordTools(source, AgentRole.PATIENT_INSIGHT)
    for name in tools.groups:
        tools.call(name, {})
    return tools


class PatientFallbackTests(unittest.TestCase):
    def test_pf1_recent_change_leads_older_drift(self):
        draft = fallback(patient_tools(with_older_sleep_drift(evidence())), AgentRole.PATIENT_INSIGHT)
        first = draft['claims'][0]
        self.assertEqual(first['findings'][0]['signal'], 'RESTING_HEART_RATE')
        self.assertTrue(draft['headline'].startswith('Your resting heart rate'))

    def test_pf2_gap_is_mentioned_when_there_is_room(self):
        source = evidence()
        source['signals'][0]['findings'] = []
        source['signals'][0]['gaps'] = [{'event_id': 'gap-1', 'type': 'SENSING_GAP', 'at': '2026-03-11'}]
        draft = fallback(patient_tools(source), AgentRole.PATIENT_INSIGHT)
        texts = ' '.join(claim['text'] for claim in draft['claims'])
        self.assertIn('gap', texts.lower())
        self.assertLessEqual(len(draft['headline'].split()), 35)


if __name__ == "__main__":
    unittest.main()
