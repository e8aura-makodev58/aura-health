"""Thin FastAPI transport; all orchestration lives in PatientEventService."""

from datetime import datetime, timezone
import os
import re
from pathlib import Path
from typing import Literal
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
from .evidence import EvidenceViewService
from .agent import AgentService
from .assessment import AssessmentService
from aura_agent.roles import AgentRole
from .workflows import WorkflowService
from .companion import CompanionService


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


class AgentIn(BaseModel):
    model_config = {"extra": "forbid", "strict": True}
    run_id: str = Field(pattern=r"^(?:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|arrival-[0-9a-f]{64})$")
    query_id: str | None = None
    question: str | None = Field(default=None, min_length=1, max_length=2000)
    window_days: int = Field(default=56, ge=1, le=180)
    client_offline: bool = False
    asker: Literal["patient", "clinician"] = "patient"

class MedicationAskIn(BaseModel):
    model_config = {"extra": "forbid", "strict": True}
    run_id: str = Field(pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
    topic_id: str | None = None
    question: str | None = Field(default=None, min_length=1, max_length=500)

class MedicationUpdateTextIn(BaseModel):
    model_config = {"extra": "forbid", "strict": True}
    request_id: str = Field(pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
    text: str = Field(min_length=1, max_length=500)

class MedicationDayIn(BaseModel):
    model_config = {"extra": "forbid", "strict": True}
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    status: Literal["ACKNOWLEDGED", "MISSED", "UNKNOWN"]
    reason: str | None = None

class MedicationUpdateIn(BaseModel):
    model_config = {"extra": "forbid", "strict": True}
    request_id: str = Field(pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
    days: list[MedicationDayIn] = Field(min_length=1, max_length=14)

class SharingIn(BaseModel):
    model_config = {"extra": "forbid", "strict": True}
    notes: bool | None = None
    readings: bool | None = None
    checkin_history: bool | None = None
    activity_details: bool | None = None

class SuggestionChoiceIn(BaseModel):
    model_config = {"extra": "forbid", "strict": True}
    option_id: str = Field(min_length=1, max_length=40, pattern=r"^[a-z_]+$")

class WorkflowIn(BaseModel):
    model_config = {'extra':'forbid'}
    run_id: str = Field(pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
    data: dict = Field(default_factory=dict)


def create_app(db_path: str | Path | None = None, service: PatientEventService | None = None,
               communication_service: PatientCommunicationService | None = None,
               agent_service: AgentService | None = None,
               *, docs_enabled: bool = False, synthetic_only: bool = False) -> FastAPI:
    if service is None:
        factory = SQLiteRepositoryFactory(db_path or os.environ.get("AURA_DEV_DB", "aura-m4-development.sqlite3"))
        factory.initialize()
        service = PatientEventService(factory)
    # M6 patient entry point remains local-only until live-model consent is governed.
    communication_service = communication_service or PatientCommunicationService(service, provider=DisabledProvider())
    view_service = PatientViewService(service, wording_provider_id=communication_service.provider.model_id,
                                     wording_provider=communication_service.provider, synthetic_only=synthetic_only)
    evidence_service = EvidenceViewService(service)
    agent_service = agent_service or AgentService(service, synthetic_only=synthetic_only)
    companion_service = CompanionService(service, provider=agent_service.provider)
    # CDN-backed Swagger conflicts with the patient UI's strict same-origin CSP.
    app = FastAPI(title="AURA prototype application API", version="milestone-7",
                  docs_url=None, redoc_url=None, openapi_url="/openapi.json" if docs_enabled else None)
    app.state.service = service
    app.state.communication_service = communication_service
    app.state.agent_service = agent_service
    workflows = WorkflowService(service, agent_service.provider, synthetic_only=synthetic_only)
    app.state.workflow_service = workflows

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

    @app.get("/signals")
    def signals():
        return service.signals()

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
        if body.event_type == EventType.MEDICATION_EVENT and "reported_later" in body.payload:
            raise AppError("INVALID_EVENT", "Past days are updated through the medication update path")
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

    @app.get("/patients/{patient_id}/companion")
    def companion(patient_id: str):
        return companion_service.get(patient_id)

    from .activities import ActivityService
    activity_service = ActivityService(service, agent_service.provider)

    @app.post("/patients/{patient_id}/activities/extract")
    def activities_extract(patient_id: str):
        return activity_service.extract_pending(patient_id)

    @app.get("/patients/{patient_id}/activities")
    def activities_patient(patient_id: str):
        return activity_service.for_patient(patient_id)

    @app.get("/patients/{patient_id}/activities/summary")
    def activities_summary(patient_id: str):
        summary = activity_service.summary(patient_id)
        # Activity phrases reach the clinician only if the patient shares them.
        if "activity_details" not in sharing_service.withheld(patient_id):
            summary["details"] = activity_service.for_patient(patient_id)["items"]
        return summary

    @app.post("/patients/{patient_id}/companion/suggestions/personalize")
    def companion_personalize(patient_id: str):
        return companion_service.personalize(patient_id)

    @app.post("/patients/{patient_id}/companion/suggestions/choose")
    def companion_choose(patient_id: str, body: SuggestionChoiceIn):
        return companion_service.choose(patient_id, body.option_id)

    from .sharing import SharingService, filter_evidence
    sharing_service = SharingService(service, default_all=agent_service.sharing_default_all)

    @app.get("/patients/{patient_id}/evidence")
    def evidence_view(patient_id: str, viewer: Literal["patient", "clinician"] = "patient"):
        evidence = evidence_service.get(patient_id)
        return filter_evidence(evidence, sharing_service.withheld(patient_id)) if viewer == "clinician" else evidence

    @app.get("/patients/{patient_id}/sharing")
    def sharing_get(patient_id: str):
        return sharing_service.get(patient_id)

    @app.post("/patients/{patient_id}/sharing")
    def sharing_set(patient_id: str, body: SharingIn):
        return sharing_service.set(patient_id, {key: value for key, value in body.model_dump().items() if value is not None})

    @app.post("/patients/{patient_id}/agent/{role}")
    def agent_run(patient_id: str, role: AgentRole, body: AgentIn):
        return agent_service.execute(patient_id, role, **body.model_dump())

    from .medication_ask import MedicationAskService
    medication_service = MedicationAskService(service, agent_service.provider)

    @app.post("/patients/{patient_id}/medication/ask")
    def medication_ask(patient_id: str, body: MedicationAskIn):
        return medication_service.ask(patient_id, **body.model_dump())

    from .record_calendar import RecordCalendarService
    calendar_service = RecordCalendarService(service, sharing_service)
    from .medication_update import MedicationUpdateService
    medication_update = MedicationUpdateService(service, agent_service.provider, window=calendar_service.window_with_now)

    @app.get("/patients/{patient_id}/medication/update-window")
    def medication_update_window(patient_id: str):
        return calendar_service.update_window(patient_id)

    @app.post("/patients/{patient_id}/medication/update")
    def medication_update_save(patient_id: str, body: MedicationUpdateIn):
        return calendar_service.save(patient_id, request_id=body.request_id, days=[day.model_dump(exclude_none=True) for day in body.days])

    @app.get("/patients/{patient_id}/coverage")
    def record_coverage(patient_id: str):
        return calendar_service.coverage(patient_id)

    @app.get("/patients/{patient_id}/calendar")
    def record_calendar(patient_id: str, month: str | None = None, viewer: Literal["patient", "clinician"] = "patient"):
        return calendar_service.calendar(patient_id, month, viewer)

    @app.get("/patients/{patient_id}/calendar/{day}")
    def record_calendar_day(patient_id: str, day: str, viewer: Literal["patient", "clinician"] = "patient"):
        return calendar_service.day(patient_id, day, viewer)

    @app.post("/patients/{patient_id}/medication/update/interpret")
    def medication_update_interpret(patient_id: str, body: MedicationUpdateTextIn):
        return medication_update.interpret(patient_id, request_id=body.request_id, text=body.text)

    @app.get("/patients/{patient_id}/agent-runs/{run_id}")
    def agent_trace(patient_id: str, run_id: str):
        return agent_service.trace(patient_id, run_id)

    @app.get('/patients/{patient_id}/assessment/{role}')
    def arrival_assessment(patient_id: str, role: AgentRole, client_offline: bool = False):
        return AssessmentService(agent_service).get(patient_id, role, client_offline=client_offline)

    @app.post('/patients/{patient_id}/workflows/{action}')
    def workflow(patient_id: str, action: str, body: WorkflowIn):
        actions = {'manual':workflows.manual, 'import-proposal':workflows.import_proposal,
                   'import-confirm':workflows.confirm_import, 'context-proposal':workflows.propose_context,
                   'context-confirm':workflows.confirm_context, 'advance':workflows.advance}
        if action not in actions: raise AppError('INVALID_EVENT','Unknown workflow')
        try: return actions[action](patient_id,run_id=body.run_id,**body.data)
        except TypeError: raise AppError('INVALID_EVENT','Invalid workflow fields') from None

    @app.get('/patients/{patient_id}/workflow-runs/{run_id}')
    def workflow_trace(patient_id: str, run_id: str):
        return workflows.trace(patient_id,run_id)

    @app.get('/patients/{patient_id}/simulator-runs/{run_id}/replay')
    def simulator_replay(patient_id: str, run_id: str):
        return workflows.replay(patient_id,run_id)

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
        if asset_name == "plain_terms.json":
            return FileResponse(ui.parent / "aura_agent" / "plain_terms.json")
        if asset_name not in {"app.js", "styles.css", "settings.js", "evidence.js", "evidence.css", "agent.js", "features.js", "companion.js", "tour.js", "catchup.js"}:
            raise HTTPException(404)
        return FileResponse(ui / asset_name)

    media = ui / "media"
    media_types = {".svg": "image/svg+xml", ".png": "image/png", ".webp": "image/webp",
                   ".jpg": "image/jpeg", ".woff2": "font/woff2"}
    @app.get("/assets/media/{media_name}", include_in_schema=False)
    def ui_media(media_name: str):
        # Flat folder of static UI art and fonts; no subpaths, no other file types.
        suffix = Path(media_name).suffix.lower()
        path = media / media_name
        if (not re.fullmatch(r"[a-z0-9][a-z0-9_-]*\.[a-z0-9]+", media_name)
                or suffix not in media_types or not path.is_file()):
            raise HTTPException(404)
        return FileResponse(path, media_type=media_types[suffix])

    @app.get("/", include_in_schema=False)
    def patient_application():
        return FileResponse(ui / "index.html", headers={"Cache-Control": "no-store"})

    return app


app = create_app()
