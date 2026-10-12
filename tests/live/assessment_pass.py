"""Opt-in hosted synthetic assessment measurements; no credentials or prose saved.

Not collected by unittest/CI. Unique run IDs measure fresh generations rather than
cached retries. Existing provider/session budgets are respected, never bypassed.
"""

import argparse
from collections import Counter
from datetime import date, timedelta
import json
from pathlib import Path
from math import ceil
from statistics import median
import time
from uuid import uuid4

import httpx


class CallBudget:
    """Conservative local ledger of shared model calls, including failed attempts.

    All calls in an HTTP run are timestamped at completion, so expiry is never
    earlier than the server's reservation. Other clients remain unobservable.
    """
    def __init__(self, *, minute=10, hour=60, interval=35, initial_calls=0, now=0):
        self.minute, self.hour, self.interval = minute, hour, interval
        self.calls = [now] * initial_calls
        self.last_start = None

    def wait_seconds(self, now, reserve):
        if not 1 <= reserve <= min(self.minute, self.hour):
            raise ValueError('Request reservation exceeds shared quota')
        waits = [0 if self.last_start is None else self.last_start + self.interval - now]
        for window, limit in ((60, self.minute), (3600, self.hour)):
            active = sorted(at for at in self.calls if now - at < window)
            excess = len(active) + reserve - limit
            if excess > 0:
                waits.append(active[excess - 1] + window - now)
        return max(0, *waits)

    def start(self, now):
        self.last_start = now

    def record(self, now, count):
        self.calls = [at for at in self.calls if now - at < 3600] + [now] * count


def trace_usage(trace):
    """Trace success entries follow calls; FALLBACK supplies a failed attempt.

    Verifier validation can fail before its success trace is appended; reserve
    that attempt once even when the error is a validator rejection.
    """
    steps = sum(row.get('action') == 'MODEL_STEP' for row in trace)
    verifier = sum(row.get('action') == 'INDEPENDENT_VERIFIER' for row in trace)
    failure = None
    for row in trace:
        if row.get('action') != 'FALLBACK':
            continue
        stage = row.get('stage')
        if stage == 'MODEL_STEP':
            steps += 1
        elif stage == 'INDEPENDENT_VERIFIER' and not verifier:
            verifier += 1
        kind = row.get('provider_failure')
        if kind:
            # Never propagate arbitrary trace strings into saved evidence.
            allowed = {'unknown', 'too_large', 'bad_json', 'request_error',
                       'empty_content', 'bad_shape', 'bad_output', 'refusal',
                       'finish_length', 'finish_content_filter', 'finish_insufficient_system_resource'}
            http_kind = (isinstance(kind, str) and kind.startswith('http_')
                         and len(kind) == 8 and kind[5:].isdigit()
                         and 100 <= int(kind[5:]) <= 599)
            failure = kind if kind in allowed or http_kind else 'unknown'
    return steps + verifier, failure


def flu_data():
    """Evaluation truth goes only to the deterministic simulator, never agents."""
    return {'days': 3, 'seed': 42, 'request': '', 'notes': False,
            'plan': {'days': 3, 'events': [{'type': 'FLU', 'start_day': 1,
                     'duration_days': 3, 'severity': 'MODERATE'}], 'feedback': []}}


class DemoFixture:
    """Recreate the same fixture through normal bootstrap after cookie expiry."""
    def __init__(self, client, request):
        self.client, self.request = client, request
        self.base = None
        self.scenario = None
        self.bootstraps = 0

    def ensure(self, scenario):
        cookie_valid = any(cookie.name == 'aura_demo' and not cookie.is_expired(time.time() + 180)
                           for cookie in self.client.cookies.jar)
        if self.base is None or not cookie_valid:
            # An almost-expired cookie must be allowed to expire normally; do not
            # edit its expiry or keep an authenticated jar beyond Max-Age.
            for cookie in self.client.cookies.jar:
                if cookie.name == 'aura_demo' and cookie.expires is not None:
                    remaining = cookie.expires - time.time()
                    while remaining > 0 and remaining <= 180:
                        time.sleep(min(remaining, 60))
                        remaining = cookie.expires - time.time()
            catalog = self.request('GET', '/demo/scenarios')
            patient = next(r['patient_id'] for r in catalog['scenarios'] if r['id'] == 'B')
            self.base = f'/patients/{patient}'
            self.scenario = 'B'
            self.bootstraps += 1
        if scenario != self.scenario:
            if scenario != 'B_PLUS_FLU_3_DAYS':
                raise ValueError('Fixture cannot rewind an existing workspace')
            self.request('POST', f'{self.base}/workflows/advance',
                         json={'run_id': str(uuid4()), 'data': flu_data()})
            self.scenario = scenario
        return self.base


def summarize(measurements):
    """Per-role/scenario evidence; HTTP timings are proxies, not DOM paint times."""
    groups = {}
    for row in measurements:
        groups.setdefault((row['scenario'], row['role']), []).append(row)
    result = []
    for (scenario, role), rows in sorted(groups.items()):
        def p95(key):
            values = sorted(row[key] for row in rows)
            return values[ceil(.95 * len(values)) - 1]
        successes = sum(bool(row.get('validated_headline')) for row in rows)
        complete = len(rows) == 20
        result.append({'scenario': scenario, 'role': role, 'samples': len(rows),
            'validated_headlines': successes, 'preview_http_p95_ms': p95('preview_ms'),
            'swap_http_p95_ms': p95('total_ms'),
            'sample_gate': 'PASS' if complete and successes >= 18 else 'FAIL' if complete else 'INCOMPLETE',
            'timing_scope': 'HTTP response timings; visible-paint acceptance needs browser instrumentation'})
    return result


def card_count(result, evidence, role):
    """Mirror current rendering eligibility only; browser screenshots stay separate."""
    channels = set()
    for fact in result.get('sources', []):
        if not fact.get('finding'):
            continue
        finding = fact['finding']
        matches = [(signal,row) for signal in evidence['signals'] for row in signal['findings']
            if signal['key']['signal'] == finding['signal'] and row['event_id'] == fact.get('source_ref')
            and row['first_seen'][:10] == finding['since'] and row['last_seen'][:10] == fact.get('at')]
        if len(matches) == 1:
            key=matches[0][0]['key'];channels.add((key['signal'],key['source'],key.get('metric') or ''))
    # Patient measurements are retained inside a closed disclosure, not default
    # cards. This metric counts the initially visible measurement cards only.
    return 0 if role == 'patient_insight' else min(len(channels), 6)


def diagnostic(evidence):
    """Read-only numerical evidence for the proposed WP2 rule, not product policy."""
    end = date.fromisoformat(evidence['period']['end'][:10])
    start = end - timedelta(days=6)
    previous = start - timedelta(days=28)
    result = []
    for signal in evidence['signals']:
        name = signal['key']['signal']
        cfg = evidence['analysis_coverage_thresholds'][name]
        by_day = {}
        for row in signal['observations']:
            if row['deferred'] or min(row['coverage'], row['data_quality']) < cfg['minimum_observation_coverage']:
                continue
            prior = by_day.get(row['day'])
            if prior is None or (row['coverage'] * row['data_quality'], row.get('commit_order', 0)) >= (
                    prior['coverage'] * prior['data_quality'], prior.get('commit_order', 0)):
                by_day[row['day']] = row
        recent = [r['value'] for d, r in by_day.items() if start.isoformat() <= d <= end.isoformat()]
        baseline = [r['value'] for d, r in by_day.items() if previous.isoformat() <= d < start.isoformat()]
        center = median(baseline) if baseline else None
        spread = 1.4826 * median(abs(v - center) for v in baseline) if baseline else None
        current = signal['current'] or {}
        result.append({'channel': signal['key'], 'enabled_in_engine': signal['registry']['enabled_in_engine'],
            'trust': current.get('trust_state'), 'sensing': current.get('sensing_state'),
            'rolling': current.get('rolling'), 'anchor': current.get('anchor'),
            'engine_finding_kinds': [r['drift']['kind'] for r in signal['findings']],
            'engineering_parameters': cfg, 'recent_count': len(recent), 'baseline_count': len(baseline),
            'recent_values': recent, 'recent_median': median(recent) if recent else None,
            'previous_median': center, 'previous_robust_spread': spread,
            'median_delta': median(recent) - center if recent and baseline else None})
    return {'recent_start': start.isoformat(), 'end': end.isoformat(), 'channels': result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='https://aura-health.makodev58.com')
    parser.add_argument('--confirm-live-synthetic-checks', action='store_true')
    parser.add_argument('--runs', type=int, default=1, help='fresh runs PER role PER scenario (20 for WP1 gate)')
    parser.add_argument('--interval', type=float, default=35, help='seconds between live requests')
    parser.add_argument('--initial-budget-calls', type=int, default=0,
        help='known recent shared calls, conservatively retained for one hour (0–60)')
    parser.add_argument('--roles',nargs='+',choices=('clinician_brief','patient_insight'),default=('clinician_brief','patient_insight'))
    parser.add_argument('--output', default='docs/evidence/final-dash-baseline.json')
    args = parser.parse_args()
    if (not args.confirm_live_synthetic_checks or not 1 <= args.runs <= 20
            or args.interval < 35 or not 0 <= args.initial_budget_calls <= 60):
        parser.error('explicit paid synthetic confirmation, 1–20 runs and interval >=35 required')
    engineering = json.loads((Path(__file__).resolve().parents[2] / 'aura_agent' /
                              'engineering_config.json').read_text())
    reservation = engineering['max_steps'] + 1
    budget = CallBudget(interval=args.interval, initial_calls=args.initial_budget_calls,
                        now=time.monotonic())
    report = {'version': 'final-dash-live-pass-v3', 'runs_per_role_per_scenario': args.runs,
              'roles':args.roles,
              'budget': {'calls_per_minute': 10, 'calls_per_hour': 60,
                  'reserved_calls_per_assessment': reservation,
                  'initial_calls': args.initial_budget_calls,
                  'scope': 'local trace ledger; concurrent external callers are unobservable'},
              'fixture': {'seed': 42, 'days': 3, 'notes': False,
                  'plan': 'explicit MODERATE FLU, days 1–3; no model planner call'},
              'interval_seconds': args.interval, 'measurements': [], 'diagnostics': {}}
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    def save():
        report['summary'] = summarize(report['measurements'])
        report['rejection_histogram'] = dict(Counter(code for row in report['measurements']
            for code in row['rejection_codes']))
        output.write_text(json.dumps(report, indent=2) + '\n')

    with httpx.Client(base_url=args.base, timeout=180, trust_env=False) as client:
        def request(method, path, **kwargs):
            response = client.request(method, path, **kwargs)
            response.raise_for_status()
            return response.json()

        status = request('GET', '/system/status')
        if not status.get('synthetic_only') or not status.get('live_enabled'):
            raise SystemExit('An enabled synthetic-only provider is required')
        report['provider'] = {key: status.get(key) for key in ('provider', 'model', 'synthetic_only')}
        fixture = DemoFixture(client, request)

        def wait_budget():
            started = time.monotonic()
            while remaining := budget.wait_seconds(time.monotonic(), reservation):
                print(json.dumps({'event': 'quota_wait', 'seconds_remaining': round(remaining, 1)}), flush=True)
                time.sleep(min(remaining, 60))
            budget.start(time.monotonic())
            return round(time.monotonic() - started, 3)

        for scenario in ('B', 'B_PLUS_FLU_3_DAYS'):
            base = fixture.ensure(scenario)
            evidence = request('GET', f'{base}/evidence')
            report['diagnostics'][scenario] = diagnostic(evidence)
            save()
            for run in range(1, args.runs + 1):
                for role in args.roles:
                    quota_wait = wait_budget()
                    base = fixture.ensure(scenario)
                    evidence = request('GET', f'{base}/evidence')
                    start = time.monotonic()
                    preview = request('GET', f'{base}/assessment/{role}')
                    preview_ms = round((time.monotonic() - start) * 1000)
                    if not preview['generation_allowed']:
                        raise SystemExit('Assessment guard prohibits generation; report retained')
                    result = request('POST', f'{base}/agent/{role}', json={
                        'run_id': str(uuid4()), 'window_days': preview['window_days'],
                        'client_offline': False})
                    call_count, provider_failure = trace_usage(result.get('trace', []))
                    # TimeoutError has no FALLBACK stage in current runtime. Its
                    # final attempt is unobservable: retain the full reservation.
                    if result.get('reason') == 'MODEL_TIMEOUT':
                        call_count, provider_failure = reservation, 'timeout'
                    budget.record(time.monotonic(), call_count)
                    codes = [r['code'] for r in result.get('trace', []) if r.get('result') == 'REJECT' and 'code' in r]
                    verifier_rejections = sum(len(r.get('rejected_indices', [])) for r in result.get('trace', [])
                                              if r.get('action') == 'INDEPENDENT_VERIFIER')
                    claims = result['draft']['claims']
                    channels = {source.get('key_id') for source in result.get('sources', [])
                        if source.get('finding') and any(source['fact_id'] in c['fact_ids'] for c in claims)}
                    row = {'scenario': scenario, 'run': run, 'role': role, 'preview_ms': preview_ms,
                        'total_ms': round((time.monotonic() - start) * 1000),
                        'model_elapsed_ms': result['elapsed_ms'], 'reason': result['reason'],
                        'outcome': 'partial' if result['reason'] == 'VALIDATED_PARTIAL_MODEL_DRAFT' else
                            'validated_model_draft' if result['generation_used'] else 'fallback',
                        'headline_present': bool(result['draft'].get('headline')),
                        'validated_headline':bool(result['generation_used'] and result['draft'].get('headline')),
                        'prompt_version':result.get('prompt_version'),'config_version':result.get('config_version'),
                        'card_count': card_count(result, evidence, role),
                        'card_count_method': 'current UI eligibility; not browser DOM measurement',
                        'verifier_rejected_items': verifier_rejections,
                        'rejection_codes': codes or ([] if result['generation_used'] else [result['reason']]),
                        'claim_count': len(claims), 'finding_channel_count': len(channels)}
                    row.update({'quota_wait_seconds': quota_wait, 'model_call_count': call_count,
                                'provider_failure': provider_failure,
                                'model_call_count_method': 'conservative reservation; timeout stage unobservable'
                                if result.get('reason') == 'MODEL_TIMEOUT' else 'trace attempts including failures'})
                    report['session_bootstraps'] = fixture.bootstraps
                    report['measurements'].append(row)
                    save()
                    print(json.dumps(row), flush=True)


if __name__ == '__main__':
    main()
