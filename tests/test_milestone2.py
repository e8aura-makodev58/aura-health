"""P4–P18 structural properties, using resolved fixture signals only."""

from dataclasses import replace
from datetime import timedelta
from threading import Thread
import unittest

from aura_safety.codec import state_to_dict
from aura_safety.domain import (
    DetectorOutput, DropoutReason, Event, EventKind, FlagName, Mode,
    Outcome, SafetyState, Status, state_valid,
)
from aura_safety.engine import SafetyEngine, SafetyStore
from aura_safety.offline import HeldInput, InMemoryInputFixture, OfflineSafetyGate
from aura_safety.output import accept_generated, output_plan
from aura_safety.resources import ResourceRegistry, fixture_bundle
from aura_safety.simulator import replay, run_scenario
from test_milestone1 import NOW, event_for, states


def evt(kind, **fields):
    return Event(kind, NOW, **fields)


def active(mode, status=Status.OPEN, peak=None, sequence=1, reason=None, flags=()):
    return SafetyState(mode, status, peak or mode, flags=flags,
                       dropout_reason=reason, sequence=sequence, episode_id="ep")


class MilestoneTwoProperties(unittest.TestCase):
    def setUp(self):
        self.engine = SafetyEngine()

    def test_p4_peak_monotonicity_inside_episode(self):
        examined = 0
        for state in states():
            for kind in EventKind:
                result = self.engine.apply(state, event_for(kind))
                if result.state.episode_id == state.episode_id and state.episode_id is not None:
                    self.assertGreaterEqual(result.state.episode_peak_tier, state.episode_peak_tier)
                    examined += 1
        self.assertGreater(examined, 1000)

    def test_p5_replay_determinism(self):
        scenario = {
            "start_at": NOW.isoformat(), "resource_version": "fixture-unverified-v1",
            "steps": [
                {"kind": "DETECTORS_COMPLETE", "episode_id": "ep1", "proposed_tier": "URGENT",
                 "detector_outputs": [{"detector_id": "D1", "proposed_tier": "URGENT",
                                       "input_id": "i1", "source_episode_id": None, "source_sequence": 0}]},
                {"kind": "URGENT_DEESCALATION_APPROVED", "based_on_sequence": "current"},
                {"type": "advance", "seconds": 3600},
                {"kind": "RECHECK_PASSED"},
                {"kind": "EPISODE_CLOSE_APPROVED", "based_on_sequence": "current"},
                {"type": "offline_input", "input_id": "offline-1", "payload": "fixture"},
                {"type": "reconnect"},
                {"kind": "DETECTORS_COMPLETE", "episode_id": "ep2", "proposed_tier": "CLARIFY"},
                {"type": "race", "events": [
                    {"kind": "LATE_DETECTOR_RESULT", "source_episode_id": "ep1",
                     "proposed_tier": "IMMEDIATE"},
                    {"kind": "CLARIFICATION_CLEARED", "based_on_sequence": 1},
                ]},
            ],
        }
        record = run_scenario(scenario)
        self.assertEqual(replay(record)["trace"], record["trace"])
        self.assertEqual(record["final_state"]["interaction_mode"], "IMMEDIATE")

    def test_p6_stale_downgrade_rejected(self):
        cases = [
            (active(Mode.CLARIFY, sequence=8), EventKind.CLARIFICATION_CLEARED),
            (active(Mode.ELEVATED, sequence=8), EventKind.ELEVATION_RESOLVED),
            (active(Mode.URGENT, sequence=8), EventKind.URGENT_DEESCALATION_APPROVED),
            (active(Mode.IMMEDIATE, sequence=8), EventKind.IMMEDIATE_DEESCALATION_APPROVED),
            (active(Mode.URGENT, Status.DROPOUT, sequence=8,
                    reason=DropoutReason.DURING_URGENT), EventKind.DROPOUT_REENTRY),
            (active(Mode.ELEVATED, Status.RECHECK_REQUIRED, peak=Mode.URGENT,
                    sequence=8), EventKind.EPISODE_CLOSE_APPROVED),
        ]
        for state, kind in cases:
            result = self.engine.apply(state, evt(kind, based_on_sequence=7))
            self.assertEqual(result.outcome, Outcome.REJECT_EVENT, kind)
            self.assertEqual(result.state, state)

    def test_p7_upward_race_safety(self):
        store = SafetyStore()
        store.initialize("p", active(Mode.CLARIFY, sequence=10))
        results = []

        def run(event):
            results.append(store.apply("p", event))

        threads = [Thread(target=run, args=(evt(EventKind.CLARIFICATION_CLEARED,
                                                 based_on_sequence=10),)),
                   Thread(target=run, args=(evt(EventKind.DETECTORS_COMPLETE,
                                                 proposed_tier=Mode.URGENT,
                                                 episode_id="race-new"),))]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(store.get("p").interaction_mode, Mode.URGENT)
        self.assertTrue(all(state_valid(r.state) for r in results))
        self.assertEqual(sorted(a["sequence"] for a in store.audit),
                         list(range(11, 11 + len(store.audit))))

    def test_p8_fail_closed_preservation_and_clock(self):
        for status, mode, peak in ((Status.OPEN, Mode.URGENT, Mode.URGENT),
                                    (Status.CLOSED, Mode.NORMAL, Mode.IMMEDIATE)):
            state = active(mode, status, peak)
            failed = self.engine.apply(state, evt(EventKind.DETECTOR_TIMEOUT))
            self.assertEqual(failed.outcome, Outcome.SET_DEGRADED)
            self.assertEqual((failed.state.interaction_mode, failed.state.episode_status,
                              failed.state.episode_peak_tier), (mode, status, peak))
            self.assertTrue(failed.state.degraded)
        urgent = self.engine.apply(active(Mode.URGENT), evt(EventKind.DETECTOR_TIMEOUT)).state
        timeout = self.engine.apply(urgent, evt(EventKind.FOLLOWUP_WINDOW_EXPIRED))
        self.assertEqual(timeout.state.episode_status, Status.DROPOUT)
        policy_failed = self.engine.apply(active(Mode.URGENT), evt(EventKind.POLICY_ERROR)).state
        deferred = self.engine.apply(policy_failed, evt(EventKind.FOLLOWUP_WINDOW_EXPIRED))
        self.assertEqual(deferred.outcome, Outcome.DEFER_EVENT)
        self.assertEqual(deferred.state, policy_failed)

    def test_p9_resource_fallback_and_staleness(self):
        def unavailable():
            raise ConnectionError("fixture outage")
        registry = ResourceRegistry(unavailable)
        resolved = registry.resolve(NOW)
        self.assertEqual(resolved.source, "built_in")
        self.assertTrue(resolved.stale)
        self.assertTrue(resolved.bundle.resources)
        self.assertIsNotNone(resolved.notice)
        self.assertIsNone(resolved.bundle.resources[0].contact_method)
        engine_result = self.engine.apply(active(Mode.URGENT), evt(EventKind.LIVE_RESOURCES_UNAVAILABLE))
        self.assertEqual(engine_result.action, "USE_BUILT_IN_RESOURCES")
        self.assertFalse(engine_result.state.degraded)

    def test_d6_only_output_cannot_establish_high_tier(self):
        result = self.engine.apply(SafetyState(), evt(
            EventKind.DETECTORS_COMPLETE, episode_id="ep",
            proposed_tier=Mode.URGENT,
            detector_outputs=(DetectorOutput("D6", Mode.CLARIFY, "i", None, 0),)))
        self.assertEqual(result.outcome, Outcome.REJECT_EVENT)

    def test_p10_llm_containment(self):
        registry = ResourceRegistry()
        for state, offline in ((active(Mode.IMMEDIATE), False),
                               (replace(active(Mode.URGENT), degraded=True,
                                        degraded_causes=frozenset({"DETECTOR_ERROR"})), False),
                               (SafetyState(), True)):
            plan = output_plan(state, registry, NOW, client_offline=offline)
            self.assertFalse(plan.may_generate)
            self.assertFalse(accept_generated(plan, "fixture")[0])
        urgent = output_plan(active(Mode.URGENT), registry, NOW)
        self.assertTrue(urgent.requires_urgent_validation)
        self.assertFalse(accept_generated(urgent, "fixture")[0])
        self.assertTrue(accept_generated(urgent, "fixture", lambda _: True)[0])

    def test_p11_pinned_resource_independence(self):
        plan = output_plan(active(Mode.URGENT), ResourceRegistry(), NOW)
        pinned = plan.pinned_resources
        self.assertIsNotNone(pinned)
        accept_generated(plan, "unsafe fixture", lambda _: False)
        self.assertEqual(plan.pinned_resources, pinned)
        self.assertEqual(pinned.bundle.version, fixture_bundle().version)

    def test_p12_dropout_validity(self):
        cases = [
            (active(Mode.URGENT), DropoutReason.DURING_URGENT),
            (active(Mode.IMMEDIATE), DropoutReason.DURING_IMMEDIATE),
            (active(Mode.ELEVATED, Status.RECHECK_REQUIRED, peak=Mode.URGENT),
             DropoutReason.RECHECK_NOT_COMPLETED),
        ]
        for state, reason in cases:
            result = self.engine.apply(state, evt(EventKind.FOLLOWUP_WINDOW_EXPIRED))
            self.assertTrue(state_valid(result.state))
            self.assertEqual(result.state.episode_status, Status.DROPOUT)
            self.assertEqual(result.state.dropout_reason, reason)

    def test_p13_dropout_reentry(self):
        for mode, peak, reason, target in (
            (Mode.URGENT, Mode.URGENT, DropoutReason.DURING_URGENT, Mode.ELEVATED),
            (Mode.IMMEDIATE, Mode.IMMEDIATE, DropoutReason.DURING_IMMEDIATE, Mode.URGENT),
            (Mode.NORMAL, Mode.URGENT, DropoutReason.RECHECK_NOT_COMPLETED, Mode.ELEVATED),
        ):
            state = active(mode, Status.DROPOUT, peak=peak, sequence=4, reason=reason)
            proposal = self.engine.apply(state, evt(EventKind.PATIENT_RETURNED))
            self.assertEqual(proposal.action, "PROPOSE_DROPOUT_REENTRY")
            self.assertEqual(proposal.state, state)
            result = self.engine.apply(state, evt(EventKind.DROPOUT_REENTRY,
                                                 based_on_sequence=4))
            self.assertEqual(result.state.episode_status, Status.RECHECK_REQUIRED)
            self.assertEqual(result.state.interaction_mode, target)
            self.assertIsNone(result.state.dropout_reason)
            self.assertEqual(result.state.episode_peak_tier, peak)

    def test_p14_recheck_closure_visibility(self):
        state = active(Mode.ELEVATED, Status.RECHECK_REQUIRED, peak=Mode.URGENT)
        self.assertEqual(self.engine.apply(state, evt(EventKind.EPISODE_CLOSE_APPROVED,
                                                       based_on_sequence=1)).outcome,
                         Outcome.REJECT_EVENT)
        passed = self.engine.apply(state, evt(EventKind.RECHECK_PASSED)).state
        self.assertIn(FlagName.RECHECK_PASSED, {f.name for f in passed.flags})
        closed = self.engine.apply(passed, evt(EventKind.EPISODE_CLOSE_APPROVED,
                                               based_on_sequence=passed.sequence))
        self.assertEqual(closed.state.episode_status, Status.CLOSED)
        self.assertEqual(closed.state.episode_peak_tier, Mode.URGENT)

    def test_p15_t2_incomplete_visibility(self):
        state = active(Mode.ELEVATED)
        timed_out = self.engine.apply(state, evt(EventKind.FOLLOWUP_WINDOW_EXPIRED)).state
        self.assertEqual(timed_out.interaction_mode, Mode.ELEVATED)
        self.assertEqual(timed_out.episode_status, Status.OPEN)
        self.assertIn(FlagName.T2_FOLLOWUP_INCOMPLETE, {f.name for f in timed_out.flags})
        self.assertIn("T2_FOLLOWUP_INCOMPLETE", str(state_to_dict(timed_out)))

    def test_p16_cross_episode_stale_result(self):
        store = SafetyStore()
        closed = active(Mode.NORMAL, Status.CLOSED, peak=Mode.URGENT)
        store.initialize("p", closed)
        store.apply("p", evt(EventKind.EPISODE_ARCHIVE_DUE))
        frozen = store.archived_episodes[("p", "ep")]
        late = evt(EventKind.LATE_DETECTOR_RESULT, source_episode_id="ep",
                   episode_id="new", proposed_tier=Mode.ELEVATED,
                   detector_outputs=(DetectorOutput("D3", Mode.ELEVATED, "old-input", "ep", 1),))
        result = store.apply("p", late)
        self.assertEqual(result.state.episode_id, "new")
        self.assertEqual(result.source_episode_id, "ep")
        self.assertEqual(store.archived_episodes[("p", "ep")], frozen)
        self.assertEqual(store.audit[-1]["source_episode_id"], "ep")
        no_concern = store.apply("p", evt(EventKind.LATE_DETECTOR_RESULT,
                                         source_episode_id="ep", proposed_tier=Mode.NORMAL))
        self.assertEqual(no_concern.outcome, Outcome.NO_STATE_CHANGE)
        self.assertEqual(store.event_log[-1]["source_episode_id"], "ep")
        self.assertEqual(store.archived_episodes[("p", "ep")], frozen)

    def test_p17_client_offline_containment(self):
        storage = InMemoryInputFixture()
        gate = OfflineSafetyGate(ResourceRegistry(), storage)
        held = HeldInput("input-1", NOW, "fixture-only text")
        plan = gate.hold(SafetyState(), held)
        self.assertFalse(plan.may_generate)
        self.assertFalse(plan.input_assessed)
        self.assertEqual(plan.pinned_resources.source, "built_in")
        self.assertEqual(gate.reconnect(), (held,))

    def test_p18_recent_high_tier_memory(self):
        state = active(Mode.NORMAL, Status.CLOSED, peak=Mode.IMMEDIATE)
        archived = self.engine.apply(state, evt(EventKind.EPISODE_ARCHIVE_DUE)).state
        flag = next(f for f in archived.flags if f.name == FlagName.RECENT_HIGH_TIER_EPISODE)
        self.assertEqual(flag.source_episode_id, "ep")
        self.assertEqual(dict(flag.metadata)["prior_peak"], "IMMEDIATE")
        self.assertEqual(flag.expires_at, NOW + timedelta(days=7))
        self.assertEqual(self.engine.apply(archived, evt(EventKind.FLAG_EXPIRY_DUE,
                                                         flag_name=FlagName.RECENT_HIGH_TIER_EPISODE)).outcome,
                         Outcome.NO_STATE_CHANGE)
        expired = self.engine.apply(archived, Event(EventKind.FLAG_EXPIRY_DUE,
                                                     NOW + timedelta(days=7),
                                                     flag_name=FlagName.RECENT_HIGH_TIER_EPISODE)).state
        self.assertFalse(any(f.name == FlagName.RECENT_HIGH_TIER_EPISODE for f in expired.flags))

    def test_simulator_accepts_structured_answers_and_d5_flags(self):
        scenario = {"start_at": NOW.isoformat(), "steps": [
            {"kind": "POLICY_FLAG_SET", "flag_name": "REPEATED_ROUGH_CHECKINS"},
            {"kind": "STRUCTURED_RESPONSE_RECEIVED", "input_id": "answer-1",
             "structured_answer": "fixture-rough"},
            {"kind": "DETECTORS_COMPLETE", "episode_id": "ep-d5",
             "detector_outputs": [{"detector_id": "D5", "proposed_tier": "CLARIFY",
                                   "input_id": "answer-1", "source_episode_id": None,
                                   "source_sequence": 1}]},
        ]}
        record = run_scenario(scenario)
        self.assertEqual(record["final_state"]["episode_id"], "ep-d5")
        self.assertIn("REPEATED_ROUGH_CHECKINS", str(record["final_state"]))
        self.assertEqual(replay(record)["final_state"], record["final_state"])


if __name__ == "__main__":
    unittest.main()
