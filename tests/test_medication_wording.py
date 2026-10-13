"""Medication-instruction rule: record-name observations pass, instructions still fail."""
import unittest

from aura_communication.validation import prohibited_claims


class MedicationWordingTests(unittest.TestCase):
    def rejected(self, text):
        return "MEDICATION_INSTRUCTION" in prohibited_claims(text)

    def test_observations_naming_routine_records_pass(self):
        for text in (
            "Activity reduced during the period covered by the medication-routine records.",
            "Sleep time increased later; medication-routine records show two missed entries.",
            "Steps decreased and reduced further while the medication routine records were Acknowledged.",
        ):
            self.assertFalse(self.rejected(text), text)

    def test_instructions_and_mixed_sentences_still_fail(self):
        for text in (
            "Reduce your medication.",
            "Activity reduced, so reduce the antidepressant.",
            "Activity reduced during the medication-routine records; stop the medication.",
            "It may help to skip a tablet on rough days.",
            "Consider switching to another pill.",
            "Increase the medication routine.",
            "Taper the antidepressant slowly.",
            "Take 20 mg tonight.",
            "Reducing it could help: the medication-routine records show misses, so lower the medication.",
        ):
            self.assertTrue(self.rejected(text), text)


if __name__ == "__main__":
    unittest.main()
