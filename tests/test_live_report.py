"""Evaluation summary mathematics, without live calls or clinical claims."""
import importlib.util
from pathlib import Path
import unittest
import httpx


spec = importlib.util.spec_from_file_location('assessment_measurement',
    Path(__file__).parent / 'live' / 'assessment_pass.py')
measurement = importlib.util.module_from_spec(spec)
spec.loader.exec_module(measurement)


class LiveReportTests(unittest.TestCase):
    def test_budget_counts_calls_not_http_requests(self):
        budget = measurement.CallBudget()
        budget.start(0)
        budget.record(5, 3)
        self.assertEqual(budget.wait_seconds(35, 9), 30)
        self.assertEqual(budget.wait_seconds(65, 9), 0)
        budget.record(65, 52)
        self.assertEqual(budget.wait_seconds(125, 9), 3540)
        self.assertEqual(budget.wait_seconds(3605, 9), 60)
        self.assertEqual(budget.wait_seconds(3665, 9), 0)

    def test_initial_known_calls_expire_conservatively_and_invalid_reservation_fails(self):
        budget = measurement.CallBudget(initial_calls=60, now=100)
        self.assertEqual(budget.wait_seconds(100, 9), 3600)
        self.assertEqual(budget.wait_seconds(3700, 9), 0)
        with self.assertRaises(ValueError):
            budget.wait_seconds(100, 11)

    def test_success_and_failed_trace_attempts_are_counted_once(self):
        trace = [{'action': 'MODEL_STEP'}, {'action': 'MODEL_STEP'},
                 {'action': 'INDEPENDENT_VERIFIER'}]
        self.assertEqual(measurement.trace_usage(trace), (3, None))
        trace.append({'action': 'FALLBACK', 'stage': 'INDEPENDENT_VERIFIER'})
        self.assertEqual(measurement.trace_usage(trace), (3, None))
        self.assertEqual(measurement.trace_usage([
            {'action': 'MODEL_STEP'}, {'action': 'FALLBACK', 'stage': 'MODEL_STEP',
             'provider_failure': 'http_400'}]), (2, 'http_400'))
        self.assertEqual(measurement.trace_usage([
            {'action': 'MODEL_STEP'}, {'action': 'FALLBACK', 'stage': 'INDEPENDENT_VERIFIER',
             'provider_failure': 'request_error'}]), (2, 'request_error'))

    def test_provider_failure_cannot_save_arbitrary_prose(self):
        self.assertEqual(measurement.trace_usage([{'action': 'FALLBACK',
            'stage': 'MODEL_STEP', 'provider_failure': 'Bearer secret patient prose'}]), (1, 'unknown'))

    def test_fixture_rebootstrap_recreates_flu_without_model_planning(self):
        calls = []
        with httpx.Client() as client:
            def request(method, path, **kwargs):
                calls.append((method, path, kwargs))
                if path == '/demo/scenarios':
                    client.cookies.set('aura_demo', 'test-fixture-cookie')
                    return {'scenarios': [{'id': 'B', 'patient_id': 'fixture-B'}]}
                return {'status': 'EXPLICIT_STRUCTURED_PLAN'}
            fixture = measurement.DemoFixture(client, request)
            self.assertEqual(fixture.ensure('B'), '/patients/fixture-B')
            fixture.ensure('B_PLUS_FLU_3_DAYS')
            fixture.ensure('B_PLUS_FLU_3_DAYS')
            self.assertEqual(len(calls), 2)
            client.cookies.clear()
            fixture.ensure('B_PLUS_FLU_3_DAYS')
            self.assertEqual(fixture.bootstraps, 2)
            self.assertEqual(len(calls), 4)
            self.assertEqual(calls[-1][2]['json']['data'], measurement.flu_data())
            self.assertFalse(measurement.flu_data()['notes'])
            self.assertEqual(measurement.flu_data()['seed'], 42)

    def test_small_smoke_sample_cannot_pass_twenty_run_gate(self):
        row = {'scenario': 'B', 'role': 'patient_insight', 'validated_headline': True,
               'preview_ms': 10, 'total_ms': 100}
        result = measurement.summarize([row])[0]
        self.assertEqual(result['sample_gate'], 'INCOMPLETE')
        self.assertIn('HTTP', result['timing_scope'])

    def test_gate_and_nearest_rank_p95_are_per_role_and_scenario(self):
        rows = [{'scenario': 'B', 'role': 'clinician_brief',
                 'validated_headline': i < 18, 'preview_ms': i + 1,
                 'total_ms': (i + 1) * 100} for i in range(20)]
        result = measurement.summarize(rows)[0]
        self.assertEqual(result['sample_gate'], 'PASS')
        self.assertEqual(result['preview_http_p95_ms'], 19)
        self.assertEqual(result['swap_http_p95_ms'], 1900)
        rows[17]['validated_headline'] = False
        self.assertEqual(measurement.summarize(rows)[0]['sample_gate'], 'FAIL')
        self.assertEqual(measurement.summarize([]), [])
