"""Bounded wording contract; deterministic cards remain record-owned, not AI-owned."""
import re

from .grounding import validate
from .roles import AgentRole


def checked_headline(raw, tools):
    if (not isinstance(raw, dict) or set(raw) != {'headline','fact_ids','question_ids'}
            or not isinstance(raw['headline'], str) or not raw['headline'].strip()
            or not isinstance(raw['fact_ids'], list) or not 1 <= len(raw['fact_ids']) <= 24
            or any(not isinstance(fid,str) or fid not in tools.delivered for fid in raw['fact_ids'])
            or len(set(raw['fact_ids'])) != len(raw['fact_ids'])):
        raise ValueError('HEADLINE_SCHEMA')
    if re.search(r'\b(?:anchored|rolling|deviation|midpoint|extraction)\b', raw['headline'], re.I):
        raise ValueError('HEADLINE_JARGON')
    if re.search(r'\bbecause\b|\bdue to\b|\bled to\b',raw['headline'],re.I):
        raise ValueError('PROHIBITED_CLAIM')
    facts = [tools.delivered[fid] for fid in raw['fact_ids']]
    # Full existing claim checks for citations/numbers/categories and metadata.
    # Runtime then validates the assembled draft in its actual role, including
    # retained-history and patient-burden requirements; neither rule is removed.
    validate({'headline':raw['headline'], 'question_ids':raw['question_ids'], 'claims':[{
        'text':raw['headline'], 'fact_ids':raw['fact_ids'],
        'findings':[{'fact_id':fact['fact_id'],**fact['finding']} for fact in facts if fact.get('finding')]}]},
        tools, AgentRole.RECORD_QA)
    return facts
