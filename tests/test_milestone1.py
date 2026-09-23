"""Exhaustive finite state-shape checks for the first safety-engine gate."""

from dataclasses import replace
from datetime import datetime, timezone
from itertools import product
import unittest

from aura_safety.config import load_config
from aura_safety.domain import (
    DropoutReason, Event, EventKind, FlagName, Mode, Outcome, PolicyFlag,
    SafetyState, Status, state_valid,
)
from aura_safety.engine import NAMED_DEESCALATIONS, SafetyEngine, SafetyStore, TRANSITION_TABLE


NOW = datetime(2026, 9, 23, tzinfo=timezone.utc)


def states():
    """Enumerate every Section 9 mode/status/peak/reason/degraded shape."""
    for status, mode, peak, reason, degraded in product(
        Status, Mode, Mode, (None, *DropoutReason), (False, True)
    ):
        for with_flag in (False, True):
            flags = ((PolicyFlag(FlagName.RECHECK_PASSED, "ep-1", NOW),)
                     if with_flag else ())
            candidate = SafetyState(
                interaction_mode=mode, episode_status=status,
                episode_peak_tier=peak, dropout_reason=reason,
                episode_id=None if status == Status.NONE else "ep-1",
                degraded=degraded,
                degraded_causes=frozenset({"DETECTOR_TIMEOUT"}) if degraded else frozenset(),
                sequence=17, flags=flags,
            )
            if state_valid(candidate):
                yield candidate


def event_for(kind):
    return Event(kind=kind, occurred_at=NOW, based_on_sequence=17,
                 proposed_tier=Mode.IMMEDIATE if kind in (EventKind.DETECTORS_COMPLETE, EventKind.LATE_DETECTOR_RESULT) else Mode.NORMAL,
                 episode_id="ep-2", source_episode_id="archived-ep")


class MilestoneOneProperties(unittest.TestCase):
    def setUp(self):
        self.engine = SafetyEngine()

    def test_p1_state_space_validity(self):
        valid = list(states())
        self.assertGreater(len(valid), 0)
        for state in valid:
            self.assertTrue(state_valid(state))
        invalid = [
            SafetyState(interaction_mode=Mode.CLARIFY),
            SafetyState(interaction_mode=Mode.NORMAL, episode_status=Status.OPEN,
                        episode_peak_tier=Mode.CLARIFY, episode_id="ep"),
            SafetyState(interaction_mode=Mode.URGENT, episode_status=Status.OPEN,
                        episode_peak_tier=Mode.ELEVATED, episode_id="ep"),
            SafetyState(interaction_mode=Mode.URGENT, episode_status=Status.DROPOUT,
                        episode_peak_tier=Mode.URGENT, episode_id="ep"),
            SafetyState(interaction_mode=Mode.ELEVATED, episode_status=Status.CLOSED,
                        episode_peak_tier=Mode.ELEVATED, episode_id="ep"),
        ]
        for state in invalid:
            self.assertFalse(state_valid(state))
            self.assertEqual(self.engine.apply(state, event_for(EventKind.CHECKIN_TAP_RECEIVED)).outcome,
                             Outcome.SET_DEGRADED)

    def test_p2_transition_completeness(self):
        # Every valid tuple and every accepted event resolves to one class.
        examined = 0
        for state in states():
            for kind in EventKind:
                self.assertIn((state.episode_status, state.interaction_mode, kind), TRANSITION_TABLE)
                result = self.engine.apply(state, event_for(kind))
                self.assertIsInstance(result.outcome, Outcome)
                self.assertTrue(state_valid(result.state), (state, kind, result))
                examined += 1
        self.assertGreater(examined, 1000)

    def test_p3_tier_monotonicity(self):
        config = replace(load_config(), urgent_deescalation_target=Mode.ELEVATED,
                         immediate_deescalation_target=Mode.URGENT)
        engine = SafetyEngine(config)
        decreases = 0
        for state in states():
            for kind in EventKind:
                result = engine.apply(state, event_for(kind))
                if result.state.interaction_mode < state.interaction_mode:
                    decreases += 1
                    self.assertIn(kind, NAMED_DEESCALATIONS)
                    self.assertEqual(event_for(kind).based_on_sequence, state.sequence)
                    self.assertEqual(result.outcome, Outcome.TRANSITION)
        self.assertGreater(decreases, 0)

    def test_cas_rejects_stale_downgrade(self):
        state = SafetyState(Mode.CLARIFY, Status.OPEN, Mode.CLARIFY,
                            sequence=18, episode_id="ep-1")
        event = Event(EventKind.CLARIFICATION_CLEARED, NOW, based_on_sequence=17)
        self.assertEqual(self.engine.apply(state, event).outcome, Outcome.REJECT_EVENT)

    def test_closed_failure_sets_overlay_and_preserves_episode(self):
        store = SafetyStore()
        store._states["patient"] = SafetyState(Mode.NORMAL, Status.CLOSED, Mode.CLARIFY,
                                                 sequence=1, episode_id="ep-1")
        result = store.apply("patient", Event(EventKind.DETECTOR_TIMEOUT, NOW))
        self.assertEqual(result.outcome, Outcome.SET_DEGRADED)
        self.assertTrue(store.is_fail_closed("patient"))
        self.assertTrue(store.get("patient").degraded)
        self.assertEqual(store.get("patient").episode_id, "ep-1")
        self.assertEqual(store.get("patient").episode_status, Status.CLOSED)
        self.assertEqual(store.apply("patient", Event(EventKind.FREE_TEXT_RECEIVED, NOW)).outcome,
                         Outcome.DEFER_EVENT)

    def test_closed_new_evidence_creates_linked_episode(self):
        closed = SafetyState(Mode.NORMAL, Status.CLOSED, Mode.URGENT,
                             sequence=17, episode_id="old")
        event = Event(EventKind.DETECTORS_COMPLETE, NOW, proposed_tier=Mode.CLARIFY,
                      episode_id="new")
        result = self.engine.apply(closed, event)
        self.assertEqual(result.outcome, Outcome.TRANSITION)
        self.assertEqual(result.archived_episode, closed)
        self.assertEqual(result.previous_episode_id, "old")
        self.assertEqual(result.state.episode_id, "new")
        self.assertEqual(result.state.episode_peak_tier, Mode.CLARIFY)
        self.assertEqual(result.state.episode_status, Status.OPEN)
        self.assertEqual(self.engine.apply(closed, Event(EventKind.DETECTORS_COMPLETE, NOW)).outcome,
                         Outcome.NO_STATE_CHANGE)

    def test_closed_recovery_evaluates_held_input_into_new_episode(self):
        closed = SafetyState(Mode.NORMAL, Status.CLOSED, Mode.IMMEDIATE,
                             sequence=4, episode_id="old")
        failed = self.engine.apply(closed, Event(EventKind.DETECTOR_TIMEOUT, NOW)).state
        self.assertTrue(failed.degraded)
        recovered_clear = self.engine.apply(failed, Event(EventKind.DETECTORS_COMPLETE, NOW))
        self.assertEqual(recovered_clear.state.episode_status, Status.CLOSED)
        self.assertEqual(recovered_clear.state.episode_id, "old")
        self.assertFalse(recovered_clear.state.degraded)
        new = self.engine.apply(failed, Event(EventKind.DETECTORS_COMPLETE, NOW,
                                              proposed_tier=Mode.ELEVATED, episode_id="new"))
        self.assertEqual(new.archived_episode, failed)
        self.assertEqual(new.state.episode_id, "new")
        self.assertEqual(new.state.episode_peak_tier, Mode.ELEVATED)
        self.assertFalse(new.state.degraded)

        store = SafetyStore()
        store.initialize("patient", closed)
        store.apply("patient", Event(EventKind.DETECTOR_TIMEOUT, NOW))
        store.apply("patient", Event(EventKind.DETECTORS_COMPLETE, NOW,
                                      proposed_tier=Mode.ELEVATED, episode_id="new"))
        self.assertEqual(store.archived_episodes[("patient", "old")], closed)
        self.assertEqual(store.closed_snapshots[("patient", "old")], closed)

    def test_configured_high_tier_deescalations(self):
        for mode, kind in ((Mode.URGENT, EventKind.URGENT_DEESCALATION_APPROVED),
                           (Mode.IMMEDIATE, EventKind.IMMEDIATE_DEESCALATION_APPROVED)):
            state = SafetyState(mode, Status.OPEN, mode, sequence=17, episode_id="ep")
            result = self.engine.apply(state, event_for(kind))
            self.assertEqual(result.outcome, Outcome.TRANSITION)
            self.assertEqual(result.state.interaction_mode, Mode.ELEVATED)
            self.assertEqual(result.state.episode_status, Status.RECHECK_REQUIRED)
            self.assertEqual(result.state.episode_peak_tier, mode)

    def test_recontact_limit_is_state_visible(self):
        state = SafetyState(Mode.ELEVATED, Status.OPEN, Mode.ELEVATED,
                            episode_id="ep-1")
        event = Event(EventKind.RECONTACT_DUE, NOW)
        first = self.engine.apply(state, event)
        self.assertEqual(first.outcome, Outcome.TRANSITION)
        self.assertEqual(first.action, "SEND_BOUNDED_RECONTACT")
        self.assertTrue(any(f.name == FlagName.RECONTACT_COUNT for f in first.state.flags))
        second = self.engine.apply(first.state, event)
        self.assertEqual(second.outcome, Outcome.NO_STATE_CHANGE)
        self.assertEqual(second.action, "RECONTACT_LIMIT_REACHED")


if __name__ == "__main__":
    unittest.main()
