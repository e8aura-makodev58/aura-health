"""Demo operator configuration, separate from patient records and domain policy."""

from collections import deque
from copy import deepcopy
import json
import os
from pathlib import Path
import re
import secrets
from tempfile import NamedTemporaryFile
from threading import RLock
from time import monotonic
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from aura_communication.config import load_config
from aura_communication.provider import ProviderUnavailable
from aura_communication.vendor import PROVIDERS, VendorProvider
from .models import AppError


class SystemSettings:
    """Single-worker development store: atomic owner-only files, write-only keys."""

    def __init__(self, root, *, transport=None, calls_per_minute=10, calls_per_hour=60):
        self.root=Path(root).resolve(); self.root.mkdir(parents=True,exist_ok=True,mode=0o700)
        os.chmod(self.root,0o700)
        self.lock=RLock(); self.transport=transport
        self.config=load_config(); self.calls=deque(); self.minute=calls_per_minute; self.hour=calls_per_hour
        self.auth_attempts=deque()
        self.token_path=self.root/"admin.token"
        if not self.token_path.exists():
            with open(self.token_path,"x",opener=lambda path,flags:os.open(path,flags,0o600)) as file:
                file.write(secrets.token_urlsafe(32))
        os.chmod(self.token_path,0o600)
        self._admin=self.token_path.read_text().strip()
        if len(self._admin)<32: raise ValueError("Invalid operator token file")
        self.state=self._load("provider-settings.json",{"provider":"openrouter","enabled":False,
            "revision":secrets.token_hex(16),"models":{key:{"model":"","variant":next(iter(value["endpoints"]))}
            for key,value in PROVIDERS.items()}})
        self.keys=self._load("provider-credentials.json",{})

    def _load(self,name,default):
        path=self.root/name
        if not path.exists(): return default
        os.chmod(path,0o600)
        return json.loads(path.read_text())

    def _write(self,name,value):
        # The rename commits only the complete file; no keys enter application/audit DBs.
        temporary=None
        try:
            with NamedTemporaryFile(mode="w",dir=self.root,delete=False) as file:
                temporary=Path(file.name); os.chmod(temporary,0o600)
                json.dump(value,file); file.flush(); os.fsync(file.fileno())
            os.replace(temporary,self.root/name)
        finally:
            if temporary and temporary.exists(): temporary.unlink()

    def _provider(self,value):
        if not isinstance(value,str) or value not in PROVIDERS:
            raise AppError("INVALID_SETTINGS","Select a supported provider")
        return value

    def _exact(self,body,fields):
        if not isinstance(body,dict) or set(body)!=set(fields):
            raise AppError("INVALID_SETTINGS","Invalid settings fields")

    def authorize(self,request):
        # Require browser same-origin HTTPS, or local loopback for an SSH-forwarded UI.
        origin=urlsplit(request.headers.get("origin","")); target=urlsplit(str(request.url))
        secure=origin.scheme=="https" or (origin.scheme=="http" and origin.hostname in {"127.0.0.1","localhost","::1"})
        if not secure or origin.netloc!=target.netloc:
            raise AppError("ADMIN_TRANSPORT_REQUIRED","Use HTTPS or a localhost SSH tunnel for system settings",403)
        with self.lock:
            now=monotonic()
            while self.auth_attempts and now-self.auth_attempts[0]>60: self.auth_attempts.popleft()
            supplied=request.headers.get("authorization","")
            valid=secrets.compare_digest(supplied.encode(),("Bearer "+self._admin).encode())
            if not valid:
                if len(self.auth_attempts)>=20: raise AppError("ADMIN_RATE_LIMIT","Too many unlock attempts; try later",429)
                self.auth_attempts.append(now)
                raise AppError("ADMIN_REQUIRED","System administrator unlock required",401)

    def snapshot(self):
        with self.lock:
            return {**deepcopy(self.state),"synthetic_only":True,
                "providers":[{"id":key,"label":value["label"],"credential_configured":bool(self.keys.get(key)),
                              "variants":list(value["endpoints"])} for key,value in PROVIDERS.items()]}

    def public_status(self):
        with self.lock:
            key=self.state["provider"]; model=self.state["models"][key]["model"]
            return {"synthetic_only":True,"live_enabled":bool(self.state["enabled"] and self.keys.get(key) and model),
                    "provider":PROVIDERS[key]["label"],"model":model,
                    "institutional_deployment":"Future intent: institution-managed on-premises or private-cloud model; not validated deployment."}

    def credential(self,body):
        self._exact(body,{"provider","api_key"}); provider=self._provider(body["provider"])
        key=body["api_key"]
        if not isinstance(key,str) or not 8<=len(key)<=1000 or any(ord(ch)<33 or ord(ch)>126 for ch in key):
            raise AppError("INVALID_SETTINGS","Enter a valid API key")
        with self.lock:
            keys={**self.keys,provider:key}; self._write("provider-credentials.json",keys); self.keys=keys
            self._revise()
            return self.snapshot()

    def remove(self,body):
        self._exact(body,{"provider"}); provider=self._provider(body["provider"])
        with self.lock:
            keys={key:value for key,value in self.keys.items() if key!=provider}
            self._write("provider-credentials.json",keys); self.keys=keys; self._revise()
            return self.snapshot()

    def _revise(self,**changes):
        state={**self.state,**changes,"revision":secrets.token_hex(16)}
        self._write("provider-settings.json",state); self.state=state

    def update(self,body):
        self._exact(body,{"provider","model","variant","enabled"}); key=self._provider(body["provider"])
        model=body["model"]; variant=body["variant"]
        if not isinstance(model,str) or not re.fullmatch(r"[A-Za-z0-9_.:/~@+-]{1,160}",model):
            raise AppError("INVALID_SETTINGS","Enter the provider's text-model ID")
        if not isinstance(variant,str) or variant not in PROVIDERS[key]["endpoints"] or type(body["enabled"]) is not bool:
            raise AppError("INVALID_SETTINGS","Select a valid endpoint and enablement option")
        with self.lock:
            if body["enabled"] and not self.keys.get(key): raise AppError("INVALID_SETTINGS","Save an API key before enabling live wording")
            models={**self.state["models"],key:{"model":model,"variant":variant}}
            self._revise(provider=key,models=models,enabled=body["enabled"])
            return self.snapshot()

    def _options(self,provider=None):
        key=provider or self.state["provider"]; entry=self.state["models"][key]
        return key,entry["model"],self.keys.get(key,""),entry["variant"],self.state["revision"]

    def reserve(self):
        with self.lock:
            now=monotonic()
            while self.calls and now-self.calls[0]>3600: self.calls.popleft()
            if len(self.calls)>=self.hour:
                raise ProviderUnavailable("Synthetic demo call budget reached", kind="demo_budget_hour")
            if sum(now-at<60 for at in self.calls)>=self.minute:
                raise ProviderUnavailable("Synthetic demo call budget reached", kind="demo_budget_minute")
            self.calls.append(now)

    def discover(self,body):
        self._exact(body,{"provider","variant"}); key=self._provider(body["provider"])
        variant=body["variant"]
        if not isinstance(variant,str) or variant not in PROVIDERS[key]["endpoints"]:
            raise AppError("INVALID_SETTINGS","Select a valid endpoint")
        with self.lock: options=self._options(key)
        if not options[2]: raise AppError("INVALID_SETTINGS","Save a key before refreshing models")
        try:
            self.reserve()
            models=VendorProvider(*options[:3],variant=variant,transport=self.transport).models()
            return {"models":models,"status":"READY"}
        except Exception:
            return {"models":[],"status":"UNAVAILABLE","message":"Discovery unavailable; enter an exact model ID from your provider console."}

    def connection_test(self,body):
        self._exact(body,{"confirm"})
        if body["confirm"]!="SYNTHETIC_TEST_MAY_COST": raise AppError("INVALID_SETTINGS","Confirm the small paid synthetic test")
        with self.lock: options=self._options()
        if not options[1] or not options[2]: raise AppError("INVALID_SETTINGS","Save a model and key first")
        candidate={"candidate_id":"synthetic-test","message":"Synthetic connection check.",
                   "acknowledged_facts":[],"question_intent":None,"cta_type":None}
        try:
            self.reserve()
            output=VendorProvider(*options[:3],variant=options[3],transport=self.transport).generate({
                "instructions":"Select this synthetic candidate; no real patient data.","request":{"candidates":[candidate]}})
            return {"status":"PASS" if output==candidate else "INVALID_OUTPUT","synthetic_only":True}
        except Exception:
            return {"status":"UNAVAILABLE","message":"Connection failed or timed out. Check key, model access and endpoint in your provider console.","synthetic_only":True}


class SyntheticSettingsProvider:
    """Only injected into the allowlisted hosted fixture service, never the ordinary API."""
    def __init__(self,settings): self.settings=settings

    @property
    def model_id(self):
        with self.settings.lock:
            key,model,secret,_variant,revision=self.settings._options()
            return f"{key}:{model}@{revision}" if self.settings.state["enabled"] and secret and model else f"disabled@{revision}"

    def generate(self,contract):
        with self.settings.lock:
            if not self.settings.state["enabled"]: raise ProviderUnavailable("Live demo wording disabled", kind="disabled")
            options=self.settings._options()
        if not options[1] or not options[2]: raise ProviderUnavailable("Provider unconfigured", kind="unconfigured")
        self.settings.reserve()
        return VendorProvider(*options[:3],variant=options[3],config=self.settings.config,transport=self.settings.transport).generate(contract)


class SyntheticAgentProvider(SyntheticSettingsProvider):
    """Native read-only agent calls share existing synthetic-only budgets/keys."""
    live = True

    def __init__(self, settings, *, config=None):
        super().__init__(settings)
        from aura_agent.runtime import load_config as agent_config
        self.agent_config = config or agent_config()

    def step(self, messages, tools):
        with self.settings.lock:
            if not self.settings.state["enabled"]:
                raise ProviderUnavailable("Live synthetic assistant disabled", kind="disabled")
            options = self.settings._options()
        if not options[1] or not options[2]:
            raise ProviderUnavailable("Provider unconfigured", kind="unconfigured")
        self.settings.reserve()
        from dataclasses import replace
        config = replace(self.settings.config, provider_timeout_seconds=self.agent_config.provider_timeout_seconds)
        return VendorProvider(*options[:3], variant=options[3], config=config,
                              transport=self.settings.transport).agent_step(messages, tools)


def settings_api(settings):
    app=FastAPI(docs_url=None,redoc_url=None,openapi_url=None)

    @app.middleware("http")
    async def private_headers(request,call_next):
        response=await call_next(request); response.headers["Cache-Control"]="no-store"
        response.headers["X-Content-Type-Options"]="nosniff"; return response

    @app.exception_handler(AppError)
    async def error(_request,exc):
        return JSONResponse({"error":{"code":exc.code,"message":str(exc)}},status_code=exc.status)

    @app.get("/system/status")
    def status(): return settings.public_status()

    def read(body):
        settings._exact(body,{})
        return settings.snapshot()

    actions={"read":read,
             "credential":settings.credential,"remove-key":settings.remove,"save":settings.update,
             "models":settings.discover,"test":settings.connection_test}

    @app.post("/system/settings/{action}")
    async def command(action:str,request:Request):
        settings.authorize(request)
        if action not in actions: raise AppError("INVALID_SETTINGS","Unknown settings command",404)
        try: body=await request.json()
        except ValueError: raise AppError("INVALID_SETTINGS","Invalid settings JSON") from None
        # Network operations run off the event loop; patient requests continue during tests.
        from starlette.concurrency import run_in_threadpool
        try: return await run_in_threadpool(actions[action],body)
        except AppError: raise
        except Exception: raise AppError("SETTINGS_UNAVAILABLE","System settings could not be saved",503) from None
    return app
