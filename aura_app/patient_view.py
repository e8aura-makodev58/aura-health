"""Read-only presentation references. No drift, safety or anchor policy lives here."""

from .service import PatientEventService


class PatientViewService:
    def __init__(self, events: PatientEventService, *, wording_provider_id="disabled", wording_provider=None,
                 synthetic_only=False):
        self.events = events
        self.wording_provider_id = wording_provider_id
        self.wording_provider=wording_provider
        self.synthetic_only=synthetic_only

    def get(self, patient_id: str) -> dict:
        provider_id=self.wording_provider.model_id if self.wording_provider else self.wording_provider_id
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
                        if event["event_type"] == "MEDICATION_EVENT" and not event["payload"].get("reported_later")), None),
                    "wording_provider_id": provider_id,
                    "synthetic_only":self.synthetic_only,
                    "privacy_notice": (("Live AI wording is enabled for synthetic demo data only. Safety policy remains deterministic. "
                        "Individual messages may use fixed fallback. Institutional on-prem/private-cloud deployment is future intent, not validated readiness."
                        if not provider_id.startswith("disabled") else
                        "Fixed wording is active; a live model is not yet enabled. This demo accepts synthetic fixtures only.")
                        if self.synthetic_only else ("This patient app uses local fixed wording. No text is sent to a live model. "
                        "Live model use remains deferred until an explicit consent workflow is reviewed."
                        if provider_id == "disabled" else
                        "An explicitly injected developer provider is configured. This is not a consent-approved "
                        "patient deployment; use synthetic data only."))}
