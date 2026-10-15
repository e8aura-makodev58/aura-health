"""Past-day medication updates, record coverage and the calendar (spec §9.2).

All reads use record-local time: "today" is the record's latest event day in the patient's
timezone, never the wall clock. Medication is grouped by the day it describes (`scheduled_time`),
so a record reported later lands on the right day. Saving a past day is a report made *now*:
`occurred_at` stays at the record's latest moment and the payload carries `reported_later`.
The calendar is a pure read projection in one transaction, filtered by the patient's sharing
choices when the clinician is the viewer. No AI here.
"""
from calendar import monthrange
from contextlib import contextmanager
from copy import copy
from datetime import date, datetime, time, timedelta, timezone
from hashlib import sha256
import json
from uuid import NAMESPACE_URL, uuid5
from zoneinfo import ZoneInfo

from aura_agent.guard import blocked_reason
from .evidence import EvidenceViewService
from .models import AppError, ApplicationEvent, EventType, MISSED_REASONS

WINDOW_DAYS = 14          # editable past days (user decision D)
PROMPT_AFTER = 3          # unresolved days before the gentle prompt (user decision D)
SCHEDULE_HOUR = 8         # synthetic once-each-morning schedule
STATUSES = ("ACKNOWLEDGED", "MISSED", "UNKNOWN")
UPDATE_SOURCE = "patient_medication_backfill"


def _shared(repo):
    class SharedTransaction:
        @contextmanager
        def transaction(self):
            yield repo
    return SharedTransaction()


class RecordCalendarService:
    def __init__(self, events, sharing, clock=None):
        self.events, self.sharing = events, sharing
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    # ---- shared reads -------------------------------------------------------------------
    def _base(self, repo, patient_id):
        patient = self.events._patient(repo, patient_id)
        rows = repo.events(patient_id)
        if not rows:
            raise AppError("INVALID_EVENT", "No record yet")
        tz = ZoneInfo(patient["timezone"])
        now = max(datetime.fromisoformat(row["occurred_at"]) for row in rows)
        return patient, rows, tz, now, now.astimezone(tz).date()

    @staticmethod
    def _medication_days(repo, rows, tz):
        """Latest report per described local day (commit order breaks ties)."""
        deferred = {row["event_id"] for row in rows if row["longitudinal_deferred"]}
        reported = {row["event_id"]: row for row in rows}
        days = {}
        for row in repo.medication_events(rows[0]["patient_id"]):
            if row["event_id"] in deferred:
                continue
            event = reported.get(row["event_id"], {})
            payload = event.get("payload", {})
            day = datetime.fromisoformat(row["scheduled_time"]).astimezone(tz).date()
            days[day] = {"status": row["status"], "reason": row.get("reason"),
                         "reported_later": bool(payload.get("reported_later")),
                         "reported_on": (datetime.fromisoformat(event["occurred_at"]).astimezone(tz).date().isoformat()
                                         if payload.get("reported_later") else None),
                         "idempotency_key": event.get("idempotency_key"), "payload": payload}
        return days

    def _window(self, repo, patient_id):
        patient, rows, tz, now, today = self._base(repo, patient_id)
        treatment = patient.get("treatment") or {}
        start = today - timedelta(days=WINDOW_DAYS - 1)
        regimen = treatment.get("regimen_start")
        if regimen:
            try:
                start = max(start, date.fromisoformat(regimen[:10]))
            except ValueError:
                pass
        recorded = self._medication_days(repo, rows, tz)
        days = []
        day = start
        while day <= today:
            row = recorded.get(day)
            days.append({"date": day.isoformat(), "weekday": day.strftime("%a"), "status": row["status"] if row else None,
                         "reported_later": bool(row and row["reported_later"]), "locked": row is not None})
            day += timedelta(days=1)
        window = {"today": today.isoformat(), "timezone": str(tz), "schedule_hour": SCHEDULE_HOUR, "max_days": WINDOW_DAYS,
                  "unresolved_count": sum(not d["locked"] for d in days), "days": days}
        return window, {"patient": patient, "tz": tz, "now": now, "recorded": recorded, "rows": rows}

    def update_window(self, patient_id):
        with self.events.repositories.transaction() as repo:
            return self._window(repo, patient_id)[0]

    def window_with_now(self, patient_id):
        """For the interpret step: the window plus the record-local moment."""
        with self.events.repositories.transaction() as repo:
            window, context = self._window(repo, patient_id)
        return {**window, "now": context["now"]}

    # ---- saving past days ----------------------------------------------------------------
    def save(self, patient_id, *, request_id, days):
        """Save past days. Window, safety, slot and retry checks and the write share ONE transaction,
        so overlapping requests cannot both fill a day. Idempotency is per day: patient + day + request,
        bound to that day's payload (a changed payload under the same key is a conflict)."""
        if not isinstance(days, list) or not days or len(days) > WINDOW_DAYS:
            raise AppError("INVALID_MEDICATION_UPDATE", "Choose at least one day to save")
        from .service import PatientEventService
        with self.events.repositories.transaction() as repo:
            window, context = self._window(repo, patient_id)
            held = any(row["longitudinal_deferred"] for row in context["rows"])
            if blocked_reason(repo.safety_state(patient_id), self.events.resource_registry, self.clock(), held=held):
                raise AppError("SAFETY_ACTIVE", "Medication updates are paused while the safety pathway is active", 409)
            editable = {d["date"] for d in window["days"]}
            tz, now = context["tz"], context["now"]
            stored = {row["idempotency_key"]: row for row in context["rows"]}
            events, seen, replayed, held_days = [], set(), [], []
            for item in days:
                if not isinstance(item, dict) or set(item) - {"date", "status", "reason"}:
                    raise AppError("INVALID_MEDICATION_UPDATE", "Each day needs a date and a status")
                when, status, reason = item.get("date"), item.get("status"), item.get("reason")
                if when not in editable or when in seen:
                    raise AppError("INVALID_MEDICATION_UPDATE", f"{when} is not a day you can update here")
                if status not in STATUSES or (reason is not None and (status != "MISSED" or reason not in MISSED_REASONS)):
                    raise AppError("INVALID_MEDICATION_UPDATE", "Use Taken, Missed or Not sure")
                seen.add(when)
                day = date.fromisoformat(when)
                payload = {"scheduled_time": datetime.combine(day, time(SCHEDULE_HOUR), tzinfo=tz).isoformat(),
                           "status": status, "reported_later": True}
                if reason:
                    payload["reason"] = reason
                key = str(uuid5(NAMESPACE_URL, f"aura-medication-backfill:{patient_id}:{when}:{request_id}"))
                prior = stored.get(key)
                if prior is not None:
                    if prior["payload"] != payload:
                        raise AppError("UPDATE_CONFLICT", f"{when} was already sent with a different answer", 409)
                    (held_days if prior["longitudinal_deferred"] else replayed).append(when)  # exact retry
                    continue
                if day in context["recorded"]:
                    raise AppError("UPDATE_CONFLICT", f"{when} already has a record", 409)
                fingerprint = sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]
                events.append(ApplicationEvent(str(uuid5(NAMESPACE_URL, f"{key}:{fingerprint}")), patient_id, EventType.MEDICATION_EVENT,
                                               now, self.clock(), UPDATE_SOURCE, payload, key, key))
            child = PatientEventService(_shared(repo), safety_gate=self.events.safety_gate, safety_engine=self.events.safety_engine,
                                        resource_registry=self.events.resource_registry, signal_registry=self.events.signal_registry)
            results = [child.process(event) for event in events]
        written = [event.payload["scheduled_time"][:10] for event in events]  # local dates, in event order
        # The safety domain may hold input (e.g. its check could not run): never report that as saved.
        held_days += [day for day, result in zip(written, results) if result.longitudinal.get("deferred")]
        saved = sorted(d for d in seen if d not in held_days)
        return {"status": "HELD" if held_days else "SAVED", "saved": saved, "held": sorted(held_days),
                "replayed": sorted(replayed), "window": self.update_window(patient_id)}

    # ---- gap, coverage ------------------------------------------------------------------
    def medication_gap(self, patient_id):
        with self.events.repositories.transaction() as repo:
            window, context = self._window(repo, patient_id)
        recorded = sorted(context["recorded"])  # the actual latest described day, even outside the window
        return {"unresolved_days": window["unresolved_count"], "window_days": WINDOW_DAYS,
                "last_record_day": recorded[-1].isoformat() if recorded else None,
                "prompt": window["unresolved_count"] >= PROMPT_AFTER}

    def coverage(self, patient_id):
        """Coverage metadata (minimum-shared): when things were last recorded, not what they said."""
        with self.events.repositories.transaction() as repo:
            window, context = self._window(repo, patient_id)
            tz = context["tz"]
            checkins = [datetime.fromisoformat(row["occurred_at"]).astimezone(tz).date()
                        for row in context["rows"] if row["event_type"] == "PATIENT_CHECKIN" and not row["longitudinal_deferred"]]
            wearable = [row["day"] for row in repo.observations(patient_id)]
        medication = sorted(context["recorded"])
        return {"today": window["today"],
                "last_medication_day": medication[-1].isoformat() if medication else None,
                "reported_later_in_window": sum(d["reported_later"] for d in window["days"]),
                "window_days": WINDOW_DAYS,
                "last_checkin_day": max(checkins).isoformat() if checkins else None,
                "last_wearable_day": max(wearable) if wearable else None}

    # ---- calendar -----------------------------------------------------------------------
    def _collect(self, repo, patient_id, viewer):
        patient, rows, tz, now, today = self._base(repo, patient_id)
        withheld = frozenset()
        if viewer == "clinician":
            # Same transaction: the consent read sees exactly the record this projection sees.
            sharing = copy(self.sharing)
            sharing.events = copy(self.events)
            sharing.events.repositories = _shared(repo)
            withheld = sharing.withheld(patient_id)
        held = any(row["longitudinal_deferred"] for row in rows)
        normal = blocked_reason(repo.safety_state(patient_id), self.events.resource_registry, self.clock(), held=held) is None
        local = lambda stamp: datetime.fromisoformat(stamp).astimezone(tz).date()
        checkins = {}
        for row in rows:
            if row["event_type"] == "PATIENT_CHECKIN" and not row["longitudinal_deferred"]:
                checkins[local(row["occurred_at"])] = row["payload"]["state"]
        assessed = {ref["event_id"] for ref in repo.safety_references(patient_id)
                    if not ref["state"]["degraded"] and ref["state"]["interaction_mode"] == "NORMAL"
                    and ref["outcome"] not in {"DEFER_EVENT", "REJECT_EVENT", "SET_DEGRADED"}}
        notes = {}
        for row in rows:
            text = row["payload"].get("text") if row["event_type"] == "PATIENT_FREE_TEXT" else None
            if (isinstance(text, str) and row["event_id"] in assessed and not row["longitudinal_deferred"]
                    and row["source"] != "patient_medication_update" and not text.startswith("fixture ")):
                notes.setdefault(local(row["occurred_at"]), []).append({"event_id": row["event_id"], "text": text[:600]})
        cleared = {item["event_id"] for items in notes.values() for item in items}
        timeline = repo.timeline(patient_id)
        activities, ideas = {}, {}
        from aura_agent.activities import LABELS
        for row in timeline:
            if row["record_type"] == "PATIENT_ACTIVITY" and row["detail"].get("note_event_id") in cleared:
                for item in row["detail"].get("items", []):
                    activities.setdefault(local(row["occurred_at"]), []).append(
                        {"phrase": item.get("phrase"), "labels": [LABELS[c] for c in item.get("categories", []) if c in LABELS],
                         "minutes": item.get("minutes")})
            elif row["record_type"] == "SUGGESTION_CHOSEN":
                ideas.setdefault(local(row["occurred_at"]), []).append(row["detail"].get("label"))
        reader = copy(self.events)
        reader.repositories = _shared(repo)
        evidence = EvidenceViewService(reader).get(patient_id)
        return {"patient": patient, "rows": rows, "tz": tz, "today": today, "withheld": withheld, "normal": normal,
                "checkins": checkins, "medication": self._medication_days(repo, rows, tz), "notes": notes,
                "activities": activities, "ideas": ideas, "evidence": evidence}

    @staticmethod
    def _coverage_by_day(evidence):
        signals = [s for s in evidence["signals"] if s["registry"]["enabled_in_engine"] and s["observations"]]
        covered = {}
        for signal in signals:
            for row in signal["observations"]:
                if not row["deferred"] and (row["coverage"] or 0) > 0:
                    covered.setdefault(row["day"], set()).add(signal["label"] + signal["key"]["metric"])
        first = min((row["day"] for s in signals for row in s["observations"]), default=None)
        return len(signals), covered, first

    def calendar(self, patient_id, month=None, viewer="patient"):
        with self.events.repositories.transaction() as repo:
            data = self._collect(repo, patient_id, viewer)
        today, withheld = data["today"], data["withheld"]
        try:
            year, number = (int(part) for part in (month or today.strftime("%Y-%m")).split("-"))
            first_day = date(year, number, 1)
        except (ValueError, TypeError):
            raise AppError("INVALID_EVENT", "month must be YYYY-MM") from None
        total, covered, first_obs = self._coverage_by_day(data["evidence"])
        days = []
        for offset in range(monthrange(first_day.year, first_day.month)[1]):
            day = first_day + timedelta(days=offset)
            key = day.isoformat()
            future = day > today
            med = data["medication"].get(day)
            if future or "readings" in withheld or not total or first_obs is None or key < first_obs:
                coverage = None
            else:
                count = len(covered.get(key, ()))
                coverage = "full" if count >= total else ("partial" if count else "none")
            days.append({"date": key, "future": future,
                         "checkin": None if "checkin_history" in withheld else data["checkins"].get(day),
                         "medication": {"status": med["status"], "reported_later": med["reported_later"]} if med else None,
                         "coverage": coverage,
                         "note": None if "notes" in withheld or not data["normal"] else (day in data["notes"]),
                         "activity": None if "activity_details" in withheld or not data["normal"] else (day in data["activities"])})
        record_start = min((datetime.fromisoformat(row["occurred_at"]).astimezone(data["tz"]).date() for row in data["rows"]))
        return {"month": first_day.strftime("%Y-%m"), "today": today.isoformat(), "viewer": viewer,
                "record_start": record_start.isoformat(), "withheld": sorted(withheld), "days": days}

    def day(self, patient_id, when, viewer="patient"):
        try:
            day = date.fromisoformat(when)
        except (ValueError, TypeError):
            raise AppError("INVALID_EVENT", "date must be YYYY-MM-DD") from None
        with self.events.repositories.transaction() as repo:
            data = self._collect(repo, patient_id, viewer)
        withheld, key = data["withheld"], day.isoformat()
        med = data["medication"].get(day)
        readings, findings, gaps = [], [], []
        for signal in data["evidence"]["signals"]:
            for row in signal["observations"]:
                if row["day"] == key and not row["deferred"]:
                    readings.append({"signal": signal["key"]["signal"], "label": signal["label"],
                                     "value": row["value"], "unit": signal["unit"]})
            for finding in signal["findings"]:
                if finding["first_seen"][:10] <= key <= finding["last_seen"][:10]:
                    findings.append({"signal": signal["key"]["signal"], "label": signal["label"],
                                     "direction": finding["drift"].get("direction") or finding["drift"]["kind"],
                                     "since": finding["first_seen"][:10]})
            for gap in signal["gaps"]:
                if gap["type"] == "SENSING_GAP" and gap["at"][:10] == key:
                    gaps.append(signal["label"])
        normal = data["normal"]
        return {"date": key, "today": data["today"].isoformat(), "future": day > data["today"],
                "checkin": None if "checkin_history" in withheld else data["checkins"].get(day),
                "medication": ({"status": med["status"], "reason": MISSED_REASONS.get(med["reason"]) if med["reason"] else None,
                                "reported_later": med["reported_later"], "reported_on": med["reported_on"]} if med else None),
                "readings": None if "readings" in withheld else readings,
                "notes": None if "notes" in withheld or not normal else [n["text"] for n in data["notes"].get(day, [])],
                "activities": None if "activity_details" in withheld or not normal else data["activities"].get(day, []),
                "ideas_chosen": data["ideas"].get(day, []) if normal else [],
                "findings": findings, "gaps": sorted(set(gaps)), "withheld": sorted(withheld)}
