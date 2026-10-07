"""Thin FastAPI transport; all orchestration lives in PatientEventService."""

from datetime import datetime, timezone
import os
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI
from fastapi.responses import FileResponse
from starlette.exceptions import HTTPException
from pydantic import BaseModel, Field

from aura_communication.domain import CommunicationPurpose
from aura_communication.provider import DisabledProvider
from .communication import PatientCommunicationService
from .models import AppError, ApplicationEvent, EventType
from .persistence import SQLiteRepositoryFactory
from .service import PatientEventService
from .patient_view import PatientViewService


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


class CommunicationIn(BaseModel):
    model_config = {"extra": "forbid"}
    purpose: CommunicationPurpose = CommunicationPurpose.AUTO
    client_offline: bool = False


def create_app(db_path: str | Path | None = None, service: PatientEventService | None = None,
               communication_service: PatientCommunicationService | None = None,
               *, docs_enabled: bool = False, synthetic_only: bool = False) -> FastAPI:
    if service is None:
        factory = SQLiteRepositoryFactory(db_path or os.environ.get("AURA_DEV_DB", "aura-m4-development.sqlite3"))
        factory.initialize()
        service = PatientEventService(factory)
    # M6 patient entry point remains local-only until live-model consent is governed.
    communication_service = communication_service or PatientCommunicationService(service, provider=DisabledProvider())
    view_service = PatientViewService(service, wording_provider_id=communication_service.provider.model_id,
                                     wording_provider=communication_service.provider, synthetic_only=synthetic_only)
    # CDN-backed Swagger conflicts with the patient UI's strict same-origin CSP.
    app = FastAPI(title="AURA prototype application API", version="milestone-7",
                  docs_url=None, redoc_url=None, openapi_url="/openapi.json" if docs_enabled else None)
    app.state.service = service
    app.state.communication_service = communication_service

    @app.middleware("http")
    async def presentation_headers(request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; connect-src 'self'; object-src 'none'; "
            "base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
        return response

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

    @app.post("/patients/{patient_id}/events/{event_id}/communication")
    def communicate(patient_id: str, event_id: str, body: CommunicationIn):
        return communication_service.render(patient_id, event_id, purpose=body.purpose,
                                            client_offline=body.client_offline)

    @app.get("/patients/{patient_id}/timeline")
    def timeline(patient_id: str):
        return service.timeline(patient_id)

    @app.get("/patients/{patient_id}/status")
    def status(patient_id: str):
        return service.status(patient_id)

    @app.get("/patients/{patient_id}/view")
    def patient_view(patient_id: str):
        return view_service.get(patient_id)

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

    ui = Path(__file__).resolve().parent.parent / "aura_ui"
    @app.get("/assets/{asset_name}", include_in_schema=False)
    def patient_asset(asset_name: str):
        if asset_name not in {"app.js", "styles.css", "settings.js"}:
            raise HTTPException(404)
        return FileResponse(ui / asset_name)

    @app.get("/", include_in_schema=False)
    def patient_application():
        return FileResponse(ui / "index.html", headers={"Cache-Control": "no-store"})

    return app


app = create_app()
