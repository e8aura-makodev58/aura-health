"""Shared read-only patient/clinician evidence. Never evaluate or replay policy.

Coordinates, labels and source links describe already committed values. Historical
snapshots remain historical; gaps/deferred results are never filled from current state.
This service is not clinician authorization or a patient sharing workflow.
"""

from datetime import datetime

from .service import PatientEventService


SIGNALS = {
    "SLEEP_MIDPOINT": ("Sleep timing", "minutes since sleep-start midnight"),
    "SLEEP_DURATION": ("Sleep duration", "hours"),
    "ACTIVITY": ("Activity", None),
    "RESTING_HEART_RATE": ("Resting heart rate", "beats/min"),
}


def identity(row):
    return row["signal"], row["source"], row.get("metric") or ""


class EvidenceViewService:
    def __init__(self, events: PatientEventService):
        self.events = events

    def get(self, patient_id: str) -> dict:
        with self.events.repositories.transaction() as repo:
            patient = self.events._patient(repo, patient_id)
            snapshots = repo.committed_results(patient_id)
            timeline = repo.timeline(patient_id)
            observations = repo.observations(patient_id)
            baselines = repo.baselines(patient_id)
            events = repo.events(patient_id)
            contexts = {row["event_id"]: row["payload"] for row in events
                        if row["event_type"] == "CONTEXT_EVENT"}
            anchor_commands = {row["event_id"]: row["payload"] for row in events
                               if row["event_type"] == "ANCHOR_COMMAND"}
            deferred = {row["event_id"] for row in snapshots
                        if (row["result"] or {}).get("longitudinal", {}).get("deferred")}
            latest = snapshots[-1]["result"] if snapshots else None
            current_projection = (latest or {}).get("longitudinal", {})
            signals = {}

            def signal_for(key):
                key_id = identity(key)
                if key_id not in signals:
                    label, unit = SIGNALS.get(key_id[0], (key_id[0], None))
                    signals[key_id] = {
                        "key": {"signal": key_id[0], "source": key_id[1], "metric": key_id[2]},
                        "label": label, "unit": unit or key_id[2] or "recorded units",
                        "current": None, "observations": [], "history": [],
                        "contexts": [], "findings": [], "anchor_commands": [], "gaps": [],
                    }
                return signals[key_id]

            for row in baselines:
                signal_for(row)["current"] = row
            for row in observations:
                signal_for(row)["observations"].append({
                    key: row[key] for key in ("event_id", "day", "value", "coverage", "data_quality")
                } | {"deferred": row["event_id"] in deferred})
            for snapshot in snapshots:
                projection = (snapshot["result"] or {}).get("longitudinal", {})
                for baseline in projection.get("baselines", []):
                    signal_for(baseline)["history"].append({
                        "event_id": snapshot["event_id"], "at": snapshot["occurred_at"],
                        "commit_order": snapshot["commit_order"],
                        "anchor": baseline["anchor"], "rolling": baseline["rolling"],
                        "sensing_state": baseline["sensing_state"], "trust_state": baseline["trust_state"],
                    })

            findings = {}
            for row in timeline:
                detail = row["detail"]
                if row["record_type"] == "LONGITUDINAL_DRIFT":
                    if detail["kind"] in {"STABLE", "INSUFFICIENT_DATA"}:
                        continue
                    key = (*identity(detail["key"]), detail["kind"])
                    finding = findings.setdefault(key, {
                        "first_seen": row["occurred_at"], "last_seen": row["occurred_at"],
                        "event_id": row["event_id"], "drift": detail,
                    })
                    finding.update(last_seen=row["occurred_at"], event_id=row["event_id"], drift=detail)
                elif row["record_type"] == "CONTEXT_EVENT" and row["event_id"] not in deferred:
                    context = contexts[row["event_id"]]
                    for signal in signals.values():
                        if signal["key"]["signal"] in detail["affected_signals"]:
                            signal["contexts"].append({"event_id": row["event_id"],
                                **{key: context.get(key) for key in ("start", "end", "category",
                                   "affected_signals", "source", "explanation")}})
                elif row["record_type"] == "ANCHOR_COMMAND":
                    command = anchor_commands[row["event_id"]]
                    signal_for(command)["anchor_commands"].append({"event_id": row["event_id"],
                        "at": row["occurred_at"], "action": command["action"],
                        "reference_start": command.get("reference_start"),
                        "reference_end": command.get("reference_end"),
                        "reviewed_by": command.get("reviewed_by")})
                elif row["record_type"] in {"SENSING_GAP", "SENSING_RETURN"}:
                    signal_for(detail)["gaps"].append({"event_id": row["event_id"],
                        "at": row["occurred_at"], "type": row["record_type"], **detail})
            for key, finding in sorted(findings.items()):
                signal_for(finding["drift"]["key"])["findings"].append(finding)

            references = [row for row in repo.safety_references(patient_id)
                          if row["episode_id"] or row["state"]["degraded"]
                          or row["state"]["interaction_mode"] != "NORMAL"]
            timestamps = {row["event_id"]: row["occurred_at"] for row in snapshots}
            references = [{**row, "at": timestamps.get(row["event_id"])} for row in references]
            stamps = [row["occurred_at"] for row in snapshots]
            ordered = sorted(signals.values(), key=lambda row: (
                list(SIGNALS).index(row["key"]["signal"]) if row["key"]["signal"] in SIGNALS else 99,
                row["key"]["source"], row["key"]["metric"]))
            return {
                "version": "read-only-evidence-v1", "patient": patient,
                "period": {"start": min(stamps, key=datetime.fromisoformat) if stamps else None,
                           "end": max(stamps, key=datetime.fromisoformat) if stamps else None},
                "snapshot_count": len(snapshots), "signals": ordered,
                "checkins": [{"event_id": row["event_id"], "at": row["occurred_at"],
                    "state": row["detail"]["state"], "deferred": row["event_id"] in deferred}
                    for row in timeline if row["record_type"] == "PATIENT_CHECKIN"],
                "medication": [{"event_id": row["event_id"], "at": row["occurred_at"],
                    "status": row["detail"]["status"], "deferred": row["event_id"] in deferred}
                    for row in timeline if row["record_type"] == "MEDICATION_EVENT"],
                "held": repo.held(patient_id), "review_items": repo.review_items(patient_id),
                "questions": [{"event_id": row["event_id"], "at": row["occurred_at"],
                    "question": row["payload"]["question"]} for row in events
                    if row["event_type"] == "REVIEW_COMMAND" and row["payload"].get("action") == "ADD_QUESTION"
                    and row["event_id"] not in deferred and row["payload"].get("question")],
                "active_context": current_projection.get("active_contexts", []),
                "current_decision": (latest or {}).get("communication_decision", "STAY_QUIET"),
                "safety": {"state": repo.safety_state(patient_id), "references": references},
                "unavailable_snapshots": [{"event_id": row["event_id"], "at": row["occurred_at"],
                    "reason": "DEFERRED" if row["event_id"] in deferred else "NO_COMMITTED_BASELINES"}
                    for row in snapshots if not (row["result"] or {}).get("longitudinal", {}).get("baselines")],
                "share_status": "NOT_SHARED", "automatically_sent": False,
                "coverage_scope": "Stored current rolling-window availability, not selected chart-period coverage",
            }
