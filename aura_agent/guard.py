"""Use the accepted safety output boundary; fail closed before any model access."""

from aura_safety.codec import state_from_dict
from aura_safety.domain import Mode, Status, state_valid
from aura_safety.output import output_plan


def blocked_reason(raw_state, registry, now, *, offline=False, held=False):
    try:
        state = state_from_dict(raw_state)
        if not state_valid(state):
            return "INVALID_SAFETY_STATE"
        plan = output_plan(state, registry, now, client_offline=offline)
        if not plan.may_generate:
            return plan.static_template_id
        if held:
            return "INPUT_HELD"
        # This read-only agent is deliberately narrower than the permitted wording
        # layer: no ordinary investigation during a required safety interaction.
        if state.interaction_mode != Mode.NORMAL or state.episode_status in {Status.RECHECK_REQUIRED, Status.DROPOUT}:
            return "SAFETY_INTERACTION_FIRST"
    except (ValueError, KeyError, TypeError, AttributeError):
        return "INVALID_SAFETY_STATE"
    return None
