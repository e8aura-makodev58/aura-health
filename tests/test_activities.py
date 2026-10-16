"""Patient-reported activities: verifiable extraction, patient-only detail, clinician aggregates. Fakes only."""
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from aura_agent.activities import check, summarize, summary_text
from aura_app.activities import ActivityService
from aura_app.agent import AgentService
from aura_app.models import ApplicationEvent, EventType
from aura_app.persistence import SQLiteRepositoryFactory
from aura_app.safety import FixtureSafetyGate
from aura_app.service import PatientEventService

NOW = datetime(2026, 3, 11, 12, tzinfo=timezone.utc)
PAINT = "I spent 10 hours painting this weekend and walked my dog with a friend"


class FakeAgent:
    live = True
    model_id = "fake:agent@1"

    def __init__(self, replies):
        self.replies, self.calls = list(replies), []

    def step(self, messages, tools, reasoning=None):
        self.calls.append(json.loads(messages[1]["content"]))
        return {"role": "assistant", "content": json.dumps(self.replies.pop(0)), "tool_calls": []}


class CheckTests(unittest.TestCase):
    def test_ac1_only_verifiable_items_are_kept(self):
        kept = check(PAINT, {"activities": [
            {"phrase": "10 hours painting", "categories": ["creative"], "minutes": 600},
            {"phrase": "walked my dog with a friend", "categories": ["physical", "social", "outdoors"], "minutes": 30},
            {"phrase": "went swimming", "categories": ["physical"], "minutes": None},
            {"phrase": "painting", "categories": ["wellbeing_score"], "minutes": None}]})
        self.assertEqual(kept, [
            {"phrase": "10 hours painting", "categories": ["creative"], "minutes": 600},
            {"phrase": "walked my dog with a friend", "categories": ["physical", "social", "outdoors"], "minutes": None}])

    def test_ac2_malformed_proposals_yield_nothing(self):
        for proposal in (None, {"activities": "x"}, {"activities": [], "score": 9}, {"activities": [{"phrase": "painting", "categories": ["creative"], "mood": "happy"}]}):
            self.assertEqual(check(PAINT, proposal), [])

    def test_ac3_summary_compares_two_windows_without_phrases(self):
        rows = [{"at": "2026-03-08T10:00:00+00:00", "items": [{"phrase": "10 hours painting", "categories": ["creative"], "minutes": 600}]},
                {"at": "2026-02-20T10:00:00+00:00", "items": [{"phrase": "a walk", "categories": ["physical"], "minutes": None}]}]
        summary = summarize(rows, date(2026, 3, 11))
        creative = next(row for row in summary["categories"] if row["category"] == "creative")
        self.assertEqual((creative["recent"], creative["earlier"]), ({"days": 1, "minutes": 600}, {"days": 0, "minutes": 0}))
        text = summary_text(summary)
        self.assertIn("Creative / hobbies: mentioned on 1 day vs 0 days, stated time 10 h vs 0 h", text)
        self.assertNotIn("painting", json.dumps(summary) + text)


class ServiceTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory(); self.addCleanup(temp.cleanup)
        factory = SQLiteRepositoryFactory(Path(temp.name) / "acts.sqlite3"); factory.initialize()
        self.gate = FixtureSafetyGate({})
        self.events = PatientEventService(factory, safety_gate=self.gate)
        self.events.create_patient(patient_id="p", display_name="Synthetic", age=35, timezone_name="UTC")

    def note(self, event_id, text, tier="NORMAL", at=NOW):
        self.gate.proposals[event_id] = (("D3", tier),)
        self.events.process(ApplicationEvent(event_id, "p", EventType.PATIENT_FREE_TEXT, at, at,
                                             "synthetic_patient", {"text": text}, event_id, event_id))

    def test_as1_extracts_once_and_keeps_details_patient_side(self):
        self.note("n1", PAINT)
        agent = FakeAgent([{"activities": [{"phrase": "10 hours painting", "categories": ["creative"], "minutes": 600}]}])
        service = ActivityService(self.events, agent, clock=lambda: NOW)
        self.assertEqual(service.extract_pending("p"), {"processed": 1})
        self.assertEqual(service.extract_pending("p"), {"processed": 0})
        self.assertEqual(len(agent.calls), 1)
        self.assertEqual(agent.calls[0]["note"], PAINT)
        patient = service.for_patient("p")
        self.assertEqual(patient["items"][0]["phrase"], "10 hours painting")
        summary = service.summary("p")
        self.assertNotIn("painting", json.dumps(summary))
        self.assertEqual(summary["categories"][0]["recent"], {"days": 1, "minutes": 600})

    def test_as2_no_extraction_outside_the_normal_state_or_without_a_live_agent(self):
        self.note("n1", "I want to stop everything", tier="URGENT")
        agent = FakeAgent([{"activities": []}])
        self.assertEqual(ActivityService(self.events, agent, clock=lambda: NOW).extract_pending("p"), {"processed": 0})
        self.assertEqual(agent.calls, [])
        self.assertEqual(ActivityService(self.events, None, clock=lambda: NOW).extract_pending("p"), {"processed": 0})

    def test_as3_clinician_agent_gets_aggregates_not_phrases(self):
        self.note("n1", PAINT)
        ActivityService(self.events, FakeAgent([{"activities": [{"phrase": "10 hours painting", "categories": ["creative"], "minutes": 600}]}]),
                        clock=lambda: NOW).extract_pending("p")
        tools, evidence = AgentService(self.events, synthetic_only=True).record_tools("p", "record_qa", 56)
        activity = [fact["text"] for fact in tools.facts.values() if fact["source_ref"].startswith("activity-summary:")]
        self.assertEqual(len(activity), 1)
        self.assertIn("Creative / hobbies", activity[0])
        self.assertNotIn("painting", activity[0])


if __name__ == "__main__":
    unittest.main()
