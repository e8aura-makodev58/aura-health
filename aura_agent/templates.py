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
        # A recent change leads a longer-running one; otherwise keep the existing order.
        def recent_first(fid):
            return 0 if tools.facts[fid].get('comparison') == 'RECENT_PATTERN' else 1
        ordered = sorted(sorted(latest.values(), key=lambda fid: tools.facts[fid].get('at') or '', reverse=True), key=recent_first)
        # Readability selection, never clinical importance or severity: prefer
        # familiar sleep/activity channels in their existing source order.
        basic = sorted([fid for fid in latest.values() if tools.facts[fid]['signal'] in
                        {'SLEEP_MIDPOINT','ACTIVITY','SLEEP_DURATION','RESTING_HEART_RATE'}], key=recent_first)
        reports = [fid for fid in tools.groups['get_decisions'] if fid in tools.delivered
                   and (tools.facts[fid].get('checkin_summary') or tools.facts[fid].get('checkin_run'))]
        reports.sort(key=lambda fid:(tools.facts[fid].get('at') or '',bool(tools.facts[fid].get('checkin_summary'))),reverse=True)
        gaps = [fid for fid in tools.groups['get_gaps'] if fid in tools.delivered
                and tools.facts[fid].get('patient',{}).get('text')]
        gaps.sort(key=lambda fid:tools.facts[fid].get('at') or '',reverse=True)
        ids = (basic or ordered)[:1]
        if reports: ids.append(reports[0])
        elif len(ids)<2: ids.extend([fid for fid in (basic or ordered) if fid not in ids][:1])
        # A recent wearable gap makes the picture incomplete; say so when there is room.
        if gaps and len(ids)<2: ids.append(gaps[0])
        if not ids: ids = gaps[:1] or held[:1]
    # Group all retained findings into bounded factual lines, never silently drop
    # them because a short brief has a smaller preferred number of sentences.
    def wording(fid):
        fact = tools.facts[fid]
        if role != AgentRole.PATIENT_INSIGHT:
            return fact['text'][:600]
        if fact.get('patient',{}).get('recap_text'):
            return fact['patient']['recap_text']
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
    if role == AgentRole.PATIENT_INSIGHT:
        selected = []
        for fid in ids:
            sentence = wording(fid)
            if len(sentence.split()) <= 25 and sum(len(wording(value).split()) for value in selected)+len(sentence.split()) <= 35:
                selected.append(fid)
        ids = selected
    claims = [{"text": wording(fid), "fact_ids": [fid], "section": "review" if fid in tools.groups['get_review_snapshot'] else "gaps" if fid in tools.groups['get_gaps'] else "routine" if fid in tools.groups['get_decisions'] else "changes",
               "findings": [{"fact_id": fid, **tools.facts[fid]['finding']}] if tools.facts[fid].get('finding') else []} for fid in ids]
    headline = "Recorded changes" if claims else ""
    if role == AgentRole.PATIENT_INSIGHT and claims:
        phrases = [claim['text'].rstrip('.') for claim in claims]
        if phrases:
            headline = phrases[0]
            if len(phrases) > 1:
                combined = headline + '. ' + phrases[1]
                if len(combined.split()) <= 35 and len(combined) < 300:
                    headline = combined
            headline += '.'
        else:
            headline = 'Your explanation is saved for your next review.'
    return {"claims": claims, "question_ids": [], "headline": headline}
