"""What the patient lets their clinician see.

A curated minimum is always shared (agreed at sign-up; required to use AURA): the changes AURA
found and their summary numbers, check-in summaries, medication routine records, activity totals,
and the safety state (a safety requirement). Everything else is optional and patient-controlled.
Each change is appended to the timeline (audit). The hosted demo defaults to everything shared;
the design handles the minimum-only choice everywhere the clinician reads the record.
"""
from .models import AppError

OPTIONAL = {
    "notes": "My notes (the words I write)",
    "readings": "Detailed wearable readings (daily values and charts)",
    "checkin_history": "Each day's check-in (not just the summary)",
    "activity_details": "What I mentioned doing (activity phrases)",
}
MINIMUM = [
    "Changes AURA found in my record, and when",
    "Check-in summary (for example, Rough on 7 of the last 7 days)",
    "Medication routine: doses taken or missed, and reasons",
    "Totals of activities I mentioned",
    "Safety state (always shared, for safety)",
]
CLINICIAN_ROLES = {"clinician_brief", "question_ranker"}


class SharingService:
    def __init__(self, events, *, default_all=True, clock=None):
        self.events, self.default_all = events, default_all
        self.clock = clock

    def _latest(self, repo, patient_id):
        rows = [row for row in repo.timeline(patient_id) if row["record_type"] == "SHARING_CONSENT"]
        return rows[-1] if rows else None

    def get(self, patient_id):
        with self.events.repositories.transaction() as repo:
            self.events._patient(repo, patient_id)
            latest = self._latest(repo, patient_id)
        optional = dict(latest["detail"]["optional"]) if latest else {key: self.default_all for key in OPTIONAL}
        return {"minimum": MINIMUM, "minimum_agreed": True,
                "optional": [{"id": key, "label": label, "shared": bool(optional.get(key))} for key, label in OPTIONAL.items()],
                "source": "patient_choice" if latest else ("demo_default_all" if self.default_all else "default_minimum"),
                "updated_at": latest["occurred_at"] if latest else None}

    def withheld(self, patient_id):
        """Optional categories the clinician may not see right now."""
        return frozenset(row["id"] for row in self.get(patient_id)["optional"] if not row["shared"])

    def set(self, patient_id, choices):
        if not isinstance(choices, dict) or not choices or set(choices) - set(OPTIONAL) or any(type(v) is not bool for v in choices.values()):
            raise AppError("INVALID_SHARING", "Choose sharing for the listed categories only")
        current = {row["id"]: row["shared"] for row in self.get(patient_id)["optional"]}
        current.update(choices)
        with self.events.repositories.transaction() as repo:
            rows = repo.events(patient_id)
            if not rows:
                raise AppError("INVALID_EVENT", "No record yet")
            latest = max(rows, key=lambda row: row["occurred_at"])
            repo.append_timeline({"patient_id": patient_id, "event_id": latest["event_id"], "record_type": "SHARING_CONSENT",
                                  "occurred_at": latest["occurred_at"], "detail": {"optional": current, "changed": choices}})
        return self.get(patient_id)


def clinician_view(role, asker):
    """True when the agent run serves the clinician (sharing applies)."""
    return role in CLINICIAN_ROLES or (role == "record_qa" and asker == "clinician")


def filter_evidence(evidence, withheld):
    """The record as a clinician may see it: withheld categories removed, findings kept."""
    import copy
    view = copy.deepcopy(evidence)
    if "readings" in withheld:
        for signal in view.get("signals", []):
            signal["observations"] = []
    if "checkin_history" in withheld:
        view["checkins"] = []
    if "notes" in withheld:
        for signal in view.get("signals", []):
            for row in signal.get("contexts", []):
                row.pop("explanation", None)
    view["sharing_withheld"] = sorted(withheld)
    return view
