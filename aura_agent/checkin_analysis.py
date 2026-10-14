"""Read-only categorical-day aggregation. No clinical inference or model arithmetic."""

from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from zoneinfo import ZoneInfo


def summarize(evidence, args, cutoff, fact_id):
    fields = {'start', 'end', 'last_days', 'state', 'denominator'}
    if set(args) != fields or args['state'] not in ('Good', 'Okay', 'Rough') or args['denominator'] not in ('recorded_days', 'calendar_days'):
        raise ValueError('UNAUTHORIZED_TOOL')
    tz_name = evidence.get('patient', {}).get('timezone', 'UTC')
    tz = ZoneInfo(tz_name)
    stamp = evidence['period']['end']
    if not stamp:
        raise ValueError('WINDOW_REQUIRED')
    finish = datetime.fromisoformat(stamp).astimezone(tz).date()
    if args['last_days'] is not None:
        if type(args['last_days']) is not int or not 1 <= args['last_days'] <= 56 or args['start'] is not None or args['end'] is not None:
            raise ValueError('WINDOW_REQUIRED')
        end = finish
        start = end - timedelta(days=args['last_days'] - 1)
    else:
        try:
            start, end = date.fromisoformat(args['start']), date.fromisoformat(args['end'])
        except (ValueError, TypeError):
            raise ValueError('WINDOW_REQUIRED') from None
    # Match the existing bounded analysis horizon, expressed in patient-local days.
    horizon = (datetime.fromisoformat(stamp).date() - date.fromisoformat(cutoff)).days
    if start > end or end > finish or start < finish - timedelta(days=horizon):
        raise ValueError('WINDOW_BUDGET')
    days = {}
    for order, row in enumerate(evidence['checkins']):
        when = datetime.fromisoformat(row['at'])
        day = when.astimezone(tz).date()
        if row['deferred'] or row['state'] not in ('Good', 'Okay', 'Rough') or not start <= day <= end:
            continue
        prior = days.get(day)
        if prior is None or (when, order) > prior[:2]:
            days[day] = (when, order, row)
    rows = [item[2] for _, item in sorted(days.items())]
    total = (end - start).days + 1
    counts = {state: sum(row['state'] == state for row in rows) for state in ('Good', 'Okay', 'Rough')}
    numerator = counts[args['state']]
    denominator = len(rows) if args['denominator'] == 'recorded_days' else total
    percentage = str((Decimal(numerator) * 100 / denominator).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)) if denominator else None
    basis = 'days with check-ins' if args['denominator'] == 'recorded_days' else 'calendar days'
    measure = (f"{percentage}% ({numerator} of {denominator} {basis}) were recorded as {args['state']}."
               if percentage is not None else f"The percentage recorded as {args['state']} is unavailable: no check-ins were recorded.")
    text = (f"From {start} through {end}: {measure} Check-ins covered {len(rows)} of {total} days; "
            f"{total-len(rows)} days had no check-in. Missing days remain unknown.")
    data = {'kind': 'checkin_proportion', 'version': 'checkin-analysis-v1', 'start': str(start), 'end': str(end),
            'timezone': tz_name, 'window_anchor': 'record_end', 'daily_selection': 'latest_nonheld_timestamp_then_commit_order',
            'counts': counts, 'state': args['state'], 'numerator': numerator, 'denominator': denominator,
            'denominator_kind': args['denominator'], 'calendar_days': total, 'recorded_days': len(rows),
            'missing_days': total-len(rows), 'percentage': percentage, 'rounding': 'half_up_1_decimal', 'display': text}
    return {'fact_id': fact_id, 'source_ref': 'analysis:' + sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16],
            'text': text, 'signal': None, 'finding': None, 'at': str(end), 'analysis': data,
            'source_refs': [row['event_id'] for row in rows]}
