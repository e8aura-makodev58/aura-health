"""Read-only companion projection. Recorded routine counts are not verified adherence.

The demo uses the latest recorded day, not the server's calendar day. No push reminder or
medication instruction is generated here. With a live provider, the agent may choose today's ideas
from the curated pool and acknowledge a choice in one checked sentence (fixed wording otherwise).
"""

from collections import Counter
from hashlib import sha256
import json
import threading
from contextlib import contextmanager
from copy import copy
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from aura_agent.guard import blocked_reason
from .evidence import EvidenceViewService
from .models import AppError, MISSED_REASONS


@dataclass(frozen=True)
class CompanionConfig:
    """Inspectable engineering display parameters, not clinical thresholds."""
    window_days: int = 7
    synthetic_morning_hour: int = 8

    def __post_init__(self):
        if type(self.window_days) is not int or self.window_days < 1:
            raise ValueError("window_days must be positive")
        if type(self.synthetic_morning_hour) is not int or not 0 <= self.synthetic_morning_hour <= 23:
            raise ValueError("invalid synthetic display hour")


def medication_lookup(name, schedule):
    # Claude owns this dependency. During independent branch review, fail honestly
    # rather than creating unreviewed substitute medication content.
    try:
        from aura_agent.medication import lookup
    except ModuleNotFoundError as error:
        if error.name != "aura_agent.medication":
            raise
        return {"name": name, "schedule": schedule, "known": False, "purpose": None,
                "how_to_take": None, "topics": [],
                "content_status": "Development content — needs pharmacist review",
                "abstain": "I'm not able to identify that medication, please check with your pharmacist."}
    return lookup(name, schedule)


def suggestion_selector(evidence, safety_normal):
    try:
        from aura_agent.suggestions import select
    except ModuleNotFoundError as error:
        if error.name != "aura_agent.suggestions":
            raise
        return None
    return select(evidence, safety_normal)


def routine_days(rows, end: date, tz: ZoneInfo, window_days: int):
    """Latest report per scheduled local day; missing days stay unrecorded.

    This single-medication, once-daily prototype does not support multi-dose
    regimens. Ties use deterministic repository commit order, not status severity.
    """
    start = end - timedelta(days=window_days - 1)
    days = {}
    ordered = sorted(enumerate(rows), key=lambda pair: (datetime.fromisoformat(pair[1]["timestamp"]), pair[0]))
    for _, row in ordered:
        scheduled = datetime.fromisoformat(row["scheduled_time"]).astimezone(tz).date()
        if start <= scheduled <= end:
            days[scheduled] = row
    return days


class CompanionService:
    def __init__(self, events, *, lookup=None, select=None, config=None, clock=None, provider=None):
        self.events = events
        # Optional live agent provider (synthetic hosted demo): picks ideas from the curated pool
        # and acknowledges a choice. Without it, the rule-based ideas and fixed wording stay.
        self.provider = provider
        self._picks = {}
        self._pick_lock = threading.Lock()  # one model pick at a time; concurrent loads reuse it
        self.lookup = lookup or medication_lookup
        self.select = select or suggestion_selector
        self.config = config or CompanionConfig()
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def get(self, patient_id):
        with self.events.repositories.transaction() as repo:
            patient = self.events._patient(repo, patient_id)
            try:
                tz = ZoneInfo(patient["timezone"])
            except (ZoneInfoNotFoundError, ValueError, TypeError):
                raise AppError("DOMAIN_ERROR", "record timezone is unavailable", 500) from None
            rows = repo.events(patient_id)
            stamps = [datetime.fromisoformat(row["occurred_at"]) for row in rows]
            latest = max(stamps) if stamps else datetime.fromisoformat(patient["created_at"])
            end = latest.astimezone(tz).date()
            deferred = {row["event_id"] for row in rows if row["longitudinal_deferred"]}
            medication_rows = [row for row in repo.medication_events(patient_id) if row["event_id"] not in deferred]
            days = routine_days(medication_rows, end, tz, self.config.window_days)
            today = days.get(end)
            reasons = Counter(row["reason"] for row in days.values()
                              if row["status"] == "MISSED" and row.get("reason"))
            treatment = patient.get("treatment") or {}
            scheduled = today["scheduled_time"] if today else None
            if scheduled is None and treatment.get("medication_schedule") == "50 mg, once each morning":
                # Display time for the explicitly synthetic fixture; not parsed
                # from arbitrary prescription prose or offered as dosing advice.
                scheduled = datetime.combine(end, time(self.config.synthetic_morning_hour), tzinfo=tz).isoformat()
            safety_normal = blocked_reason(repo.safety_state(patient_id), self.events.resource_registry,
                                           self.clock(), held=bool(deferred)) is None
            medication = self.lookup(treatment["medication_name"], treatment.get("medication_schedule")) if (
                safety_normal and treatment.get("medication_name")) else None
            suggestions = None
            if safety_normal:
                # Share the transaction with the accepted evidence projection:
                # one consistent read, no replay and no second SQLite connection.
                class SharedTransaction:
                    @contextmanager
                    def transaction(self):
                        yield repo
                reader = copy(self.events)
                reader.repositories = SharedTransaction()
                evidence = EvidenceViewService(reader).get(patient_id)
                suggestions = self.select(evidence, True)
            coming_up = []
            review = treatment.get("next_review")
            if review:
                try:
                    review_day = date.fromisoformat(review[:10])
                except (ValueError, TypeError):
                    review_day = None
                if review_day is not None and review_day >= end:
                    coming_up.append({"kind": "MEDICATION_REVIEW", "date": review_day.isoformat(),
                                      "label": "Medication review with your doctor"})
                # A review date alone is not evidence of a booked appointment.
            supply, refill = treatment.get("supply_days"), treatment.get("last_refill")
            if type(supply) is int and supply > 0 and refill:
                try:
                    refill_day = date.fromisoformat(refill) + timedelta(days=supply)
                except (ValueError, TypeError, OverflowError):
                    refill_day = None
                if refill_day is not None and refill_day >= end:
                    coming_up.append({"kind": "REFILL", "date": refill_day.isoformat(), "label": "Refill estimated"})
            coming_up.sort(key=lambda item: (item["date"], item["kind"]))
            # Same demo-day rule as choose(): the latest recorded event's date.
            latest_day = max(rows, key=lambda row: datetime.fromisoformat(row["occurred_at"]))["occurred_at"][:10] if rows else None
            chosen = [row["detail"] for row in repo.timeline(patient_id)
                      if row["record_type"] == "SUGGESTION_CHOSEN" and row["occurred_at"][:10] == latest_day]
            return {"safety_normal": safety_normal, "medication": medication,
                    "dose_today": {"scheduled_time": scheduled, "status": today["status"] if today else None},
                    "adherence": {"window_days": self.config.window_days,
                        "taken_days": sum(row["status"] == "ACKNOWLEDGED" for row in days.values()),
                        "recorded_days": len(days),
                        "missed_days": sum(row["status"] == "MISSED" for row in days.values()),
                        "missed_reasons": [{"reason": reason, "label": label, "count": reasons[reason]}
                                           for reason, label in MISSED_REASONS.items() if reasons[reason]]},
                    "coming_up": coming_up, "suggestions": suggestions, "chosen_today": chosen}

    def _live(self):
        return bool(self.provider is not None and getattr(self.provider, "live", False))

    def _recent_notes(self, patient_id, limit=3):
        """Safety-cleared patient notes from the last week of the record (never held input)."""
        with self.events.repositories.transaction() as repo:
            rows = repo.events(patient_id)
        if not rows:
            return []
        end = max(datetime.fromisoformat(row["occurred_at"]) for row in rows)
        notes = [row["payload"]["text"][:300] for row in rows
                 if row["event_type"] == "PATIENT_FREE_TEXT" and not row["longitudinal_deferred"]
                 and row["source"] != "patient_medication_update"
                 and datetime.fromisoformat(row["occurred_at"]) > end - timedelta(days=7)
                 and isinstance(row["payload"].get("text"), str) and not row["payload"]["text"].startswith("fixture ")]
        return notes[-limit:]

    def personalize(self, patient_id):
        """Agent-chosen ideas from the curated pool, with a checked line about why; else rule-based."""
        base = self.get(patient_id)
        suggestions = base["suggestions"]
        if not base["safety_normal"] or not suggestions or not self._live():
            return {"personalized": False}
        notes = self._recent_notes(patient_id)
        key = sha256(json.dumps([patient_id, suggestions, notes, self.provider.model_id], sort_keys=True).encode()).hexdigest()
        with self._pick_lock:
            if key not in self._picks:
                try:
                    from aura_agent.suggestions import personalize
                    self._picks[key] = personalize(self.provider, suggestions, notes)
                except Exception:
                    self._picks[key] = None
                if len(self._picks) > 256:
                    self._picks.pop(next(iter(self._picks)))
            pick = self._picks[key]
        if pick is None:
            return {"personalized": False}
        return {"personalized": True, "because": suggestions["because"], "why": pick["why"], "options": pick["options"]}

    def choose(self, patient_id, option_id):
        """Record the person's chosen idea for the demo day and acknowledge it briefly."""
        from aura_agent.suggestions import FIXED_ACK, POOL, acknowledge
        if not isinstance(option_id, str) or option_id not in POOL:
            raise AppError("INVALID_SUGGESTION", "Choose one of the offered ideas")
        base = self.get(patient_id)
        if not base["safety_normal"]:
            raise AppError("SAFETY_ACTIVE", "Ideas are paused while the safety pathway is active", 409)
        option = POOL[option_id]
        with self.events.repositories.transaction() as repo:
            rows = repo.events(patient_id)
            if not rows:
                raise AppError("INVALID_EVENT", "No record to attach the choice to")
            latest = max(rows, key=lambda row: datetime.fromisoformat(row["occurred_at"]))
            day = latest["occurred_at"][:10]
            already = any(row["record_type"] == "SUGGESTION_CHOSEN" and row["occurred_at"][:10] == day
                          and row["detail"].get("option_id") == option_id for row in repo.timeline(patient_id))
            if not already:
                repo.append_timeline({"patient_id": patient_id, "event_id": latest["event_id"],
                                      "record_type": "SUGGESTION_CHOSEN", "occurred_at": latest["occurred_at"],
                                      "detail": {"option_id": option_id, "label": option["label"]}})
        message, generated = None, False
        if self._live():
            try:
                message = acknowledge(self.provider, option)
                generated = message is not None
            except Exception:
                message = None
        return {"option_id": option_id, "label": option["label"], "message": message or FIXED_ACK,
                "generation_used": generated, "replay": already}
