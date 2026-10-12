"""Deterministic wording projection; original facts and finding metadata stay intact."""
from datetime import date
import json
from pathlib import Path
import re

PLAIN_TERMS = json.loads(Path(__file__).with_name('plain_terms.json').read_text())
VOICE_EXAMPLES = json.loads(Path(__file__).with_name('voice_examples.json').read_text())
LABELS = {'SLEEP_MIDPOINT':'sleep time', 'SLEEP_DURATION':'sleep duration',
          'ACTIVITY':'activity', 'RESTING_HEART_RATE':'resting heart rate',
          'HRV':'variation in time between your heartbeats', 'RESPIRATORY_RATE':'breathing rate',
          'SKIN_TEMPERATURE_DEVIATION':'skin temperature', 'SPO2':'oxygen reading',
          'BODY_TEMPERATURE':'temperature', 'WEIGHT':'weight',
          'BLOOD_PRESSURE_SYSTOLIC':'upper blood pressure reading',
          'BLOOD_PRESSURE_DIASTOLIC':'lower blood pressure reading'}


def jargon(text, patient=False):
    terms = PLAIN_TERMS['patient' if patient else 'clinician']
    return any(re.search(r'\b'+re.escape(row['term'])+r'\b', text, re.I) for row in terms)


def date_label(value):
    day = date.fromisoformat(value[:10])
    return f'{day.day} {day.strftime("%b")}'


def since_phrase(value):
    day = date.fromisoformat(value[:10])
    part = 'early' if day.day <= 10 else 'mid' if day.day <= 20 else 'late'
    return f'since {part} {day.strftime("%B")}'


def prepare_fact(fact, keys, patient):
    """Added numeric phrases are part of the source text, never validator exemptions."""
    raw = fact['text']
    fact['raw_text'] = raw
    friendly = {'text':'', 'since_phrase':'', 'duration_phrase':'', 'magnitude_phrase':'',
                'source_label':'Your entries', 'date_label':date_label(fact['at']) if fact.get('at') else ''}
    finding = fact.get('finding')
    if finding:
        label = LABELS.get(fact['signal'], 'reading')
        direction = finding['direction'].lower()
        reference = 'in your recent records' if fact.get('comparison') == 'RECENT_PATTERN' else 'your usual'
        friendly['since_phrase'] = since_phrase(finding['since'])
        span = (date.fromisoformat(fact['at'])-date.fromisoformat(finding['since'])).days+1
        friendly['duration_phrase'] = f'about {max(1, round(span/7))} weeks' if span >= 14 else f'{span} days'
        friendly['date_label'] = date_label(finding['since'])+' – '+date_label(fact['at'])
        magnitude = fact.get('magnitude',{})
        amount = magnitude.get('value')
        if amount is not None:
            amount = abs(amount)
            if fact['signal'] == 'SLEEP_MIDPOINT':
                friendly['magnitude_phrase'] = (f'about {round(amount/60)} hours' if amount >= 90 else
                    f'about {max(1,round(amount/5)*5)} minutes')
            elif fact['signal'] == 'SLEEP_DURATION':
                friendly['magnitude_phrase'] = f'about {round(amount,1):g} hours'
            elif fact['signal'] == 'RESTING_HEART_RATE':
                friendly['magnitude_phrase'] = f'about {round(amount)} beats per minute'
            elif fact['signal'] == 'RESPIRATORY_RATE':
                friendly['magnitude_phrase'] = f'about {round(amount,1):g} breaths per minute'
            elif fact['signal'] == 'SKIN_TEMPERATURE_DEVIATION':
                friendly['magnitude_phrase'] = f'about {round(amount,1):g} degrees'
        amount_phrase = (friendly['magnitude_phrase']+' ') if friendly['magnitude_phrase'] else ''
        friendly['text'] = f'Your {label} was {amount_phrase}{direction} than {reference} {friendly["since_phrase"]}.'
        friendly['source_label'] = 'Your measurements'
    elif fact.get('checkin_run'):
        run = fact['checkin_run']
        friendly['text'] = f'You marked {len(run["source_refs"])} days in a row as {run["state"]} in your check-ins.'
        friendly['source_label'] = 'Your check-ins'
        friendly['date_label'] = date_label(run['start'])+' – '+date_label(run['end'])
    elif fact.get('checkin_summary'):
        summary = fact['checkin_summary']
        friendly['text'] = f'You marked {summary["count"]} of the last {summary["window_days"]} days as {summary["state"]} in your check-ins.'
        friendly['source_label'] = 'Your check-ins'
    elif fact['source_ref'].startswith('held:'):
        friendly['text'] = 'Your explanation is saved for your next review. Your usual has not been changed.'
    elif fact.get('at') and 'SENSING_GAP' in raw:
        friendly['text'] = f'There was a gap in your {LABELS.get(fact["signal"], "watch")} readings on {date_label(fact["at"])}.'
        friendly['source_label'] = 'Your measurements'
    elif raw.startswith('Patient check-in '):
        state = raw.rsplit(': ',1)[-1].rstrip('.')
        friendly['text'] = f'You marked {state} in your check-in on {date_label(raw.split()[2].rstrip(":"))}.'
        friendly['source_label'] = 'Your check-ins'
    friendly['recap_text'] = friendly['text']
    if finding:
        reference = 'in your recent records' if fact.get('comparison') == 'RECENT_PATTERN' else 'your usual'
        if fact['signal'] == 'SLEEP_MIDPOINT':
            friendly['recap_text'] = f'Your sleep time shifted {finding["direction"].lower()} than {reference} {friendly["since_phrase"]}.'
        elif fact['signal'] == 'ACTIVITY':
            movement = 'less' if finding['direction'] == 'LOWER' else 'more'
            friendly['recap_text'] = f'You\'ve been moving {movement} than {reference} {friendly["since_phrase"]}.'
        elif fact['signal'] == 'SLEEP_DURATION':
            length = 'shorter' if finding['direction'] == 'LOWER' else 'longer'
            friendly['recap_text'] = f'Your sleep was {length} than {reference} {friendly["since_phrase"]}.'
        elif fact['signal'] == 'HRV':
            variation = 'less' if finding['direction'] == 'LOWER' else 'more'
            friendly['recap_text'] = f'Your heartbeat timing varied {variation} than {reference} {friendly["since_phrase"]}.'
        else:
            friendly['recap_text'] = f'Your {label} was {direction} than {reference} {friendly["since_phrase"]}.'
    elif fact.get('checkin_run') or fact.get('checkin_summary'):
        friendly['recap_text'] = friendly['text'].replace('You marked',"You've marked",1)
    elif fact['source_ref'].startswith('held:'):
        friendly['recap_text'] = 'Your explanation is saved for your next review.'
    fact['patient'] = friendly
    if patient and friendly['text']:
        fact['text'] = friendly['text']
        if friendly['recap_text'] != friendly['text']:
            fact['text'] += ' '+friendly['recap_text']
        if finding:
            # This is the interval between the first and last supporting entry,
            # not a reading count or a claim of complete daily coverage.
            fact['text'] += f' First-to-last entry interval: {friendly["duration_phrase"]}.'
    elif not patient and (raw.startswith('Patient note ') or 'patient-reported context:' in raw):
        return  # Never rewrite a patient's quoted words.
    elif not patient:
        text = raw
        for row in sorted(PLAIN_TERMS['clinician'],key=lambda row:len(row['term']),reverse=True):
            text = re.sub(r'\b'+re.escape(row['term'])+r'\b',row['replacement'],text,flags=re.I)
        # Internal categorical codes remain in raw_text and finding metadata.
        for code, label in {**LABELS, 'STAY_QUIET':'No prompt needed', 'TRANSIENT_DEVIATION':'Recent change',
                            'REESTABLISHING':'Usual still being learned', 'PROVISIONAL':'Usual still being learned',
                            'UNOBSERVED':'No readings', 'SENSING_GAP':'Watch data gap'}.items():
            text = text.replace(code,label)
        text = re.sub(r'\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b',
                      lambda match:match.group().replace('_',' ').capitalize(),text)
        fact['text'] = text
