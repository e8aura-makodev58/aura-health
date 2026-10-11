"""Application-approved read-only agent execution with durable, race-checked trace."""

from datetime import datetime, timezone
from dataclasses import asdict
from hashlib import sha256
import json
import threading

from aura_agent.guard import blocked_reason
from aura_agent.providers import ScriptedAgentProvider
from aura_agent.roles import AgentRole, QUERIES, QUESTIONS, QUESTION_CATALOG
from aura_agent.runtime import load_config, run
from aura_agent.tools import RecordTools
from .evidence import EvidenceViewService
from .models import AppError, ApplicationEvent, EventType
from .service import requires_safety_gate


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class AgentService:
    def __init__(self, events, *, provider=None, config=None, synthetic_only=False, clock=None):
        self.events = events
        self.provider = provider or ScriptedAgentProvider()
        self.config = config or load_config()
        self.synthetic_only = synthetic_only
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        # Coalesce identical run IDs locally without holding a DB transaction
        # across a model call. Hosted demo has one service per private workspace.
        self.lock = threading.Lock()

    def _approval(self, repo, patient_id, offline):
        self.events._patient(repo, patient_id)
        rows = repo.events(patient_id)
        references = {ref["event_id"]: ref for ref in repo.safety_references(patient_id)}
        held = False
        for row in rows:
            envelope = ApplicationEvent(row["event_id"], patient_id, EventType(row["event_type"]),
                datetime.fromisoformat(row["occurred_at"]), datetime.fromisoformat(row["received_at"]),
                row["source"], row["payload"], row["correlation_id"], row["idempotency_key"])
            ref = references.get(row["event_id"])
            if row["longitudinal_deferred"] or (requires_safety_gate(envelope) and
                    (not ref or ref["state"]["degraded"] or ref["outcome"] in {"DEFER_EVENT", "REJECT_EVENT", "SET_DEGRADED"})):
                held = True
        state = repo.safety_state(patient_id)
        # Historical held inputs are excluded from facts; current safety still blocks.
        reason = blocked_reason(state, self.events.resource_registry, self.clock(), offline=offline)
        signature = digest({"events": [r["event_id"] for r in rows], "state": state,
                            "baselines": repo.baselines(patient_id), "held": repo.held(patient_id),
                            "agent_config": asdict(self.config),
                            "signal_registry": self.events.signal_registry.fingerprint,
                            'question_catalog': QUESTION_CATALOG,
                            "references": references, "model": self.provider.model_id, "blocked": reason})
        return signature, reason, (rows[-1] if rows else None), state

    def execute(self, patient_id, role, *, run_id, query_id=None, question=None, window_days=56, client_offline=False):
        try:
            return self._execute(patient_id, role, run_id=run_id, query_id=query_id, question=question,
                                 window_days=window_days, client_offline=client_offline)
        except AppError:
            raise
        except Exception:
            raise AppError("AGENT_UNAVAILABLE", "Assistant could not complete this read-only request", 503) from None

    def record_tools(self, patient_id, role, window_days):
        """Shared, safety-assessed fact preparation for preview and checked generation."""
        evidence = EvidenceViewService(self.events).get(patient_id)
        with self.events.repositories.transaction() as repo:
            assessed = {ref['event_id'] for ref in repo.safety_references(patient_id)
                if not ref['state']['degraded'] and ref['outcome'] not in {'DEFER_EVENT', 'REJECT_EVENT', 'SET_DEGRADED'}}
            evidence['agent_assessed_context_ids'] = sorted(assessed)
            evidence['assessed_notes'] = [{'event_id': row['event_id'], 'at': row['occurred_at'], 'text': row['payload']['text']}
                for row in repo.events(patient_id) if row['event_type'] == 'PATIENT_FREE_TEXT'
                and row['event_id'] in assessed and not row['longitudinal_deferred']]
        return RecordTools(evidence, role, window_days=window_days, recent_readings_days=self.config.recent_readings_days), evidence

    def _execute(self, patient_id, role, *, run_id, query_id=None, question=None, window_days=56, client_offline=False):
        try:
            role = AgentRole(role)
        except ValueError:
            raise AppError("INVALID_AGENT_ROLE", "Unknown assistant skill") from None
        if (not isinstance(run_id, str) or not 1 <= len(run_id) <= 100 or
                type(window_days) is not int or not 1 <= window_days <= 180 or type(client_offline) is not bool):
            raise AppError("INVALID_AGENT_REQUEST", "Invalid assistant options")
        if (question is not None and (role != AgentRole.RECORD_QA or query_id is not None or not isinstance(question, str) or not 1 <= len(question.strip()) <= 2000)):
            raise AppError('INVALID_AGENT_REQUEST', 'Provide one bounded record question')
        if (role == AgentRole.RECORD_QA and question is None and query_id not in QUERIES) or (role != AgentRole.RECORD_QA and query_id is not None):
            raise AppError("INVALID_AGENT_REQUEST", "Select an approved record question; free text is not accepted")
        options = digest({"role": role.value, "query": query_id, 'question_hash': digest(question), "window": window_days, "offline": client_offline})
        with self.lock:
            if question is not None and not client_offline:
                from uuid import uuid5, NAMESPACE_URL
                question_id = str(uuid5(NAMESPACE_URL, f'aura-qa:{patient_id}:{run_id}:{digest(question)}'))
                with self.events.repositories.transaction() as repo:
                    prior = repo.agent_run(patient_id, run_id)
                    if prior and prior['request_fingerprint'] != options:
                        raise AppError('AGENT_RUN_CONFLICT', 'Run ID belongs to different options', 409)
                    rows = repo.events(patient_id)
                    at = datetime.fromisoformat(rows[-1]['occurred_at']) if rows else self.clock()
                self.events.process(ApplicationEvent(question_id, patient_id, EventType.PATIENT_FREE_TEXT,
                    at, self.clock(), 'synthetic_patient_ui', {'text': question}, question_id, question_id))
            with self.events.repositories.transaction() as repo:
                signature, blocked, latest, state = self._approval(repo, patient_id, client_offline)
                if run_id.startswith('arrival-'):
                    from .assessment import arrival_id
                    if role not in {AgentRole.CLINICIAN_BRIEF, AgentRole.PATIENT_INSIGHT} or run_id != arrival_id(role, window_days, signature):
                        raise AppError('STALE_ASSESSMENT', 'Record changed; reload the current assessment', 409)
                cached = repo.agent_run(patient_id, run_id)
                if cached:
                    if cached["request_fingerprint"] != options:
                        raise AppError("AGENT_RUN_CONFLICT", "Run ID belongs to different options", 409)
                    # Do not replay old permitted content over newly unsafe state.
                    if cached["state_fingerprint"] != signature:
                        return {"run_id": run_id, "status": "STALE", "draft": {"claims": [], "question_ids": []},
                                "generation_used": False, "disclosure": "Record changed. Request a fresh draft.", "sources": [], "trace": []}
                    return {**cached, "idempotent_replay": True}
            if getattr(self.provider, "live", False) and not self.synthetic_only:
                blocked = blocked or "LIVE_SYNTHETIC_ONLY"
            result = {"draft": {"claims": [], "question_ids": []}, "trace": [], "sources": [],
                      "reason": blocked, "generation_used": False, "elapsed_ms": 0,
                      "prompt_version": "aura-agent-v1", "config_version": self.config.version}
            if not blocked:
                tools, evidence = self.record_tools(patient_id, role, window_days)
                with self.events.repositories.transaction() as repo:
                    if self._approval(repo, patient_id, client_offline)[0] != signature:
                        blocked = "STATE_CHANGED_BEFORE_GENERATION"
                if not blocked:
                    result = run(role, question or QUERIES.get(query_id), tools, self.provider, self.config,
                                 presentation=role in {AgentRole.CLINICIAN_BRIEF, AgentRole.PATIENT_INSIGHT})
                    if role == AgentRole.PATIENT_INSIGHT:
                        import re
                        if re.search(r'\b(?:baseline|drift|anchor|reestablishing)\b', json.dumps(result['draft']).lower()):
                            from aura_agent.templates import fallback
                            result.update(draft=fallback(tools, role), generation_used=False, reason='PLAIN_LANGUAGE_EXTRACTION')
                    # Patient recap is optional; no new interruption authorization.
                    if role == AgentRole.PATIENT_INSIGHT and not tools.required:
                        result["draft"] = {"claims": [], "question_ids": []}
                    if role == AgentRole.QUESTION_RANKER and evidence["current_decision"] == "STAY_QUIET":
                        result["draft"]["question_ids"] = []
            with self.events.repositories.transaction() as repo:
                current, new_block, latest, state = self._approval(repo, patient_id, client_offline)
                if current != signature:
                    blocked = new_block or "STATE_CHANGED_DURING_GENERATION"
                if blocked:
                    result.update(draft={"claims": [], "question_ids": []}, sources=[], generation_used=False, reason=blocked)
                result.update(run_id=run_id, patient_id=patient_id, role=role.value,
                    query_id=query_id, window_days=window_days, status="BLOCKED" if blocked else "COMPLETE",
                    created_at=self.clock().isoformat(), request_fingerprint=options, state_fingerprint=signature,
                    model_id=self.provider.model_id, safety_reference={"sequence": (state or {}).get("sequence"), "episode_id": (state or {}).get("episode_id")},
                    question_options=QUESTIONS, share_status="NOT_SENT", automatically_sent=False,
                    disclosure=("Assistant paused: safety interaction or record evaluation comes first." if blocked else
                                "Checked AI claims; unsupported claims removed. Required history uses labelled source extraction where needed." if result.get('reason')=='VALIDATED_PARTIAL_MODEL_DRAFT' else
                                "AI draft from synthetic records — check the linked sources." if result["generation_used"] else
                                "Summary from the record; generated wording is unavailable or was not validated."))
                repo.append_agent_run(result)
                repo.append_audit({"patient_id": patient_id, "event_id": latest["event_id"] if latest else "agent-no-event",
                    "correlation_id": run_id, "action": "AGENT_RUN", "called_domains": ["aura_agent", "aura_safety.output"],
                    "communication": result["reason"], "safety_ref": result["safety_reference"]["episode_id"],
                    "review_item_ids": [], "anchor_command": None, "idempotency_result": "NEW", "timestamp": result["created_at"]})
                return result

    def trace(self, patient_id, run_id):
        with self.events.repositories.transaction() as repo:
            self.events._patient(repo, patient_id)
            result = repo.agent_run(patient_id, run_id)
            if result is None:
                raise AppError("AGENT_RUN_NOT_FOUND", "Assistant run not found", 404)
            return result
