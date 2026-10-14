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


# The record name "medication-routine record(s)" names stored routine entries, not a
# medication. It is neutralised ONLY for the instruction rule, so an observation such
# as "activity reduced during the medication-routine records" is not read as advice.
# Every other medication word (medication, antidepressant, tablet, pill, mg) still counts.
RECORD_NAME = re.compile(r"\bmedication[-\s]routine\s+records?\b", re.IGNORECASE)


def prohibited_claims(text: str) -> tuple[str, ...]:
    normalized = unicodedata.normalize("NFKC", text)
    def scanned(code):
        return RECORD_NAME.sub("routine records", normalized) if code == "MEDICATION_INSTRUCTION" else normalized
    return tuple(code for code, expression in PROHIBITED.items()
                 if re.search(expression, scanned(code), re.IGNORECASE | re.DOTALL))


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


# Agent-written patient sentences (note replies, idea picks and acknowledgements) are free text,
# so they get stricter checks than the closed-candidate path: on top of PROHIBITED, no medicine or
# care-team talk, no numbers, links or contact details, no claims that anything was sent, and no
# instructions. A failure always falls back to fixed wording.
PATIENT_TEXT_RULES = {
    "MEDICINE_TALK": r"\b(medic\w*|antidepress\w*|tablet\w*|pill\w*|dos(?:e|es|age|ing)|mg|prescri\w*|sertraline|ssri\w*|side[-\s]effect\w*)\b",
    "CARE_TEAM_CLAIM": r"\b(doctor\w*|clinician\w*|psychiatr\w*|therap\w*|counsell?or\w*|nurse\w*|pharmacist\w*|gp)\b",
    "SENT_OR_SHARED": r"\b(sent|send(?:ing)? (?:it|this|that)|shared with|shar(?:e|ing) (?:it|this|that) with|forward\w*|notif\w*|alert\w*|report(?:ed)? to)\b",
    "NUMBER_OR_CONTACT": r"\d|https?://|www\.|@|\.com\b",
    "INSTRUCTION": r"\b(you should|you must|you need to|make sure|be sure to|don't forget)\b",
    "CRISIS_WORDS": r"\b(crisis|emergency|hotline|helpline|harm|unsafe|danger\w*)\b",
}


def patient_text_problems(text, max_length=280, max_sentences=3):
    """Reasons an agent-written patient sentence is not acceptable; empty when it passes."""
    if not isinstance(text, str) or not text.strip():
        return ("EMPTY_OR_NOT_TEXT",)
    normalized = unicodedata.normalize("NFKC", text).strip()
    reasons = list(prohibited_claims(normalized))
    reasons += [code for code, expression in PATIENT_TEXT_RULES.items() if re.search(expression, normalized, re.IGNORECASE)]
    if len(normalized) > max_length:
        reasons.append("RESPONSE_TOO_LONG")
    if len(re.findall(r"[.!?](?:\s|$)", normalized)) > max_sentences:
        reasons.append("TOO_MANY_SENTENCES")
    if any(ord(ch) < 32 and ch not in "\n" for ch in normalized) or "<" in normalized or ">" in normalized:
        reasons.append("MARKUP_OR_CONTROL")
    return tuple(dict.fromkeys(reasons))
