"""L1–L13: descriptive longitudinal behavior and safety delegation."""

from datetime import date, datetime, timedelta, timezone
import unittest

from aura_longitudinal.baseline import AnchorAction, AnchorCommand, BaselineManager
from aura_longitudinal.communication import CommunicationEngine, CommunicationOutcome
from aura_longitudinal.context import (
    EvidenceEvent, EvidenceKind, HeldDriftRegistry, HeldStatus, apply_context,
)
from aura_longitudinal.domain import (
    ActivityObservation, BaselineTrustState, CheckinState, ContextCategory,
    ContextEvent, MedicationEvent, MedicationStatus, ObservationPoint,
    PatientCheckin, RestingHeartRateObservation, SensingState, Signal,
    SignalKey, SleepObservation,
)
from aura_longitudinal.drift import DriftAssessment, DriftKind, TrendDirection, assess_drift
from aura_safety import Event, EventKind, Mode, SafetyStore


NOW = datetime(2026, 9, 23, tzinfo=timezone.utc)
DAY = NOW.date()
SLEEP = SignalKey(Signal.SLEEP_MIDPOINT, "wearable")
HR = SignalKey(Signal.RESTING_HEART_RATE, "wearable")


def point(key, offset, value, coverage=1.0):
    return ObservationPoint(key, DAY + timedelta(days=offset), value, coverage, coverage)


def seeded_manager(key=SLEEP, center=1500.0):
    manager = BaselineManager()
    reference = tuple(point(key, offset, center + (offset % 3 - 1) * 2)
                      for offset in range(14))
    for observation in reference:
        manager.ingest(observation)
    anchor = manager.apply_anchor_command(AnchorCommand(
        AnchorAction.CREATE_PROVISIONAL_ANCHOR, key, NOW, reference))
    return manager, anchor


def persistent_drift(key=SLEEP):
    return DriftAssessment(key, DriftKind.PERSISTENT_DRIFT, 10.0, 180.0,
                           TrendDirection.INCREASING, 12.0, 1.0, 1.0,
                           "Observed pattern differs from anchored reference.")


class LongitudinalPartOne(unittest.TestCase):
    def test_l1_anchor_moves_only_on_named_event(self):
        manager, anchor = seeded_manager()
        manager.ingest(point(SLEEP, 20, 1800))
        manager.rolling(SLEEP, DAY + timedelta(days=20))
        self.assertEqual(manager.anchor(SLEEP), anchor)
        self.assertEqual(manager.apply_anchor_command(AnchorCommand(
            AnchorAction.TRUST_ANCHOR, SLEEP, NOW, reviewed_by="reviewer-fixture")), anchor)
        self.assertEqual(manager.anchor(SLEEP).center, anchor.center)
        with self.assertRaises(ValueError):
            manager.apply_anchor_command(AnchorCommand(
                AnchorAction.CREATE_PROVISIONAL_ANCHOR, SLEEP, NOW,
                tuple(point(SLEEP, n + 20, 1800) for n in range(14))))
        new = manager.apply_anchor_command(AnchorCommand(
            AnchorAction.CLINICAL_REVIEW_REANCHOR, SLEEP, NOW + timedelta(days=30),
            tuple(point(SLEEP, n + 20, 1800) for n in range(14)), "reviewer-fixture"))
        self.assertNotEqual(new.center, anchor.center)
        self.assertEqual(new.version, anchor.version + 1)

    def test_l2_rolling_updates_without_anchor_change(self):
        manager, anchor = seeded_manager()
        before = manager.rolling(SLEEP, DAY + timedelta(days=13))
        for offset in range(14, 28):
            manager.ingest(point(SLEEP, offset, 1800))
        after = manager.rolling(SLEEP, DAY + timedelta(days=27))
        self.assertNotEqual(before.median, after.median)
        self.assertEqual(manager.anchor(SLEEP), anchor)

    def test_l3_missingness_remains_unknown(self):
        manager = BaselineManager()
        empty = manager.rolling(SLEEP, DAY)
        self.assertFalse(empty.sufficient)
        self.assertIsNone(empty.mean)
        self.assertIsNone(empty.latest_value)
        self.assertEqual(manager.sensing_state(SLEEP, DAY), SensingState.UNOBSERVED)
        manager.ingest(point(SLEEP, 0, 1550, coverage=0.1))
        self.assertEqual(manager.sensing_state(SLEEP, DAY), SensingState.UNOBSERVED)
        self.assertIsNone(manager.rolling(SLEEP, DAY).mean)
        self.assertEqual(assess_drift(empty, None).kind, DriftKind.INSUFFICIENT_DATA)
        manager.ingest(point(SLEEP, 10, 1600))
        self.assertEqual(manager.sensing_state(SLEEP, DAY), SensingState.UNOBSERVED)
        manager.ingest(point(SLEEP, 10, 0, coverage=0.1))
        self.assertEqual(manager.rolling(SLEEP, DAY + timedelta(days=10)).points[0].value, 1600)

    def test_l4_sensing_and_trust_are_orthogonal(self):
        manager, _ = seeded_manager()
        self.assertEqual((manager.sensing_state(SLEEP, DAY + timedelta(days=13)),
                          manager.trust_state(SLEEP)),
                         (SensingState.OBSERVED, BaselineTrustState.PROVISIONAL))
        manager.apply_anchor_command(AnchorCommand(AnchorAction.TRUST_ANCHOR, SLEEP, NOW,
                                                    reviewed_by="reviewer-fixture"))
        self.assertEqual((manager.sensing_state(SLEEP, DAY + timedelta(days=13)),
                          manager.trust_state(SLEEP)),
                         (SensingState.OBSERVED, BaselineTrustState.TRUSTED))
        self.assertEqual((manager.sensing_state(SLEEP, DAY + timedelta(days=40)),
                          manager.trust_state(SLEEP)),
                         (SensingState.UNOBSERVED, BaselineTrustState.TRUSTED))

    def test_l5_slow_drift_detected_against_anchor(self):
        manager, _ = seeded_manager()
        for offset in range(14, 42):
            manager.ingest(point(SLEEP, offset, 1500 + 20 * (offset - 13)))
        rolling = manager.rolling(SLEEP, DAY + timedelta(days=41))
        drift = assess_drift(rolling, manager.anchor(SLEEP))
        self.assertEqual(drift.kind, DriftKind.ROLLING_ANCHOR_DIVERGENCE)
        self.assertGreater(drift.rolling_vs_anchor, 0)
        self.assertGreater(drift.trend_magnitude_per_day, 0)
        self.assertIn("anchored reference", drift.description)
        self.assertNotIn("depression", drift.description.lower())

    def test_l6_benign_context_is_signal_scoped(self):
        context = ContextEvent(NOW, None, ContextCategory.BENIGN_CONTEXT,
                               (Signal.RESTING_HEART_RATE,), "patient", "acute illness")
        self.assertTrue(apply_context(persistent_drift(HR), (context,), NOW).attenuated)
        self.assertFalse(apply_context(persistent_drift(SLEEP), (context,), NOW).attenuated)
        risk = ContextEvent(NOW, None, ContextCategory.RISK_CONTEXT,
                            (Signal.RESTING_HEART_RATE,), "patient", "work stress")
        self.assertFalse(apply_context(persistent_drift(HR), (risk,), NOW).attenuated)

    def test_l7_benign_context_cannot_clear_subjective_change(self):
        context = ContextEvent(NOW, None, ContextCategory.BENIGN_CONTEXT,
                               (Signal.RESTING_HEART_RATE,), "patient", "acute illness")
        hr = apply_context(persistent_drift(HR), (context,), NOW)
        earlier = PatientCheckin(NOW - timedelta(days=1), CheckinState.GOOD)
        current = PatientCheckin(NOW, CheckinState.ROUGH)
        decision = CommunicationEngine().decide((hr,), HeldDriftRegistry(), NOW,
                                                 previous_checkin=earlier, current_checkin=current)
        self.assertEqual(decision.outcome, CommunicationOutcome.TARGETED_CLARIFICATION)

    def test_l8_hold_does_not_move_anchor(self):
        manager, anchor = seeded_manager()
        held = HeldDriftRegistry().hold(persistent_drift(), "new work schedule", NOW)
        self.assertEqual(held.status, HeldStatus.EXPLAINED_HELD_FOR_REVIEW)
        self.assertEqual(manager.anchor(SLEEP), anchor)
        self.assertTrue(held.inspectable)
        self.assertTrue(held.clinician_review_item)

    def test_l9_held_drift_suppresses_duplicates(self):
        registry = HeldDriftRegistry()
        original = registry.hold(persistent_drift(), "new work schedule", NOW)
        repeated = registry.hold(persistent_drift(), "duplicate explanation", NOW + timedelta(days=1))
        self.assertIs(repeated, original)
        decision = CommunicationEngine().decide(
            (apply_context(persistent_drift(), (), NOW),), registry, NOW)
        self.assertEqual(decision.outcome, CommunicationOutcome.STAY_QUIET)
        self.assertIn(SLEEP, decision.inspectable_signals)
        self.assertIn(SLEEP, decision.clinician_review_signals)
        opposite = DriftAssessment(SLEEP, DriftKind.PERSISTENT_DRIFT, -10.0, -180.0,
                                   TrendDirection.DECREASING, 12.0, 1.0, 1.0,
                                   "Observed shift in the opposite direction.")
        new_direction = CommunicationEngine().decide(
            (apply_context(opposite, (), NOW),), registry, NOW)
        self.assertEqual(new_direction.outcome, CommunicationOutcome.MICRO_CHECKIN)

    def test_l10_relevant_evidence_reopens_hold(self):
        for kind in EvidenceKind:
            registry = HeldDriftRegistry()
            registry.hold(persistent_drift(), "new schedule", NOW)
            evidence = EvidenceEvent(kind, NOW + timedelta(days=1),
                                     signal=HR if kind == EvidenceKind.NEW_LONGITUDINAL_SIGNAL else None)
            reopened = registry.reopen(SLEEP, evidence)
            self.assertEqual(reopened.status, HeldStatus.REOPENED, kind)
            self.assertFalse(reopened.suppress_duplicate_notification)
        registry = HeldDriftRegistry()
        registry.hold(persistent_drift(), "new schedule", NOW)
        earlier = PatientCheckin(NOW - timedelta(days=1), CheckinState.GOOD)
        current = PatientCheckin(NOW, CheckinState.ROUGH)
        CommunicationEngine().decide((), registry, NOW, previous_checkin=earlier,
                                     current_checkin=current)
        self.assertEqual(registry.get(SLEEP).status, HeldStatus.REOPENED)
        for kwargs in (
            {"structured_assessment_changed": True},
            {"new_longitudinal_signal": HR},
            {"medication_event": MedicationEvent(NOW, NOW, MedicationStatus.MISSED, "patient")},
        ):
            registry = HeldDriftRegistry()
            registry.hold(persistent_drift(), "new schedule", NOW)
            CommunicationEngine().decide((), registry, NOW, **kwargs)
            self.assertEqual(registry.get(SLEEP).status, HeldStatus.REOPENED)

    def test_l11_return_after_gap_reestablishes(self):
        manager, anchor = seeded_manager()
        manager.apply_anchor_command(AnchorCommand(AnchorAction.TRUST_ANCHOR, SLEEP, NOW,
                                                    reviewed_by="reviewer-fixture"))
        manager.ingest(point(SLEEP, 40, 1600))
        self.assertEqual(manager.sensing_state(SLEEP, DAY + timedelta(days=40)),
                         SensingState.OBSERVED)
        self.assertEqual(manager.trust_state(SLEEP), BaselineTrustState.REESTABLISHING)
        self.assertEqual(manager.anchor(SLEEP), anchor)

    def test_l12_stable_state_stays_quiet(self):
        stable = DriftAssessment(SLEEP, DriftKind.STABLE, 0, 0, TrendDirection.FLAT,
                                 0, 1, 1, "No configured descriptive drift")
        decision = CommunicationEngine().decide((apply_context(stable, (), NOW),),
                                                 HeldDriftRegistry(), NOW)
        self.assertEqual(decision.outcome, CommunicationOutcome.STAY_QUIET)
        self.assertIn(SLEEP, decision.inspectable_signals)

    def test_l13_safety_is_delegated_to_aura_safety(self):
        store = SafetyStore()
        safety_event = Event(EventKind.DETECTORS_COMPLETE, NOW, proposed_tier=Mode.CLARIFY,
                             episode_id="safety-episode")
        decision = CommunicationEngine().decide((), HeldDriftRegistry(), NOW,
                                                 safety_event=safety_event,
                                                 safety_store=store, patient_id="p")
        self.assertEqual(decision.outcome, CommunicationOutcome.SAFETY_REVIEW_REQUIRED)
        self.assertEqual(decision.safety_result.state, store.get("p"))
        self.assertEqual(store.get("p").interaction_mode, Mode.CLARIFY)

    def test_domain_observation_adapters_preserve_real_zero_and_source(self):
        activity = ActivityObservation(DAY, (("steps", 0.0),), 1.0, "watch")
        self.assertEqual(activity.points()[0].value, 0.0)
        self.assertEqual(activity.points()[0].key.source, "watch")
        heart = RestingHeartRateObservation(DAY, 62, 1.0, "watch")
        self.assertEqual(heart.points()[0].value, 62)
        start = NOW.replace(hour=23)
        sleep = SleepObservation(DAY, start, start + timedelta(hours=8),
                                 timedelta(hours=8), 1.0, 1.0, "watch")
        self.assertEqual(len(sleep.points()), 2)
        self.assertGreater(sleep.points()[0].value, 1440)


if __name__ == "__main__":
    unittest.main()
