"""Synthetic A–E behavior and L14 deterministic replay."""

import json
import unittest

from aura_longitudinal.evaluation import AURA, METHODS
from aura_longitudinal.simulator import replay, run_cases


def day(record, case, index):
    return next(item for item in record["results"][case]["trace"]
                if item["index"] == index)


class LongitudinalPartTwo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record = run_cases(("A", "B", "C", "D", "E"), 7)

    def test_l14_same_seed_config_timeline_and_events_replay_exactly(self):
        repeated = run_cases(("A", "B", "C", "D", "E"), 7)
        self.assertEqual(repeated, self.record)
        serialized = json.loads(json.dumps(self.record))
        self.assertEqual(replay(serialized), serialized)
        changed = run_cases(("A",), 8)
        self.assertNotEqual(changed["timelines"]["A"], self.record["timelines"]["A"])
        tampered = json.loads(json.dumps(self.record))
        tampered["results"]["A"]["metrics"][AURA]["patient_interruptions"] += 1
        with self.assertRaises(AssertionError):
            replay(tampered)

    def test_case_a_illness_changes_detected_and_scoped(self):
        observed = day(self.record, "A", 30)
        for signal in ("RESTING_HEART_RATE", "SLEEP_DURATION", "ACTIVITY:steps"):
            self.assertNotEqual(observed["signals"][signal]["kind"], "STABLE")
            self.assertTrue(observed["signals"][signal]["attenuated"])
        self.assertEqual(observed["checkin"], "Good")
        self.assertEqual(self.record["results"]["A"]["metrics"][AURA]["unnecessary_notifications"], 0)
        self.assertTrue(all("depression" not in signal["description"].lower()
                            and "relapse" not in signal["description"].lower()
                            for row in self.record["results"]["A"]["trace"]
                            for signal in row["signals"].values()))

    def test_case_b_rolling_follows_but_anchor_exposes_slow_drift(self):
        observed = day(self.record, "B", 45)
        activity = observed["signals"]["ACTIVITY:steps"]
        self.assertEqual(activity["kind"], "ROLLING_ANCHOR_DIVERGENCE")
        self.assertGreater(abs(activity["rolling_vs_anchor"]),
                           abs(activity["current_vs_rolling"]))
        self.assertEqual(day(self.record, "B", 50)["checkin"], "Rough")
        self.assertEqual(self.record["results"]["B"]["metrics"][AURA]["missed_persistent_drift"], 0)

    def test_case_c_illness_does_not_clear_independent_evidence(self):
        observed = day(self.record, "C", 40)
        self.assertTrue(observed["signals"]["RESTING_HEART_RATE"]["attenuated"])
        self.assertFalse(observed["signals"]["SLEEP_MIDPOINT"]["attenuated"])
        self.assertIn(observed["signals"]["SLEEP_MIDPOINT"]["kind"],
                      {"PERSISTENT_DRIFT", "ROLLING_ANCHOR_DIVERGENCE"})
        self.assertEqual(observed["checkin"], "Rough")
        self.assertTrue(observed["decisions"][AURA]["interrupt"])

    def test_case_d_explanation_holds_drift_and_anchor(self):
        result = self.record["results"]["D"]
        observed = day(self.record, "D", 35)
        self.assertEqual(observed["held_statuses"]["SLEEP_MIDPOINT"],
                         "EXPLAINED_HELD_FOR_REVIEW")
        self.assertEqual(result["metrics"][AURA]["duplicate_notifications_for_explained_drift"], 0)
        self.assertGreater(result["metrics"][AURA]["clinician_review_items"], 0)
        for key, center in result["reference_centers"].items():
            self.assertEqual(center, observed["signals"][key]["anchor_center"])

    def test_case_e_missingness_and_reestablishing(self):
        gap = day(self.record, "E", 45)
        returned = day(self.record, "E", 55)
        later = day(self.record, "E", 65)
        for signal in gap["signals"].values():
            self.assertEqual(signal["sensing_state"], "UNOBSERVED")
            self.assertEqual(signal["kind"], "INSUFFICIENT_DATA")
        for signal in returned["signals"].values():
            self.assertEqual(signal["sensing_state"], "OBSERVED")
            self.assertEqual(signal["baseline_trust_state"], "REESTABLISHING")
        self.assertTrue(all(signal["kind"] == "INSUFFICIENT_DATA"
                            for signal in later["signals"].values()))
        self.assertEqual(self.record["results"]["E"]["metrics"][AURA]["patient_interruptions"], 0)

    def test_metrics_are_present_for_every_comparator(self):
        required = {"patient_interruptions", "unnecessary_notifications",
                    "persistent_drift_detection_latency_days", "missed_persistent_drift",
                    "duplicate_notifications_for_explained_drift", "data_coverage",
                    "stay_quiet_proportion", "clinician_review_items"}
        for case in "ABCDE":
            for method in METHODS:
                self.assertEqual(set(self.record["results"][case]["metrics"][method]), required)
                self.assertGreaterEqual(self.record["results"][case]["metrics"][method]["data_coverage"], 0)


if __name__ == "__main__":
    unittest.main()
