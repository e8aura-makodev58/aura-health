"""Thin FastAPI transport; all orchestration lives in PatientEventService."""

from datetime import datetime, timezone
import os
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .models import AppError, ApplicationEvent, EventType
from .persistence import SQLiteRepositoryFactory
from .service import PatientEventService


class PatientIn(BaseModel):
    patient_id: str
    display_name: str
    age: int
    timezone: str = "UTC"
    onboarding_status: str = "PROTOTYPE"
    treatment: dict = Field(default_factory=dict)
    consents: list[dict] = Field(default_factory=list)
    wearable_sources: list[dict] = Field(default_factory=list)


class EventIn(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: EventType
    occurred_at: datetime
    source: str
    payload: dict
    correlation_id: str = Field(default_factory=lambda: str(uuid4()))
    idempotency_key: str


class ExplanationIn(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime
    context_event_id: str
    relevant_drift_ref: str | None = None
    explanation: str
    affected_signals: list[str]
    idempotency_key: str
    correlation_id: str = Field(default_factory=lambda: str(uuid4()))


class AnchorIn(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime
    signal: str
    source: str
    metric: str | None = None
    reference_start: str | None = None
    reference_end: str | None = None
    reviewed_by: str | None = None
    idempotency_key: str
    correlation_id: str = Field(default_factory=lambda: str(uuid4()))


def create_app(db_path: str | Path | None = None, service: PatientEventService | None = None) -> FastAPI:
    if service is None:
        factory = SQLiteRepositoryFactory(db_path or os.environ.get("AURA_DEV_DB", "aura-m4-development.sqlite3"))
        factory.initialize()
        service = PatientEventService(factory)
    app = FastAPI(title="AURA prototype application API", version="milestone-4")
    app.state.service = service

    @app.exception_handler(AppError)
    async def app_error(_request, exc: AppError):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=exc.status, content={"error": {"code": exc.code, "message": str(exc)}})

    @app.get("/health")
    def health():
        return {"status": "ok", "prototype": True}

    @app.post("/patients")
    def create_patient(body: PatientIn):
        return service.create_patient(patient_id=body.patient_id, display_name=body.display_name,
                                      age=body.age, timezone_name=body.timezone,
                                      onboarding_status=body.onboarding_status,
                                      treatment=body.treatment, consents=body.consents,
                                      wearable_sources=body.wearable_sources)

    @app.get("/patients/{patient_id}")
    def get_patient(patient_id: str):
        return service.get_patient(patient_id)

    def envelope(patient_id: str, body: EventIn) -> ApplicationEvent:
        return ApplicationEvent(body.event_id, patient_id, body.event_type, body.occurred_at,
                                datetime.now(timezone.utc), body.source, body.payload,
                                body.correlation_id, body.idempotency_key)

    @app.post("/patients/{patient_id}/events")
    def ingest(patient_id: str, body: EventIn):
        return service.process(envelope(patient_id, body))

    @app.get("/patients/{patient_id}/timeline")
    def timeline(patient_id: str):
        return service.timeline(patient_id)

    @app.get("/patients/{patient_id}/status")
    def status(patient_id: str):
        return service.status(patient_id)

    @app.post("/patients/{patient_id}/context-explanations")
    def explain(patient_id: str, body: ExplanationIn):
        event = ApplicationEvent(body.event_id, patient_id, EventType.CONTEXT_EXPLANATION,
                                 body.occurred_at, datetime.now(timezone.utc), "patient",
                                 {"context_event_id": body.context_event_id,
                                  "relevant_drift_ref": body.relevant_drift_ref,
                                  "explanation": body.explanation,
                                  "affected_signals": body.affected_signals},
                                 body.correlation_id, body.idempotency_key)
        return service.process(event)

    @app.get("/patients/{patient_id}/review-snapshot")
    def review_snapshot(patient_id: str):
        return service.review_snapshot(patient_id)

    def anchor(patient_id: str, body: AnchorIn, action: str):
        event = ApplicationEvent(body.event_id, patient_id, EventType.ANCHOR_COMMAND,
                                 body.occurred_at, datetime.now(timezone.utc), "governed_command",
                                 {"action": action, "signal": body.signal, "source": body.source,
                                  "metric": body.metric, "reference_start": body.reference_start,
                                  "reference_end": body.reference_end,
                                  "reviewed_by": body.reviewed_by},
                                 body.correlation_id, body.idempotency_key)
        return service.command_anchor(event)

    @app.post("/patients/{patient_id}/anchors/provisional")
    def create_anchor(patient_id: str, body: AnchorIn):
        return anchor(patient_id, body, "CREATE_PROVISIONAL_ANCHOR")

    @app.post("/patients/{patient_id}/anchors/trust")
    def trust_anchor(patient_id: str, body: AnchorIn):
        return anchor(patient_id, body, "TRUST_ANCHOR")

    @app.post("/patients/{patient_id}/anchors/reanchor")
    def reanchor(patient_id: str, body: AnchorIn):
        return anchor(patient_id, body, "CLINICAL_REVIEW_REANCHOR")

    return app


app = create_app()
