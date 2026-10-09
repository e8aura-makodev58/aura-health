"""Opt-in synthetic arrival/cache/timing check; never reads provider credentials."""

import argparse
import json
from pathlib import Path
import time
from uuid import uuid4

import httpx


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='http://127.0.0.1:8017')
    parser.add_argument('--confirm-live-synthetic-checks', action='store_true')
    parser.add_argument('--flu', action='store_true', help='also commit a three-day synthetic flu')
    parser.add_argument('--roles', nargs='+', choices=('clinician_brief', 'patient_insight'),
                        default=('clinician_brief', 'patient_insight'))
    parser.add_argument('--output', default='/tmp/aura-impression-smoke.json')
    args = parser.parse_args()
    if not args.confirm_live_synthetic_checks:
        parser.error('explicit paid synthetic smoke confirmation required')
    report = {'checks': []}
    with httpx.Client(base_url=args.base, timeout=180, trust_env=False) as client:
        def request(method, path, **kwargs):
            response = client.request(method, path, **kwargs)
            response.raise_for_status()
            return response.json()

        status = request('GET', '/system/status')
        if not status.get('synthetic_only') or not status.get('live_enabled'):
            raise SystemExit('Live synthetic provider must be enabled for this smoke')
        report['provider'] = {key: status.get(key) for key in ('provider', 'model', 'synthetic_only', 'live_enabled')}
        catalog = request('GET', '/demo/scenarios')
        patient = next(row['patient_id'] for row in catalog['scenarios'] if row['id'] == 'B')
        base = f'/patients/{patient}'

        def assessment(role):
            start = time.monotonic()
            arrival = request('GET', f'{base}/assessment/{role}')
            preview_ms = round((time.monotonic() - start) * 1000)
            assert arrival['generation_allowed'] and arrival['preview']['draft']['claims']
            body = {'run_id': arrival['run_id'], 'window_days': arrival['window_days'], 'client_offline': False}
            result = request('POST', f'{base}/agent/{role}', json=body)
            total_ms = round((time.monotonic() - start) * 1000)
            cached = request('GET', f'{base}/assessment/{role}')
            retry = request('POST', f'{base}/agent/{role}', json=body)
            assert cached['run_id'] == arrival['run_id']
            assert cached['cached']['draft'] == result['draft']
            assert retry.get('idempotent_replay') and retry['draft'] == result['draft']
            offline = request('GET', f'{base}/assessment/{role}', params={'client_offline': 'true'})
            assert not offline['generation_allowed'] and offline['cached'] is None
            assert not offline['preview']['draft']['claims']
            check = {'role': role, 'preview_ms': preview_ms, 'total_ms': total_ms,
                     'model_elapsed_ms': result['elapsed_ms'], 'reason': result['reason'],
                     'generation_used': result['generation_used'], 'claim_count': len(result['draft']['claims']),
                     'exact_cache_and_retry': True, 'offline_contains_no_claims': True,
                     'validated_live_under_5s': result['generation_used'] and total_ms < 5000,
                     'run_id': result['run_id']}
            report['checks'].append(check)
            print(json.dumps(check), flush=True)
            return result

        for index, role in enumerate(args.roles):
            if index:
                time.sleep(35)  # Respect the existing operator/provider call budget.
            assessment(role)
        if args.flu:
            time.sleep(35)
            old = request('GET', f'{base}/assessment/clinician_brief')['run_id']
            start = time.monotonic()
            simulated = request('POST', f'{base}/workflows/advance', json={
                'run_id': str(uuid4()), 'data': {'days': 3, 'seed': 42,
                    'request': 'Three days of flu', 'notes': False}})
            arrival = request('GET', f'{base}/assessment/clinician_brief')
            elapsed_ms = round((time.monotonic() - start) * 1000)
            assert arrival['run_id'] != old and arrival['cached'] is None
            replay = request('GET', f"{base}/simulator-runs/{simulated['run_id']}/replay")
            assert replay['matched']
            check = {'scenario': 'flu_3_days', 'commit_and_preview_ms': elapsed_ms,
                     'under_30s': elapsed_ms <= 30000, 'fingerprint_changed': True,
                     'replay_matched': True, 'status': simulated['status'],
                     'preview_claim_count': len(arrival['preview']['draft']['claims'])}
            report['checks'].append(check)
            print(json.dumps(check), flush=True)
    Path(args.output).write_text(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
