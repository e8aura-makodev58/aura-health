"""Read committed decisions, approve wording, and persist validated presentation output.

Model calls hold no DB transaction. Their result is discarded if product state changes.
Only this application boundary prepares production generation requests.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from time import perf_counter

from aura_communication.catalog import STATIC_TEXT, candidates_for
from aura_communication.config import CommunicationConfig, load_config
from aura_communication.domain import (
    ApprovedPolicyQuestion, CommunicationPurpose, Fact, GenerationMode, GenerationRequest,
)
from aura_communication.prompts import prompt_contract
from aura_communication.provider import GenerationProvider, provider_from_environment
from aura_communication.validation import patient_text_problems, validate_output
from aura_safety.codec import state_from_dict
from aura_safety.domain import Mode, Status, state_valid
from aura_safety.engine import POLICY_VERSION
from aura_safety.output import OutputPlan, output_plan

from .models import AppError, EventType
from .service import PatientEventService, requires_safety_gate


def _hash(value) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _resources(plan: OutputPlan) -> dict | None:
    resolved = plan.pinned_resources
    if resolved is None:
        return None
    return {"version": resolved.bundle.version, "source": resolved.source,
            "stale": resolved.stale, "notice": resolved.notice,
            "resources": [{"resource_id": r.resource_id, "label": r.label,
                           "contact_method": r.contact_method, "locale": r.locale}
                          for r in resolved.bundle.resources]}


@dataclass(frozen=True)
class Approval:
    cache_key: str
    event_id: str
    patient_id: str
    correlation_id: str
    sequence: int | None
    episode_id: str | None
    request: GenerationRequest | None
    template_id: str | None
    plan: OutputPlan


class PatientCommunicationService:
    """No state/anchor mutation or detector work. Optional wording of committed events only."""

    def __init__(self, events: PatientEventService, *, provider: GenerationProvider | None = None,
                 config: CommunicationConfig | None = None,
                 policy_question: ApprovedPolicyQuestion | None = None, clock=None, reply_provider=None):
        self.events = events
        # Optional live agent provider for replies to safety-cleared notes (synthetic hosted demo only).
        self.reply_provider = reply_provider
        self.repositories = events.repositories
        self.config = config or load_config()
        self.provider = provider if provider is not None else provider_from_environment(self.config)
        self.policy_question = policy_question
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def render(self, patient_id: str, event_id: str, *, purpose=CommunicationPurpose.AUTO,
               client_offline: bool = False) -> dict:
        try:
            return self._render(patient_id, event_id, purpose=purpose, client_offline=client_offline)
        except AppError:
            raise
        except Exception as exc:
            raise AppError("PERSISTENCE_ERROR", "communication output failed atomically", 500) from exc

    def _render(self, patient_id, event_id, *, purpose, client_offline):
        if not isinstance(purpose, CommunicationPurpose) or type(client_offline) is not bool:
            raise AppError("INVALID_EVENT", "invalid communication options")
        with self.repositories.transaction() as repo:
            approval = self._approve(repo, patient_id, event_id, purpose, client_offline)
            cached = repo.communication_record(approval.cache_key)
            if cached is not None:
                return {**cached, "pinned_resources": _resources(approval.plan), "idempotent_replay": True}

        # A model cannot see unassessed text or any write-capable application object.
        attempted = approval.request is not None
        started = perf_counter()
        reason, validation, model_id = "STATIC_POLICY", "NOT_RUN", None
        selected = None
        if approval.request is not None and approval.request.mode == GenerationMode.NORMAL_SUPPORT and self._replies_live():
            # A safety-cleared note in the normal state: the agent may reply in its own words.
            # Strict patient-text checks; any failure keeps the approved fixed sentence.
            model_id = self.reply_provider.model_id
            try:
                from aura_agent.tasks import structured_task
                reply = structured_task(self.reply_provider, "note_reply", {"note": approval.request.patient_context}, reasoning="low")
                message = reply.get("message") if isinstance(reply, dict) and set(reply) == {"message"} else None
                problems = patient_text_problems(message, self.config.max_response_length)
                if problems:
                    reason, validation = "INVALID_GENERATION", list(problems)
                else:
                    selected = {"candidate_id": "agent-note-reply", "message": message.strip(), "acknowledged_facts": [],
                                "question_intent": None, "cta_type": None}
                    reason, validation = "GENERATED_VALIDATED", "PASS"
            except TimeoutError:
                reason, validation = "MODEL_TIMEOUT", "NOT_RUN"
            except Exception:
                reason, validation = "MODEL_UNAVAILABLE", "NOT_RUN"
        elif approval.request is not None:
            model_id = self.provider.model_id
            try:
                raw = self.provider.generate(prompt_contract(approval.request))
                checked = validate_output(approval.request, raw)
                if checked.accepted:
                    selected, reason, validation = raw, "GENERATED_VALIDATED", "PASS"
                else:
                    reason, validation = "INVALID_GENERATION", list(checked.reasons)
            except TimeoutError:
                reason, validation = "MODEL_TIMEOUT", "NOT_RUN"
            except Exception:
                reason, validation = "MODEL_UNAVAILABLE", "NOT_RUN"
        latency_ms = round((perf_counter() - started) * 1000, 3) if attempted else 0.0

        with self.repositories.transaction() as repo:
            current = self._approve(repo, patient_id, event_id, purpose, client_offline)
            if current.cache_key != approval.cache_key:
                # New evidence wins. Never replay an old normal message over a newer safety result.
                selected, reason = None, "STATE_CHANGED_DURING_GENERATION"
            cached = repo.communication_record(current.cache_key)
            if cached is not None:
                return {**cached, "pinned_resources": _resources(current.plan), "idempotent_replay": True}
            result = self._result(current, selected, reason, validation, model_id, attempted, latency_ms)
            repo.append_communication_record(current.cache_key, result)
            repo.append_audit({"patient_id": patient_id, "event_id": event_id,
                               "correlation_id": current.correlation_id, "action": "RENDER_COMMUNICATION",
                               "called_domains": ["aura_communication", "aura_safety.output"],
                               "communication": result["mode"] or current.template_id,
                               "safety_ref": current.episode_id, "review_item_ids": [],
                               "anchor_command": None, "idempotency_result": "NEW",
                               "timestamp": result["created_at"]})
            repo.append_timeline({"patient_id": patient_id, "event_id": event_id,
                                  "record_type": "COMMUNICATION_OUTPUT", "occurred_at": result["created_at"],
                                  "detail": {"communication_id": current.cache_key, "mode": result["mode"],
                                             "generation_used": result["generation_used"],
                                             "fallback_reason": result["fallback_reason"],
                                             "template_id": result["static_template_id"]}})
            return result

    def _replies_live(self):
        return bool(self.reply_provider is not None and getattr(self.reply_provider, "live", False))

    def _approve(self, repo, patient_id, event_id, purpose, offline) -> Approval:
        self.events._patient(repo, patient_id)
        rows = repo.events(patient_id)
        event = next((row for row in rows if row["event_id"] == event_id), None)
        if event is None:
            raise AppError("EVENT_NOT_FOUND", "committed event not found", 404)
        result = repo.prior_result(patient_id, event["idempotency_key"])
        if result is None:
            raise AppError("INVALID_EVENT", "event processing has not committed")
        now = self.clock()
        if now.tzinfo is None:
            raise AppError("DOMAIN_ERROR", "communication clock requires a timezone", 500)
        raw_state = repo.safety_state(patient_id)
        state = None
        try:
            state = state_from_dict(raw_state) if raw_state else None
            if state is None or not state_valid(state):
                state = None
        except (ValueError, KeyError, TypeError):
            pass
        if state is None:
            plan = OutputPlan(False, False, "SERVER_FAIL_CLOSED",
                              self.events.resource_registry.resolve(now, offline=offline), False)
        else:
            try:
                plan = output_plan(state, self.events.resource_registry, now, client_offline=offline)
            except ValueError as exc:
                raise AppError("SAFETY_UNAVAILABLE", "safety resources could not be rendered", 503) from exc

        # This mirrors input routing, not safety detection. Verify a committed gate reference.
        from .models import ApplicationEvent
        envelope = ApplicationEvent(event_id, patient_id, EventType(event["event_type"]),
                                    datetime.fromisoformat(event["occurred_at"]),
                                    datetime.fromisoformat(event["received_at"]), event["source"],
                                    event["payload"], event["correlation_id"], event["idempotency_key"])
        references = repo.safety_references(patient_id)
        evaluated = next((ref for ref in references if ref["event_id"] == event_id), None)
        gate_complete = (not requires_safety_gate(envelope) or
                         bool(evaluated and not evaluated["state"]["degraded"]
                              and evaluated["outcome"] not in {"DEFER_EVENT", "REJECT_EVENT", "SET_DEGRADED"}))
        input_held = event["longitudinal_deferred"] or not gate_complete
        mode, template, question = None, None, None
        if not plan.may_generate:
            template = plan.static_template_id
        elif input_held:
            template = "SERVER_FAIL_CLOSED"
            plan = OutputPlan(False, False, template,
                              self.events.resource_registry.resolve(now), False)
        elif state.interaction_mode == Mode.URGENT:
            template = "URGENT_STATIC_FALLBACK"  # Deliberately static M5 subset of allowed policy.
        elif state.episode_status in {Status.RECHECK_REQUIRED, Status.DROPOUT}:
            template = "RECHECK_PENDING_REVIEW"
        elif state.interaction_mode == Mode.CLARIFY:
            question = self.policy_question
            if question is not None and question.policy_version == POLICY_VERSION:
                mode = GenerationMode.POLICY_CLARIFICATION
            else:
                template = "CLARIFY_PENDING_REVIEW"
        elif state.interaction_mode == Mode.ELEVATED:
            mode = GenerationMode.ELEVATED_SUPPORT
        elif rows[-1]["event_id"] != event_id:
            template = "SUPERSEDED_EVENT"
        elif purpose == CommunicationPurpose.EXPLAIN_OBSERVATION:
            mode = GenerationMode.OBSERVATION_EXPLANATION
        elif envelope.source == "patient_medication_update":
            # Words describing past doses are a records update, not a note: no reply card.
            template = "STAY_QUIET"
        elif envelope.event_type == EventType.PATIENT_FREE_TEXT:
            mode = GenerationMode.NORMAL_SUPPORT
        else:
            decision = result["communication_decision"]
            mode = {"MICRO_CHECKIN": GenerationMode.MICRO_CHECKIN,
                    "TARGETED_CLARIFICATION": GenerationMode.TARGETED_CLARIFICATION}.get(decision)
            template = {"STAY_QUIET": "STAY_QUIET", "CLINICIAN_REVIEW_ITEM": "CLINICIAN_REVIEW_ITEM",
                        "STRUCTURED_ASSESSMENT": "STRUCTURED_ASSESSMENT_PENDING"}.get(decision)
            if mode is None and template is None:
                template = "SERVER_FAIL_CLOSED"

        facts = self._facts(event, result, include_checkin=mode != GenerationMode.OBSERVATION_EXPLANATION) if mode not in {
            None, GenerationMode.POLICY_CLARIFICATION, GenerationMode.ELEVATED_SUPPORT,
            GenerationMode.NORMAL_SUPPORT} else ()
        if mode == GenerationMode.OBSERVATION_EXPLANATION and not facts:
            mode, template = None, "NO_OBSERVATION"
        candidates = candidates_for(mode, facts, question=question) if mode is not None else ()
        context = (envelope.payload["text"][:self.config.max_context_chars]
                   if mode == GenerationMode.NORMAL_SUPPORT else None)
        request = (GenerationRequest(mode, mode.value, facts, candidates, context,
                                     self.config.max_response_length, POLICY_VERSION,
                                     self.events.safety_engine.config.version,
                                     self.config.prompt_version, self.config.version) if mode else None)
        # Configuration that cannot fit its own approved fallback must not cause generation.
        if request and any(not validate_output(request, candidate.public()).accepted for candidate in candidates):
            request, template = None, "SERVER_FAIL_CLOSED"
        signature = {"event_id": event_id, "latest_event_id": rows[-1]["event_id"],
                     "state": raw_state, "input_held": input_held, "purpose": purpose.value,
                     "offline": offline, "config": self.config.fingerprint,
                     "policy_config": self.events.safety_engine.config.version,
                     "model": self.provider.model_id, "request": request.public() if request else None,
                     "reply_model": self.reply_provider.model_id if self._replies_live() and mode == GenerationMode.NORMAL_SUPPORT else None,
                     "template": template, "resources": _resources(plan)}
        return Approval(_hash(signature), event_id, patient_id, event["correlation_id"],
                        state.sequence if state else None, state.episode_id if state else None,
                        request, template, plan)

    def _facts(self, event, result, *, include_checkin=True) -> tuple[Fact, ...]:
        facts = []
        # Engine descriptions use known signal labels, never source/metric/patient free text.
        approved_description = re.compile(
            r"(?:Sleep midpoint|Sleep duration|Activity|Resting heart rate) is "
            r"(?:later|earlier|higher|lower) relative to the (?:anchored reference|recent rolling pattern)\.")
        for index, drift in enumerate(result["longitudinal"].get("drifts", [])):
            if drift["kind"] not in {"STABLE", "INSUFFICIENT_DATA"}:
                description = drift.get("description", "")
                if approved_description.fullmatch(description):
                    facts.append(Fact(f"{event['event_id']}:drift:{index}", description))
        if include_checkin and event["event_type"] == EventType.PATIENT_CHECKIN.value:
            state = event["payload"].get("state")
            if state in {"Good", "Okay", "Rough"}:
                facts.insert(0, Fact(f"{event['event_id']}:checkin", f"You recorded a {state} check-in."))
        return tuple(facts[:self.config.max_facts])

    def _result(self, approval, selected, reason, validation, model_id, attempted, latency_ms):
        request = approval.request
        if selected is None and request is not None:
            selected = request.candidates[0].public()
        generated = reason == "GENERATED_VALIDATED"
        return {"communication_id": approval.cache_key, "event_id": approval.event_id,
                "patient_id": approval.patient_id, "mode": request.mode.value if request else None,
                "message": selected["message"] if selected else STATIC_TEXT[approval.template_id],
                "acknowledged_facts": selected["acknowledged_facts"] if selected else [],
                "question_intent": selected["question_intent"] if selected else None,
                "cta_type": selected["cta_type"] if selected else None,
                "generation_used": generated, "generation_attempted": attempted,
                "validator_result": validation, "fallback_reason": None if generated else reason,
                "static_template_id": approval.template_id if request is None else
                                      (None if generated else f"{request.mode.value}_FIXED_FALLBACK"),
                "prompt_version": self.config.prompt_version, "config_version": self.config.version,
                "content_version": self.config.content_version, "policy_version": POLICY_VERSION,
                "policy_config_version": self.events.safety_engine.config.version,
                "model_id": model_id, "latency_ms": latency_ms,
                "input_assessed": approval.plan.input_assessed,
                "safety_reference": {"episode_id": approval.episode_id, "sequence": approval.sequence},
                "pinned_resources": _resources(approval.plan), "idempotent_replay": False,
                "content_review_status": "DEVELOPMENT_FIXTURE_REQUIRES_REVIEW",
                "created_at": self.clock().isoformat()}
