"""SQLite development adapter. A single transaction encloses each event and output."""

from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3
from typing import Any, Iterator

from .repositories import RepositoryConflict


SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS patients (
 patient_id TEXT PRIMARY KEY, display_name TEXT NOT NULL, age INTEGER NOT NULL,
 timezone TEXT NOT NULL, onboarding_status TEXT NOT NULL, created_at TEXT NOT NULL,
 active INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS treatment_context (
 patient_id TEXT PRIMARY KEY, medication_name TEXT, medication_schedule TEXT,
 regimen_start TEXT, stable_since TEXT, treating_clinician_ref TEXT,
 review_cadence TEXT, next_review TEXT, treatment_notes TEXT, supply_days INTEGER, last_refill TEXT,
 FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
);
CREATE TABLE IF NOT EXISTS consents (
 patient_id TEXT NOT NULL, consent_type TEXT NOT NULL, granted INTEGER NOT NULL,
 timestamp TEXT NOT NULL, version TEXT NOT NULL,
 PRIMARY KEY(patient_id, consent_type), FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
);
CREATE TABLE IF NOT EXISTS wearable_sources (
 patient_id TEXT NOT NULL, source_id TEXT NOT NULL, source_type TEXT NOT NULL,
 connected INTEGER NOT NULL, last_seen TEXT, consent_status TEXT NOT NULL,
 PRIMARY KEY(patient_id, source_id), FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
);
CREATE TABLE IF NOT EXISTS app_events (
 event_id TEXT PRIMARY KEY, patient_id TEXT NOT NULL, event_type TEXT NOT NULL,
 occurred_at TEXT NOT NULL, received_at TEXT NOT NULL, source TEXT NOT NULL,
 payload_json TEXT NOT NULL, correlation_id TEXT NOT NULL, idempotency_key TEXT NOT NULL,
 result_json TEXT, UNIQUE(patient_id, idempotency_key),
 FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
);
CREATE TABLE IF NOT EXISTS observations (
 event_id TEXT NOT NULL, patient_id TEXT NOT NULL, signal TEXT NOT NULL, source TEXT NOT NULL,
 metric TEXT NOT NULL DEFAULT '', day TEXT NOT NULL, value REAL NOT NULL,
 coverage REAL NOT NULL, data_quality REAL NOT NULL,
 PRIMARY KEY(event_id, signal, source, metric), FOREIGN KEY(event_id) REFERENCES app_events(event_id)
);
CREATE TABLE IF NOT EXISTS checkins (
 event_id TEXT PRIMARY KEY, patient_id TEXT NOT NULL, timestamp TEXT NOT NULL,
 state TEXT NOT NULL, structured_json TEXT NOT NULL, tags_json TEXT NOT NULL,
 FOREIGN KEY(event_id) REFERENCES app_events(event_id)
);
CREATE TABLE IF NOT EXISTS medication_events (
 event_id TEXT PRIMARY KEY, patient_id TEXT NOT NULL, scheduled_time TEXT NOT NULL,
 timestamp TEXT NOT NULL, status TEXT NOT NULL, source TEXT NOT NULL, reason TEXT,
 FOREIGN KEY(event_id) REFERENCES app_events(event_id)
);
CREATE TABLE IF NOT EXISTS contexts (
 event_id TEXT PRIMARY KEY, patient_id TEXT NOT NULL, start_at TEXT NOT NULL,
 end_at TEXT, category TEXT NOT NULL, affected_json TEXT NOT NULL,
 source TEXT NOT NULL, explanation TEXT,
 FOREIGN KEY(event_id) REFERENCES app_events(event_id)
);
CREATE TABLE IF NOT EXISTS context_explanations (
 event_id TEXT PRIMARY KEY, patient_id TEXT NOT NULL, relevant_drift_ref TEXT,
 explanation TEXT NOT NULL, affected_json TEXT NOT NULL, created_at TEXT NOT NULL,
 status TEXT NOT NULL, FOREIGN KEY(event_id) REFERENCES app_events(event_id)
);
CREATE TABLE IF NOT EXISTS baselines (
 patient_id TEXT NOT NULL, signal TEXT NOT NULL, source TEXT NOT NULL, metric TEXT NOT NULL DEFAULT '',
 anchor_json TEXT, trust_state TEXT NOT NULL, sensing_state TEXT NOT NULL,
 rolling_json TEXT NOT NULL, updated_at TEXT NOT NULL,
 PRIMARY KEY(patient_id, signal, source, metric), FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
);
CREATE TABLE IF NOT EXISTS held_drifts (
 patient_id TEXT NOT NULL, signal TEXT NOT NULL, source TEXT NOT NULL, metric TEXT NOT NULL DEFAULT '',
 direction INTEGER NOT NULL, status TEXT NOT NULL, record_json TEXT NOT NULL,
 PRIMARY KEY(patient_id, signal, source, metric, direction), FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
);
CREATE TABLE IF NOT EXISTS review_items (
 item_id TEXT PRIMARY KEY, patient_id TEXT NOT NULL, source_ref TEXT NOT NULL,
 summary TEXT NOT NULL, created_at TEXT NOT NULL, status TEXT NOT NULL,
 patient_visible INTEGER NOT NULL, share_status TEXT NOT NULL,
 UNIQUE(patient_id, source_ref), FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
);
CREATE TABLE IF NOT EXISTS safety_states (
 patient_id TEXT PRIMARY KEY, state_json TEXT NOT NULL, FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
);
CREATE TABLE IF NOT EXISTS safety_references (
 event_id TEXT PRIMARY KEY, patient_id TEXT NOT NULL, episode_id TEXT,
 source_episode_id TEXT, previous_episode_id TEXT, sequence INTEGER NOT NULL, outcome TEXT NOT NULL,
 state_json TEXT NOT NULL, FOREIGN KEY(event_id) REFERENCES app_events(event_id)
);
CREATE TABLE IF NOT EXISTS archived_safety_episodes (
 patient_id TEXT NOT NULL, episode_id TEXT NOT NULL, final_state_json TEXT NOT NULL,
 archived_by_event_id TEXT NOT NULL, previous_episode_id TEXT,
 PRIMARY KEY(patient_id, episode_id), FOREIGN KEY(archived_by_event_id) REFERENCES app_events(event_id)
);
CREATE TABLE IF NOT EXISTS timeline (
 entry_id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id TEXT NOT NULL, event_id TEXT NOT NULL,
 record_type TEXT NOT NULL, occurred_at TEXT NOT NULL, detail_json TEXT NOT NULL,
 FOREIGN KEY(event_id) REFERENCES app_events(event_id)
);
CREATE INDEX IF NOT EXISTS timeline_order ON timeline(patient_id, occurred_at, entry_id);
CREATE TABLE IF NOT EXISTS audit (
 audit_id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id TEXT NOT NULL, event_id TEXT NOT NULL,
 correlation_id TEXT NOT NULL, action TEXT NOT NULL, domains_json TEXT NOT NULL,
 communication TEXT, safety_ref TEXT, review_items_json TEXT NOT NULL,
 anchor_command TEXT, idempotency_result TEXT NOT NULL, timestamp TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS safety_audit (
 attempt_id INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT NOT NULL, patient_id TEXT NOT NULL, episode_id TEXT,
 sequence INTEGER NOT NULL, policy_version TEXT NOT NULL, policy_config_version TEXT NOT NULL,
 record_json TEXT NOT NULL, FOREIGN KEY(event_id) REFERENCES app_events(event_id)
);
CREATE TABLE IF NOT EXISTS communication_outputs (
 communication_id TEXT PRIMARY KEY, patient_id TEXT NOT NULL, event_id TEXT NOT NULL,
 safety_sequence INTEGER, episode_id TEXT, mode TEXT, prompt_version TEXT NOT NULL,
 config_version TEXT NOT NULL, model_id TEXT, generation_used INTEGER NOT NULL,
 created_at TEXT NOT NULL, result_json TEXT NOT NULL,
 FOREIGN KEY(patient_id) REFERENCES patients(patient_id),
 FOREIGN KEY(event_id) REFERENCES app_events(event_id)
);
CREATE INDEX IF NOT EXISTS communication_patient ON communication_outputs(patient_id, created_at);
CREATE TABLE IF NOT EXISTS agent_runs (
 run_id TEXT NOT NULL, patient_id TEXT NOT NULL, role TEXT NOT NULL,
 created_at TEXT NOT NULL, result_json TEXT NOT NULL,
 PRIMARY KEY(patient_id,run_id), FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
);
CREATE TRIGGER IF NOT EXISTS agent_runs_no_update BEFORE UPDATE ON agent_runs
BEGIN SELECT RAISE(ABORT, 'agent runs are append-only'); END;
CREATE TRIGGER IF NOT EXISTS agent_runs_no_delete BEFORE DELETE ON agent_runs
BEGIN SELECT RAISE(ABORT, 'agent runs are append-only'); END;
CREATE TABLE IF NOT EXISTS workflow_runs (
 patient_id TEXT NOT NULL, run_id TEXT NOT NULL, kind TEXT NOT NULL,
 created_at TEXT NOT NULL, result_json TEXT NOT NULL,
 PRIMARY KEY(patient_id,run_id), FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
);
CREATE TRIGGER IF NOT EXISTS workflow_runs_no_update BEFORE UPDATE ON workflow_runs
BEGIN SELECT RAISE(ABORT, 'workflow runs are append-only'); END;
CREATE TRIGGER IF NOT EXISTS workflow_runs_no_delete BEFORE DELETE ON workflow_runs
BEGIN SELECT RAISE(ABORT, 'workflow runs are append-only'); END;
"""


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


class SQLiteUnitOfWork:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def _one(self, sql: str, args: tuple = ()) -> dict | None:
        row = self.conn.execute(sql, args).fetchone()
        return dict(row) if row else None

    def _all(self, sql: str, args: tuple = ()) -> list[dict]:
        return [dict(row) for row in self.conn.execute(sql, args).fetchall()]

    def patient(self, patient_id):
        row = self._one("SELECT * FROM patients WHERE patient_id=?", (patient_id,))
        if row:
            row["active"] = bool(row["active"])
            legacy = row.pop("treatment_json", None)
            treatment = self._one("SELECT * FROM treatment_context WHERE patient_id=?", (patient_id,))
            if treatment:
                treatment.pop("patient_id")
            row["treatment"] = treatment or (json.loads(legacy) if legacy else {})
        return row

    def create_patient(self, row):
        try:
            self.conn.execute("INSERT INTO patients(patient_id,display_name,age,timezone,onboarding_status,created_at,active) VALUES (?,?,?,?,?,?,?)",
                              (row["patient_id"], row["display_name"], row["age"], row["timezone"],
                               row["onboarding_status"], row["created_at"], int(row["active"])))
        except sqlite3.IntegrityError as exc:
            raise RepositoryConflict("patient already exists") from exc

    def save_treatment(self, row):
        self.conn.execute("INSERT INTO treatment_context (patient_id,medication_name,medication_schedule,regimen_start,stable_since,treating_clinician_ref,review_cadence,next_review,treatment_notes,supply_days,last_refill) VALUES (?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(patient_id) DO UPDATE SET medication_name=excluded.medication_name,medication_schedule=excluded.medication_schedule,regimen_start=excluded.regimen_start,stable_since=excluded.stable_since,treating_clinician_ref=excluded.treating_clinician_ref,review_cadence=excluded.review_cadence,next_review=excluded.next_review,treatment_notes=excluded.treatment_notes,supply_days=excluded.supply_days,last_refill=excluded.last_refill",
                          (row["patient_id"], row.get("medication_name"), row.get("medication_schedule"),
                           row.get("regimen_start"), row.get("stable_since"), row.get("treating_clinician_ref"),
                           row.get("review_cadence"), row.get("next_review"), row.get("treatment_notes"),
                           row.get("supply_days"), row.get("last_refill")))

    def consents(self, patient_id):
        return self._all("SELECT * FROM consents WHERE patient_id=? ORDER BY consent_type", (patient_id,))

    def save_wearable_source(self, row):
        self.conn.execute("INSERT INTO wearable_sources VALUES (?,?,?,?,?,?)",
                          (row["patient_id"], row["source_id"], row["source_type"], int(row["connected"]),
                           row.get("last_seen"), row["consent_status"]))

    def save_consent(self, row):
        self.conn.execute("INSERT INTO consents VALUES (?,?,?,?,?) ON CONFLICT(patient_id,consent_type) DO UPDATE SET granted=excluded.granted,timestamp=excluded.timestamp,version=excluded.version",
                          (row["patient_id"], row["consent_type"], int(row["granted"]), row["timestamp"], row["version"]))

    def prior_result(self, patient_id, idempotency_key):
        row = self._one("SELECT result_json FROM app_events WHERE patient_id=? AND idempotency_key=?", (patient_id, idempotency_key))
        return json.loads(row["result_json"]) if row and row["result_json"] else None

    def events(self, patient_id):
        rows = self._all("SELECT * FROM app_events WHERE patient_id=? ORDER BY rowid", (patient_id,))
        for row in rows:
            row["payload"] = json.loads(row.pop("payload_json"))
            result_json = row.pop("result_json")
            result = json.loads(result_json) if result_json else None
            row["longitudinal_deferred"] = bool(result and result.get("longitudinal", {}).get("deferred"))
        return rows

    def save_event(self, row):
        try:
            self.conn.execute("INSERT INTO app_events VALUES (?,?,?,?,?,?,?,?,?,NULL)",
                              (row["event_id"], row["patient_id"], row["event_type"], row["occurred_at"],
                               row["received_at"], row["source"], _json(row["payload"]),
                               row["correlation_id"], row["idempotency_key"]))
        except sqlite3.IntegrityError as exc:
            raise RepositoryConflict("event ID or idempotency key exists") from exc

    def committed_results(self, patient_id):
        """Original committed snapshots, not replay or today's mutable baselines."""
        rows = self._all("SELECT rowid AS commit_order,event_id,event_type,occurred_at,received_at,result_json "
                         "FROM app_events WHERE patient_id=? ORDER BY rowid", (patient_id,))
        for row in rows:
            raw = row.pop("result_json")
            row["result"] = json.loads(raw) if raw else None
        return rows

    def save_result(self, event_id, result):
        self.conn.execute("UPDATE app_events SET result_json=? WHERE event_id=?", (_json(result), event_id))

    def append_timeline(self, row):
        self.conn.execute("INSERT INTO timeline(patient_id,event_id,record_type,occurred_at,detail_json) VALUES (?,?,?,?,?)",
                          (row["patient_id"], row["event_id"], row["record_type"], row["occurred_at"], _json(row["detail"])))

    def timeline(self, patient_id):
        rows = self._all("SELECT entry_id,event_id,record_type,occurred_at,detail_json FROM timeline WHERE patient_id=? ORDER BY occurred_at,entry_id", (patient_id,))
        for row in rows:
            row["detail"] = json.loads(row.pop("detail_json"))
        return rows

    def save_observation(self, row):
        self.conn.execute("INSERT INTO observations VALUES (?,?,?,?,?,?,?,?,?)",
                          (row["event_id"], row["patient_id"], row["signal"], row["source"], row.get("metric") or "",
                           row["day"], row["value"], row["coverage"], row["data_quality"]))
        self.conn.execute("UPDATE wearable_sources SET last_seen=? WHERE patient_id=? AND source_id=?",
                          (row["day"], row["patient_id"], row["source"]))

    def observations(self, patient_id):
        return self._all("SELECT * FROM observations WHERE patient_id=? ORDER BY day,event_id,signal", (patient_id,))

    def save_checkin(self, row):
        self.conn.execute("INSERT INTO checkins VALUES (?,?,?,?,?,?)",
                          (row["event_id"], row["patient_id"], row["timestamp"], row["state"],
                           _json(row.get("structured_answers", {})), _json(row.get("context_tags", []))))

    def save_medication(self, row):
        self.conn.execute("INSERT INTO medication_events (event_id,patient_id,scheduled_time,timestamp,status,source,reason) VALUES (?,?,?,?,?,?,?)",
                          (row["event_id"], row["patient_id"], row["scheduled_time"], row["timestamp"],
                           row["status"], row["source"], row.get("reason")))

    def medication_events(self, patient_id):
        return self._all("SELECT * FROM medication_events WHERE patient_id=? ORDER BY rowid", (patient_id,))

    def save_baseline(self, row):
        self.conn.execute("INSERT INTO baselines VALUES (?,?,?,?,?,?,?, ?,?) ON CONFLICT(patient_id,signal,source,metric) DO UPDATE SET anchor_json=excluded.anchor_json,trust_state=excluded.trust_state,sensing_state=excluded.sensing_state,rolling_json=excluded.rolling_json,updated_at=excluded.updated_at",
                          (row["patient_id"], row["signal"], row["source"], row.get("metric") or "",
                           _json(row["anchor"]) if row["anchor"] else None, row["trust_state"], row["sensing_state"],
                           _json(row["rolling"]), row["updated_at"]))

    def baselines(self, patient_id):
        rows = self._all("SELECT * FROM baselines WHERE patient_id=? ORDER BY signal,source,metric", (patient_id,))
        for row in rows:
            row["anchor"] = json.loads(row.pop("anchor_json")) if row["anchor_json"] else None
            row["rolling"] = json.loads(row.pop("rolling_json"))
        return rows

    def save_context(self, row):
        self.conn.execute("INSERT INTO contexts VALUES (?,?,?,?,?,?,?,?)",
                          (row["event_id"], row["patient_id"], row["start_at"], row.get("end_at"), row["category"],
                           _json(row["affected_signals"]), row["source"], row.get("explanation")))

    def save_explanation(self, row):
        self.conn.execute("INSERT INTO context_explanations VALUES (?,?,?,?,?,?,?)",
                          (row["event_id"], row["patient_id"], row.get("relevant_drift_ref"), row["explanation"],
                          _json(row["affected_signals"]), row["created_at"], row["status"]))

    def update_explanation_status(self, event_id, status):
        self.conn.execute("UPDATE context_explanations SET status=? WHERE event_id=?", (status, event_id))

    def save_held(self, row):
        self.conn.execute("INSERT INTO held_drifts VALUES (?,?,?,?,?,?,?) ON CONFLICT(patient_id,signal,source,metric,direction) DO UPDATE SET status=excluded.status,record_json=excluded.record_json",
                          (row["patient_id"], row["signal"], row["source"], row.get("metric") or "",
                           row["direction"], row["status"], _json(row["record"])))

    def held(self, patient_id):
        rows = self._all("SELECT * FROM held_drifts WHERE patient_id=? ORDER BY signal,source,metric,direction", (patient_id,))
        for row in rows:
            row["record"] = json.loads(row.pop("record_json"))
        return rows

    def save_review_item(self, row):
        self.conn.execute("INSERT OR IGNORE INTO review_items VALUES (?,?,?,?,?,?,?,?)",
                          (row["item_id"], row["patient_id"], row["source_ref"], row["summary"], row["created_at"],
                           row.get("status", "OPEN"), int(row.get("patient_visible", True)), row.get("share_status", "NOT_SHARED")))

    def review_items(self, patient_id):
        rows = self._all("SELECT * FROM review_items WHERE patient_id=? ORDER BY created_at,item_id", (patient_id,))
        for row in rows:
            row["patient_visible"] = bool(row["patient_visible"])
        return rows

    def safety_state(self, patient_id):
        row = self._one("SELECT state_json FROM safety_states WHERE patient_id=?", (patient_id,))
        return json.loads(row["state_json"]) if row else None

    def save_safety_state(self, patient_id, state):
        self.conn.execute("INSERT INTO safety_states VALUES (?,?) ON CONFLICT(patient_id) DO UPDATE SET state_json=excluded.state_json",
                          (patient_id, _json(state)))

    def save_safety_reference(self, row):
        self.conn.execute("INSERT INTO safety_references(event_id,patient_id,episode_id,source_episode_id,previous_episode_id,sequence,outcome,state_json) VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(event_id) DO UPDATE SET episode_id=excluded.episode_id,source_episode_id=excluded.source_episode_id,previous_episode_id=excluded.previous_episode_id,sequence=excluded.sequence,outcome=excluded.outcome,state_json=excluded.state_json",
                          (row["event_id"], row["patient_id"], row.get("episode_id"), row.get("source_episode_id"),
                           row.get("previous_episode_id"),
                           row["sequence"], row["outcome"], _json(row["state"])))

    def save_archived_safety_episode(self, row):
        self.conn.execute("INSERT OR IGNORE INTO archived_safety_episodes VALUES (?,?,?,?,?)",
                          (row["patient_id"], row["episode_id"], _json(row["final_state"]),
                           row["archived_by_event_id"], row.get("previous_episode_id")))

    def safety_references(self, patient_id):
        rows = self._all("SELECT * FROM safety_references WHERE patient_id=? ORDER BY rowid", (patient_id,))
        for row in rows:
            row["state"] = json.loads(row.pop("state_json"))
        return rows

    def append_audit(self, row):
        self.conn.execute("INSERT INTO audit(patient_id,event_id,correlation_id,action,domains_json,communication,safety_ref,review_items_json,anchor_command,idempotency_result,timestamp) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                          (row["patient_id"], row["event_id"], row["correlation_id"], row["action"],
                           _json(row["called_domains"]), row.get("communication"), row.get("safety_ref"),
                           _json(row.get("review_item_ids", [])), row.get("anchor_command"),
                           row["idempotency_result"], row["timestamp"]))

    def audit(self, patient_id):
        rows = self._all("SELECT * FROM audit WHERE patient_id=? ORDER BY audit_id", (patient_id,))
        for row in rows:
            row["called_domains"] = json.loads(row.pop("domains_json"))
            row["review_item_ids"] = json.loads(row.pop("review_items_json"))
        return rows

    def append_safety_audit(self, row):
        self.conn.execute("INSERT INTO safety_audit(event_id,patient_id,episode_id,sequence,policy_version,policy_config_version,record_json) VALUES (?,?,?,?,?,?,?)",
                          (row["event_id"], row["patient_id"], row.get("episode_id"), row["sequence"],
                           row["policy_version"], row["policy_config_version"], _json(row["record"])))

    def communication_record(self, communication_id):
        row = self._one("SELECT result_json FROM communication_outputs WHERE communication_id=?", (communication_id,))
        return json.loads(row["result_json"]) if row else None

    def append_communication_record(self, communication_id, row):
        self.conn.execute("INSERT INTO communication_outputs VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                          (communication_id, row["patient_id"], row["event_id"], row["safety_reference"]["sequence"],
                           row["safety_reference"]["episode_id"], row["mode"], row["prompt_version"],
                           row["config_version"], row["model_id"], int(row["generation_used"]),
                           row["created_at"], _json(row)))

    def communication_records(self, patient_id):
        rows = self._all("SELECT result_json FROM communication_outputs WHERE patient_id=? ORDER BY rowid", (patient_id,))
        return [json.loads(row["result_json"]) for row in rows]

    def agent_run(self, patient_id, run_id):
        row = self._one("SELECT result_json FROM agent_runs WHERE patient_id=? AND run_id=?", (patient_id, run_id))
        return json.loads(row["result_json"]) if row else None

    def append_agent_run(self, row):
        self.conn.execute("INSERT INTO agent_runs VALUES (?,?,?,?,?)",
                          (row["run_id"], row["patient_id"], row["role"], row["created_at"], _json(row)))

    def workflow_run(self, patient_id, run_id):
        row = self._one('SELECT result_json FROM workflow_runs WHERE patient_id=? AND run_id=?', (patient_id, run_id))
        return json.loads(row['result_json']) if row else None

    def append_workflow_run(self, row):
        self.conn.execute('INSERT INTO workflow_runs VALUES (?,?,?,?,?)',
                          (row['patient_id'], row['run_id'], row['kind'], row['created_at'], _json(row)))

    def workflow_runs(self,patient_id):
        return [json.loads(row['result_json']) for row in self._all('SELECT result_json FROM workflow_runs WHERE patient_id=? ORDER BY rowid',(patient_id,))]


class SQLiteRepositoryFactory:
    def __init__(self, path: str | Path):
        self.path = str(path)

    def initialize(self):
        with sqlite3.connect(self.path) as conn:
            conn.executescript(SCHEMA)
            columns = {row[1] for row in conn.execute("PRAGMA table_info(safety_references)")}
            if "previous_episode_id" not in columns:
                conn.execute("ALTER TABLE safety_references ADD COLUMN previous_episode_id TEXT")
            for table, additions in {
                "treatment_context": {"supply_days": "INTEGER", "last_refill": "TEXT"},
                "medication_events": {"reason": "TEXT"},
            }.items():
                columns = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
                for name, sql_type in additions.items():
                    if name not in columns:
                        conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {sql_type}")

    @contextmanager
    def transaction(self) -> Iterator[SQLiteUnitOfWork]:
        conn = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("BEGIN IMMEDIATE")
        try:
            yield SQLiteUnitOfWork(conn)
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description="Initialize the AURA development SQLite schema")
    parser.add_argument("--db", default="aura-m4-development.sqlite3")
    args = parser.parse_args(argv)
    SQLiteRepositoryFactory(args.db).initialize()
    print(f"Initialized development DB: {args.db}")


if __name__ == "__main__":
    main()
