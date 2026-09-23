"""Policy output permissions. This module generates no patient-facing text."""

from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from .domain import Mode, SafetyState
from .resources import ResolvedResources, ResourceRegistry


@dataclass(frozen=True)
class OutputPlan:
    may_generate: bool
    requires_urgent_validation: bool
    static_template_id: str | None
    pinned_resources: ResolvedResources | None
    input_assessed: bool


def output_plan(state: SafetyState, registry: ResourceRegistry, now: datetime,
                *, client_offline: bool = False) -> OutputPlan:
    fail_closed = client_offline or state.degraded
    safety_surface = fail_closed or state.interaction_mode >= Mode.CLARIFY
    resources = registry.resolve(now, offline=client_offline) if safety_surface else None
    if client_offline:
        return OutputPlan(False, False, "OFFLINE_FAIL_CLOSED", resources, False)
    if state.degraded:
        return OutputPlan(False, False, "SERVER_FAIL_CLOSED", resources, False)
    if state.interaction_mode == Mode.IMMEDIATE:
        return OutputPlan(False, False, "IMMEDIATE_FIXED", resources, True)
    if state.interaction_mode == Mode.URGENT:
        return OutputPlan(True, True, "URGENT_STATIC_FALLBACK", resources, True)
    return OutputPlan(True, False, None, resources, True)


def accept_generated(plan: OutputPlan, text: str,
                     urgent_validator: Callable[[str], bool] | None = None) -> tuple[bool, str | None]:
    """Returns acceptance and a fallback template identifier, never fabricated copy."""
    if not plan.may_generate:
        return False, plan.static_template_id
    if plan.requires_urgent_validation and (urgent_validator is None or not urgent_validator(text)):
        return False, plan.static_template_id
    return True, None
