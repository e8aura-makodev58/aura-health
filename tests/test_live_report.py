"""Evaluation summary mathematics, without live calls or clinical claims."""
import importlib.util
from pathlib import Path
import unittest


spec = importlib.util.spec_from_file_location('assessment_measurement',
    Path(__file__).parent / 'live' / 'assessment_pass.py')
measurement = importlib.util.module_from_spec(spec)
spec.loader.exec_module(measurement)


class LiveReportTests(unittest.TestCase):
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
