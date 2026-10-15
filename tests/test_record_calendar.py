"""Past-day medication records, coverage and the calendar projector (spec §9.2). Synthetic fixtures only."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from uuid import uuid4
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
from fastapi.testclient import TestClient

from aura_app.demo import create_demo_app

PID = "demo-B-7"


class RecordCalendarTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.client = TestClient(create_demo_app(Path(temp.name) / "d.sqlite3"))
        self.base = f"/patients/{PID}"
        self.window = self.client.get(f"{self.base}/medication/update-window").json()

    def save(self, days, request_id=None):
        return self.client.post(f"{self.base}/medication/update", json={"request_id": request_id or str(uuid4()), "days": days})

    def test_rc1_window_is_record_local_and_unrecorded_days_count(self):
        w = self.window
        self.assertEqual(w["today"], "2026-03-11")          # latest record day, not the wall clock
        self.assertEqual([d["date"] for d in w["days"]][0], "2026-02-26")
        self.assertEqual(len(w["days"]), 14)
        self.assertEqual(w["unresolved_count"], 14)
        gap = self.client.get(f"{self.base}/companion").json()["medication_gap"]
        self.assertEqual(gap, {"unresolved_days": 14, "window_days": 14, "last_record_day": None, "prompt": True})

    def test_rc2_save_marks_days_reported_later_without_moving_today(self):
        result = self.save([{"date": "2026-03-10", "status": "MISSED", "reason": "FORGOT"},
                            {"date": "2026-03-09", "status": "ACKNOWLEDGED"}])
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["saved"], ["2026-03-09", "2026-03-10"])
        window = result.json()["window"]
        self.assertEqual(window["today"], "2026-03-11")
        locked = {d["date"]: d for d in window["days"] if d["locked"]}
        self.assertEqual(set(locked), {"2026-03-09", "2026-03-10"})
        self.assertTrue(all(d["reported_later"] for d in locked.values()))
        # Today's dose state is not taken from a past-day report.
        self.assertIsNone(self.client.get(f"{self.base}/view").json()["latest_medication"])
        self.assertIsNone(self.client.get(f"{self.base}/companion").json()["dose_today"]["status"])

    def test_rc3_exact_retry_replays_and_changed_payload_conflicts(self):
        request_id = str(uuid4())
        days = [{"date": "2026-03-10", "status": "MISSED"}]
        self.assertEqual(self.save(days, request_id).status_code, 200)
        retry = self.save(days, request_id)
        self.assertEqual((retry.status_code, retry.json()["replayed"]), (200, ["2026-03-10"]))
        changed = self.save([{"date": "2026-03-10", "status": "ACKNOWLEDGED"}], request_id)
        self.assertEqual((changed.status_code, changed.json()["error"]["code"]), (409, "UPDATE_CONFLICT"))
        other = self.save(days)  # a new request can't overwrite a recorded day either
        self.assertEqual(other.status_code, 409)

    def test_rc4_window_and_shape_rules(self):
        self.assertEqual(self.save([]).status_code, 422)
        for bad in ([{"date": "2026-02-01", "status": "MISSED"}],                     # outside the window
                    [{"date": "2026-03-12", "status": "MISSED"}],                     # future
                    [{"date": "2026-03-10", "status": "ACKNOWLEDGED", "reason": "FORGOT"}],  # reason only for MISSED
                    [{"date": "2026-03-10", "status": "MISSED"}, {"date": "2026-03-10", "status": "MISSED"}]):
            self.assertEqual(self.save(bad).status_code, 400, bad)
        self.assertEqual(self.save([{"date": "2026-03-10", "status": "DOUBLED"}]).status_code, 422)
        # Clients may not set the server-only flag on the ordinary event path.
        sneaky = self.client.post(f"{self.base}/events", json={"event_type": "MEDICATION_EVENT", "occurred_at": "2026-03-11T12:00:00+00:00",
            "source": "x", "payload": {"scheduled_time": "2026-03-05T08:00:00+00:00", "status": "ACKNOWLEDGED", "reported_later": True},
            "idempotency_key": str(uuid4())})
        self.assertEqual(sneaky.status_code, 400)

    def test_rc5_coverage_and_agent_fact(self):
        self.save([{"date": "2026-03-10", "status": "MISSED"}])
        coverage = self.client.get(f"{self.base}/coverage").json()
        self.assertEqual(coverage, {"today": "2026-03-11", "last_medication_day": "2026-03-10", "reported_later_in_window": 1,
                                    "window_days": 14, "last_checkin_day": "2026-03-11", "last_wearable_day": "2026-03-11"})
        tools, _ = self.client.app.state.agent_service.record_tools(PID, "record_qa", 56)
        texts = [fact["text"] for fact in tools.facts.values()]
        self.assertIn("Medication-routine record 2026-03-10: MISSED (reported later on 2026-03-11).", texts)
        self.assertTrue(any(text.startswith("Record coverage: last medication-routine record 2026-03-10") for text in texts))

    def test_rc6_calendar_grid_and_day_detail_follow_sharing(self):
        self.save([{"date": "2026-03-10", "status": "MISSED", "reason": "FORGOT"}])
        grid = self.client.get(f"{self.base}/calendar").json()
        self.assertEqual((grid["month"], grid["today"]), ("2026-03", "2026-03-11"))
        day = next(d for d in grid["days"] if d["date"] == "2026-03-10")
        self.assertEqual(day["medication"], {"status": "MISSED", "reported_later": True})
        self.assertIsNotNone(day["checkin"]); self.assertEqual(day["coverage"], "full")
        self.assertIsNone(next(d for d in grid["days"] if d["date"] == "2026-03-12")["medication"])
        self.assertTrue(next(d for d in grid["days"] if d["date"] == "2026-03-12")["future"])
        detail = self.client.get(f"{self.base}/calendar/2026-03-10").json()
        self.assertEqual(detail["medication"], {"status": "MISSED", "reason": "Forgot", "reported_later": True, "reported_on": "2026-03-11"})
        self.assertTrue(detail["readings"])
        self.client.post(f"{self.base}/sharing", json={"readings": False, "checkin_history": False, "notes": False, "activity_details": False})
        clinician = self.client.get(f"{self.base}/calendar?viewer=clinician").json()
        day = next(d for d in clinician["days"] if d["date"] == "2026-03-10")
        self.assertEqual((day["checkin"], day["coverage"], day["note"], day["activity"]), (None, None, None, None))
        self.assertEqual(day["medication"]["status"], "MISSED")           # medication routine is in the minimum
        detail = self.client.get(f"{self.base}/calendar/2026-03-10?viewer=clinician").json()
        self.assertEqual((detail["readings"], detail["notes"], detail["checkin"]), (None, None, None))
        self.assertEqual(self.client.get(f"{self.base}/calendar?viewer=patient").json()["withheld"], [])
        self.assertEqual(self.client.get(f"{self.base}/calendar?month=2026-13").status_code, 400)


if __name__ == "__main__":
    unittest.main()
