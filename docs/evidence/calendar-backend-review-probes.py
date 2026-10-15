"""Diagnostic reproductions for REVIEW2_CODEX; run against the reviewed source with PYTHONPATH set.

Uses temporary synthetic records and fake gates only. Prints observations rather than asserting
the bugs should remain; this is review evidence, not a production regression suite.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
from aura_app.models import ApplicationEvent, EventType
from aura_app.persistence import SQLiteRepositoryFactory
from aura_app.service import PatientEventService
from aura_app.record_calendar import RecordCalendarService
from aura_app.sharing import SharingService
from aura_app.evidence import EvidenceViewService
from aura_app.safety import SafetyGateUnavailable
from aura_agent.tools import RecordTools

NOW = datetime(2026, 3, 11, 23, tzinfo=timezone.utc)
class Gate:
    fail = False
    def resolve(self, *args):
        if self.fail:
            raise SafetyGateUnavailable('review fake unavailable')
        return ()

with TemporaryDirectory() as folder:
    factory = SQLiteRepositoryFactory(Path(folder) / 'review.sqlite3')
    factory.initialize()
    gate = Gate()
    events = PatientEventService(factory, safety_gate=gate)
    cal = RecordCalendarService(events, SharingService(events), clock=lambda: NOW)
    def patient(pid, zone='UTC'):
        events.create_patient(patient_id=pid, display_name='Synthetic review', age=35, timezone_name=zone,
                              treatment={'medication_name':'Sertraline', 'medication_schedule':'50 mg, once each morning',
                                         'regimen_start':'2026-02-01'})
        events.process(ApplicationEvent(pid+'-seed', pid, EventType.PATIENT_CHECKIN, NOW, NOW,
                                        'review', {'state':'Okay'}, pid+'-seed', pid+'-seed'))
    def save(pid, day, status, request=None, reason=None):
        item = {'date':day, 'status':status}
        if reason:
            item['reason'] = reason
        return cal.save(pid, request_id=request or str(uuid4()), days=[item])

    # Interleave a competing save after A's read transaction but before A's write.
    patient('race')
    original = events.process_batch
    def competing(batch):
        events.process_batch = original
        save('race', '2026-03-10', 'MISSED')
        return original(batch)
    events.process_batch = competing
    response = save('race', '2026-03-10', 'ACKNOWLEDGED')
    with factory.transaction() as repo:
        rows = repo.medication_events('race')
    print(json.dumps({'probe':'different_request_race', 'saved':response['saved'], 'rows':len(rows),
                      'statuses':[r['status'] for r in rows]}))

    patient('samekey')
    request = str(uuid4())
    def changed_body(batch):
        events.process_batch = original
        save('samekey', '2026-03-10', 'MISSED', request)
        return original(batch)
    events.process_batch = changed_body
    response = save('samekey', '2026-03-10', 'ACKNOWLEDGED', request)
    with factory.transaction() as repo:
        rows = repo.medication_events('samekey')
    print(json.dumps({'probe':'same_request_changed_payload_race', 'saved':response['saved'],
                      'requested':'ACKNOWLEDGED', 'persisted':[r['status'] for r in rows]}))

    patient('body')
    request = str(uuid4())
    save('body', '2026-03-09', 'MISSED', request)
    response = save('body', '2026-03-10', 'ACKNOWLEDGED', request)
    print(json.dumps({'probe':'same_request_replaced_day_list', 'second_save':response['saved']}))

    patient('late')
    save('late', '2026-03-09', 'MISSED', reason='FORGOT')
    snapshot = events.review_snapshot('late')
    with factory.transaction() as repo:
        row = repo.medication_events('late')[0]
    print(json.dumps({'probe':'late_provenance', 'review_events':snapshot['medication_routine_events'],
                      'review_items':snapshot['unresolved_items'], 'normalized_columns':list(row)}))

    patient('zone', 'Asia/Singapore')
    save('zone', '2026-03-10', 'MISSED')
    evidence = EvidenceViewService(events).get('zone')
    tools = RecordTools(evidence, 'record_qa')
    print(json.dumps({'probe':'local_report_day', 'calendar':cal.day('zone','2026-03-10')['medication'],
                      'facts':[f['text'] for f in tools.facts.values() if 'Medication-routine' in f['text']]}))

    synthetic_coverage = {'signals':[
        {'registry':{'enabled_in_engine':True}, 'label':'A', 'key':{'metric':''},
         'observations':[{'day':'2026-03-10', 'coverage':1, 'deferred':False}]},
        {'registry':{'enabled_in_engine':True}, 'label':'B', 'key':{'metric':''}, 'observations':[]}
    ]}
    total, covered, _ = cal._coverage_by_day(synthetic_coverage)
    print(json.dumps({'probe':'coverage_denominator', 'enabled_signals':2, 'used_denominator':total,
                      'covered_signals':len(covered['2026-03-10'])}))

    patient('old')
    events.process(ApplicationEvent('old-med', 'old', EventType.MEDICATION_EVENT, NOW, NOW,
                    'review', {'scheduled_time':'2026-02-10T08:00:00+00:00', 'status':'ACKNOWLEDGED'}, 'old-med', 'old-med'))
    print(json.dumps({'probe':'older_last_medication', 'gap':cal.medication_gap('old'),
                      'coverage_last':cal.coverage('old')['last_medication_day']}))

    patient('held')
    gate.fail = True
    response = save('held', '2026-03-10', 'MISSED')
    with factory.transaction() as repo:
        deferred = [r['longitudinal_deferred'] for r in repo.events('held') if r['event_type']=='MEDICATION_EVENT']
    print(json.dumps({'probe':'gate_unavailable_at_ingest', 'saved':response['saved'],
                      'still_unresolved':response['window']['unresolved_count'], 'deferred':deferred}))
