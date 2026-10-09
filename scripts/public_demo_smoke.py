"""Public synthetic cases/isolation smoke. No model calls or credentials."""
import argparse
import json
from uuid import uuid4
import httpx

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--base',required=True)
    parser.add_argument('--confirm-synthetic-write',action='store_true')
    args=parser.parse_args()
    if not args.confirm_synthetic_write:parser.error('explicit synthetic workspace write confirmation required')
    with httpx.Client(base_url=args.base,timeout=90,trust_env=False) as first,httpx.Client(base_url=args.base,timeout=90,trust_env=False) as second:
        def read(client,path):
            response=client.get(path);response.raise_for_status();return response.json()
        assert read(first,'/health')['synthetic_only']
        catalog=read(first,'/demo/scenarios');read(second,'/demo/scenarios')
        rows=[]
        for case in 'ABCDEF':
            patient=next(row['patient_id'] for row in catalog['scenarios'] if row['id']==case)
            result={name:read(first,f'/patients/{patient}/{name}') for name in ('status','evidence','review-snapshot','timeline')}
            rows.append({'case':case,'status':'PASS','timeline_entries':len(result['timeline'])})
        patient=next(row['patient_id'] for row in catalog['scenarios'] if row['id']=='B')
        before=read(second,f'/patients/{patient}/evidence')
        body={'run_id':str(uuid4()),'data':{'day':before['period']['end'][:10],'values':{'BODY_TEMPERATURE':38.1}}}
        response=first.post(f'/patients/{patient}/workflows/manual',json=body);response.raise_for_status()
        original=response.json()
        response=first.post(f'/patients/{patient}/workflows/manual',json=body);response.raise_for_status()
        assert response.json()['idempotent_replay'] and response.json()['event_ids']==original['event_ids']
        assert read(second,f'/patients/{patient}/evidence')==before
        other=second.get(f"/patients/{patient}/workflow-runs/{body['run_id']}")
        assert other.status_code==404
        print(json.dumps({'cases':rows,'workspace_isolation':'PASS','manual_retry':'PASS','cross_session_trace':'404','paid_calls':0}))

if __name__=='__main__':main()
