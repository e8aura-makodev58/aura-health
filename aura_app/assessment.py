"""Read-only arrival presentation; existing agent service owns generation and guards."""
from aura_agent.roles import AgentRole, QUESTIONS
from aura_agent.templates import fallback
from .agent import digest
from .models import AppError


def arrival_id(role, window_days, signature):
    return 'arrival-' + digest({'version': 'arrival-v11', 'role': role.value,
                                'window': window_days, 'state': signature})


class AssessmentService:
    def __init__(self, agent):
        self.agent = agent

    def get(self, patient_id, role, *, client_offline=False):
        if type(client_offline) is not bool:
            raise AppError('INVALID_AGENT_REQUEST', 'Offline state must be boolean')
        try:
            role = AgentRole(role)
        except ValueError:
            raise AppError('INVALID_AGENT_ROLE', 'Unknown arrival role') from None
        if role not in {AgentRole.CLINICIAN_BRIEF, AgentRole.PATIENT_INSIGHT}:
            raise AppError('INVALID_AGENT_ROLE', 'Arrival supports assessment and patient recap only')
        window = 30 if role == AgentRole.PATIENT_INSIGHT else 56
        with self.agent.events.repositories.transaction() as repo:
            signature, blocked, _, state = self.agent._approval(repo, patient_id, client_offline)
            run_id = arrival_id(role, window, signature)
            cached = repo.agent_run(patient_id, run_id) if not blocked else None
            if cached and (cached.get('state_fingerprint') != signature or cached.get('role') != role.value
                           or cached.get('window_days') != window):
                cached = None
        if getattr(self.agent.provider, 'live', False) and not self.agent.synthetic_only:
            blocked = blocked or 'LIVE_SYNTHETIC_ONLY'
            cached = None
        result = {'run_id': run_id, 'state_fingerprint': signature, 'role': role.value,
            'window_days': window, 'status': 'BLOCKED' if blocked else 'COMPLETE',
            'draft': {'claims': [], 'question_ids': [], 'headline': ''}, 'sources': [],
            'trace': [], 'question_options': QUESTIONS, 'generation_used': False,
            'reason': blocked or 'OFFLINE_EXTRACTION', 'elapsed_ms': 0,
            'share_status': 'NOT_SENT', 'automatically_sent': False,
            'safety_reference': {'episode_id': (state or {}).get('episode_id'), 'sequence': (state or {}).get('sequence')},
            'disclosure': 'Assistant paused: safety interaction or record evaluation comes first.' if blocked else 'Source extraction while checked wording is prepared.'}
        if not blocked:
            tools, _ = self.agent.record_tools(patient_id, role, window)
            for name in ('get_series', 'get_context', 'get_gaps', 'get_decisions', 'get_review_snapshot'):
                tools.call(name, {})
            result['draft'] = fallback(tools, role)
            if role == AgentRole.PATIENT_INSIGHT:
                result['fallback_headline_fact_ids'] = [fid for claim in result['draft']['claims'] for fid in claim['fact_ids']]
            # Attach numerical companion facts without modifying required finding coverage.
            if role == AgentRole.CLINICIAN_BRIEF:
                for claim in result['draft']['claims']:
                    fact = tools.facts[claim['fact_ids'][0]]
                    numeric = next((row for row in tools.facts.values() if row['source_ref'] == fact['source_ref']
                        and row['signal'] == fact['signal'] and not row['finding'] and 'deviation' in row.get('raw_text',row['text'])), None)
                    if numeric:
                        claim['text'] = (claim['text'] + ' ' + numeric['text'])[:600]
                        claim['fact_ids'].append(numeric['fact_id'])
            result['sources'] = list(tools.delivered.values())
            from aura_agent.presentation import record_presentation
            result['record_presentation'] = record_presentation(tools,self.agent.config)
            result['draft']['question_ids'] = result['record_presentation']['question_ids']
            with self.agent.events.repositories.transaction() as repo:
                current, new_block, _, _ = self.agent._approval(repo, patient_id, client_offline)
            if current != signature:
                result.update(status='STALE', draft={'claims': [], 'question_ids': []}, sources=[], reason=new_block or 'STATE_CHANGED')
                result.pop('fallback_headline_fact_ids',None)
                result.pop('record_presentation',None)
                cached = None
        return {'preview': result, 'cached': cached, 'run_id': run_id, 'state_fingerprint': signature,
                'generation_allowed': not blocked and result['status'] == 'COMPLETE', 'window_days': window}
