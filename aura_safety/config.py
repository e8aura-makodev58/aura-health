"""External policy parameters. Null de-escalation targets await clinical approval."""

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .domain import Mode


@dataclass(frozen=True)
class PolicyConfig:
    version: str
    t2_timeout_action: str
    recheck_failed_target_by_peak: dict[Mode, Mode]
    dropout_reentry_target_by_peak: dict[Mode, Mode]
    recent_high_tier_ttl: str
    max_recontacts_per_phase: int
    benign_corpus_fp_budget: float
    urgent_deescalation_target: Mode | None
    immediate_deescalation_target: Mode | None


def parse_config(raw: dict) -> PolicyConfig:
    mapping = lambda key: {Mode[k]: Mode[v] for k, v in raw[key].items()}
    config = PolicyConfig(
        version=raw["version"],
        t2_timeout_action=raw["CFG_T2_TIMEOUT_ACTION"],
        recheck_failed_target_by_peak=mapping("CFG_RECHECK_FAILED_TARGET_BY_PEAK"),
        dropout_reentry_target_by_peak=mapping("CFG_DROPOUT_REENTRY_TARGET_BY_PEAK"),
        recent_high_tier_ttl=raw["CFG_RECENT_HIGH_TIER_TTL"],
        max_recontacts_per_phase=raw["CFG_MAX_RECONTACTS_PER_PHASE"],
        benign_corpus_fp_budget=raw["CFG_BENIGN_CORPUS_FP_BUDGET"],
        urgent_deescalation_target=Mode[raw["CFG_URGENT_DEESCALATION_TARGET"]] if raw["CFG_URGENT_DEESCALATION_TARGET"] else None,
        immediate_deescalation_target=Mode[raw["CFG_IMMEDIATE_DEESCALATION_TARGET"]] if raw["CFG_IMMEDIATE_DEESCALATION_TARGET"] else None,
    )
    if config.t2_timeout_action != "HOLD_ELEVATED_WITH_FLAG" or not re.fullmatch(r"P\d+D", config.recent_high_tier_ttl):
        raise ValueError("Unsupported policy branch/configuration")
    if set(config.recheck_failed_target_by_peak) != {Mode.URGENT, Mode.IMMEDIATE} or set(config.dropout_reentry_target_by_peak) != {Mode.URGENT, Mode.IMMEDIATE}:
        raise ValueError("High-tier mapping must cover T3 and T4")
    if any(config.dropout_reentry_target_by_peak[p] > p or config.recheck_failed_target_by_peak[p] > p for p in (Mode.URGENT, Mode.IMMEDIATE)):
        raise ValueError("Targets cannot exceed episode peak")
    if config.urgent_deescalation_target is not None and config.urgent_deescalation_target >= Mode.URGENT:
        raise ValueError("Urgent de-escalation target must be lower")
    if config.immediate_deescalation_target is not None and config.immediate_deescalation_target >= Mode.IMMEDIATE:
        raise ValueError("Immediate de-escalation target must be lower")
    if type(config.max_recontacts_per_phase) is not int or config.max_recontacts_per_phase < 0:
        raise ValueError("Invalid recontact limit")
    return config


def load_config(path: Path | None = None) -> PolicyConfig:
    return parse_config(json.loads((path or Path(__file__).with_name("policy_config.json")).read_text()))


def config_dict(config: PolicyConfig) -> dict:
    return {
        "version": config.version,
        "CFG_T2_TIMEOUT_ACTION": config.t2_timeout_action,
        "CFG_RECHECK_FAILED_TARGET_BY_PEAK": {k.name: v.name for k, v in config.recheck_failed_target_by_peak.items()},
        "CFG_DROPOUT_REENTRY_TARGET_BY_PEAK": {k.name: v.name for k, v in config.dropout_reentry_target_by_peak.items()},
        "CFG_RECENT_HIGH_TIER_TTL": config.recent_high_tier_ttl,
        "CFG_MAX_RECONTACTS_PER_PHASE": config.max_recontacts_per_phase,
        "CFG_BENIGN_CORPUS_FP_BUDGET": config.benign_corpus_fp_budget,
        "CFG_URGENT_DEESCALATION_TARGET": config.urgent_deescalation_target.name if config.urgent_deescalation_target else None,
        "CFG_IMMEDIATE_DEESCALATION_TARGET": config.immediate_deescalation_target.name if config.immediate_deescalation_target else None,
    }
