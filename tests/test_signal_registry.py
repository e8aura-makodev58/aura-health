"""SR1–SR16: sponsor configuration, real missingness, and new-signal isolation.

Only synthetic measurements. No real wearable, detector or live model calls.
"""

from copy import deepcopy
from dataclasses import asdict, replace
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from aura_agent.grounding import validate
from aura_agent.roles import AgentRole
from aura_agent.tools import RecordTools
from aura_app.api import create_app
from aura_app.agent import AgentService
from aura_app.evidence import EvidenceViewService
from aura_app.models import AppError, ApplicationEvent, EventType
from aura_app.persistence import SQLiteRepositoryFactory
from aura_app.service import PatientEventService
from aura_longitudinal.baseline import AnchorAction, AnchorCommand, BaselineManager
from aura_longitudinal.config import load_config
from aura_longitudinal.domain import ObservationPoint, Signal, SignalKey
from aura_longitudinal.drift import assess_drift, DriftKind
from aura_longitudinal.registry import LEGACY_SIGNALS, load_registry, SignalRegistry


START = datetime(2026, 1, 1, 12, tzinfo=timezone.utc)


def registry_with(signal, **updates):
    raw = load_registry().public()
    raw = {key: raw[key] for key in ("version", "signals", "communication_overrides")}
    for definition in raw["signals"]:
        if definition["name"] == signal.value:
            definition.update(updates)
    return SignalRegistry(raw)


def point(key, day, value):
    return ObservationPoint(key, START.date() + timedelta(days=day), value, 1, 1)


def scalar(signal, day, value, *, unit=None):
    return {"kind": "scalar", "signal": signal.value,
            "date": (START + timedelta(days=day)).date().isoformat(), "value": value,
            "coverage": 1, "data_quality": 1, "source": "synthetic_sensor",
            "unit": unit or load_registry().definition(signal).unit}


class SignalRegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "registry.sqlite3"
        self.factory = SQLiteRepositoryFactory(self.db)
        self.factory.initialize()
        self.service = PatientEventService(self.factory)
        self.service.create_patient(patient_id="synthetic-registry", display_name="Synthetic",
                                    age=38, timezone_name="UTC",
                                    consents=[{"consent_type": "WEARABLE", "granted": True}])

    def ingest(self, observations, day, service=None, suffix=""):
        eid = f"measurement-{day}{suffix}"
        at = START + timedelta(days=day)
        event = ApplicationEvent(eid, "synthetic-registry", EventType.WEARABLE_OBSERVATION,
                                 at, at, "SIMULATOR", {"observations": observations}, eid, eid)
        return (service or self.service).process(event)

    def test_sr1_legacy_values_are_unchanged(self):
        registry = load_registry()
        for signal in LEGACY_SIGNALS:
            self.assertEqual(asdict(registry.config_for(signal)), asdict(load_config()))
            self.assertTrue(registry.definition(signal).enabled_in_engine)
            self.assertEqual(registry.definition(signal).engineering_overrides, {})

    def test_sr2_research_defaults_and_sparse_flags(self):
        registry = load_registry()
        for signal in (Signal.HRV, Signal.RESPIRATORY_RATE, Signal.SKIN_TEMPERATURE_DEVIATION):
            self.assertTrue(registry.definition(signal).enabled_in_engine)
            self.assertEqual(registry.definition(signal).evidence_tier, "E3_RESEARCH")
        for signal in set(Signal) - LEGACY_SIGNALS - {Signal.HRV, Signal.RESPIRATORY_RATE, Signal.SKIN_TEMPERATURE_DEVIATION}:
            self.assertFalse(registry.definition(signal).enabled_in_engine)
            self.assertTrue(registry.definition(signal).display)

    def test_sr3_sparse_opt_in_stays_insufficient_without_interpolation(self):
        registry = registry_with(Signal.BLOOD_PRESSURE_SYSTOLIC, enabled_in_engine=True)
        key = SignalKey(Signal.BLOOD_PRESSURE_SYSTOLIC, "cuff")
        manager = BaselineManager(registry=registry)
        for day in (0, 3, 6, 9, 12):
            manager.ingest(point(key, day, 150))
        rolling = manager.rolling(key, START.date() + timedelta(days=13))
        self.assertEqual((rolling.sample_count, rolling.coverage_ratio), (5, 5 / 14))
        self.assertFalse(rolling.sufficient)
        self.assertIsNone(rolling.mean)
        self.assertEqual(len(rolling.points), 5)
        self.assertEqual(assess_drift(rolling, None).kind, DriftKind.INSUFFICIENT_DATA)

    def test_sr4_sparse_anchor_cannot_be_manufactured(self):
        registry = registry_with(Signal.WEIGHT, enabled_in_engine=True)
        key = SignalKey(Signal.WEIGHT, "scale")
        manager = BaselineManager(registry=registry)
        refs = tuple(point(key, day, 70) for day in range(0, 70, 7))
        with self.assertRaisesRegex(ValueError, "calendar coverage"):
            manager.apply_anchor_command(AnchorCommand(AnchorAction.CREATE_PROVISIONAL_ANCHOR, key, START, refs))
        self.assertIsNone(manager.anchor(key))

    def test_sr5_repeated_same_day_values_do_not_inflate_coverage(self):
        registry = registry_with(Signal.BLOOD_PRESSURE_DIASTOLIC, enabled_in_engine=True)
        key = SignalKey(Signal.BLOOD_PRESSURE_DIASTOLIC, "cuff")
        manager = BaselineManager(registry=registry)
        for value in range(70, 100):
            manager.ingest(point(key, 0, value))
        rolling = manager.rolling(key, START.date())
        self.assertEqual(rolling.sample_count, 1)
        self.assertFalse(rolling.sufficient)
        self.assertEqual(rolling.coverage_ratio, 1 / 14)

    def test_sr6_display_only_is_persisted_but_not_decision_evidence(self):
        result = self.ingest([scalar(Signal.BODY_TEMPERATURE, 0, 39.5), scalar(Signal.WEIGHT, 0, 70)], 0)
        self.assertEqual(result.communication_decision, "STAY_QUIET")
        self.assertEqual(result.longitudinal["drifts"], [])
        self.assertEqual(result.longitudinal["baselines"], [])
        evidence = EvidenceViewService(self.service).get("synthetic-registry")
        self.assertEqual(len(evidence["signals"]), 2)
        self.assertTrue(all(not row["registry"]["enabled_in_engine"] for row in evidence["signals"]))
        self.assertTrue(all(row["current"] is None and not row["findings"] for row in evidence["signals"]))
        tools = RecordTools(evidence, AgentRole.CLINICIAN_BRIEF)
        tools.call("get_series", {})
        self.assertTrue(any("39.5 degC" in fact["text"] for fact in tools.delivered.values()))
        status = tools.call("get_status", {})
        self.assertTrue(any("display-only" in fact["text"] for fact in status["facts"]))

    def test_sr7_units_nonfinite_and_hidden_truth_are_rejected_atomically(self):
        valid = scalar(Signal.HRV, 0, 40)
        invalid = [dict(valid, unit="seconds"), dict(valid, value=float("nan")),
                   dict(valid, value=True), dict(valid, latent_truth="flu"), dict(valid, coverage=2)]
        for row in invalid:
            with self.assertRaises(AppError):
                self.ingest([row], 0)
        self.assertEqual(self.service.timeline("synthetic-registry"), [])

    def test_sr8_configurable_threshold_is_scoped_to_one_signal(self):
        registry = registry_with(Signal.HRV, engineering_overrides={"rolling_window_days": 21, "minimum_points": 10})
        self.assertEqual(registry.config_for(Signal.HRV).rolling_window_days, 21)
        self.assertEqual(asdict(registry.config_for(Signal.RESTING_HEART_RATE)), asdict(load_config()))
        manager = BaselineManager(registry=registry)
        key = SignalKey(Signal.HRV, "watch")
        for day in range(14): manager.ingest(point(key, day, 40))
        self.assertEqual(manager.rolling(key, START.date() + timedelta(days=13)).coverage_ratio, 14 / 21)

    def test_sr9_zero_center_temperature_uses_inspectable_floor(self):
        registry = load_registry()
        manager = BaselineManager(registry=registry)
        key = SignalKey(Signal.SKIN_TEMPERATURE_DEVIATION, "ring")
        refs = tuple(point(key, day, 0) for day in range(14))
        for item in refs: manager.ingest(item)
        anchor = manager.apply_anchor_command(AnchorCommand(AnchorAction.CREATE_PROVISIONAL_ANCHOR, key, START, refs))
        for day in range(14, 28): manager.ingest(point(key, day, 0.05))
        rolling = manager.rolling(key, START.date() + timedelta(days=27))
        self.assertEqual(assess_drift(rolling, anchor).kind, DriftKind.STABLE)
        for day in range(28, 42): manager.ingest(point(key, day, 0.4))
        rolling = manager.rolling(key, START.date() + timedelta(days=41))
        self.assertEqual(assess_drift(rolling, anchor).kind, DriftKind.PERSISTENT_DRIFT)
        self.assertEqual(manager.anchor(key), anchor)

    def test_sr10_registry_rejects_ambiguous_or_invalid_configuration(self):
        raw = load_registry().public()
        raw = {key: raw[key] for key in ("version", "signals", "communication_overrides")}
        variations = []
        missing = deepcopy(raw); missing["signals"].pop(); variations.append(missing)
        duplicate = deepcopy(raw); duplicate["signals"].append(duplicate["signals"][0]); variations.append(duplicate)
        flag = deepcopy(raw); flag["signals"][0]["enabled_in_engine"] = "false"; variations.append(flag)
        nan = deepcopy(raw); nan["signals"][0]["engineering_overrides"] = {"relative_spread_floor": float("nan")}; variations.append(nan)
        day = deepcopy(raw); day["signals"][0]["engineering_overrides"] = {"rolling_window_days": 3.2}; variations.append(day)
        for variant in variations:
            with self.assertRaises(ValueError): SignalRegistry(variant)

    def test_sr11_external_file_load_and_fingerprint_are_deterministic(self):
        registry = registry_with(Signal.SPO2, enabled_in_engine=True)
        raw = registry.public()
        path = Path(self.temp.name) / "sponsor.json"
        path.write_text(json.dumps({key: raw[key] for key in ("version", "signals", "communication_overrides")}))
        with patch.dict("os.environ", {"AURA_SIGNAL_REGISTRY": str(path)}):
            self.assertEqual(load_registry().fingerprint, registry.fingerprint)
        self.assertNotEqual(registry.fingerprint, load_registry().fingerprint)
        self.assertEqual(registry.fingerprint, registry_with(Signal.SPO2, enabled_in_engine=True).fingerprint)
        original = AgentService(self.service).execute("synthetic-registry", AgentRole.CLINICIAN_BRIEF, run_id="registry-cache")
        self.assertEqual(original["status"], "COMPLETE")
        changed = PatientEventService(self.factory, signal_registry=registry)
        retry = AgentService(changed).execute("synthetic-registry", AgentRole.CLINICIAN_BRIEF, run_id="registry-cache")
        self.assertEqual(retry["status"], "STALE")
        self.assertEqual(retry["draft"]["claims"], [])

    def test_sr12_api_and_restart_preserve_new_measurement(self):
        self.ingest([scalar(Signal.RESPIRATORY_RATE, 0, 15)], 0)
        reopened = PatientEventService(SQLiteRepositoryFactory(self.db))
        with TestClient(create_app(service=reopened)) as client:
            self.assertEqual(len(client.get("/signals").json()["signals"]), 12)
            evidence = client.get("/patients/synthetic-registry/evidence").json()
            self.assertEqual(evidence["signals"][0]["observations"][0]["value"], 15)
            self.assertEqual(evidence["signals"][0]["unit"], "breaths/min")
            self.assertEqual(evidence["signals"][0]["registry"]["evidence_tier"], "E3_RESEARCH")

    def test_sr13_disable_does_not_rewrite_stored_anchor_or_break_history_replay(self):
        for day in range(14): self.ingest([scalar(Signal.HRV, day, 40)], day)
        event = ApplicationEvent("anchor", "synthetic-registry", EventType.ANCHOR_COMMAND,
            START + timedelta(days=14), START + timedelta(days=14), "fixture_reviewer",
            {"signal": "HRV", "source": "synthetic_sensor", "action": "CREATE_PROVISIONAL_ANCHOR"}, "anchor", "anchor")
        self.service.command_anchor(event)
        before = self.service.status("synthetic-registry")["signals"][0]["anchor"]
        disabled = PatientEventService(self.factory, signal_registry=registry_with(Signal.HRV, enabled_in_engine=False))
        result = self.ingest([scalar(Signal.HRV, 15, 10)], 15, disabled)
        self.assertEqual(result.longitudinal["drifts"], [])
        self.assertEqual(disabled.status("synthetic-registry")["signals"], [])
        with self.factory.transaction() as repo:
            self.assertEqual(repo.baselines("synthetic-registry")[0]["anchor"], before)
        with self.assertRaisesRegex(AppError, "display-only"):
            disabled.command_anchor(replace(event, event_id="new-anchor", idempotency_key="new-anchor"))

    def test_sr14_new_signal_ordinary_input_never_moves_anchor(self):
        for day in range(14): self.ingest([scalar(Signal.HRV, day, 40)], day)
        event = ApplicationEvent("anchor", "synthetic-registry", EventType.ANCHOR_COMMAND,
            START + timedelta(days=14), START + timedelta(days=14), "fixture_reviewer",
            {"signal": "HRV", "source": "synthetic_sensor", "action": "CREATE_PROVISIONAL_ANCHOR"}, "anchor", "anchor")
        self.service.command_anchor(event)
        anchor = self.service.status("synthetic-registry")["signals"][0]["anchor"]
        result = self.ingest([scalar(Signal.HRV, 15, 15)], 15)
        self.assertEqual(result.longitudinal["baselines"][0]["anchor"], anchor)
        self.assertEqual(result.longitudinal["registry_reference"]["fingerprint"], load_registry().fingerprint)

    def test_sr15_sponsor_display_switch_is_obeyed(self):
        hidden = PatientEventService(self.factory, signal_registry=registry_with(Signal.WEIGHT, display=False))
        self.ingest([scalar(Signal.WEIGHT, 0, 70)], 0, hidden)
        self.assertEqual(EvidenceViewService(hidden).get("synthetic-registry")["signals"], [])
        with self.factory.transaction() as repo:
            self.assertEqual(len(repo.observations("synthetic-registry")), 1)

    def test_sr16_new_signal_claims_require_matching_source(self):
        self.ingest([scalar(Signal.BODY_TEMPERATURE, 0, 39.5), scalar(Signal.HRV, 0, 40)], 0)
        tools = RecordTools(EvidenceViewService(self.service).get("synthetic-registry"), AgentRole.RECORD_QA)
        tools.call("get_series", {})
        fid = next(fid for fid, fact in tools.delivered.items() if fact["signal"] == "BODY_TEMPERATURE")
        with self.assertRaises(ValueError):
            validate({"claims": [{"text": "HRV recorded 39.5.", "fact_ids": [fid]}], "question_ids": []}, tools, AgentRole.RECORD_QA)
        self.assertIsNotNone(validate({"claims": [{"text": tools.delivered[fid]["text"], "fact_ids": [fid]}], "question_ids": []}, tools, AgentRole.RECORD_QA))


if __name__ == "__main__":
    unittest.main()
