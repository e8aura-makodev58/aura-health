"""Agent replies to safety-cleared notes, agent-picked ideas and acknowledged choices. Fakes only."""
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock

from aura_app.communication import PatientCommunicationService
from aura_app.companion import CompanionService
from aura_app.models import AppError, ApplicationEvent, EventType
from aura_app.persistence import SQLiteRepositoryFactory
from aura_app.safety import FixtureSafetyGate
from aura_app.service import PatientEventService
from aura_app.simulator import fixture_treatment
from aura_communication.provider import FixtureProvider
from aura_communication.validation import patient_text_problems

NOW = datetime(2026, 10, 2, 12, tzinfo=timezone.utc)
CHESS = "I had fun playing chess with a friend today"


class FakeAgent:
    """Live agent provider double: answers each structured task from a script."""
    live = True
    model_id = "fake:agent@1"

    def __init__(self, replies):
        self.replies, self.calls = replies, []

    def step(self, messages, tools, reasoning=None):
        task = json.loads(messages[1]["content"])
        self.calls.append({"system": messages[0]["content"], "data": task, "reasoning": reasoning})
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return {"role": "assistant", "content": json.dumps(reply), "tool_calls": []}


class NoteReplyTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory(); self.addCleanup(temp.cleanup)
        factory = SQLiteRepositoryFactory(Path(temp.name) / "replies.sqlite3"); factory.initialize()
        self.gate = FixtureSafetyGate({})
        self.events = PatientEventService(factory, safety_gate=self.gate)
        self.events.create_patient(patient_id="p", display_name="Synthetic alias", age=35, timezone_name="UTC")

    def note(self, text=CHESS, tier="NORMAL", event_id="note"):
        self.gate.proposals[event_id] = (("D3", tier),)
        self.events.process(ApplicationEvent(event_id, "p", EventType.PATIENT_FREE_TEXT, NOW, NOW,
                                             "synthetic-fixture", {"text": text}, event_id, event_id))

    def render(self, agent):
        return PatientCommunicationService(self.events, provider=FixtureProvider(), clock=lambda: NOW,
                                           reply_provider=agent).render("p", "note")

    def test_nr1_agent_replies_to_what_the_patient_wrote(self):
        self.note()
        agent = FakeAgent([{"message": "Chess with a friend sounds like a lovely afternoon. I've kept your note with today's record."}])
        out = self.render(agent)
        self.assertEqual(out["mode"], "NORMAL_SUPPORT")
        self.assertTrue(out["generation_used"])
        self.assertIn("Chess with a friend", out["message"])
        self.assertEqual(agent.calls[0]["data"], {"note": CHESS})
        self.assertEqual(agent.calls[0]["reasoning"], "low")

    def test_nr2_unsafe_or_off_limits_reply_falls_back_to_fixed_wording(self):
        for bad in ("You should take your dose earlier.", "I've shared this with your doctor.", "Call 999 now."):
            with self.subTest(bad=bad):
                self.setUp(); self.note()
                out = self.render(FakeAgent([{"message": bad}]))
                self.assertFalse(out["generation_used"])
                self.assertEqual(out["message"], "Thanks for sharing. What would you like to focus on today?")
                self.assertEqual(out["fallback_reason"], "INVALID_GENERATION")

    def test_nr3_provider_failure_or_wrong_shape_keeps_fixed_wording(self):
        for reply in (RuntimeError("down"), {"message": "ok", "extra": 1}):
            with self.subTest(reply=type(reply).__name__):
                self.setUp(); self.note()
                out = self.render(FakeAgent([reply]))
                self.assertFalse(out["generation_used"])

    def test_nr4_no_agent_reply_outside_the_normal_state(self):
        self.note(tier="URGENT")
        agent = FakeAgent([{"message": "Lovely."}])
        out = self.render(agent)
        self.assertEqual(agent.calls, [])
        self.assertIsNotNone(out["pinned_resources"])

    def test_nr5_without_a_live_agent_behaviour_is_unchanged(self):
        self.note()
        out = PatientCommunicationService(self.events, provider=FixtureProvider(), clock=lambda: NOW).render("p", "note")
        self.assertEqual(out["mode"], "NORMAL_SUPPORT")
        self.assertNotIn("chess", out["message"].lower())

    def test_nr6_patient_text_rules(self):
        self.assertEqual(patient_text_problems("Thanks for sharing. That sounds like a good day."), ())
        self.assertIn("MEDICINE_TALK", patient_text_problems("Remember your medication."))
        self.assertIn("SENT_OR_SHARED", patient_text_problems("I've notified your care team."))
        self.assertIn("NUMBER_OR_CONTACT", patient_text_problems("See www.example.com"))
        self.assertIn("TOO_MANY_SENTENCES", patient_text_problems("One. Two. Three. Four."))


BASE = datetime(2026, 3, 1, 9, tzinfo=timezone.utc)
SUGGESTIONS = {"because": "You've been moving less than your usual since early March.",
               "trigger": {"signal": "ACTIVITY", "direction": "LOWER", "since": "2026-03-01"},
               "options": [{"id": "short_walk", "label": "A short walk outside, at your own pace"}]}


class ClearGate:
    def resolve(self, *args):
        return ()


class IdeaTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory(); self.addCleanup(temp.cleanup)
        factory = SQLiteRepositoryFactory(Path(temp.name) / "ideas.sqlite3"); factory.initialize()
        self.service = PatientEventService(factory, safety_gate=ClearGate())
        self.pid = "demo-B-7"
        self.service.create_patient(patient_id=self.pid, display_name="Synthetic", age=35, timezone_name="UTC",
                                    treatment=fixture_treatment(date(2026, 1, 1), BASE.date()), created_at=BASE)
        self.service.process(ApplicationEvent("n1", self.pid, EventType.PATIENT_FREE_TEXT, BASE, BASE,
                                              "synthetic_patient", {"text": CHESS}, "n1", "n1"))
        self.lookup = Mock(return_value=None)

    def companion(self, agent):
        return CompanionService(self.service, lookup=self.lookup, select=Mock(return_value=SUGGESTIONS), provider=agent)

    def test_id1_agent_picks_from_the_curated_pool_with_a_checked_line(self):
        agent = FakeAgent([{"ids": ["time_with_friend", "short_walk"], "why": "You enjoyed time with a friend, and moving a little more could feel good."}])
        result = self.companion(agent).personalize(self.pid)
        self.assertTrue(result["personalized"])
        self.assertEqual([row["id"] for row in result["options"]], ["time_with_friend", "short_walk"])
        self.assertEqual(agent.calls[0]["data"]["recent_notes"], [CHESS])
        self.assertEqual(agent.calls[0]["reasoning"], "low")

    def test_id2_unknown_ids_or_unsafe_lines_keep_the_rule_based_ideas(self):
        for reply in ({"ids": ["invented_idea"], "why": "Fine."}, {"ids": ["short_walk"], "why": "You should double your dose."},
                      {"ids": "short_walk", "why": "x"}):
            with self.subTest(reply=reply):
                self.assertEqual(self.companion(FakeAgent([reply])).personalize(self.pid), {"personalized": False})

    def test_id3_pick_is_cached_per_record_and_model(self):
        agent = FakeAgent([{"ids": ["music"], "why": "Something gentle for today."}])
        service = self.companion(agent)
        service.personalize(self.pid); service.personalize(self.pid)
        self.assertEqual(len(agent.calls), 1)

    def test_id4_choosing_an_idea_is_recorded_once_and_acknowledged(self):
        agent = FakeAgent([{"message": "A walk at your own pace sounds lovely."}])
        service = self.companion(agent)
        result = service.choose(self.pid, "short_walk")
        self.assertEqual(result["message"], "A walk at your own pace sounds lovely.")
        self.assertTrue(result["generation_used"])
        again = service.choose(self.pid, "short_walk")
        self.assertTrue(again["replay"])
        chosen = [row for row in self.service.timeline(self.pid) if row["record_type"] == "SUGGESTION_CHOSEN"]
        self.assertEqual(len(chosen), 1)
        self.assertEqual(service.get(self.pid)["chosen_today"], [{"option_id": "short_walk", "label": "A short walk outside, at your own pace"}])

    def test_id5_choice_without_agent_uses_fixed_wording_and_rejects_unknown_ids(self):
        service = self.companion(None)
        self.assertEqual(service.choose(self.pid, "daylight")["message"], "Noted for today. Go at your own pace.")
        with self.assertRaises(AppError):
            service.choose(self.pid, "not_an_idea")
        self.assertEqual(service.personalize(self.pid), {"personalized": False})


if __name__ == "__main__":
    unittest.main()
