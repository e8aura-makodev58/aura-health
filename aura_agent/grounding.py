"""Structural/numeric grounding checks, not proof of semantic/clinical truth."""

import re
import unicodedata

from aura_communication.validation import prohibited_claims
from .roles import AgentRole, QUESTIONS
from .schemas import AgentDraft


# Closed connective vocabulary permits synthesis without admitting arbitrary new
# factual entities. Unfamiliar paraphrases fall back; this is not a general
# semantic entailment or clinical-truth detector.
CONNECTIVES = "a an the and or but with without of to from in on at by for as is are was were be been being has have had it its they their you your this these those that there here also both each only not no then now still across alongside between during over same some any all more less most recent recently earlier later first last recorded record records recording report reports reported reporting observation observations observed change changes changed changing pattern patterns reference references own personal stored available retained historic historical currently active necessarily remain remains including includes include about against compared compare comparison relative separately rather than while when which what where whether since until together associated association descriptive reviewed review reviewing context contexts checkins checkin check ins routine routines month window dates date time timing summary missing gap gaps return returned returning neither independent evidence explicitly provisional trusted reestablishing unchanged equivalent underlying draft selected current preceding subsequent period beginning ending start end days day weeks week months patient source sources clinician visit note notes question questions preparation prepared before after mentioned noted limited status data values value hours minutes beats min units latest previous acknowledged acknowledgement verified adherence explanation explained held concern concerns discussion discuss optional availability category instruction instructions uncertainty insufficient sufficient stable temporal"


def factual_tokens(text):
    words = re.findall(r"[a-z]+", text.lower().replace("_", " "))
    return {word[:-1] if word.endswith("s") and len(word) > 4 else word for word in words}


CONNECTIVES += " through throughout within around respectively span spans spanned spanning additional further relevant related unrelated particular specific overall retrieved provided documented linked item items entry entries information detail details"


class GroundingError(ValueError):
    def __init__(self, code, unsupported_words):
        super().__init__(code)
        # Bounded alphabetic diagnostic, not the complete rejected draft or notes.
        self.unsupported_words = sorted(word[:24] for word in unsupported_words)[:16]


def validate(raw, tools, role):
    draft = AgentDraft.model_validate(raw)
    if len(set(draft.question_ids)) != len(draft.question_ids) or any(q not in QUESTIONS for q in draft.question_ids):
        raise ValueError("UNAPPROVED_QUESTION")
    used = set()
    for claim in draft.claims:
        text = unicodedata.normalize("NFKC", claim.text)
        if prohibited_claims(text) or re.search(r"normal range|caus(?:e[ds]?|ing)|proves?|mental deterioration|risk level|healthy|pathological|guarantee|ignore .*instructions|system prompt", text, re.I):
            raise ValueError("PROHIBITED_CLAIM")
        if any(fid not in tools.delivered for fid in claim.fact_ids):
            raise ValueError("UNDELIVERED_FACT")
        sources = " ".join(tools.delivered[fid]["text"] for fid in claim.fact_ids)
        missing = factual_tokens(text) - (factual_tokens(sources) | factual_tokens(CONNECTIVES))
        if missing:
            raise GroundingError("UNSUPPORTED_FACTUAL_VOCABULARY", missing)
        for date in re.findall(r"\b\d{4}-\d{2}-\d{2}\b", text):
            if date not in sources:
                raise ValueError("FABRICATED_NUMBER_OR_DATE")
        numbers = set(re.findall(r"\d+(?:\.\d+)?", sources))
        if not set(re.findall(r"\d+(?:\.\d+)?", text)) <= numbers:
            raise ValueError("FABRICATED_NUMBER_OR_DATE")
        for label, signal in (("sleep timing", "SLEEP_MIDPOINT"), ("sleep duration", "SLEEP_DURATION"), ("activity", "ACTIVITY"), ("heart rate", "RESTING_HEART_RATE")):
            if label in text.lower() and not any(tools.delivered[fid]["signal"] == signal for fid in claim.fact_ids):
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
    if role == AgentRole.QUESTION_RANKER and draft.claims:
        raise ValueError("QUESTION_RANKER_CONTENT")
    return draft.model_dump()
