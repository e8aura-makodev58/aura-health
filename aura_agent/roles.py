"""Explicit product skills, not safety policies or executable model plugins."""

from enum import Enum
from pathlib import Path


class AgentRole(str, Enum):
    CLINICIAN_BRIEF = "clinician_brief"
    RECORD_QA = "record_qa"
    PATIENT_INSIGHT = "patient_insight"
    VISIT_PREP = "visit_prep"
    QUESTION_RANKER = "question_ranker"


QUERIES = {
    "sleep_change": "When were changes in sleep timing recorded, and what context was recorded alongside them?",
    "recorded_context": "Which context was recorded alongside the observed changes? Do not infer causation.",
    "wearable_gaps": "Which wearable gaps and returns were recorded?",
    "routine": "What medication-routine events and check-ins were recorded?",
}
QUESTIONS = {
    "context": "Is there any context you would like to add to these recorded changes?",
    "recording": "Were there any gaps in what you were able to record?",
    "visit": "Which of these observations would you like to discuss at your appointment?",
}
TOOLS = ("get_status", "get_series", "get_context", "get_decisions", "get_review_snapshot", "get_gaps")
ROLE_TOOLS = {role: TOOLS for role in AgentRole}
PROMPT_VERSION = "aura-agent-v1"


def instructions(role: AgentRole) -> str:
    return (Path(__file__).parent / "skills" / role.value / "SKILL.md").read_text()
