"""Demo-only life director. Models choose life events; seeded code owns telemetry.

Plans and hidden event labels stay in evaluation storage, never decision payloads.
All effects are inspectable engineering fixtures, not physiological predictions.
"""

from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
import json
import random
from pathlib import Path
import os
from types import SimpleNamespace
from typing import Literal
from pydantic import BaseModel, Field, model_validator
from aura_agent.tasks import structured_task

KINDS = ('FLU', 'TRAVEL', 'WORK_STRESS', 'ALCOHOL', 'MISSED_MEDICATION', 'WEARABLE_OFF', 'EXERCISE')

class LifeEvent(BaseModel):
    model_config = {'extra': 'forbid', 'strict': True}
    type: Literal['FLU', 'TRAVEL', 'WORK_STRESS', 'ALCOHOL', 'MISSED_MEDICATION', 'WEARABLE_OFF', 'EXERCISE']
    start_day: int = Field(ge=1, le=30)
    duration_days: int = Field(ge=1, le=30)
    severity: Literal['MILD', 'MODERATE', 'STRONG']

class Feedback(BaseModel):
    model_config = {'extra': 'forbid', 'strict': True}
    day: int = Field(ge=1, le=30)
    checkin: Literal['Good', 'Okay', 'Rough'] | None = None
    medication: Literal['ACKNOWLEDGED', 'MISSED', 'UNKNOWN'] | None = None
    note_theme: Literal['NONE', 'UNWELL', 'TRAVEL', 'BUSY', 'EXERCISE'] = 'NONE'

class LifePlan(BaseModel):
    model_config = {'extra': 'forbid', 'strict': True}
    days: int = Field(ge=1, le=30)
    events: list[LifeEvent] = Field(max_length=8)
    feedback: list[Feedback] = Field(default_factory=list, max_length=30)

    @model_validator(mode='after')
    def windows(self):
        if any(e.start_day + e.duration_days - 1 > self.days for e in self.events) or any(f.day > self.days for f in self.feedback):
            raise ValueError('event outside requested advance')
        if len({f.day for f in self.feedback}) != len(self.feedback):
            raise ValueError('duplicate feedback day')
        return self

def load_effects():
    return json.loads(Path(os.environ.get('AURA_LIFE_EFFECTS') or Path(__file__).with_name('life_effects.json')).read_text())

def offline_plan(days, request):
    words = request.lower()
    aliases = {'FLU': ('flu', 'ill', 'fever'), 'TRAVEL': ('travel', 'trip'),
               'WORK_STRESS': ('stress',), 'ALCOHOL': ('alcohol',),
               'MISSED_MEDICATION': ('missed',), 'WEARABLE_OFF': ('off', 'gap'), 'EXERCISE': ('exercise',)}
    effects = load_effects()
    events = [{'type': kind, 'start_day': 1, 'duration_days': min(days, effects['durations'][kind][0]), 'severity': 'MODERATE'}
              for kind, terms in aliases.items() if any(term in words for term in terms)]
    return LifePlan.model_validate({'days': days, 'events': events[:8], 'feedback': []})

def direct(provider, days, request, digest):
    try:
        raw = structured_task(provider, 'life_director', {'schema': LifePlan.model_json_schema(),
            'days': days, 'request': request, 'observable_digest': digest})
        plan = LifePlan.model_validate(raw)
        if plan.days != days: raise ValueError('wrong advance')
        return plan, 'VALIDATED_MODEL_PLAN'
    except Exception:
        return offline_plan(days, request), 'OFFLINE_KEYWORD_PLAN'

def generate(plan, *, seed, patient_id, start, profile, effects=None, notes=True, carry_events=()):
    """Return observable rows only. Sparse sources are never filled/interpolated."""
    effects = effects or load_effects()
    result = []
    severity = effects['severity']
    themes = effects['note_themes']
    if len(carry_events)>240 or any(set(e)!={'type','start_day','duration_days','severity'} or e['type'] not in KINDS or
        type(e['start_day']) is not int or not -30<=e['start_day']<=0 or type(e['duration_days']) is not int or
        not 1<=e['duration_days']<=30 or e['start_day']+e['duration_days']-1>0 or e['severity'] not in severity for e in carry_events):
        raise ValueError('invalid historical recovery events')
    historical = [SimpleNamespace(**event) for event in carry_events]
    all_events = [*plan.events, *historical]
    feedback = {f.day: f for f in plan.feedback}
    for offset in range(1, plan.days + 1):
        day = date.fromisoformat(start) + timedelta(days=offset)
        rng = random.Random(int(sha256(f'{seed}:{patient_id}:{day}'.encode()).hexdigest(), 16))
        active = [e for e in plan.events if e.start_day <= offset < e.start_day + e.duration_days]
        values = {key: max(.01, profile[key] + rng.uniform(-effects['noise'].get(key, 0), effects['noise'].get(key, 0))) for key in sorted(profile)}
        values['SKIN_TEMPERATURE_DEVIATION'] = rng.uniform(-.08, .08)
        for event in active:
            for signal, change in effects['effects'][event.type].items():
                multiplier = severity[event.severity]*min(1,(offset-event.start_day+1)/effects['ramps'][event.type])
                if change['operation'] == 'add': values[signal] += change['value'] * multiplier
                else: values[signal] *= max(.1, 1 + change['value'] * multiplier)
        for event in all_events:
            elapsed=offset-(event.start_day+event.duration_days-1)
            if event.type in {'ALCOHOL','MISSED_MEDICATION','WEARABLE_OFF'} or not 1<=elapsed<=effects['recovery_tail_days']:continue
            recovery=(effects['recovery_tail_days']-elapsed+1)/(effects['recovery_tail_days']+1)
            for signal,change in effects['effects'][event.type].items():
                factor=severity[event.severity]*recovery
                if change['operation']=='add':values[signal]+=change['value']*factor
                else:values[signal]*=max(.1,1+change['value']*factor)
        for signal in values:
            if signal in effects['clamps']:
                lower,upper=effects['clamps'][signal];values[signal]=max(lower,min(upper,values[signal]))
        flu = any(e.type == 'FLU' for e in active)
        if day.weekday() not in (0, 3, 5):
            values.pop('BLOOD_PRESSURE_SYSTOLIC', None); values.pop('BLOOD_PRESSURE_DIASTOLIC', None)
        if day.weekday() != 0: values.pop('WEIGHT', None)
        # Thermometer readings remain intermittent, with a short recovery check
        # and one post-recovery reading rather than inventing daily healthy data.
        recovery_temperature = any(e.type=='FLU' and 1<=offset-(e.start_day+e.duration_days-1)<=effects['recovery_tail_days']+1 for e in all_events)
        if not flu and not recovery_temperature: values.pop('BODY_TEMPERATURE', None)
        if day.weekday() == 2: values.pop('SPO2', None)
        if any(e.type == 'WEARABLE_OFF' for e in active):
            for key in ('SLEEP_MIDPOINT','SLEEP_DURATION','ACTIVITY','RESTING_HEART_RATE','HRV','RESPIRATORY_RATE','SKIN_TEMPERATURE_DEVIATION','SPO2'):
                values.pop(key, None)
        f = feedback.get(offset)
        theme = f.note_theme if f else ('UNWELL' if flu else 'NONE')
        result.append({'date': day.isoformat(), 'values': {k: round(v, 3) for k, v in values.items()},
            'checkin': (f.checkin if f and f.checkin else 'Rough' if flu else 'Good'),
            'medication': (f.medication if f and f.medication else 'MISSED' if any(e.type == 'MISSED_MEDICATION' for e in active) else 'ACKNOWLEDGED'),
            'note': themes[theme] if notes and theme != 'NONE' else None})
    return result
