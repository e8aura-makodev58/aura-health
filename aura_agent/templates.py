"""Transparent extraction fallback, not AI investigation or prioritization."""

from .roles import AgentRole


def fallback(tools, role, query=None):
    if role == AgentRole.QUESTION_RANKER:
        return {"claims": [], "question_ids": []}
    ids = sorted(tools.required, key=lambda fid: int(fid[1:]))
    if role == AgentRole.RECORD_QA:
        selected_tools = {
            "When were changes in sleep timing recorded, and what context was recorded alongside them?": ("get_series", "get_context"),
            "Which context was recorded alongside the observed changes? Do not infer causation.": ("get_context",),
            "Which wearable gaps and returns were recorded?": ("get_gaps",),
            "What medication-routine events and check-ins were recorded?": ("get_decisions",),
        }.get(query, tuple(tools.groups))
        ids = [fid for name in selected_tools for fid in tools.groups[name] if fid in tools.delivered][:6]
    if role == AgentRole.PATIENT_INSIGHT:
        ids = ids[:2]
    # Group all retained findings into bounded factual lines, never silently drop
    # them because a short brief has a smaller preferred number of sentences.
    claims = [{"text": tools.facts[fid]["text"][:600], "fact_ids": [fid], "section": "review" if fid in tools.groups['get_review_snapshot'] else "changes",
               "findings": [{"fact_id": fid, **tools.facts[fid]['finding']}] if tools.facts[fid].get('finding') else []} for fid in ids]
    return {"claims": claims, "question_ids": [], "headline": "Recorded changes" if claims else ""}
