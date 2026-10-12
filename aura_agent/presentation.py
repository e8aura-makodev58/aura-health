"""Bounded wording contract; deterministic cards remain record-owned, not AI-owned."""
import re
from datetime import date, timedelta

from .grounding import validate
from .roles import AgentRole
from .voice import jargon

SYNTHESIS_LABELS = {
    'SLEEP_MIDPOINT':'Sleep timing', 'SLEEP_DURATION':'Sleep duration',
    'ACTIVITY':'Activity', 'RESTING_HEART_RATE':'Resting heart rate',
    'HRV':'HRV', 'RESPIRATORY_RATE':'Respiratory rate',
    'SKIN_TEMPERATURE_DEVIATION':'Skin temperature', 'SPO2':'SpO2',
    'BLOOD_PRESSURE_SYSTOLIC':'Systolic blood pressure',
    'BLOOD_PRESSURE_DIASTOLIC':'Diastolic blood pressure',
    'BODY_TEMPERATURE':'Thermometer temperature', 'WEIGHT':'Body weight',
}


def checked_headline(raw, tools, role=None):
    if (not isinstance(raw, dict) or set(raw) != {'headline','fact_ids','question_ids'}
            or not isinstance(raw['headline'], str) or not raw['headline'].strip()
            or not isinstance(raw['fact_ids'], list) or not 1 <= len(raw['fact_ids']) <= 24
            or any(not isinstance(fid,str) or fid not in tools.delivered for fid in raw['fact_ids'])
            or len(set(raw['fact_ids'])) != len(raw['fact_ids'])):
        raise ValueError('HEADLINE_SCHEMA')
    if jargon(raw['headline'], role == AgentRole.PATIENT_INSIGHT):
        raise ValueError('HEADLINE_JARGON')
    if re.search(r'\bbecause\b|\bdue to\b|\bled to\b',raw['headline'],re.I):
        raise ValueError('PROHIBITED_CLAIM')
    if role == AgentRole.PATIENT_INSIGHT:
        text = raw['headline']
        if re.search(r'<[A-Z_]+>|\d{4}-\d{2}-\d{2}|\bbedtime\b|later nights|[!😀-🙏]|\b(?:you feel|you are feeling|you\x27re feeling)\b',text,re.I):
            raise ValueError('PATIENT_HEADLINE_STYLE')
        if re.search(r'\bnothing (?:else )?(?:has )?(?:changed|moved)|\b(?:steady|stable)\b',text,re.I):
            raise ValueError('PROHIBITED_CLAIM')
        if re.search(r'\b(?:baseline|drift|anchor|reestablishing|hrv|rmssd|spo2|'
                     r'physiology|physiological|respiratory|systolic|diastolic|'
                     r'variability|telemetry|biomarker)\b', text, re.I):
            raise ValueError('HEADLINE_JARGON')
        if (re.search(r'[\n\r:;]|^\s*[-*•]', text) or
                re.search(r'^\s*(?:recorded changes|changes in|recent changes in)\b', text, re.I) or
                re.search(r'\b(?:sleep|activity|heart rate|breathing|temperature)\s+'
                          r'(?:later|earlier|higher|lower)\s*(?:,|\band\b)', text, re.I)):
            raise ValueError('PATIENT_HEADLINE_STYLE')
        if re.search(r'\b(?:I|we|my|our)\b', text, re.I):
            raise ValueError('PATIENT_HEADLINE_PERSPECTIVE')
        if re.search(r'\b(?:should|must|try|consider|remember|please|contact|call|seek)\b|'
                     r'\b(?:take|get|make) (?:a |some |more |less |your )|'
                     r'\byou (?:need|ought) to\b|'
                     r'^\s*(?:rest|drink|eat|avoid|exercise|book|schedule|talk|speak|keep)\b|'
                     r'\b(?:nothing to worry|no concerns?|everything (?:is )?fine|all (?:is )?well|'
                     r'you(?: are|\'re) (?:fine|okay|safe))\b', text, re.I):
            raise ValueError('PROHIBITED_CLAIM')
        for pattern, signal in ((r'\bsleep time\b', 'SLEEP_MIDPOINT'),
                                (r'\bsleep (?:has been |was |is )?(?:shorter|longer)\b', 'SLEEP_DURATION'),
                                (r'\bmoving (?:more|less)\b', 'ACTIVITY'),
                                (r'\bbreathing\b', 'RESPIRATORY_RATE'),
                                (r'\btime between .*heartbeats\b|\bheartbeat timing\b', 'HRV')):
            if re.search(pattern, text, re.I) and not any(
                    tools.delivered[fid]['signal'] == signal for fid in raw['fact_ids']):
                raise ValueError('UNSUPPORTED_SIGNAL')
    facts = [tools.delivered[fid] for fid in raw['fact_ids']]
    # Full existing claim checks for citations/numbers/categories and metadata.
    # Runtime then validates the assembled draft in its actual role, including
    # retained-history and patient-burden requirements; neither rule is removed.
    validate({'headline':raw['headline'], 'question_ids':raw['question_ids'], 'claims':[{
        'text':raw['headline'], 'fact_ids':raw['fact_ids'],
        'findings':[{'fact_id':fact['fact_id'],**fact['finding']} for fact in facts if fact.get('finding')]}]},
        tools, AgentRole.PATIENT_INSIGHT if role == AgentRole.PATIENT_INSIGHT else AgentRole.RECORD_QA)
    return facts


def checked_synthesis(raw, tools, group):
    """Additional bounded sentence checks, followed by the unchanged validator."""
    if (not isinstance(raw, dict) or set(raw) != {'text', 'fact_ids'} or
            not isinstance(raw['text'], str) or not raw['text'].strip() or
            not isinstance(raw['fact_ids'], list) or len(set(raw['fact_ids'])) < 2 or
            len(raw['fact_ids']) != len(set(raw['fact_ids'])) or
            set(raw['fact_ids']) != set(group['fact_ids'])):
        raise ValueError('SYNTHESIS_GROUP_MISMATCH')
    if re.search(r'\bbecause\b|\bdue to\b|\bled to\b', raw['text'], re.I):
        raise ValueError('PROHIBITED_CLAIM')
    if jargon(raw['text']):
        raise ValueError('SYNTHESIS_JARGON')
    validate({'headline':'', 'question_ids':[], 'claims':[{
        'text':raw['text'], 'fact_ids':raw['fact_ids'], 'findings':[
            {'fact_id':fid, **tools.delivered[fid]['finding']}
            for fid in raw['fact_ids'] if tools.delivered[fid].get('finding')]}]}, tools, AgentRole.RECORD_QA)
    return raw


def record_presentation(tools, config):
    """Deterministic interval intersection and approved questions, never scoring."""
    latest = {}
    for fact in tools.delivered.values():
        if fact.get('finding'):
            key = fact['key_id']
            if key not in latest or (fact['at'], fact['finding']['since']) > (latest[key]['at'], latest[key]['finding']['since']):
                latest[key] = fact
    spans = []
    for fact in latest.values():
        spans.append((fact, fact['finding']['since'], fact['at']))
    for fact in tools.delivered.values():
        if fact.get('checkin_run'):
            run = fact['checkin_run']
            spans.append((fact, run['start'], run['end']))
    groups = []
    gap_facts = [tools.delivered[fid] for fid in tools.groups['get_gaps']
                 if fid in tools.delivered and 'SENSING_GAP' in tools.delivered[fid].get('raw_text',tools.delivered[fid]['text'])]
    for start in sorted({start for _,start,_ in spans}):
        finish = (date.fromisoformat(start)+timedelta(days=config.co_occurrence_days-1)).isoformat()
        overlap = [(fact,a,b) for fact,a,b in spans if a <= start and b >= finish and
                   not any(gap['key_id']==fact['key_id'] and start <= gap['at'] <= finish for gap in gap_facts)]
        # Check-ins alone never create an assessment synthesis.
        if len(overlap) >= 2 and any(fact.get('finding') for fact,_,_ in overlap):
            groups.append({'fact_ids':[fact['fact_id'] for fact,_,_ in overlap],
                           'start':start, 'end':finish})
    group = max(groups, key=lambda group:(len(group['fact_ids']),group['start']), default=None)
    synthesis = None
    if group:
        labels = []
        for fid in group['fact_ids']:
            fact = tools.delivered[fid]
            label = ('Check-ins' if fact.get('checkin_run') else
                     SYNTHESIS_LABELS.get(fact['signal'],tools.keys[fact['key_id']]['label']))
            if label not in labels: labels.append(label)
        wording = ', '.join(labels[:-1])+' and '+labels[-1]
        # The overlap date may not be printed in every cited fact. Omit dates
        # from the sentence; exact common bounds remain in source disclosure.
        synthesis = checked_synthesis({'text':wording+' were recorded over the same period.',
                                       'fact_ids':group['fact_ids']},tools,group)
        synthesis.update(group=group, generation_used=False)
    contexts = [tools.delivered[fid] for fid in tools.groups['get_context'] if fid in tools.delivered]
    missing_context = any(not any(context['key_id']==fact['key_id'] and context.get('context_span') and
        context['context_span']['start'] <= fact['at'] and context['context_span']['end'] >= fact['finding']['since']
        for context in contexts) for fact in latest.values())
    gaps = any(fid in tools.delivered and 'SENSING_GAP' in tools.delivered[fid].get('raw_text',tools.delivered[fid]['text']) for fid in tools.groups['get_gaps'])
    questions = []
    if missing_context: questions.append('context')
    if gaps: questions.append('recording')
    if not questions and latest: questions.append('visit')
    checkins = next((fact for fact in tools.delivered.values() if fact.get('checkin_summary')),None)
    return {'synthesis':synthesis,'checkins':checkins,'question_ids':questions[:2]}
