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
        # Display selection only: one latest retained finding per exact channel,
        # in the existing signal/source order, never a severity ranking.
        latest = {}
        held = []
        for fid in ids:
            fact = tools.facts[fid]
            if not fact.get('finding'):
                held.append(fid)
                continue
            key = fact['key_id']
            prior = latest.get(key)
            if prior is None or (fact.get('at') or '') > (tools.facts[prior].get('at') or ''):
                latest[key] = fid
        ids = sorted(latest.values(),key=lambda fid:tools.facts[fid].get('at') or '',reverse=True)[:2]
        if len(ids)<2:ids.extend(held[:2-len(ids)])
    # Group all retained findings into bounded factual lines, never silently drop
    # them because a short brief has a smaller preferred number of sentences.
    def wording(fid):
        fact = tools.facts[fid]
        if role != AgentRole.PATIENT_INSIGHT:
            return fact['text'][:600]
        finding = fact.get('finding')
        labels = {'SLEEP_MIDPOINT': 'Your sleep time', 'SLEEP_DURATION': 'Your sleep duration',
                  'ACTIVITY': 'Your activity', 'RESTING_HEART_RATE': 'Your resting heart rate',
                  'HRV': 'The variation in time between your heartbeats',
                  'RESPIRATORY_RATE': 'Your breathing rate',
                  'SKIN_TEMPERATURE_DEVIATION': 'Your skin temperature'}
        if finding:
            direction = {'LATER': 'later', 'EARLIER': 'earlier', 'HIGHER': 'higher', 'LOWER': 'lower'}[finding['direction']]
            reference = 'in your recent records' if fact.get('comparison') == 'RECENT_PATTERN' else 'your usual'
            # A transient compares a reading with the recent pattern, whereas
            # persistent findings compare with the person's own reference.
            return f"{labels.get(finding['signal'], 'Your ' + tools.keys[fact['key_id']]['label'].lower())} was {direction} than {reference}, recorded from {finding['since']} to {fact['at']}."
        if fid in tools.groups['get_review_snapshot']:
            return 'Your explanation is saved for your next review. Your usual has not been changed.'
        return fact['text'][:600]
    claims = [{"text": wording(fid), "fact_ids": [fid], "section": "review" if fid in tools.groups['get_review_snapshot'] else "changes",
               "findings": [{"fact_id": fid, **tools.facts[fid]['finding']}] if tools.facts[fid].get('finding') else []} for fid in ids]
    headline = "Recorded changes" if claims else ""
    if role == AgentRole.PATIENT_INSIGHT and claims:
        phrases = [claim['text'].split(', recorded from ')[0] for claim in claims
                   if claim['findings']]
        if phrases:
            headline = phrases[0]
            if len(phrases) > 1:
                combined = headline + ', and ' + phrases[1][0].lower() + phrases[1][1:]
                if len(combined.split()) <= 20 and len(combined) < 160:
                    headline = combined
            headline += '.'
        else:
            headline = 'Your explanation is saved for your next review.'
    return {"claims": claims, "question_ids": [], "headline": headline}
