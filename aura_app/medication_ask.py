"""Patient medication questions: safety first, curated answers only, honest abstention.

The model may only choose which approved topic a typed question is about. Every answer is
curated text from aura_agent/medication_info.json or a fixed abstention line.
"""

from datetime import datetime, timezone
from uuid import NAMESPACE_URL, uuid5

from aura_agent import medication
from aura_agent.guard import blocked_reason
from .models import AppError, ApplicationEvent, EventType


class MedicationAskService:
    def __init__(self, events, provider, *, clock=None):
        self.events, self.provider = events, provider
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def _treatment(self, patient_id):
        with self.events.repositories.transaction() as repo:
            patient = self.events._patient(repo, patient_id)
            rows = repo.events(patient_id)
        treatment = (patient or {}).get("treatment") or {}
        at = datetime.fromisoformat(rows[-1]["occurred_at"]) if rows else self.clock()
        return treatment.get("medication_name"), treatment.get("medication_schedule"), at

    def _blocked(self, patient_id):
        with self.events.repositories.transaction() as repo:
            state = repo.safety_state(patient_id)
        return blocked_reason(state, self.events.resource_registry, self.clock())

    def ask(self, patient_id, *, run_id, topic_id=None, question=None):
        if (topic_id is None) == (question is None):
            raise AppError("INVALID_MEDICATION_QUESTION", "Choose a topic or type one question")
        if topic_id is not None and topic_id not in medication.TOPIC_IDS:
            raise AppError("INVALID_MEDICATION_QUESTION", "Unknown medication topic")
        if question is not None and (not isinstance(question, str) or not 1 <= len(question.strip()) <= 500):
            raise AppError("INVALID_MEDICATION_QUESTION", "Ask one short question")
        name, schedule, at = self._treatment(patient_id)
        trace = []
        if question is not None:
            # A typed question is the patient's own words: safety-assess it first, like any patient text.
            event_id = str(uuid5(NAMESPACE_URL, f"aura-medication-question:{patient_id}:{run_id}"))
            self.events.process(ApplicationEvent(event_id, patient_id, EventType.PATIENT_FREE_TEXT, at, self.clock(),
                                                 "synthetic_patient_ui", {"text": question}, event_id, event_id))
            trace.append({"step": "safety_check", "result": "assessed"})
        reason = self._blocked(patient_id)
        if reason:
            trace.append({"step": "safety_state", "result": "blocked"})
            return {"status": "BLOCKED", "topic_id": None, "answer": "", "source_label": None, "trace": trace}
        source = medication.INFO["source_label"]
        if not name or not medication.lookup(name)["known"]:
            trace.append({"step": "medication", "result": "not_identified"})
            return {"status": "ABSTAINED", "topic_id": None, "answer": medication.ABSTAIN_MEDICATION,
                    "source_label": source, "trace": trace}
        if topic_id is not None:
            trace.append({"step": "topic", "method": "chosen", "result": topic_id})
            return {"status": "ANSWERED", "topic_id": topic_id, "answer": medication.answer(name, topic_id, schedule),
                    "source_label": source, "trace": trace}
        kind, chosen = medication.match_topic(question, name)
        method = "keywords"
        if kind is None and getattr(self.provider, "live", False):
            method = "model"
            try:
                kind, chosen = medication.classify(self.provider, question, name)
            except Exception:
                kind, chosen = None, None
                trace.append({"step": "topic", "method": "model", "result": "unavailable"})
        trace.append({"step": "topic", "method": method, "result": chosen or kind or "none"})
        if kind == "topic":
            return {"status": "ANSWERED", "topic_id": chosen, "answer": medication.answer(name, chosen, schedule),
                    "source_label": source, "trace": trace}
        answer = {"advice_request": medication.ADVICE_REQUEST,
                  "other_medication": medication.ABSTAIN_MEDICATION}.get(kind, medication.ABSTAIN_TOPIC)
        return {"status": "ABSTAINED", "topic_id": None, "answer": answer, "source_label": source, "trace": trace}
