"""Restricted synthetic-only hosting. No real-data intake or production authentication.

Each browser receives a private synthetic workspace. A reset creates a new workspace
from a verified immutable baseline, not a safety downgrade in a patient's episode.
"""

import asyncio
from dataclasses import replace
from datetime import datetime
from http.cookies import SimpleCookie
from ipaddress import ip_address
import os
from pathlib import Path
import secrets
import shutil
from time import monotonic
from urllib.parse import urlsplit

from fastapi import Request
from fastapi.responses import JSONResponse

from .api import create_app
from .agent import AgentService
from .system_settings import SyntheticAgentProvider
from .communication import PatientCommunicationService
from .demo import DemoFixtureGate, demo_catalog, prepare
from .models import AppError, EventType
from .persistence import SQLiteRepositoryFactory
from .service import PatientEventService
from .system_settings import SystemSettings, SyntheticSettingsProvider, settings_api


class SyntheticOnlyService(PatientEventService):
    """Allowlisted demo inputs, not a safety detector or context-credibility classifier."""

    def __init__(self, factory, seed=7):
        self.allowed = frozenset(item["patient_id"] for item in demo_catalog(seed))
        super().__init__(factory, safety_gate=DemoFixtureGate(self.allowed))

    def _patient(self, repo, patient_id):
        if patient_id not in self.allowed:
            raise AppError("SYNTHETIC_ONLY", "Hosted demo accepts catalog fixtures only", 403)
        return super()._patient(repo, patient_id)

    def create_patient(self, **_kwargs):
        raise AppError("SYNTHETIC_ONLY", "No sign-up or real patient intake in this public demo", 403)

    def command_anchor(self, event):
        raise AppError("SYNTHETIC_ONLY", "Reviewer/anchor commands are not publicly enabled", 403)

    def process(self, event):
        with self.repositories.transaction() as repo:
            self._patient(repo, event.patient_id)
            rows = repo.events(event.patient_id)
            at = datetime.fromisoformat(rows[-1]["occurred_at"])
            contexts = {row["event_id"]: row["payload"] for row in rows if row["event_type"] == "CONTEXT_EVENT"}
        payload = event.payload
        permitted = False
        if event.event_type == EventType.PATIENT_CHECKIN:
            permitted = set(payload) == {"state"} and isinstance(payload["state"],str) and payload["state"] in {"Good", "Okay", "Rough"}
        elif event.event_type == EventType.PATIENT_FREE_TEXT:
            permitted = set(payload) == {"text"} and isinstance(payload["text"],str) and payload["text"] in {"fixture ordinary message", "fixture safety concern"}
        elif event.event_type == EventType.MEDICATION_EVENT:
            permitted = (set(payload) == {"status", "scheduled_time"}
                         and isinstance(payload["status"],str) and payload["status"] in {"ACKNOWLEDGED", "MISSED", "UNKNOWN"}
                         and payload["scheduled_time"] == at.isoformat())
        elif event.event_type == EventType.CONTEXT_EXPLANATION:
            context = contexts.get(payload.get("context_event_id"), {}) if isinstance(payload.get("context_event_id"),str) else {}
            permitted = (set(payload) <= {"context_event_id", "relevant_drift_ref", "explanation", "affected_signals"}
                         and payload.get("explanation") == "new stable work schedule"
                         and context.get("explanation") == payload.get("explanation")
                         and isinstance(payload.get("affected_signals"), list)
                         and all(isinstance(signal,str) for signal in payload["affected_signals"])
                         and bool(payload["affected_signals"])
                         and set(payload["affected_signals"]) <= set(context.get("affected_signals", []))
                         and payload.get("relevant_drift_ref") is None)
        elif event.event_type == EventType.REVIEW_COMMAND:
            permitted = payload == {"action":"ADD_QUESTION", "question":"fixture review question"}
        if not permitted:
            raise AppError("SYNTHETIC_ONLY", "Only the labelled synthetic inputs are accepted; do not enter real information", 403)
        # Never store client-controlled metadata as a covert free-text intake channel.
        from uuid import UUID
        try:
            identifiers = [str(UUID(value)) for value in (event.event_id, event.idempotency_key, event.correlation_id)]
        except (ValueError, AttributeError, TypeError) as exc:
            raise AppError("INVALID_EVENT", "Hosted event identifiers must be UUIDs") from exc
        return super().process(replace(event, event_id=identifiers[0], idempotency_key=identifiers[1],
                                       correlation_id=identifiers[2], occurred_at=at, source="synthetic_patient_ui"))


class HostedDemo:
    """One worker; session isolation is demo infrastructure, not authenticated care."""

    def __init__(self, root, *, seed=7, secure_cookie=True, max_sessions=16, ttl_seconds=3600,
                 settings=None, http_demo_hosts=()):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.seed, self.secure_cookie = seed, secure_cookie
        # Operator-selected private IP literals only. This is NOT authorization:
        # it permits an unencrypted synthetic cookie on a specific LAN address,
        # without disabling Secure cookies for the public HTTPS hostname.
        self.http_demo_hosts = frozenset(str(ip_address(host)) for host in http_demo_hosts)
        if any(not (ip_address(host).is_private or ip_address(host).is_loopback)
               or ip_address(host).is_unspecified for host in self.http_demo_hosts):
            raise ValueError("HTTP demo hosts must be explicit private or loopback IP addresses")
        self.max_sessions, self.ttl = max_sessions, ttl_seconds
        if max_sessions < 1 or ttl_seconds < 1:
            raise ValueError("invalid engineering session limits")
        self.baseline = self.root / "baseline.sqlite3"
        prepare(self.baseline, seed)
        self.sessions = {}
        self.lock = asyncio.Lock()
        self.settings = settings or SystemSettings(self.root / "system")
        self.system_app = settings_api(self.settings)
        # Presentation never needs a private workspace. Dispatch ONLY the shell
        # and allowlisted assets here; baseline patient routes are never exposed.
        self.presentation_app = create_app(
            service=SyntheticOnlyService(SQLiteRepositoryFactory(self.baseline), seed),
            synthetic_only=True)
        self.app = self  # ASGI entry point

    def _workspace(self, session):
        destination = self.root / f"session-{secrets.token_hex(16)}.sqlite3"
        shutil.copyfile(self.baseline, destination)
        factory = SQLiteRepositoryFactory(destination)
        factory.initialize()  # Additive agent trace table for pre-agent baselines.
        service = SyntheticOnlyService(factory, self.seed)
        app = create_app(service=service, communication_service=PatientCommunicationService(service, provider=SyntheticSettingsProvider(self.settings)),
                         agent_service=AgentService(service, provider=SyntheticAgentProvider(self.settings), synthetic_only=True),
                         synthetic_only=True)

        @app.get("/demo/scenarios")
        def scenarios():
            return {"synthetic_only": True, "hosted": True, "can_reset": True,
                    "scenarios": demo_catalog(self.seed),
                    "notice": "Private synthetic session. Only labelled fixtures are accepted; no real-data intake."}

        @app.post("/demo/reset")
        async def reset(request: Request):
            try:
                confirmation = await request.json()
            except ValueError:
                confirmation = None
            if confirmation != {"confirm": "RESET_SYNTHETIC_SESSION"}:
                return JSONResponse({"error":{"code":"INVALID_RESET","message":"Explicit synthetic-session confirmation required"}}, status_code=400)
            async with self.lock:
                record = self.sessions[session]
                if len(record["archives"]) >= 4:
                    return JSONResponse({"error":{"code":"DEMO_BUSY","message":"Session reset budget reached; try a new session later"}},status_code=429)
                new_app, new_path = self._workspace(session)
                record["app"], record["path"] = new_app, new_path
                # Old workspace is retained until session expiry. In-flight responses
                # cannot write the replacement. UI reload follows reset completion.
                record["archives"].append(destination)
            return {"reset":True, "synthetic_only":True, "seed":self.seed}

        return app, destination

    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    await send({"type":"lifespan.startup.complete"})
                elif message["type"] == "lifespan.shutdown":
                    await send({"type":"lifespan.shutdown.complete"}); return
        if scope["type"] != "http":
            return
        headers = {key.lower():value for key,value in scope["headers"]}
        secure_cookie = self.secure_cookie
        if secure_cookie and scope.get("scheme") == "http":
            try:
                authority = urlsplit("//" + headers.get(b"host", b"").decode("latin1"))
                host = str(ip_address(authority.hostname))
                if authority.username is None and authority.password is None and host in self.http_demo_hosts:
                    secure_cookie = False
            except (ValueError, TypeError):
                pass  # Malformed/non-IP hosts never weaken the public cookie.
        if scope["path"] == "/health":
            await JSONResponse({"status":"ok", "synthetic_only":True, "seed":self.seed})(scope, receive, send)
            return
        if scope["path"] in {"/", "/signals"} or scope["path"].startswith("/assets/"):
            await self.presentation_app(scope, receive, send)
            return
        if not (scope["path"].startswith("/patients") or
                scope["path"] in {"/demo/scenarios", "/demo/reset"} or
                scope["path"].startswith("/system/")):
            await JSONResponse({"detail":"Not Found"}, status_code=404)(scope, receive, send)
            return
        # No body/log inspection. Size is engineering containment, not clinical policy.
        chunks, size = [], 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            size += len(message.get("body", b""))
            if size > 8192:
                await JSONResponse({"error":{"code":"INVALID_EVENT","message":"Demo input is too large"}}, status_code=413)(scope, receive, send)
                return
            chunks.append(message.get("body", b""))
            if not message.get("more_body", False):
                break
        async def replay_receive():
            nonlocal chunks
            if chunks:
                body = b"".join(chunks); chunks = []
                return {"type":"http.request", "body":body, "more_body":False}
            return await receive()
        if scope["path"].startswith("/system/"):
            await self.system_app(scope,replay_receive,send)
            return
        cookie = SimpleCookie()
        try:
            cookie.load(headers.get(b"cookie",b"").decode("latin1"))
        except Exception:
            pass
        session = cookie["aura_demo"].value if "aura_demo" in cookie else None
        async with self.lock:
            now = monotonic()
            expired = [key for key, record in self.sessions.items() if now - record["touched"] > self.ttl]
            for key in expired:
                record = self.sessions.pop(key)
                # Explicit server-created paths only, never a glob or user-supplied directory.
                for file in [record["path"], *record["archives"]]:
                    file.unlink(missing_ok=True)
            fresh = session not in self.sessions
            if fresh:
                # Only the explicit bootstrap may allocate a workspace. A browser
                # rejecting its cookie must not create one per parallel API call.
                if scope["path"] != "/demo/scenarios" or scope["method"] != "GET":
                    await JSONResponse({"error":{"code":"DEMO_SESSION_REQUIRED",
                        "message":"Demo session cookie missing or expired. Reload the page and allow cookies. Secure-cookie hosting requires HTTPS; LAN HTTP requires the operator's explicit HTTP demo configuration."}},
                        status_code=409)(scope, replay_receive, send)
                    return
                if len(self.sessions) >= self.max_sessions:
                    await JSONResponse({"error":{"code":"DEMO_BUSY","message":"All private demo sessions are in use. Existing sessions are preserved; please retry later."}}, status_code=503, headers={"Retry-After":"60"})(scope, replay_receive, send)
                    return
                session = secrets.token_hex(32)
                app, db = self._workspace(session)
                self.sessions[session] = {"app":app,"path":db,"archives":[],"touched":now}
            record = self.sessions[session]
            record["touched"] = now
            app = record["app"]
        async def with_cookie(message):
            if fresh and message["type"] == "http.response.start":
                value = f"aura_demo={session}; Path=/; HttpOnly; SameSite=Strict; Max-Age={self.ttl}" + ("; Secure" if secure_cookie else "")
                message = {**message,"headers":[*message.get("headers",[]),(b"set-cookie",value.encode())]}
            await send(message)
        await app(scope, replay_receive, with_cookie)


def create_hosted_app():
    return HostedDemo(os.environ.get("AURA_DEMO_ROOT", "aura-demo-workspaces"),
                      secure_cookie=os.environ.get("AURA_SECURE_COOKIE", "true") == "true",
                      max_sessions=int(os.environ.get("AURA_MAX_DEMO_SESSIONS", "16")),
                      ttl_seconds=int(os.environ.get("AURA_DEMO_SESSION_TTL", "3600")),
                      http_demo_hosts=tuple(host.strip() for host in os.environ.get("AURA_HTTP_DEMO_HOSTS", "").split(",") if host.strip()))
