"""Explicit product skills, not safety policies or executable model plugins."""

from enum import Enum
from pathlib import Path
import json
import os


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
QUESTION_CATALOG=json.loads(Path(os.environ.get('AURA_AGENT_QUESTIONS') or Path(__file__).with_name('questions.json')).read_text())
QUESTIONS=QUESTION_CATALOG['questions']
if set(QUESTIONS)!={'context','recording','visit'} or any(not isinstance(text,str) or not 1<=len(text)<=300 for text in QUESTIONS.values()):
    raise ValueError('invalid approved question wording')
TOOLS = ("get_status", "get_series", "get_context", "get_decisions", "get_review_snapshot", "get_gaps",
         "compare_windows", "day_of_week", "summarize_gaps")
ROLE_TOOLS = {role: TOOLS for role in AgentRole}
PROMPT_VERSION = "aura-agent-v10"


def instructions(role: AgentRole) -> str:
    from .voice import PLAIN_TERMS, VOICE_EXAMPLES
    examples = VOICE_EXAMPLES['patient' if role == AgentRole.PATIENT_INSIGHT else 'clinician']
    # Vary by role without randomness so identical cached requests remain reproducible.
    examples = examples[1:] + examples[:1]
    return ((Path(__file__).parent / "skills" / role.value / "SKILL.md").read_text()+
            '\nAvoid these internal terms in prose: '+json.dumps(PLAIN_TERMS['patient' if role == AgentRole.PATIENT_INSIGHT else 'clinician'])+
            '\nStyle examples only; NEVER copy wording or placeholders, numbers or dates. Every claim must come from cited facts: '+json.dumps(examples))
