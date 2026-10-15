"""Patient-reported activities: extraction from safety-cleared notes, patient detail, clinician aggregates.

Extraction runs only in the normal safety state, on notes that passed the safety gate and were
not held. Each processed note gets one PATIENT_ACTIVITY timeline row (possibly empty), so a note
is never sent to the model twice. Clinician-facing output carries aggregates only.
"""
from datetime import date, datetime, timedelta

from aura_agent.activities import LABELS, extract, summarize
from aura_agent.guard import blocked_reason
from .models import AppError


class ActivityService:
    def __init__(self, events, provider=None, clock=None):
        self.events, self.provider = events, provider
        self.clock = clock or (lambda: datetime.now(__import__("datetime").timezone.utc))

    def _live(self):
        return bool(self.provider is not None and getattr(self.provider, "live", False))

    def _state(self, repo, patient_id):
        self.events._patient(repo, patient_id)
        rows = repo.events(patient_id)
        assessed = {ref["event_id"] for ref in repo.safety_references(patient_id)
                    if not ref["state"]["degraded"] and ref["outcome"] not in {"DEFER_EVENT", "REJECT_EVENT", "SET_DEGRADED"}}
        notes = [row for row in rows if row["event_type"] == "PATIENT_FREE_TEXT" and row["event_id"] in assessed
                 and row["source"] != "patient_medication_update"
                 and not row["longitudinal_deferred"] and isinstance(row["payload"].get("text"), str)
                 and not row["payload"]["text"].startswith("fixture ")]
        stored = [row for row in repo.timeline(patient_id) if row["record_type"] == "PATIENT_ACTIVITY"]
        end = max((datetime.fromisoformat(row["occurred_at"]) for row in rows), default=None)
        held = any(row["longitudinal_deferred"] for row in rows)
        normal = blocked_reason(repo.safety_state(patient_id), self.events.resource_registry, self.clock(), held=held) is None
        return notes, stored, end, normal

    def extract_pending(self, patient_id, limit=5):
        """Tag activities in up to `limit` cleared notes not yet processed. Returns how many were processed."""
        with self.events.repositories.transaction() as repo:
            notes, stored, _end, normal = self._state(repo, patient_id)
        if not normal or not self._live():
            return {"processed": 0}
        done = {row["detail"].get("note_event_id") for row in stored}
        pending = [row for row in notes if row["event_id"] not in done][-limit:]
        results = []
        for note in pending:
            try:
                items = extract(self.provider, note["payload"]["text"][:600])
            except Exception:
                continue  # leave unprocessed; a later call may succeed
            results.append((note, items))
        with self.events.repositories.transaction() as repo:
            already = {row["detail"].get("note_event_id") for row in repo.timeline(patient_id) if row["record_type"] == "PATIENT_ACTIVITY"}
            for note, items in results:
                if note["event_id"] in already:
                    continue
                repo.append_timeline({"patient_id": patient_id, "event_id": note["event_id"], "record_type": "PATIENT_ACTIVITY",
                                      "occurred_at": note["occurred_at"], "detail": {"note_event_id": note["event_id"], "items": items}})
        return {"processed": len(results)}

    def _rows(self, repo, patient_id):
        notes, stored, end, normal = self._state(repo, patient_id)
        cleared = {row["event_id"] for row in notes}
        rows = [{"at": row["occurred_at"], "items": row["detail"]["items"]} for row in stored
                if row["detail"].get("note_event_id") in cleared]
        return rows, end, normal

    def for_patient(self, patient_id, days=14):
        """Detail for the patient: what they mentioned, in their own words."""
        with self.events.repositories.transaction() as repo:
            rows, end, normal = self._rows(repo, patient_id)
        if not normal or end is None:
            return {"available": False, "items": []}
        start = end.date() - timedelta(days=days - 1)
        items = [{"at": row["at"][:10], **item, "labels": [LABELS[c] for c in item["categories"]]}
                 for row in rows if date.fromisoformat(row["at"][:10]) >= start for item in row["items"]]
        return {"available": True, "items": list(reversed(items))}

    def summary(self, patient_id):
        """Aggregates for the clinician: days mentioned and stated time per category, no phrases."""
        with self.events.repositories.transaction() as repo:
            rows, end, _normal = self._rows(repo, patient_id)
        if end is None:
            raise AppError("INVALID_EVENT", "No record yet")
        return summarize(rows, end.date())
