"""Explicit observable-only bridge into the accepted application/domain engines."""

from dataclasses import asdict
from datetime import date, datetime, time, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path

from aura_app.communication import PatientCommunicationService
from aura_app.models import ApplicationEvent, EventType
from aura_app.persistence import SQLiteRepositoryFactory
from aura_app.safety import FixtureSafetyGate
from aura_app.service import PatientEventService
from aura_communication.provider import DisabledProvider


MESSAGES = {"ORDINARY":"fixture ordinary message", "SAFETY_CONCERN":"fixture safety concern",
            "FIGURATIVE":"This deadline is killing me. I mean it is a busy day.",
            "GATE_TIMEOUT":"synthetic detector timeout fixture"}


def at(raw, hour=12):
    return datetime.combine(date.fromisoformat(raw),time(hour),tzinfo=timezone.utc)


def observable_events(timeline):
    """Construct allowlisted values field-by-field; never forward timeline dictionaries."""
    start = date.fromisoformat(timeline["start_date"])
    frames = []
    plan = timeline["plan"]
    def add(day, kind, payload, suffix, hour=12, fixture="NORMAL"):
        frames.append({"event_id":f"observable-{day}-{suffix}","event_type":kind,
                       "occurred_at":at((start+timedelta(days=day)).isoformat(),hour).isoformat(),
                       "payload":payload, "resolved_fixture":fixture})
    for raw in timeline["days"]:
        index = raw["index"]
        for ci, context in enumerate(timeline["contexts"]):
            if context["start_day"] == index:
                add(index,"CONTEXT_EVENT",{"start":at((start+timedelta(days=index)).isoformat(),0).isoformat(),
                    "end":at((start+timedelta(days=context["end_day"]+1)).isoformat(),0).isoformat(),
                    "category":context["category"],"affected_signals":list(context["affected_signals"]),
                    "source":"synthetic_patient","explanation":context["explanation"]},f"context-{ci}",0)
        if raw["sleep_start"] is not None:
            begin = datetime.fromisoformat(raw["sleep_start"])
            add(index,"WEARABLE_OBSERVATION",{"observations":[
                {"kind":"sleep","date":begin.date().isoformat(),"sleep_start":begin.isoformat(),
                 "sleep_end":(begin+timedelta(hours=raw["duration_hours"])).isoformat(),"coverage":raw["coverage"],"source":"synthetic_wearable"},
                {"kind":"activity","date":raw["date"],"metrics":{"steps":raw["activity_steps"]},"coverage":raw["coverage"],"source":"synthetic_wearable"},
                {"kind":"resting_hr","date":raw["date"],"value":raw["resting_hr"],"coverage":raw["coverage"],"source":"synthetic_wearable"}]},"wearable")
        if index == 13:
            for signal, metric in (("SLEEP_MIDPOINT",None),("SLEEP_DURATION",None),("ACTIVITY","steps"),("RESTING_HEART_RATE",None)):
                fields = {"signal":signal,"metric":metric,"source":"synthetic_wearable",
                          "reference_start":timeline["start_date"],"reference_end":raw["date"]}
                add(index,"ANCHOR_COMMAND",{**fields,"action":"CREATE_PROVISIONAL_ANCHOR"},f"anchor-{signal}")
                add(index,"ANCHOR_COMMAND",{**fields,"action":"TRUST_ANCHOR","reviewed_by":"explicit-synthetic-anchor-review"},f"trust-{signal}")
        explanation_day = plan.get("explanation_day")
        if explanation_day is None and plan["case"] == "D":
            explanation_day = 30
        if index == explanation_day:
            for ci, context in enumerate(timeline["contexts"]):
                if context["category"] == "BENIGN_CONTEXT" and context["start_day"] <= index:
                    add(index,"CONTEXT_EXPLANATION",{"context_event_id":f"observable-{context['start_day']}-context-{ci}",
                        "explanation":context["explanation"],"affected_signals":list(context["affected_signals"])},f"explanation-{ci}")
        add(index,"PATIENT_CHECKIN",{"state":raw["checkin"]},"checkin")
        fixtures = [message["fixture"] for message in plan["messages"] if message["day"] == index]
        if plan["case"] == "F" and index == len(timeline["days"])-1:
            fixtures.append("SAFETY_CONCERN")
        for mi, fixture in enumerate(fixtures):
            add(index,"PATIENT_FREE_TEXT",{"text":MESSAGES[fixture]},f"message-{mi}",18,fixture)
    return frames


def configuration_fingerprint():
    roots = [Path(__file__).resolve().parents[1]/name for name in ("aura_safety","aura_longitudinal","aura_communication")]
    files = sorted(file for root in roots for file in root.glob("*.json"))
    return sha256(b"".join(file.name.encode()+file.read_bytes() for file in files)).hexdigest()


def drive(frames, db):
    factory = SQLiteRepositoryFactory(db); factory.initialize()
    proposals = {frame["event_id"]: (("D3","CLARIFY"),) if frame["resolved_fixture"] == "SAFETY_CONCERN" else ()
                 for frame in frames if frame["resolved_fixture"] != "GATE_TIMEOUT"}
    events = PatientEventService(factory,safety_gate=FixtureSafetyGate(proposals))
    events.create_patient(patient_id="synthetic-replay",display_name="Synthetic replay",age=35,timezone_name="UTC",
                          created_at=datetime.fromisoformat(frames[0]["occurred_at"]),
                          consents=[{"consent_type":"WEARABLE","granted":True,"version":"synthetic-v1"}])
    trace = []
    for frame in frames:
        moment = datetime.fromisoformat(frame["occurred_at"])
        event = ApplicationEvent(frame["event_id"],"synthetic-replay",EventType(frame["event_type"]),moment,moment,
                                 "synthetic_wearable" if frame["event_type"] == "WEARABLE_OBSERVATION" else "synthetic_patient",
                                 frame["payload"],frame["event_id"],frame["event_id"])
        result = events.command_anchor(event) if event.event_type == EventType.ANCHOR_COMMAND else events.process(event)
        wording = PatientCommunicationService(events,provider=DisabledProvider(),clock=lambda:moment).render("synthetic-replay",event.event_id)
        # Replay contract: committed semantic states/actions/facts, not diagnostic
        # wall-clock timings or random surrogate review-item row identifiers.
        with factory.transaction() as repo:
            reviews = [{"source_ref":item["source_ref"],"summary":item["summary"],"status":item["status"],"share_status":item["share_status"]}
                       for item in repo.review_items("synthetic-replay")]
            reviews.sort(key=lambda item:item["source_ref"])
        trace.append({"event_id":event.event_id,"communication_decision":result.communication_decision,
                      "safety":result.safety,"longitudinal":result.longitudinal,"review_items":reviews,
                      "wording":{key:wording[key] for key in ("message","mode","static_template_id","input_assessed","pinned_resources","safety_reference","generation_used")}})
    return {"configuration_fingerprint":configuration_fingerprint(),"resource_version":"fixture-unverified-v1",
            "events":frames,"trace":trace}
