"""Development wording only. Clinical safety questions/resources are not invented here."""

from .domain import Candidate, Fact, GenerationMode


STATIC_TEXT = {
    "STAY_QUIET": "",
    "SUPERSEDED_EVENT": "",
    "SERVER_FAIL_CLOSED": "AURA cannot safely process this input right now. It is held pending safety evaluation. The separate safety resource panel remains available.",
    "OFFLINE_FAIL_CLOSED": "AURA cannot assess this input while offline. Hold it for server safety evaluation. The built-in resource panel remains available.",
    "URGENT_STATIC_FALLBACK": "AURA's urgent safety pathway is active. Use the separate safety guidance and resource panel. AURA is not an emergency monitoring service.",
    "IMMEDIATE_FIXED": "AURA's immediate safety pathway is active. Use the fixed safety guidance and separate resource panel. AURA is not an emergency monitoring service.",
    "CLARIFY_PENDING_REVIEW": "A structured safety clarification is required before continuing. Reviewed question content has not been configured in this development prototype.",
    "RECHECK_PENDING_REVIEW": "A structured safety follow-up is still required. Reviewed follow-up questions have not been configured in this development prototype.",
    "STRUCTURED_ASSESSMENT_PENDING": "A structured check-in has been requested. This prototype has not configured a production assessment workflow.",
    "CLINICIAN_REVIEW_ITEM": "Information is available for your next clinician review. It has not been sent anywhere.",
    "NO_OBSERVATION": "There is no descriptive observation available to explain for this event.",
}


def candidates_for(mode: GenerationMode, facts: tuple[Fact, ...], *, question=None) -> tuple[Candidate, ...]:
    references = tuple(f.fact_id for f in facts)
    observation = " ".join(f.text for f in facts)
    if mode == GenerationMode.POLICY_CLARIFICATION:
        return tuple(Candidate(f"policy-{index}", text, (), question.question_id,
                               "STRUCTURED_SAFETY_ANSWER")
                     for index, text in enumerate(question.variants))
    if mode == GenerationMode.NORMAL_SUPPORT:
        texts = ("Thanks for sharing. What would you like to focus on today?",
                 "We can keep this focused on what matters to you. What would you like to discuss?")
        intent, cta = "PATIENT_CHOSEN_TOPIC", "REPLY"
    elif mode == GenerationMode.ELEVATED_SUPPORT:
        texts = ("We can keep this focused on what you have reported. The structured safety follow-up remains available.",
                 "Thank you for telling AURA. Please continue with the structured safety follow-up.")
        intent, cta = None, "STRUCTURED_SAFETY_ANSWER"
    elif mode == GenerationMode.MICRO_CHECKIN:
        texts = (f"{observation} How have things felt for you recently?".strip(),
                 f"{observation} Would you like to add a little context?".strip())
        intent, cta = "LOW_BURDEN_CONTEXT", "CHECKIN"
    elif mode == GenerationMode.TARGETED_CLARIFICATION:
        texts = (f"{observation} Has anything changed recently that you would like to add?".strip(),
                 f"{observation} What context would you like AURA to keep with this?".strip())
        intent, cta = "CONTEXT_FOR_APPROVED_CHANGE", "ADD_CONTEXT"
    else:
        texts = (f"{observation} This describes your recorded pattern, not a clinical conclusion.",
                 f"Here is the recorded change: {observation} AURA is describing observations only.")
        intent, cta = None, None
    return tuple(Candidate(f"{mode.value.lower()}-{index}", text, references, intent, cta)
                 for index, text in enumerate(texts))
