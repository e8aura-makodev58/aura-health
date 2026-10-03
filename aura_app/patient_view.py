"""Read-only presentation references. No drift, safety or anchor policy lives here."""

from .service import PatientEventService


class PatientViewService:
    def __init__(self, events: PatientEventService, *, wording_provider_id="disabled"):
        self.events = events
        self.wording_provider_id = wording_provider_id

    def get(self, patient_id: str) -> dict:
        with self.events.repositories.transaction() as repo:
            patient = self.events._patient(repo, patient_id)
            events = repo.events(patient_id)
            latest = events[-1] if events else None
            result = repo.prior_result(patient_id, latest["idempotency_key"]) if latest else None
            projection = result["longitudinal"] if result else {}
            # Only an existing explicitly linked benign context can be offered for a hold.
            # The production context/hold engine still validates each submitted command.
            contexts = [event for event in events if event["event_type"] == "CONTEXT_EVENT"
                        and not event["longitudinal_deferred"]
                        and event["payload"].get("category") == "BENIGN_CONTEXT"]
            return {"patient": patient, "latest_event_id": latest["event_id"] if latest else None,
                    "latest_occurred_at": latest["occurred_at"] if latest else None,
                    "decision_reason": projection.get("reason"),
                    "active_context": projection.get("active_contexts", []),
                    "explanation_options": [{"context_event_id": event["event_id"],
                        "affected_signals": event["payload"]["affected_signals"],
                        "explanation": event["payload"].get("explanation"),
                        "start": event["payload"]["start"], "end": event["payload"].get("end")}
                        for event in contexts],
                    "latest_medication": next((event["payload"] for event in reversed(events)
                        if event["event_type"] == "MEDICATION_EVENT"), None),
                    "wording_provider_id": self.wording_provider_id,
                    "privacy_notice": ("This patient app uses local fixed wording. No text is sent to a live model. "
                        "Live model use remains deferred until an explicit consent workflow is reviewed."
                        if self.wording_provider_id == "disabled" else
                        "An explicitly injected developer provider is configured. This is not a consent-approved "
                        "patient deployment; use synthetic data only.")}
