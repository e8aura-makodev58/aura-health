"""Explicit operator smoke of synthetic-only live skills; never reads keys."""
import argparse
import json
from pathlib import Path
import time
from uuid import uuid4
import httpx

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--base',default='http://127.0.0.1:8017');parser.add_argument('--confirm-live-synthetic-checks',action='store_true');parser.add_argument('--output',default='/tmp/aura-live-agent-sweep.json');args=parser.parse_args()
    if not args.confirm_live_synthetic_checks:parser.error('explicit paid synthetic smoke confirmation required')
    results=[]
    with httpx.Client(base_url=args.base,timeout=90,trust_env=False) as client:
        status=client.get('/system/status').json()
        if not status.get('synthetic_only') or not status.get('live_enabled'):raise SystemExit('Live synthetic provider is not enabled')
        catalog=client.get('/demo/scenarios');catalog.raise_for_status()
        patient=next(s['patient_id'] for s in catalog.json()['scenarios'] if s['id']=='B')
        for role in ('clinician_brief','record_qa','patient_insight','visit_prep','question_ranker'):
            if results:time.sleep(35)
            body={'run_id':str(uuid4()),'window_days':30 if role=='patient_insight' else 56,'client_offline':False}
            if role=='record_qa':body['query_id']='sleep_change'
            response=client.post(f'/patients/{patient}/agent/{role}',json=body);response.raise_for_status();row=response.json()
            retry=client.post(f'/patients/{patient}/agent/{role}',json=body);retry.raise_for_status()
            report={'role':role,'status':row['status'],'reason':row['reason'],'generation_used':row['generation_used'],
                    'elapsed_ms':row['elapsed_ms'],'claim_count':len(row['draft']['claims']),
                    'tool_calls':[t for t in row['trace'] if 'tool' in t],
                    'validation':[t for t in row['trace'] if t.get('action') in ('VALIDATION','INDEPENDENT_VERIFIER','FALLBACK')],
                    'exact_retry':row['draft']==retry.json()['draft'] and retry.json().get('idempotent_replay',False),
                    'run_id':row['run_id']}
            results.append(report);print(json.dumps(report),flush=True)
        # Authorized free question, import proposal and life director use the same
        # workspace/provider; isolated from other browser sessions.
        time.sleep(20)
        qa=client.post(f'/patients/{patient}/agent/record_qa',json={'run_id':str(uuid4()),'question':'Compare my recent sleep timing with the earlier recorded weeks.','window_days':56});qa.raise_for_status()
        print(json.dumps({'free_question_status':qa.json()['status'],'reason':qa.json()['reason']}),flush=True)
        time.sleep(20)
        proposed=client.post(f'/patients/{patient}/workflows/import-proposal',json={'run_id':str(uuid4()),'data':{'format':'csv','content':'date,resting_hr\n2026-03-12,66'}});proposed.raise_for_status()
        print(json.dumps({'import_mapping_status':proposed.json()['status'],'mapping':proposed.json()['mapping']}),flush=True)
        time.sleep(20)
        simulated=client.post(f'/patients/{patient}/workflows/advance',json={'run_id':str(uuid4()),'data':{'days':3,'seed':42,'request':'Three days of flu with a raised thermometer temperature and lower activity.','notes':False}});simulated.raise_for_status()
        replay=client.get(f"/patients/{patient}/simulator-runs/{simulated.json()['run_id']}/replay");replay.raise_for_status()
        print(json.dumps({'life_director_status':simulated.json()['status'],'plan':simulated.json()['plan'],'replay':replay.json()}),flush=True)
    Path(args.output).write_text(json.dumps({'provider':status,'skills':results,'free_question':{'status':qa.json()['status'],'reason':qa.json()['reason']},'import':{'status':proposed.json()['status'],'mapping':proposed.json()['mapping']},'simulator':{'status':simulated.json()['status'],'plan':simulated.json()['plan'],'replay':replay.json()}},indent=2))

if __name__=='__main__':main()
