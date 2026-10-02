"""Deterministic checks; closed candidate grounding does not claim semantic truth detection."""

from dataclasses import dataclass
import re
import unicodedata

from .domain import GenerationMode, GenerationRequest


PROHIBITED = {
    "DIAGNOSTIC_CLAIM": r"\b(depress(?:ion|ed|ive)|diagnos\w*|clinical deterioration)\b",
    "RELAPSE_CLAIM": r"\brelaps\w*\b",
    "SUICIDE_RISK_CLAIM": r"\b(suicid\w*|you are safe|no risk|low risk)\b",
    "MEDICATION_INSTRUCTION": r"\b(taper\w*|dos(?:e|age)|stop\w*|reduc\w*|increas\w*|skip\w*|switch\w*)\b.*\b(medication|antidepressant|tablet|pill|mg)\b|\b\d+\s*mg\b",
    "MONITORING_CLAIM": r"\b(monitoring you|watching you|notified|emergency services|ambulance|call\s+\d+)\b",
    "INTERNAL_RISK_LANGUAGE": r"\b(T[0-5]|risk score|risk percentage|safety tier|psychiatric risk)\b|\d+\s*%",
}


def prohibited_claims(text: str) -> tuple[str, ...]:
    normalized = unicodedata.normalize("NFKC", text)
    return tuple(code for code, expression in PROHIBITED.items()
                 if re.search(expression, normalized, re.IGNORECASE | re.DOTALL))


@dataclass(frozen=True)
class ValidationResult:
    accepted: bool
    reasons: tuple[str, ...]


def validate_output(request: GenerationRequest, raw: object) -> ValidationResult:
    fields = {"candidate_id", "message", "acknowledged_facts", "question_intent", "cta_type"}
    if not isinstance(raw, dict) or set(raw) != fields:
        return ValidationResult(False, ("INVALID_OUTPUT_SCHEMA",))
    if (not isinstance(raw["candidate_id"], str) or not isinstance(raw["message"], str)
            or not isinstance(raw["acknowledged_facts"], list)
            or any(not isinstance(value, str) for value in raw["acknowledged_facts"])
            or any(raw[key] is not None and not isinstance(raw[key], str)
                   for key in ("question_intent", "cta_type"))):
        return ValidationResult(False, ("INVALID_OUTPUT_SCHEMA",))
    candidate = next((c for c in request.candidates if c.candidate_id == raw["candidate_id"]), None)
    exact_match = candidate is not None and candidate.public() == raw
    # Reviewed policy questions may contain clinical vocabulary. Exact reproduction
    # is governed content, not an inferred claim; no added/changed wording is allowed.
    reviewed_question = request.mode == GenerationMode.POLICY_CLARIFICATION and exact_match
    reasons = [] if reviewed_question else list(prohibited_claims(raw["message"]))
    if len(raw["message"]) > request.max_response_length:
        reasons.append("RESPONSE_TOO_LONG")
    if not exact_match:
        reasons.append("UNAPPROVED_CONTENT_OR_INTENT")
    return ValidationResult(not reasons, tuple(reasons))
