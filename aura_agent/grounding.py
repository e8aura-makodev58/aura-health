"""Structural/numeric grounding checks, not proof of semantic/clinical truth."""

import re
import unicodedata

from aura_communication.validation import prohibited_claims
from .roles import AgentRole, QUESTIONS
from .schemas import AgentDraft
from .voice import jargon


def validate(raw, tools, role):
    draft = AgentDraft.model_validate(raw)
    if draft.headline and jargon(draft.headline,role == AgentRole.PATIENT_INSIGHT):
        raise ValueError('HEADLINE_JARGON')
    if draft.headline and (prohibited_claims(draft.headline) or re.search(r'causes?|proves?|healthy|pathological|risk level|normal range',draft.headline,re.I)):
        raise ValueError('PROHIBITED_CLAIM')
    if len(set(draft.question_ids)) != len(draft.question_ids) or any(q not in QUESTIONS for q in draft.question_ids):
        raise ValueError("UNAPPROVED_QUESTION")
    used = set()
    for claim in draft.claims:
        text = unicodedata.normalize("NFKC", claim.text)
        if role == AgentRole.PATIENT_INSIGHT:
            if jargon(text,True):
                raise ValueError('HEADLINE_JARGON')
            if re.search(r'<[A-Z_]+>|\d{4}-\d{2}-\d{2}|\bbedtime\b|later nights|!|\b(?:you feel|you are feeling|you\x27re feeling)\b',text,re.I):
                raise ValueError('PATIENT_HEADLINE_STYLE')
        if prohibited_claims(text) or re.search(r"normal range|caus(?:e[ds]?|ing)|proves?|mental deterioration|risk level|healthy|pathological|guarantee|ignore .*instructions|system prompt", text, re.I):
            raise ValueError("PROHIBITED_CLAIM")
        if any(fid not in tools.delivered for fid in claim.fact_ids):
            raise ValueError("UNDELIVERED_FACT")
        sources = " ".join(tools.delivered[fid]["text"] for fid in claim.fact_ids)
        expected = {fid: tools.delivered[fid]["finding"] for fid in claim.fact_ids if tools.delivered[fid].get("finding")}
        supplied = {item.fact_id: {"signal": item.signal, "direction": item.direction, "since": item.since} for item in claim.findings}
        if supplied != expected or len(supplied) != len(claim.findings):
            raise ValueError("FINDING_MISMATCH")
        for date in re.findall(r"\b\d{4}-\d{2}-\d{2}\b", text):
            if date not in sources:
                error = ValueError("FABRICATED_NUMBER_OR_DATE"); error.detail = {"unmatched": [date]}
                raise error
        numbers = set(re.findall(r"\d+(?:\.\d+)?", sources))
        # A thousands separator is formatting, not a new number: "5,265.825" must
        # equal "5265.825" exactly. Rounded or calculated values still fail.
        written = re.sub(r"(?<=\d),(?=\d{3}\b)", "", text)
        unmatched = set(re.findall(r"\d+(?:\.\d+)?", written)) - numbers
        if unmatched:
            # The offending tokens (numbers only, never text) make rejections diagnosable.
            error = ValueError("FABRICATED_NUMBER_OR_DATE"); error.detail = {"unmatched": sorted(unmatched)[:8]}
            raise error
        for label, signal in (("sleep timing", "SLEEP_MIDPOINT"), ("sleep duration", "SLEEP_DURATION"), ("activity", "ACTIVITY"), ("heart rate", "RESTING_HEART_RATE")):
            if label in text.lower() and not any(tools.delivered[fid]["signal"] == signal for fid in claim.fact_ids):
                raise ValueError("UNSUPPORTED_SIGNAL")
        for pattern, signal in ((r"\bhrv\b|\brmssd\b", "HRV"),
                                (r"respiratory rate", "RESPIRATORY_RATE"),
                                (r"skin.temperature", "SKIN_TEMPERATURE_DEVIATION"),
                                (r"\bspo2\b", "SPO2"),
                                (r"systolic", "BLOOD_PRESSURE_SYSTOLIC"),
                                (r"diastolic", "BLOOD_PRESSURE_DIASTOLIC"),
                                (r"thermometer temperature|body temperature", "BODY_TEMPERATURE"),
                                (r"body weight|\bweight\b", "WEIGHT")):
            if re.search(pattern, text, re.I) and not any(tools.delivered[fid]["signal"] == signal for fid in claim.fact_ids):
                raise ValueError("UNSUPPORTED_SIGNAL")
        # Prevent polarity reversals for categorical facts. Broader natural-language
        # inference is not claimed to be verified by this deterministic validator.
        for word in ("Good", "Okay", "Rough", "acknowledged", "missed", "unknown", "UNOBSERVED", "REESTABLISHING"):
            if re.search(r"\b" + word + r"\b", text, re.I) and word.lower() not in sources.lower():
                raise ValueError("UNSUPPORTED_CATEGORY")
        used.update(claim.fact_ids)
    if role in {AgentRole.CLINICIAN_BRIEF, AgentRole.VISIT_PREP} and not tools.required <= used:
        raise ValueError("OMITTED_RETAINED_FINDING")
    if role == AgentRole.PATIENT_INSIGHT and len(draft.claims) > 2:
        raise ValueError("PATIENT_BURDEN")
    if role == AgentRole.PATIENT_INSIGHT and tools.required and not draft.claims:
        raise ValueError('OMITTED_RETAINED_FINDING')
    if role == AgentRole.QUESTION_RANKER and draft.claims:
        raise ValueError("QUESTION_RANKER_CONTENT")
    if len(draft.headline.split()) > (35 if role == AgentRole.PATIENT_INSIGHT else 20):
        raise ValueError("HEADLINE_BUDGET")
    if role != AgentRole.PATIENT_INSIGHT and len(draft.headline) > 160:
        raise ValueError('HEADLINE_BUDGET')
    if role == AgentRole.PATIENT_INSIGHT and any(len(sentence.split()) > 25 for sentence in re.split(r'[.!?]+',draft.headline)):
        raise ValueError('HEADLINE_BUDGET')
    return draft.model_dump()
