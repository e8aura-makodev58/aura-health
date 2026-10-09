"""Confirmed synthetic intake, contextual proposals and demo life simulation.

No clinical policy here. All mutations route through PatientEventService; proposal
and completion traces are append-only. Models never write measurements or anchors.
"""

from contextlib import contextmanager
from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
import csv
import io
import json
import math
import threading
import os
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from aura_agent.guard import blocked_reason
from aura_agent.tasks import structured_task
from aura_longitudinal.domain import Signal
from aura_simulation.life import LifePlan, direct, generate, load_effects
from .models import AppError, ApplicationEvent, EventType
from .service import PatientEventService

def digest(value):
    return sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()

def risk_context_terms():
    raw=json.loads(Path(os.environ.get('AURA_CONTEXT_GUARD') or Path(__file__).with_name('context_guard.json')).read_text())
    return raw['risk_terms']

def measurements(day, values, registry, sources=None, coverage=1.0):
    """Exact supplied units. Missing values omitted, never replaced with zero."""
    date.fromisoformat(day)
    if not values or set(values) - {signal.value for signal in Signal}:
        raise ValueError('unknown or empty measurement selection')
    if any(type(v) not in {float, int} or not math.isfinite(v) for v in values.values()):
        raise ValueError('measurements must be finite numbers')
    sources = sources or {}
    def source(key): return sources.get(key, 'synthetic_'+registry.definition(Signal(key)).source_type)
    base = {'date': day, 'coverage': coverage}
    rows = []
    sleep = {'SLEEP_MIDPOINT', 'SLEEP_DURATION'}
    if set(values) & sleep:
        if not sleep <= set(values): raise ValueError('sleep timing and duration must be provided together; no invented missing value')
        midpoint, duration = values['SLEEP_MIDPOINT'], values['SLEEP_DURATION']
        if not 0 < duration <= 24 or not 0 <= midpoint <= 2880: raise ValueError('invalid sleep representation')
        start = datetime.combine(date.fromisoformat(day), datetime.min.time(), timezone.utc) + timedelta(minutes=midpoint-duration*30)
        if start.date().isoformat() != day: raise ValueError('midpoint must use minutes since sleep-start midnight')
        rows.append({**base, 'kind': 'sleep', 'source': source('SLEEP_MIDPOINT'), 'sleep_start': start.isoformat(),
                     'sleep_end': (start+timedelta(hours=duration)).isoformat(), 'data_quality': coverage})
    if 'ACTIVITY' in values:
        if values['ACTIVITY'] < 0: raise ValueError('activity cannot be negative')
        rows.append({**base, 'kind': 'activity', 'source': source('ACTIVITY'), 'metrics': {'steps': values['ACTIVITY']}})
    if 'RESTING_HEART_RATE' in values:
        if values['RESTING_HEART_RATE'] <= 0: raise ValueError('heart-rate representation must be positive')
        rows.append({**base, 'kind': 'resting_hr', 'source': source('RESTING_HEART_RATE'), 'value': values['RESTING_HEART_RATE']})
    for key, value in values.items():
        if key in sleep | {'ACTIVITY','RESTING_HEART_RATE'}: continue
        definition = registry.definition(Signal(key))
        rows.append({**base, 'kind': 'scalar', 'signal': key, 'value': value, 'source': source(key), 'data_quality': coverage, 'unit': definition.unit})
    return {'observations': rows}

class WorkflowService:
    def __init__(self, events, provider, *, synthetic_only=False, clock=None):
        self.events, self.provider, self.synthetic_only = events, provider, synthetic_only
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.lock = threading.RLock()

    def _read(self, patient_id):
        if not self.synthetic_only: raise AppError('SYNTHETIC_ONLY', 'Workflow is available in the synthetic demo only', 403)
        with self.events.repositories.transaction() as repo:
            self.events._patient(repo, patient_id)
            rows = repo.events(patient_id)
            baselines = repo.baselines(patient_id)
            state = repo.safety_state(patient_id)
        return rows, baselines, state

    def _signature(self, patient_id):
        rows, baselines, state = self._read(patient_id)
        return digest({'ids': [r['event_id'] for r in rows], 'baselines': baselines, 'state': state,
                       'registry': self.events.signal_registry.fingerprint})

    def _cached(self, patient_id, run_id, fingerprint):
        with self.events.repositories.transaction() as repo:
            self.events._patient(repo, patient_id)
            cached = repo.workflow_run(patient_id, run_id)
        if cached and cached['request_fingerprint'] != fingerprint:
            raise AppError('WORKFLOW_CONFLICT', 'Run ID belongs to different inputs', 409)
        return {**cached, 'idempotent_replay': True} if cached else None

    def _record(self, patient_id, run_id, kind, fingerprint, data, events=(), *, signature=None):
        with self.events.repositories.transaction() as repo:
            self.events._patient(repo, patient_id)
            prior = repo.workflow_run(patient_id, run_id)
            if prior:
                if prior['request_fingerprint'] != fingerprint: raise AppError('WORKFLOW_CONFLICT','Run ID conflict',409)
                return {**prior, 'idempotent_replay': True}
            if signature is not None:
                actual = digest({'ids': [r['event_id'] for r in repo.events(patient_id)], 'baselines': repo.baselines(patient_id),
                                 'state': repo.safety_state(patient_id), 'registry': self.events.signal_registry.fingerprint})
                if actual != signature: raise AppError('STALE_PROPOSAL','Record changed; request a new proposal',409)
            class Shared:
                @contextmanager
                def transaction(self): yield repo
            child = PatientEventService(Shared(), safety_gate=self.events.safety_gate, safety_engine=self.events.safety_engine,
                resource_registry=self.events.resource_registry, signal_registry=self.events.signal_registry)
            results = [asdict(child.command_anchor(e) if e.event_type == EventType.ANCHOR_COMMAND else child.process(e)) for e in events]
            row = {'patient_id': patient_id, 'run_id': run_id, 'kind': kind, 'created_at': self.clock().isoformat(),
                   'request_fingerprint': fingerprint, **data, 'event_ids': [e.event_id for e in events], 'results': results,
                   'policy_config_version': self.events.safety_engine.config.version,
                   'registry_fingerprint': self.events.signal_registry.fingerprint, 'model_id': self.provider.model_id}
            row['observable_event_hashes']=[digest({'event_id':e.event_id,'event_type':e.event_type.value,'occurred_at':e.occurred_at.isoformat(),'source':e.source,'payload':e.payload}) for e in events]
            repo.append_workflow_run(row)
            repo.append_audit({'patient_id':patient_id, 'event_id':events[-1].event_id if events else 'workflow-proposal',
                'correlation_id':run_id,'action':kind, 'called_domains':['aura_app.workflows'], 'communication':None,
                'safety_ref':None,'review_item_ids':[], 'anchor_command':None, 'idempotency_result':'NEW','timestamp':row['created_at']})
            return row

    def _event(self, patient_id, run_id, index, kind, at, payload, *, source='SIMULATOR'):
        ident = str(uuid5(NAMESPACE_URL, f'aura-workflow:{patient_id}:{run_id}:{index}'))
        return ApplicationEvent(ident, patient_id, EventType(kind), at, self.clock(), source, payload, ident, ident)

    def manual(self, patient_id, *, run_id, day, values):
        self._read(patient_id)
        fp = digest({'day':day,'values':values})
        if cached := self._cached(patient_id,run_id,fp): return cached
        try: payload = measurements(day, values, self.events.signal_registry)
        except (ValueError,TypeError): raise AppError('INVALID_EVENT','Use finite values and exact displayed units; sleep requires timing and duration') from None
        rows, baselines, _ = self._read(patient_id)
        sources = {b['signal']:b['source'] for b in baselines}
        payload = measurements(day, values, self.events.signal_registry,sources)
        latest = datetime.fromisoformat(rows[-1]['occurred_at']).date()
        if abs((date.fromisoformat(day)-latest).days)>365: raise AppError('INVALID_EVENT','Date outside demo intake window')
        event = self._event(patient_id,run_id,0,'WEARABLE_OBSERVATION',datetime.fromisoformat(day+'T12:00:00+00:00'),payload,source='SYNTHETIC_MANUAL')
        return self._record(patient_id,run_id,'MANUAL_ENTRY',fp,{},[event])

    def import_proposal(self, patient_id, *, run_id, format, content):
        self._read(patient_id)
        fp = digest({'format':format,'content':content})
        if cached := self._cached(patient_id,run_id,fp): return cached
        try:
            rows = list(csv.DictReader(io.StringIO(content))) if format=='csv' else json.loads(content) if format=='json' else None
            if not isinstance(rows,list) or not 1<=len(rows)<=60 or any(not isinstance(row,dict) or not 1<=len(row)<=20 for row in rows): raise ValueError()
            headers = list(rows[0])
            if any(set(row)!=set(headers) for row in rows) or any(not isinstance(key,str) or len(key)>100 for key in headers): raise ValueError()
            if any(any(type(value) not in {str,int,float,type(None)} for value in row.values()) for row in rows): raise ValueError()
        except Exception: raise AppError('INVALID_IMPORT','Use CSV or a JSON list with 1–60 consistent rows and at most 20 columns') from None
        registry = self.events.signals()
        catalog = {s['name']:('steps' if s['name']=='ACTIVITY' else s['unit']) for s in registry['signals']}
        try:
            mapping = structured_task(self.provider,'map_import',{'headers':headers,'sample':rows[:2],'allowed_signals':catalog})
            self._validate_mapping(mapping,headers,catalog)
            reason = 'MODEL_MAPPING_REQUIRES_CONFIRMATION'
        except Exception as error:
            mapping = {'date_column': 'date' if 'date' in headers else headers[0], 'columns':[{'column':key,'signal':key,'unit':catalog[key]} for key in headers if key in catalog]}
            reason = 'OFFLINE_EXACT_HEADER_MAPPING'
        return self._record(patient_id,run_id,'IMPORT_PROPOSAL',fp,{'rows':rows,'headers':headers,'mapping':mapping,'status':reason,
            'state_fingerprint':self._signature(patient_id),'confirmed':False})

    @staticmethod
    def _validate_mapping(mapping,headers,catalog):
        if set(mapping)!= {'date_column','columns'} or mapping['date_column'] not in headers or not isinstance(mapping['columns'],list) or len(mapping['columns'])>12: raise ValueError('invalid mapping')
        used, signals = set(),set()
        for c in mapping['columns']:
            if set(c)!= {'column','signal','unit'} or c['column'] not in headers or c['column']==mapping['date_column'] or c['signal'] not in catalog or c['unit']!=catalog[c['signal']] or c['column'] in used or c['signal'] in signals: raise ValueError('invalid mapping')
            used.add(c['column']);signals.add(c['signal'])

    def confirm_import(self,patient_id,*,run_id,proposal_id,mapping,confirm):
        if confirm!='IMPORT_SYNTHETIC_DATA': raise AppError('CONFIRMATION_REQUIRED','Explicit synthetic import confirmation required')
        self._read(patient_id); fp=digest({'proposal':proposal_id,'mapping':mapping,'confirm':confirm})
        if cached:=self._cached(patient_id,run_id,fp): return cached
        with self.events.repositories.transaction() as repo: proposal=repo.workflow_run(patient_id,proposal_id)
        if not proposal or proposal['kind']!='IMPORT_PROPOSAL': raise AppError('INVALID_IMPORT','Unknown mapping proposal')
        catalog={s['name']:('steps' if s['name']=='ACTIVITY' else s['unit']) for s in self.events.signals()['signals']}
        try:
            self._validate_mapping(mapping,proposal['headers'],catalog)
            if not mapping['columns']: raise ValueError()
            sources={b['signal']:b['source'] for b in self._read(patient_id)[1]}
            events=[]; days=set()
            latest=datetime.fromisoformat(self._read(patient_id)[0][-1]['occurred_at']).date()
            for index,row in enumerate(proposal['rows']):
                day=str(row[mapping['date_column']]); parsed=date.fromisoformat(day)
                if day in days or abs((parsed-latest).days)>365: raise ValueError()
                days.add(day)
                values={c['signal']:float(row[c['column']]) for c in mapping['columns'] if row[c['column']] not in ('',None)}
                if not values: continue
                payload=measurements(day,values,self.events.signal_registry,sources)
                events.append(self._event(patient_id,run_id,index,'WEARABLE_OBSERVATION',datetime.fromisoformat(day+'T12:00:00+00:00'),payload,source='SYNTHETIC_IMPORT'))
        except (ValueError,TypeError,KeyError): raise AppError('INVALID_IMPORT','Invalid date/value/unit mapping; missing cells are omitted, sleep requires both fields') from None
        return self._record(patient_id,run_id,'IMPORT_CONFIRMED',fp,{'proposal_id':proposal_id,'mapping':mapping,'confirmed':True},events,signature=proposal['state_fingerprint'])

    def propose_context(self,patient_id,*,run_id,text):
        if not isinstance(text,str) or not 1<=len(text)<=2000: raise AppError('INVALID_EVENT','Bounded explanation required')
        rows,_,state=self._read(patient_id); fp=digest(text)
        if cached:=self._cached(patient_id,run_id,fp): return cached
        # Safety first. Even a failed proposal leaves an audited safety-gated note.
        note=self._event(patient_id,run_id,'note','PATIENT_FREE_TEXT',datetime.fromisoformat(rows[-1]['occurred_at']),{'text':text},source='synthetic_patient_ui')
        self.events.process(note)
        rows,baselines,state=self._read(patient_id)
        if blocked_reason(state,self.events.resource_registry,self.clock()): raise AppError('SAFETY_INTERACTION_FIRST','Safety review takes precedence; explanation held',409)
        signals=sorted({b['signal'] for b in baselines})
        try:
            proposal=structured_task(self.provider,'context',{'explanation':text,'allowed_signals':signals})
            if set(proposal)!= {'category','affected_signals'} or proposal['category'] not in {'BENIGN_CONTEXT','RISK_CONTEXT'} or not proposal['affected_signals'] or not set(proposal['affected_signals'])<=set(signals): raise ValueError()
            # Conservative fixture guard: risk-context terms cannot be benign-cleared.
            if any(word in text.lower() for word in risk_context_terms()): proposal['category']='RISK_CONTEXT'
            reason='MODEL_PROPOSAL_REQUIRES_CONFIRMATION'
        except Exception:
            proposal={'category':'RISK_CONTEXT','affected_signals':[]};reason='MANUAL_ASSOCIATION_REQUIRED'
        return self._record(patient_id,run_id,'CONTEXT_PROPOSAL',fp,{'text':text,'proposal':proposal,'status':reason,'state_fingerprint':self._signature(patient_id)})

    def confirm_context(self,patient_id,*,run_id,proposal_id,category,affected_signals,confirm):
        self._read(patient_id)
        if confirm!='KEEP_EXPLICIT_CONTEXT': raise AppError('CONFIRMATION_REQUIRED','Confirm explicit signal association')
        fp=digest({'proposal_id':proposal_id,'category':category,'signals':affected_signals})
        if cached:=self._cached(patient_id,run_id,fp):return cached
        with self.events.repositories.transaction() as repo: proposal=repo.workflow_run(patient_id,proposal_id)
        if not proposal or proposal['kind']!='CONTEXT_PROPOSAL':raise AppError('INVALID_EVENT','Unknown explanation proposal')
        if category not in {'BENIGN_CONTEXT','RISK_CONTEXT'} or not affected_signals or not set(affected_signals)<={s.value for s in Signal}:raise AppError('INVALID_EVENT','Select category and explicit signals')
        if proposal['proposal']['category']=='RISK_CONTEXT' and category=='BENIGN_CONTEXT':raise AppError('INVALID_EVENT','Risk context cannot be used to explain deterioration away')
        at=datetime.fromisoformat(self._read(patient_id)[0][-1]['occurred_at'])
        context=self._event(patient_id,run_id,0,'CONTEXT_EVENT',at,{'start':at.isoformat(),'end':None,'category':category,'affected_signals':affected_signals,'source':'patient','explanation':proposal['text']},source='synthetic_patient_ui')
        events=[context]
        if category=='BENIGN_CONTEXT':events.append(self._event(patient_id,run_id,1,'CONTEXT_EXPLANATION',at,{'context_event_id':context.event_id,'explanation':proposal['text'],'affected_signals':affected_signals,'relevant_drift_ref':None},source='synthetic_patient_ui'))
        return self._record(patient_id,run_id,'CONTEXT_CONFIRMED',fp,{'proposal_id':proposal_id,'confirmed':True},events,signature=proposal['state_fingerprint'])

    def advance(self,patient_id,*,run_id,days=3,seed=7,request='',notes=True,plan=None):
        if type(days) is not int or not 1<=days<=30 or type(seed) is not int or not 0<=seed<=2**31-1 or type(notes) is not bool or not isinstance(request,str) or len(request)>2000:raise AppError('INVALID_SIMULATION','Invalid advance/options')
        with self.lock:
            rows,baselines,state=self._read(patient_id);fp=digest({'days':days,'seed':seed,'request':request,'notes':notes,'plan':plan})
            if cached:=self._cached(patient_id,run_id,fp):return cached
            effects=load_effects()
            with self.events.repositories.transaction() as repo:runs=[r for r in repo.workflow_runs(patient_id) if r['kind']=='SIMULATOR_RUN']
            if sum(r['plan']['days'] for r in runs)+days>effects['max_session_days'] or len(runs)>=effects['max_session_runs']:raise AppError('SIMULATION_BUDGET','Demo advance budget reached; reset the session',429)
            start=max(datetime.fromisoformat(r['occurred_at']).date() for r in rows).isoformat();signature=self._signature(patient_id)
            if plan is not None:
                try:resolved=LifePlan.model_validate(plan)
                except ValueError:raise AppError('INVALID_SIMULATION','Invalid structured life plan') from None
                if resolved.days!=days:raise AppError('INVALID_SIMULATION','Plan length mismatch')
                reason='EXPLICIT_STRUCTURED_PLAN'
            else:
                with self.events.repositories.transaction() as repo:patient=repo.patient(patient_id)
                observed={'recent_checkins':[r['payload']['state'] for r in rows if r['event_type']=='PATIENT_CHECKIN'][-7:],
                          'persona':{'age':patient['age'],'regimen':'stable clinician-managed maintenance'},'current_date':start,
                          'baseline_sensing':[{'signal':b['signal'],'state':b['sensing_state']} for b in baselines]}
                resolved,reason=direct(self.provider,days,request,observed)
            profile=dict(effects['profile']);sources={b['signal']:b['source'] for b in baselines}
            for b in baselines:
                if b['anchor']:profile[b['signal']]=b['anchor']['center']
            carry=[]
            for prior in runs:
                shift=(date.fromisoformat(prior['start'])-date.fromisoformat(start)).days
                for old in prior['plan']['events']:
                    relative={**old,'start_day':old['start_day']+shift}
                    end=relative['start_day']+relative['duration_days']-1
                    if -effects['recovery_tail_days']<=end<=0 and old['type'] not in {'ALCOHOL','MISSED_MEDICATION','WEARABLE_OFF'}:
                        carry.append(relative)
            generated=generate(resolved,seed=seed,patient_id=patient_id,start=start,profile=profile,effects=effects,notes=notes,carry_events=carry)
            events=[]
            # New continuous channels receive an EXPLICIT synthetic reference-review
            # command, never an automatic reference rewrite from evaluated data.
            known={b['signal'] for b in baselines if b['anchor']}
            new=[s.value for s in (Signal.HRV,Signal.RESPIRATORY_RATE,Signal.SKIN_TEMPERATURE_DEVIATION) if s.value not in known and self.events.signal_registry.definition(s).enabled_in_engine]
            if new:
                reference_start=date.fromisoformat(start)-timedelta(days=27)
                for offset in range(28):
                    d=(reference_start+timedelta(days=offset)).isoformat()
                    stable=generate(LifePlan(days=1,events=[]),seed=seed,patient_id=patient_id,start=(date.fromisoformat(d)-timedelta(days=1)).isoformat(),profile=profile,effects=effects,notes=False)[0]
                    events.append(self._event(patient_id,run_id,f'reference-{offset}','WEARABLE_OBSERVATION',datetime.fromisoformat(d+'T11:00:00+00:00'),measurements(d,{s:stable['values'][s] for s in new},self.events.signal_registry,sources)))
                for signal in new:
                    events.append(self._event(patient_id,run_id,'anchor-'+signal,'ANCHOR_COMMAND',datetime.fromisoformat(start+'T12:00:00+00:00'),
                        {'action':'CREATE_PROVISIONAL_ANCHOR','signal':signal,'source':sources.get(signal,'synthetic_wearable'),'metric':None,'reference_start':reference_start.isoformat(),'reference_end':start,'reviewed_by':None}))
                    events.append(self._event(patient_id,run_id,'trust-'+signal,'ANCHOR_COMMAND',datetime.fromisoformat(start+'T12:00:00+00:00'),
                        {'action':'TRUST_ANCHOR','signal':signal,'source':sources.get(signal,'synthetic_wearable'),'metric':None,'reviewed_by':'synthetic-fixture-review-v1'}))
            for row in generated:
                at=datetime.fromisoformat(row['date']+'T12:00:00+00:00')
                if row['values']:events.append(self._event(patient_id,run_id,row['date']+'-measure','WEARABLE_OBSERVATION',at,measurements(row['date'],row['values'],self.events.signal_registry,sources)))
                if notes:
                    events.append(self._event(patient_id,run_id,row['date']+'-checkin','PATIENT_CHECKIN',at,{'state':row['checkin']}))
                    events.append(self._event(patient_id,run_id,row['date']+'-med','MEDICATION_EVENT',at,{'status':row['medication'],'scheduled_time':at.isoformat()}))
                if row['note']:events.append(self._event(patient_id,run_id,row['date']+'-note','PATIENT_FREE_TEXT',at,{'text':row['note']}))
            return self._record(patient_id,run_id,'SIMULATOR_RUN',fp,{'plan':resolved.model_dump(),'carry_events':carry,'seed':seed,'start':start,'profile':profile,'effects':effects,'status':reason,'generated':generated,'notes_enabled':notes,'synthetic_only':True},events,signature=signature)

    def trace(self,patient_id,run_id):
        self._read(patient_id)
        with self.events.repositories.transaction() as repo:row=repo.workflow_run(patient_id,run_id)
        if not row:raise AppError('WORKFLOW_NOT_FOUND','Unknown run',404)
        return row

    def replay(self,patient_id,run_id):
        row=self.trace(patient_id,run_id)
        if row['kind']!='SIMULATOR_RUN':raise AppError('INVALID_SIMULATION','Run is not a simulator trace')
        generated=generate(LifePlan.model_validate(row['plan']),seed=row['seed'],patient_id=patient_id,start=row['start'],profile=row['profile'],effects=row['effects'],notes=row['notes_enabled'],carry_events=row.get('carry_events',[]))
        with self.events.repositories.transaction() as repo:events={e['event_id']:e for e in repo.events(patient_id)}
        hashes=[digest({key:events[event_id][key] for key in ('event_id','event_type','occurred_at','source','payload')}) for event_id in row['event_ids'] if event_id in events]
        committed=hashes==row['observable_event_hashes']
        return {'run_id':run_id,'matched':generated==row['generated'] and committed,'committed_events_match':committed,'event_count':len(hashes),'days':len(generated),'measurements_hash':digest(generated),'writes':0}
