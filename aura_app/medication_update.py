"""Updating past medication records from the patient's own words (spec §9.3).

The typed text is patient free text: it is safety-assessed first (source `patient_medication_update`,
which gets no note reply, ideas or activity tagging). Only then may the agent *propose* statuses for
days in the update window. Plain-code checks keep dates inside the window, skip locked days, use the
fixed enum and mark days inferred from words like "most days". Nothing is saved here: saving is the
backend update endpoint (§9.2), after the patient confirms in the preview.
"""
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
import re
from uuid import NAMESPACE_URL, uuid5
from zoneinfo import ZoneInfo

from aura_agent import medication
from aura_agent.guard import blocked_reason
from .models import AppError, ApplicationEvent, EventType

SOURCE = "patient_medication_update"
STATUSES = ("ACKNOWLEDGED", "MISSED", "UNKNOWN")
BASES = ("explicit", "from_most_days")
MAX_DAYS = 14
# Narrower than the medication-question list: describing past days ("less sleep", "more tired")
# must not read as a request to change treatment.
STOP_OR_CHANGE = re.compile(r"\b(stop(ped|ping)?|quit(ting)?|doubl(e|ed|ing)|halv(e|ed|ing)|switch(ed|ing)?|"
                            r"taper(ed|ing)?|came off|come off|coming off|(in|de)creas(e|ed|ing) (the |my )?dose|"
                            r"chang(e|ed|ing) (the |my )?dose|reduc(e|ed|ing) (the |my )?dose)\b", re.IGNORECASE)


class MedicationUpdateService:
    def __init__(self, events, provider, *, window=None, clock=None):
        self.events, self.provider = events, provider
        self.window = window  # Codex's §9.2 update-window projector, when available
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def _local_window(self, patient_id):
        """Fallback window until §9.2 lands: last 14 record days; locked = already recorded."""
        with self.events.repositories.transaction() as repo:
            patient = self.events._patient(repo, patient_id)
            rows = repo.events(patient_id)
            tz = ZoneInfo(patient["timezone"])
            if not rows:
                raise AppError("INVALID_EVENT", "No record yet")
            now = max(datetime.fromisoformat(row["occurred_at"]) for row in rows)
            today = now.astimezone(tz).date()
            recorded = {}
            for row in repo.events(patient_id):
                if row["event_type"] == "MEDICATION_EVENT" and not row["longitudinal_deferred"]:
                    day = datetime.fromisoformat(row["payload"]["scheduled_time"]).astimezone(tz).date()
                    recorded[day] = row["payload"]
        days = []
        for offset in range(MAX_DAYS - 1, -1, -1):
            day = today - timedelta(days=offset)
            row = recorded.get(day)
            days.append({"date": day.isoformat(), "weekday": day.strftime("%a"), "status": row["status"] if row else None,
                         "reported_later": bool(row and row.get("reported_later")), "locked": row is not None})
        return {"today": today.isoformat(), "timezone": str(tz), "max_days": MAX_DAYS,
                "unresolved_count": sum(not d["locked"] for d in days), "days": days, "now": now}

    def window_for(self, patient_id):
        return self.window(patient_id) if self.window else self._local_window(patient_id)

    def interpret(self, patient_id, *, request_id, text):
        if not isinstance(text, str) or not 1 <= len(text.strip()) <= 500:
            raise AppError("INVALID_MEDICATION_UPDATE", "Describe the days in one short message")
        window = self.window_for(patient_id)
        now = window.get("now") or datetime.fromisoformat(window["today"] + "T12:00:00+00:00")
        # Safety first: the words are the patient's, assessed like any typed text.
        event_id = str(uuid5(NAMESPACE_URL, f"aura-medication-update:{patient_id}:{request_id}:{sha256(text.encode()).hexdigest()}"))
        self.events.process(ApplicationEvent(event_id, patient_id, EventType.PATIENT_FREE_TEXT, now, self.clock(),
                                             SOURCE, {"text": text}, event_id, event_id))
        with self.events.repositories.transaction() as repo:
            blocked = blocked_reason(repo.safety_state(patient_id), self.events.resource_registry, self.clock())
        base = {"window": {k: v for k, v in window.items() if k != "now"}, "days": [], "question": None,
                "out_of_window": [], "advice_request": False, "message": None}
        if blocked:
            return {**base, "status": "BLOCKED"}
        if STOP_OR_CHANGE.search(text):
            # Version one: no AI date inference for stop/change statements (user decision B).
            return {**base, "status": "ADVICE_REQUEST", "advice_request": True, "message": medication.ADVICE_REQUEST}
        if not getattr(self.provider, "live", False):
            return {**base, "status": "TAP_ONLY", "message": "Tap each day to set it."}
        try:
            from aura_agent.tasks import structured_task
            proposal = structured_task(self.provider, "medication_backfill", {
                "note": text, "today": window["today"],
                "days": [{"date": d["date"], "weekday": d["weekday"], "already_recorded": d["locked"]} for d in window["days"]]},
                reasoning="low")
        except Exception:
            return {**base, "status": "TAP_ONLY", "message": "AURA couldn't work that out. You can tap the days instead."}
        return {**base, **check_proposal(proposal, window)}


def check_proposal(proposal, window):
    """Keep only verifiable proposals; build the one confirmation question in plain code."""
    editable = {d["date"]: d for d in window["days"] if not d["locked"]}
    if not isinstance(proposal, dict) or not isinstance(proposal.get("days"), list):
        return {"status": "TAP_ONLY", "message": "AURA couldn't work that out. You can tap the days instead."}
    days, out_of_window, seen = [], [], set()
    for item in proposal["days"][:60]:
        if not isinstance(item, dict):
            continue
        when, status, basis = item.get("date"), item.get("status"), item.get("basis", "explicit")
        try:
            date.fromisoformat(when)
        except (TypeError, ValueError):
            continue
        if when not in editable:
            if when not in {d["date"] for d in window["days"]}:
                out_of_window.append(when)
            continue
        if when in seen or status not in STATUSES or basis not in BASES:
            continue
        seen.add(when)
        days.append({"date": when, "status": status, "basis": basis})
    if not days:
        return {"status": "TAP_ONLY", "days": [], "out_of_window": sorted(set(out_of_window)),
                "message": "AURA couldn't match that to specific days. You can tap the days instead."}
    question = None
    if any(d["basis"] == "from_most_days" for d in days):
        missed = [d for d in days if d["status"] == "MISSED" and d["basis"] == "explicit"]
        names = [f"{editable[d['date']]['weekday']} {date.fromisoformat(d['date']).day} "
                 f"{date.fromisoformat(d['date']).strftime('%b')}" for d in missed]
        question = (f"Were {', '.join(names[:-1]) + ' and ' + names[-1] if len(names) > 1 else names[0]} the only days you missed?"
                    if names else "Did you take it on all the other days?")
    return {"status": "PROPOSED", "days": sorted(days, key=lambda d: d["date"]),
            "out_of_window": sorted(set(out_of_window)), "question": question, "message": None}
