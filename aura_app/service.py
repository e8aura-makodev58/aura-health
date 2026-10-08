"""Transactional application orchestration; domain decisions stay in accepted engines."""

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from aura_safety import Event as SafetyEvent, EventKind, Mode, SafetyEngine, SafetyState
from aura_safety.codec import state_from_dict, state_to_dict
from aura_safety.domain import Outcome
from aura_safety.engine import POLICY_VERSION
from aura_safety.output import output_plan
from aura_safety.resources import ResourceRegistry
from aura_longitudinal.registry import SignalRegistry, load_registry

from .longitudinal import LongitudinalProjector, Projection, key_from, points_from_payload
from .models import AppError, ApplicationEvent, ApplicationResult, EventType
from .repositories import RepositoryConflict, RepositoryFactory, UnitOfWork
from .safety import ResolvedSafetyGate, SafetyGateUnavailable, UnconfiguredSafetyGate


SAFETY_INPUTS = frozenset({
    EventType.PATIENT_FREE_TEXT, EventType.STRUCTURED_ASSESSMENT_RESPONSE,
    EventType.CONTEXT_EXPLANATION, EventType.PATIENT_CHECKIN,
    EventType.MEDICATION_EVENT,
})


def requires_safety_gate(event: ApplicationEvent) -> bool:
    return (event.event_type in SAFETY_INPUTS
            or (event.event_type == EventType.CONTEXT_EVENT and bool(event.payload.get("explanation")))
            or (event.event_type == EventType.REVIEW_COMMAND and bool(event.payload.get("question"))))


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        raise AppError("INVALID_EVENT", "timestamps must include a timezone")
    return value.isoformat()


def _event_row(event: ApplicationEvent) -> dict:
    return {"event_id": event.event_id, "patient_id": event.patient_id,
            "event_type": event.event_type.value, "occurred_at": _iso(event.occurred_at),
            "received_at": _iso(event.received_at), "source": event.source,
            "payload": event.payload, "correlation_id": event.correlation_id,
            "idempotency_key": event.idempotency_key}


class PatientEventService:
    def __init__(self, repositories: RepositoryFactory, *,
                 safety_gate: ResolvedSafetyGate | None = None,
                 safety_engine: SafetyEngine | None = None,
                 resource_registry: ResourceRegistry | None = None,
                 signal_registry: SignalRegistry | None = None):
        self.repositories = repositories
        self.safety_gate = safety_gate or UnconfiguredSafetyGate()
        self.safety_engine = safety_engine or SafetyEngine()
        self.resource_registry = resource_registry or ResourceRegistry()
        self.signal_registry = signal_registry or load_registry()

    def signals(self) -> dict:
        return self.signal_registry.public()

    def create_patient(self, *, patient_id: str, display_name: str, age: int,
                       timezone_name: str, onboarding_status: str = "PROTOTYPE",
                       treatment: dict | None = None, consents: list[dict] | None = None,
                       wearable_sources: list[dict] | None = None,
                       created_at: datetime | None = None) -> dict:
        if not 25 <= age <= 60:
            raise AppError("INVALID_EVENT", "prototype is limited to ages 25–60")
        if not patient_id or not display_name or not timezone_name:
            raise AppError("INVALID_EVENT", "patient ID, alias, and timezone are required")
        if treatment and treatment.get("treatment_notes"):
            raise AppError("INVALID_EVENT", "free-text treatment notes require the safety-gated event path")
        allowed_treatment = {"medication_name", "medication_schedule", "regimen_start", "stable_since",
                             "treating_clinician_ref", "review_cadence", "next_review", "treatment_notes"}
        if treatment and set(treatment) - allowed_treatment:
            raise AppError("INVALID_EVENT", "unsupported treatment context field")
        at = _iso(created_at or datetime.now(timezone.utc))
        row = {"patient_id": patient_id, "display_name": display_name, "age": age,
               "timezone": timezone_name, "onboarding_status": onboarding_status,
               "created_at": at, "active": True, "treatment": treatment or {}}
        try:
            with self.repositories.transaction() as repo:
                repo.create_patient(row)
                repo.save_treatment({"patient_id": patient_id, **(treatment or {})})
                for consent in consents or []:
                    repo.save_consent({"patient_id": patient_id,
                                       "consent_type": consent["consent_type"],
                                       "granted": bool(consent["granted"]),
                                       "timestamp": at, "version": consent.get("version", "prototype-v1")})
                for source in wearable_sources or []:
                    repo.save_wearable_source({"patient_id": patient_id, "source_id": source["source_id"],
                                               "source_type": source["source_type"],
                                               "connected": source.get("connected", True),
                                               "last_seen": source.get("last_seen"),
                                               "consent_status": source.get("consent_status", "GRANTED")})
                repo.save_safety_state(patient_id, state_to_dict(SafetyState()))
        except RepositoryConflict as exc:
            raise AppError("DUPLICATE_EVENT", "patient ID already exists", 409) from exc
        return row

    def get_patient(self, patient_id: str) -> dict:
        with self.repositories.transaction() as repo:
            return self._patient(repo, patient_id)

    @staticmethod
    def _patient(repo: UnitOfWork, patient_id: str) -> dict:
        patient = repo.patient(patient_id)
        if patient is None or not patient["active"]:
            raise AppError("PATIENT_NOT_FOUND", "patient not found", 404)
        return patient

    def process(self, event: ApplicationEvent) -> ApplicationResult:
        if event.event_type == EventType.ANCHOR_COMMAND:
            raise AppError("INVALID_ANCHOR_COMMAND", "use the explicit anchor command path")
        return self._process(event)

    def command_anchor(self, event: ApplicationEvent) -> ApplicationResult:
        if event.event_type != EventType.ANCHOR_COMMAND:
            raise AppError("INVALID_ANCHOR_COMMAND", "anchor command event required")
        return self._process(event)

    def _process(self, event: ApplicationEvent) -> ApplicationResult:
        if not isinstance(event.event_type, EventType) or not event.event_id or not event.idempotency_key or not event.correlation_id:
            raise AppError("INVALID_EVENT", "event type and identifiers are required")
        if not event.source or not isinstance(event.payload, dict):
            raise AppError("INVALID_EVENT", "event source and payload are required")
        if any(name in event.payload for name in ("proposed_tier", "interaction_mode", "safety_tier", "detector_outputs")):
            raise AppError("INVALID_EVENT", "safety proposals are not accepted from patient event payloads")
        row = _event_row(event)
        try:
            with self.repositories.transaction() as repo:
                self._patient(repo, event.patient_id)
                prior = repo.prior_result(event.patient_id, event.idempotency_key)
                if prior is not None:
                    return ApplicationResult(**{**prior, "review_item_ids": tuple(prior["review_item_ids"]),
                                                "idempotent_replay": True})
                self._validate_and_consent(repo, event)
                self._recover_pending(repo, event)
                repo.save_event(row)
                self._save_normalized(repo, event)
                safety = self._safety_boundary(repo, event)
                safety_relevant_ids = {item["event_id"] for item in repo.safety_references(event.patient_id)
                                       if item["state"]["interaction_mode"] != "NORMAL" or item["state"]["degraded"]}
                current_safety_state = safety["state"] if safety else repo.safety_state(event.patient_id)
                safety_held = bool(current_safety_state and current_safety_state["degraded"])
                if safety_held:
                    projection = Projection("STAY_QUIET", "Input held pending safety evaluation",
                                            [], [], [], [], [], [])
                    repo.append_timeline({"patient_id": event.patient_id, "event_id": event.event_id,
                                          "record_type": "INPUT_HELD_FOR_SAFETY", "occurred_at": row["occurred_at"],
                                          "detail": {"reason": "SAFETY_GATE_UNAVAILABLE"}})
                else:
                    eligible = [item for item in repo.events(event.patient_id)
                                if not item["longitudinal_deferred"]]
                    projection = LongitudinalProjector(self.signal_registry).run(eligible, safety_relevant_ids)
                    self._persist_projection(repo, event, projection)
                decision = projection.decision
                safety_state = safety["state"] if safety else repo.safety_state(event.patient_id)
                if safety_state and (safety_state["interaction_mode"] != "NORMAL" or safety_state["degraded"]):
                    decision = "SAFETY_REVIEW_REQUIRED"
                conversation = None
                if event.event_type == EventType.PATIENT_FREE_TEXT:
                    conversation = ("NORMAL_CONVERSATION_ALLOWED" if safety and
                                    safety_state["interaction_mode"] == "NORMAL" and not safety_state["degraded"]
                                    else "SAFETY_HANDOFF_OR_HELD")
                review_ids = tuple(self._sync_review_items(repo, event, projection)) if not safety_held else ()
                result = ApplicationResult(event.event_id, event.patient_id, decision,
                                           safety, {**projection.public(), "deferred": safety_held},
                                           review_ids, False, conversation)
                serialized = asdict(result)
                serialized["review_item_ids"] = list(review_ids)
                repo.save_result(event.event_id, serialized)
                repo.append_timeline({"patient_id": event.patient_id, "event_id": event.event_id,
                                      "record_type": "COMMUNICATION_DECISION",
                                      "occurred_at": row["occurred_at"],
                                      "detail": {"outcome": decision, "reason": projection.reason}})
                repo.append_audit({"patient_id": event.patient_id, "event_id": event.event_id,
                                   "correlation_id": event.correlation_id, "action": "PROCESS_EVENT",
                                   "called_domains": ["aura_longitudinal"] + (["aura_safety"] if safety else []),
                                   "communication": decision, "safety_ref": safety["episode_id"] if safety else None,
                                   "review_item_ids": list(review_ids),
                                   "anchor_command": event.payload.get("action") if event.event_type == EventType.ANCHOR_COMMAND else None,
                                   "idempotency_result": "NEW", "timestamp": _iso(event.received_at)})
                return result
        except AppError:
            raise
        except RepositoryConflict as exc:
            raise AppError("DUPLICATE_EVENT", "event ID or idempotency key already exists", 409) from exc
        except (ValueError, KeyError, TypeError) as exc:
            raise AppError("INVALID_EVENT", str(exc)) from exc
        except Exception as exc:
            raise AppError("PERSISTENCE_ERROR", "event processing failed atomically", 500) from exc

    def _validate_and_consent(self, repo: UnitOfWork, event: ApplicationEvent):
        if event.event_type == EventType.WEARABLE_OBSERVATION:
            if not any(row["consent_type"] == "WEARABLE" and row["granted"] for row in repo.consents(event.patient_id)):
                raise AppError("CONSENT_REQUIRED", "wearable consent is required", 403)
            points_from_payload(event.payload, self.signal_registry)
        elif event.event_type == EventType.ANCHOR_COMMAND:
            key = key_from(event.payload)
            if not self.signal_registry.definition(key.signal).enabled_in_engine:
                raise AppError("INVALID_ANCHOR_COMMAND", "display-only signals cannot receive new engine anchors")
            if event.payload.get("action") not in {"CREATE_PROVISIONAL_ANCHOR", "TRUST_ANCHOR", "CLINICAL_REVIEW_REANCHOR"}:
                raise AppError("INVALID_ANCHOR_COMMAND", "named anchor command required")
            if event.payload["action"] != "CREATE_PROVISIONAL_ANCHOR" and not event.payload.get("reviewed_by"):
                raise AppError("INVALID_ANCHOR_COMMAND", "reviewer reference required")
        elif event.event_type == EventType.PATIENT_FREE_TEXT and not event.payload.get("text", "").strip():
            raise AppError("INVALID_EVENT", "non-empty text required")
        elif event.event_type == EventType.CONTEXT_EXPLANATION and not event.payload.get("explanation", "").strip():
            raise AppError("INVALID_EVENT", "non-empty explanation required")

    def _save_normalized(self, repo: UnitOfWork, event: ApplicationEvent):
        row = _event_row(event)
        kind = event.event_type
        detail: dict[str, Any] = {"source": event.source}
        if kind == EventType.WEARABLE_OBSERVATION:
            detail["signals"] = []
            for point in points_from_payload(event.payload, self.signal_registry):
                normalized = {"event_id": event.event_id, "patient_id": event.patient_id,
                              "signal": point.key.signal.value, "source": point.key.source,
                              "metric": point.key.metric, "day": point.day.isoformat(),
                              "value": point.value, "coverage": point.coverage,
                              "data_quality": point.data_quality}
                repo.save_observation(normalized)
                detail["signals"].append(normalized)
        elif kind == EventType.PATIENT_CHECKIN:
            repo.save_checkin({"event_id": event.event_id, "patient_id": event.patient_id,
                               "timestamp": row["occurred_at"], "state": event.payload["state"],
                               "structured_answers": event.payload.get("structured_answers", {}),
                               "context_tags": event.payload.get("context_tags", [])})
            detail["state"] = event.payload["state"]
        elif kind == EventType.MEDICATION_EVENT:
            repo.save_medication({"event_id": event.event_id, "patient_id": event.patient_id,
                                  "scheduled_time": event.payload["scheduled_time"], "timestamp": row["occurred_at"],
                                  "status": event.payload["status"], "source": event.source})
            detail["status"] = event.payload["status"]
        elif kind == EventType.CONTEXT_EVENT:
            repo.save_context({"event_id": event.event_id, "patient_id": event.patient_id,
                               "start_at": event.payload["start"], "end_at": event.payload.get("end"),
                               "category": event.payload["category"],
                               "affected_signals": event.payload["affected_signals"],
                               "source": event.payload["source"],
                               "explanation": event.payload.get("explanation")})
            detail.update({"category": event.payload["category"],
                           "affected_signals": event.payload["affected_signals"]})
        elif kind == EventType.CONTEXT_EXPLANATION:
            repo.save_explanation({"event_id": event.event_id, "patient_id": event.patient_id,
                                   "relevant_drift_ref": event.payload.get("relevant_drift_ref"),
                                   "explanation": event.payload["explanation"],
                                   "affected_signals": event.payload["affected_signals"],
                                   "created_at": row["occurred_at"], "status": "PENDING_DRIFT"})
            detail["affected_signals"] = event.payload["affected_signals"]
        elif kind == EventType.ANCHOR_COMMAND:
            detail["action"] = event.payload["action"]
            detail["signal"] = event.payload["signal"]
        elif kind == EventType.PATIENT_FREE_TEXT:
            detail["content_stored_in_event"] = True
        elif kind == EventType.STRUCTURED_ASSESSMENT_RESPONSE:
            detail["response_keys"] = sorted(event.payload)
        elif kind == EventType.REVIEW_COMMAND:
            detail["action"] = event.payload.get("action")
        repo.append_timeline({"patient_id": event.patient_id, "event_id": event.event_id,
                              "record_type": kind.value, "occurred_at": row["occurred_at"], "detail": detail})

    def _recover_pending(self, repo: UnitOfWork, current: ApplicationEvent) -> None:
        before = repo.safety_state(current.patient_id)
        if not before or not before["degraded"] or not requires_safety_gate(current):
            return
        pending = [row for row in repo.events(current.patient_id) if row["longitudinal_deferred"]]
        safety_ids = {row["event_id"] for row in repo.safety_references(current.patient_id)}
        # Preflight: a missing fixture/service cannot release any held input.
        for row in pending:
            if row["event_id"] in safety_ids:
                previous = state_from_dict(repo.safety_state(current.patient_id))
                held = ApplicationEvent(row["event_id"], row["patient_id"], EventType(row["event_type"]),
                                        datetime.fromisoformat(row["occurred_at"]),
                                        datetime.fromisoformat(row["received_at"]), row["source"], row["payload"],
                                        row["correlation_id"], row["idempotency_key"])
                try:
                    self.safety_gate.resolve(held, previous.episode_id, previous.sequence)
                except Exception:
                    return
        for row in pending:
            if row["event_id"] in safety_ids:
                held = ApplicationEvent(row["event_id"], row["patient_id"], EventType(row["event_type"]),
                                        datetime.fromisoformat(row["occurred_at"]),
                                        datetime.fromisoformat(row["received_at"]), row["source"], row["payload"],
                                        row["correlation_id"], row["idempotency_key"])
                result = self._safety_boundary(repo, held, safety_time=current.received_at)
                if result is None or result["state"]["degraded"]:
                    return
            prior = repo.prior_result(current.patient_id, row["idempotency_key"])
            prior["longitudinal"]["deferred"] = False
            prior["longitudinal"]["released_on_recovery"] = True
            repo.save_result(row["event_id"], prior)
            repo.append_timeline({"patient_id": current.patient_id, "event_id": row["event_id"],
                                  "record_type": "HELD_INPUT_RELEASED", "occurred_at": _iso(current.received_at),
                                  "detail": {"released_by_event_id": current.event_id}})

    def _safety_boundary(self, repo: UnitOfWork, event: ApplicationEvent,
                         safety_time: datetime | None = None) -> dict | None:
        if not requires_safety_gate(event):
            return None
        processed_at = safety_time or event.received_at
        before = state_from_dict(repo.safety_state(event.patient_id) or state_to_dict(SafetyState()))
        kind = (EventKind.FREE_TEXT_RECEIVED if event.event_type in {EventType.PATIENT_FREE_TEXT, EventType.CONTEXT_EXPLANATION, EventType.CONTEXT_EVENT, EventType.REVIEW_COMMAND}
                else EventKind.STRUCTURED_RESPONSE_RECEIVED if event.event_type == EventType.STRUCTURED_ASSESSMENT_RESPONSE
                else EventKind.CHECKIN_TAP_RECEIVED if event.event_type == EventType.PATIENT_CHECKIN
                else EventKind.MEDICATION_EVENT_RECEIVED)
        try:
            intake = self.safety_engine.apply(before, SafetyEvent(kind, processed_at, input_id=event.event_id))
        except Exception as exc:
            raise AppError("SAFETY_UNAVAILABLE", "safety policy could not process this input", 503) from exc
        if intake.outcome not in {Outcome.NO_STATE_CHANGE, Outcome.DEFER_EVENT}:
            raise AppError("DOMAIN_ERROR", "safety intake rejected", 500)
        try:
            outputs = self.safety_gate.resolve(event, before.episode_id, before.sequence)
            proposal = max((output.proposed_tier for output in outputs), default=Mode.NORMAL)
            safety_event = SafetyEvent(EventKind.DETECTORS_COMPLETE, processed_at,
                                       proposed_tier=proposal, detector_outputs=outputs,
                                       episode_id=f"episode-{event.event_id}", input_id=event.event_id)
        except SafetyGateUnavailable:
            safety_event = SafetyEvent(EventKind.DETECTOR_TIMEOUT, processed_at,
                                       input_id=event.event_id)
        except Exception:
            safety_event = SafetyEvent(EventKind.DETECTOR_ERROR, processed_at,
                                       input_id=event.event_id)
        try:
            result = self.safety_engine.apply(before, safety_event)
        except Exception as exc:
            raise AppError("SAFETY_UNAVAILABLE", "safety policy could not process this input", 503) from exc
        if result.outcome == Outcome.REJECT_EVENT:
            raise AppError("DOMAIN_ERROR", "safety event rejected", 500)
        state = state_to_dict(result.state)
        repo.save_safety_state(event.patient_id, state)
        if result.archived_episode is not None:
            repo.save_archived_safety_episode({"patient_id": event.patient_id,
                                                "episode_id": result.archived_episode.episode_id,
                                                "final_state": state_to_dict(result.archived_episode),
                                                "archived_by_event_id": event.event_id,
                                                "previous_episode_id": result.previous_episode_id})
        ref = {"event_id": event.event_id, "patient_id": event.patient_id,
               "episode_id": result.state.episode_id, "source_episode_id": result.source_episode_id,
               "previous_episode_id": result.previous_episode_id,
               "sequence": result.state.sequence, "outcome": result.outcome.value, "state": state}
        repo.save_safety_reference(ref)
        try:
            plan = output_plan(result.state, self.resource_registry, processed_at)
        except Exception as exc:
            raise AppError("SAFETY_UNAVAILABLE", "safety resource integrity failed", 503) from exc
        repo.append_safety_audit({"event_id": event.event_id, "patient_id": event.patient_id,
                                  "episode_id": result.state.episode_id, "sequence": result.state.sequence,
                                  "policy_version": POLICY_VERSION,
                                  "policy_config_version": self.safety_engine.config.version,
                                  "record": {"source_episode_id": result.source_episode_id,
                                             "previous_episode_id": result.previous_episode_id,
                                             "previous_state": state_to_dict(before),
                                             "event": safety_event.kind.value,
                                             "detector_outputs": [{"detector_id": output.detector_id,
                                                                   "proposed_tier": output.proposed_tier.name,
                                                                   "input_id": output.input_id,
                                                                   "source_episode_id": output.source_episode_id,
                                                                   "source_sequence": output.source_sequence}
                                                                  for output in safety_event.detector_outputs],
                                             "proposed_tier": safety_event.proposed_tier.name,
                                             "resulting_state": state, "outcome": result.outcome.value,
                                             "clock_timestamp": _iso(processed_at),
                                             "original_input_timestamp": _iso(event.occurred_at),
                                             "resource_version": (plan.pinned_resources.bundle.version
                                                                  if plan.pinned_resources else None),
                                             "degraded_causes": state["degraded_causes"]}})
        repo.append_timeline({"patient_id": event.patient_id, "event_id": event.event_id,
                              "record_type": "SAFETY_BOUNDARY", "occurred_at": _iso(event.occurred_at),
                              "detail": {"episode_id": result.state.episode_id,
                                         "sequence": result.state.sequence, "outcome": result.outcome.value,
                                         "interaction_mode": result.state.interaction_mode.name,
                                         "degraded": result.state.degraded}})
        pinned = None
        if plan.pinned_resources:
            resources = plan.pinned_resources
            pinned = {"version": resources.bundle.version, "source": resources.source,
                      "stale": resources.stale, "notice": resources.notice,
                      "resources": [{"resource_id": item.resource_id, "label": item.label,
                                     "contact_method": item.contact_method, "locale": item.locale}
                                    for item in resources.bundle.resources]}
        return {"episode_id": result.state.episode_id, "sequence": result.state.sequence,
                "outcome": result.outcome.value, "state": state,
                "action": result.action,
                "output": {"generation_used": False, "static_template_id": plan.static_template_id,
                           "pinned_resources": pinned}}

    def _persist_projection(self, repo: UnitOfWork, event: ApplicationEvent, projection):
        at = _iso(event.occurred_at)
        prior_baselines = {(row["signal"], row["source"], row["metric"]): row
                           for row in repo.baselines(event.patient_id)}
        for baseline in projection.baselines:
            key = (baseline["signal"], baseline["source"], baseline.get("metric") or "")
            previous = prior_baselines.get(key)
            if previous and previous["sensing_state"] != baseline["sensing_state"]:
                label = "SENSING_GAP" if baseline["sensing_state"] == "UNOBSERVED" else "SENSING_RETURN"
                repo.append_timeline({"patient_id": event.patient_id, "event_id": event.event_id,
                                      "record_type": label, "occurred_at": at,
                                      "detail": {"signal": baseline["signal"], "source": baseline["source"],
                                                 "metric": baseline.get("metric"),
                                                 "sensing_state": baseline["sensing_state"],
                                                 "trust_state": baseline["trust_state"]}})
            repo.save_baseline({"patient_id": event.patient_id, **baseline, "updated_at": at})
        for item in projection.held:
            key = item["key"]
            repo.save_held({"patient_id": event.patient_id, **key, "direction": item["direction"],
                            "status": item["status"], "record": item})
        for drift in projection.drifts:
            repo.append_timeline({"patient_id": event.patient_id, "event_id": event.event_id,
                                  "record_type": "LONGITUDINAL_DRIFT", "occurred_at": at,
                                  "detail": drift})
            if drift["attenuated"]:
                repo.append_timeline({"patient_id": event.patient_id, "event_id": event.event_id,
                                      "record_type": "CONTEXT_ATTENUATION", "occurred_at": at,
                                      "detail": {"key": drift["key"], "kind": drift["kind"],
                                                 "benign_contexts": drift["benign_contexts"]}})
        if event.event_type == EventType.CONTEXT_EXPLANATION:
            repo.update_explanation_status(event.event_id, projection.explanation_status)
            repo.append_timeline({"patient_id": event.patient_id, "event_id": event.event_id,
                                  "record_type": "HELD_FOR_REVIEW", "occurred_at": at,
                                  "detail": {"status": projection.explanation_status,
                                             "affected_signals": event.payload["affected_signals"]}})

    def _sync_review_items(self, repo: UnitOfWork, event: ApplicationEvent, projection) -> list[str]:
        created = []
        existing = {item["source_ref"] for item in repo.review_items(event.patient_id)}
        for held in projection.held:
            key = held["key"]
            source_ref = f"held:{key['signal']}:{key['source']}:{key.get('metric') or ''}:{held['direction']}"
            if source_ref not in existing:
                item_id = str(uuid4())
                repo.save_review_item({"item_id": item_id, "patient_id": event.patient_id,
                                       "source_ref": source_ref, "summary": held["detected_drift"]["description"],
                                       "created_at": _iso(event.occurred_at), "status": "OPEN",
                                       "patient_visible": True, "share_status": "NOT_SHARED"})
                created.append(item_id)
                repo.append_timeline({"patient_id": event.patient_id, "event_id": event.event_id,
                                      "record_type": "CLINICIAN_REVIEW_ITEM", "occurred_at": _iso(event.occurred_at),
                                      "detail": {"item_id": item_id, "source_ref": source_ref,
                                                 "share_status": "NOT_SHARED"}})
        return created

    def timeline(self, patient_id: str) -> list[dict]:
        with self.repositories.transaction() as repo:
            self._patient(repo, patient_id)
            return repo.timeline(patient_id)

    def status(self, patient_id: str) -> dict:
        with self.repositories.transaction() as repo:
            self._patient(repo, patient_id)
            events = repo.events(patient_id)
            latest = repo.prior_result(patient_id, events[-1]["idempotency_key"]) if events else None
            enabled = {item["name"] for item in self.signals()["signals"] if item["enabled_in_engine"]}
            current_baselines = [row for row in repo.baselines(patient_id) if row["signal"] in enabled]
            return {"patient_id": patient_id, "signals": current_baselines,
                    "active_longitudinal_observations": [row for row in latest["longitudinal"]["drifts"]
                        if row["key"]["signal"] in enabled] if latest else [],
                    "held_for_review": repo.held(patient_id),
                    "latest_communication_decision": latest["communication_decision"] if latest else "STAY_QUIET",
                    "safety": repo.safety_state(patient_id),
                    "data_coverage": {f"{row['signal']}:{row['source']}:{row['metric']}": row["rolling"]["coverage_ratio"]
                                      for row in current_baselines},
                    "signal_registry": {"version": self.signal_registry.version,
                                        "fingerprint": self.signal_registry.fingerprint}}

    def review_snapshot(self, patient_id: str) -> dict:
        with self.repositories.transaction() as repo:
            self._patient(repo, patient_id)
            events = repo.events(patient_id)
            timeline = repo.timeline(patient_id)
            baselines = repo.baselines(patient_id)
            held = repo.held(patient_id)
            deferred_ids = {row["event_id"] for row in events if row["longitudinal_deferred"]}
            checkins = [row for row in timeline if row["record_type"] == "PATIENT_CHECKIN"
                        and row["event_id"] not in deferred_ids]
            medication = [row for row in timeline if row["record_type"] == "MEDICATION_EVENT"
                          and row["event_id"] not in deferred_ids]
            active = repo.prior_result(patient_id, events[-1]["idempotency_key"]) if events else None
            questions = [row["payload"]["question"] for row in events
                         if row["event_type"] == "REVIEW_COMMAND" and row["payload"].get("action") == "ADD_QUESTION"
                         and row["payload"].get("question") and row["event_id"] not in deferred_ids]
            safety = repo.safety_references(patient_id)
            changes: dict[tuple[str, str, str, str], dict] = {}
            for row in timeline:
                if row["record_type"] != "LONGITUDINAL_DRIFT" or row["detail"]["kind"] in {"STABLE", "INSUFFICIENT_DATA"}:
                    continue
                drift = row["detail"]
                key = drift["key"]
                identity = (key["signal"], key["source"], key.get("metric") or "", drift["kind"])
                if identity not in changes:
                    changes[identity] = {"first_seen": row["occurred_at"], "last_seen": row["occurred_at"],
                                         "observations": 0, "latest": drift}
                changes[identity]["last_seen"] = row["occurred_at"]
                changes[identity]["observations"] += 1
                changes[identity]["latest"] = drift
            return {"patient_id": patient_id,
                    "review_period": {"start": events[0]["occurred_at"] if events else None,
                                      "end": events[-1]["occurred_at"] if events else None},
                    "sensing_coverage": {f"{b['signal']}:{b['source']}:{b['metric']}": b["rolling"]["coverage_ratio"] for b in baselines},
                    "baseline_status": [{"signal": b["signal"], "source": b["source"],
                                         "metric": b["metric"], "trust_state": b["trust_state"],
                                         "anchor_version": b["anchor"]["version"] if b["anchor"] else None}
                                        for b in baselines],
                    "meaningful_longitudinal_changes": list(changes.values()),
                    "patient_checkin_trend": [{"at": row["occurred_at"], "state": row["detail"]["state"]} for row in checkins],
                    "medication_routine_events": [{"at": row["occurred_at"], "status": row["detail"]["status"]} for row in medication],
                    "active_context": active["longitudinal"]["active_contexts"] if active else [],
                    "explained_held_for_review": held,
                    "unresolved_items": repo.review_items(patient_id),
                    "safety_episode_references": [{"episode_id": ref["episode_id"], "sequence": ref["sequence"],
                                                   "outcome": ref["outcome"],
                                                   "previous_episode_id": ref.get("previous_episode_id")}
                                                  for ref in safety],
                    "patient_selected_questions": questions,
                    "share_status": "NOT_SHARED", "automatically_sent": False}
