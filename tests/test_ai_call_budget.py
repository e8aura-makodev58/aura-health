import os
import unittest
from unittest.mock import patch

from aura_app.hosted import ai_call_budget


class AiCallBudgetTests(unittest.TestCase):
    def test_unset_keeps_conservative_default(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("AURA_AI_CALLS_PER_MINUTE", None); os.environ.pop("AURA_AI_CALLS_PER_HOUR", None)
            self.assertEqual(ai_call_budget(), {"calls_per_minute": 10, "calls_per_hour": 60})

    def test_explicit_judging_allowance(self):
        with patch.dict(os.environ, {"AURA_AI_CALLS_PER_MINUTE": "30", "AURA_AI_CALLS_PER_HOUR": "300"}):
            self.assertEqual(ai_call_budget(), {"calls_per_minute": 30, "calls_per_hour": 300})

    def test_invalid_values_refuse_to_start(self):
        for minute, hour in (("0", "300"), ("500", "300"), ("40", "30"), ("x", "300")):
            with patch.dict(os.environ, {"AURA_AI_CALLS_PER_MINUTE": minute, "AURA_AI_CALLS_PER_HOUR": hour}):
                with self.assertRaises(ValueError):
                    ai_call_budget()


if __name__ == "__main__":
    unittest.main()
