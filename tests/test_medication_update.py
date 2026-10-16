"""Updating past medication records from the patient's words: safety first, checked proposals. Fakes only."""
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from uuid import uuid4

from aura_app.activities import ActivityService
from aura_app.communication import PatientCommunicationService
from aura_app.medication_update import MedicationUpdateService, check_proposal
from aura_app.models import ApplicationEvent, EventType
from aura_app.persistence import SQLiteRepositoryFactory
from aura_app.service import PatientEventService
from aura_communication.provider import FixtureProvider

NOW = datetime(2026, 3, 11, 9, tzinfo=timezone.utc)   # a Wednesday
TEXT = "I took it most days except last Friday and yesterday"


def window(locked=()):
    days = []
    for offset in range(13, -1, -1):
        d = NOW.date() - timedelta(days=offset)
        days.append({"date": d.isoformat(), "weekday": d.strftime("%a"), "status": "ACKNOWLEDGED" if d.isoformat() in locked else None,
                     "reported_later": False, "locked": d.isoformat() in locked})
    return {"today": NOW.date().isoformat(), "timezone": "UTC", "max_days": 14, "unresolved_count": 14 - len(locked), "days": days}


class SwitchGate:
    """Clears every input; when text_tier is set, typed text gets that safety tier instead."""
    text_tier = None

    def resolve(self, event, *args):
        return (("D3", self.text_tier),) if self.text_tier and "text" in event.payload else ()


class FakeAgent:
    live = True
    model_id = "fake:agent@1"

    def __init__(self, reply):
        self.reply, self.calls = reply, []

    def step(self, messages, tools, reasoning=None):
        self.calls.append(json.loads(messages[1]["content"]))
        return {"role": "assistant", "content": json.dumps(self.reply), "tool_calls": []}


class CheckTests(unittest.TestCase):
    def test_mu1_most_days_with_named_exceptions_asks_one_question(self):
        friday, yesterday = "2026-03-06", "2026-03-10"
        proposal = {"days": [{"date": friday, "status": "MISSED", "basis": "explicit"},
                             {"date": yesterday, "status": "MISSED", "basis": "explicit"},
                             {"date": "2026-03-09", "status": "ACKNOWLEDGED", "basis": "from_most_days"}]}
        result = check_proposal(proposal, window())
        self.assertEqual(result["status"], "PROPOSED")
        self.assertEqual(result["question"], "Were Fri 6 Mar and Tue 10 Mar the only days you missed?")
        self.assertEqual([d["basis"] for d in result["days"]], ["explicit", "from_most_days", "explicit"])

    def test_mu2_out_of_window_locked_and_invalid_items_are_not_kept(self):
        proposal = {"days": [{"date": "2026-01-01", "status": "MISSED", "basis": "explicit"},          # outside window
                             {"date": "2026-03-09", "status": "ACKNOWLEDGED", "basis": "explicit"},    # locked
                             {"date": "2026-03-08", "status": "DOUBLED", "basis": "explicit"},         # bad status
                             {"date": "2026-03-07", "status": "MISSED", "basis": "guess"},             # bad basis
                             {"date": "2026-03-05", "status": "MISSED", "basis": "explicit"},
                             {"date": "2026-03-05", "status": "ACKNOWLEDGED", "basis": "explicit"}]}   # duplicate
        result = check_proposal(proposal, window(locked={"2026-03-09"}))
        self.assertEqual(result["days"], [{"date": "2026-03-05", "status": "MISSED", "basis": "explicit"}])
        self.assertEqual(result["out_of_window"], ["2026-01-01"])
        self.assertIsNone(result["question"])

    def test_mu3_nothing_usable_falls_back_to_tapping(self):
        for proposal in (None, {"days": "x"}, {"days": [{"date": "2027-01-01", "status": "MISSED"}]}):
            self.assertEqual(check_proposal(proposal, window())["status"], "TAP_ONLY")


class ServiceTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory(); self.addCleanup(temp.cleanup)
        factory = SQLiteRepositoryFactory(Path(temp.name) / "mu.sqlite3"); factory.initialize()
        self.gate = SwitchGate()
        self.events = PatientEventService(factory, safety_gate=self.gate)
        self.events.create_patient(patient_id="p", display_name="Synthetic", age=35, timezone_name="UTC")
        self.events.process(ApplicationEvent("seed", "p", EventType.PATIENT_CHECKIN, NOW, NOW, "synthetic_patient",
                                             {"state": "Okay"}, "seed", "seed"))

    def interpret(self, agent, text=TEXT, tier=None):
        self.gate.text_tier = tier
        return MedicationUpdateService(self.events, agent, clock=lambda: NOW).interpret("p", request_id=str(uuid4()), text=text)

    def test_mu4_normal_text_gets_a_checked_proposal(self):
        agent = FakeAgent({"days": [{"date": "2026-03-10", "status": "MISSED", "basis": "explicit"},
                                    {"date": "2026-03-09", "status": "ACKNOWLEDGED", "basis": "from_most_days"}]})
        result = self.interpret(agent)
        self.assertEqual(result["status"], "PROPOSED")
        self.assertEqual(agent.calls[0]["today"], "2026-03-11")
        self.assertEqual(len(agent.calls[0]["days"]), 14)
        self.assertEqual(result["question"], "Were Tue 10 Mar the only days you missed?")

    def test_mu5_stop_or_change_words_get_the_fixed_line_and_no_ai(self):
        agent = FakeAgent({"days": []})
        result = self.interpret(agent, text="I stopped taking it last week")
        self.assertEqual(result["status"], "ADVICE_REQUEST")
        self.assertIn("doctor or pharmacist", result["message"])
        self.assertEqual(agent.calls, [])

    def test_mu5b_safety_blocked_text_reaches_no_ai(self):
        agent = FakeAgent({"days": []})
        self.assertEqual(self.interpret(agent, tier="URGENT")["status"], "BLOCKED")
        self.assertEqual(agent.calls, [])

    def test_mu6_without_a_live_agent_it_is_tap_only(self):
        self.assertEqual(self.interpret(None)["status"], "TAP_ONLY")

    def test_mu7_update_text_gets_no_reply_card_and_no_activity_tags(self):
        self.interpret(FakeAgent({"days": [{"date": "2026-03-10", "status": "MISSED", "basis": "explicit"}]}),
                       text="I took it every day and painted for 3 hours")
        with self.events.repositories.transaction() as repo:
            event_id = [r for r in repo.events("p") if r["source"] == "patient_medication_update"][0]["event_id"]
        output = PatientCommunicationService(self.events, provider=FixtureProvider(), clock=lambda: NOW).render("p", event_id)
        self.assertEqual(output["message"], "")
        tagger = FakeAgent({"activities": [{"phrase": "painted for 3 hours", "categories": ["creative"], "minutes": 180}]})
        self.assertEqual(ActivityService(self.events, tagger, clock=lambda: NOW).extract_pending("p"), {"processed": 0})
        self.assertEqual(tagger.calls, [])


if __name__ == "__main__":
    unittest.main()
