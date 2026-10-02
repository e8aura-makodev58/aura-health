"""Immutable facts and wording contracts handed to a model after application approval."""

from dataclasses import asdict, dataclass
from enum import Enum


class GenerationMode(str, Enum):
    NORMAL_SUPPORT = "NORMAL_SUPPORT"
    MICRO_CHECKIN = "MICRO_CHECKIN"
    TARGETED_CLARIFICATION = "TARGETED_CLARIFICATION"
    OBSERVATION_EXPLANATION = "OBSERVATION_EXPLANATION"
    POLICY_CLARIFICATION = "POLICY_CLARIFICATION"
    ELEVATED_SUPPORT = "ELEVATED_SUPPORT"


class CommunicationPurpose(str, Enum):
    AUTO = "AUTO"
    EXPLAIN_OBSERVATION = "EXPLAIN_OBSERVATION"


@dataclass(frozen=True)
class Fact:
    fact_id: str
    text: str


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    message: str
    acknowledged_facts: tuple[str, ...]
    question_intent: str | None
    cta_type: str | None

    def public(self) -> dict:
        row = asdict(self)
        row["acknowledged_facts"] = list(self.acknowledged_facts)
        return row


@dataclass(frozen=True)
class GenerationRequest:
    mode: GenerationMode
    allowed_intent: str
    facts: tuple[Fact, ...]
    candidates: tuple[Candidate, ...]
    patient_context: str | None
    max_response_length: int
    policy_version: str
    policy_config_version: str
    prompt_version: str
    config_version: str

    def public(self) -> dict:
        return {**asdict(self), "mode": self.mode.value,
                "facts": [asdict(fact) for fact in self.facts],
                "candidates": [candidate.public() for candidate in self.candidates]}


@dataclass(frozen=True)
class ApprovedPolicyQuestion:
    """Deployment-supplied reviewed content, never supplied by a patient/API caller."""

    question_id: str
    variants: tuple[str, ...]
    policy_version: str
    review_reference: str

    def __post_init__(self):
        if (not isinstance(self.variants, tuple) or not self.variants or
                not all(isinstance(value, str) and value for value in
                        (self.question_id, self.policy_version, self.review_reference))):
            raise ValueError("policy question requires reviewed variants and provenance")
        if any(not isinstance(text, str) or not text.strip() for text in self.variants):
            raise ValueError("policy question variants must be nonempty text")
