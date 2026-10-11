"""Twenty-seed measurement of unchanged engine behavior, not clinical validation."""
import argparse
from copy import deepcopy
from datetime import date, datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from aura_longitudinal.baseline import AnchorAction, AnchorCommand, BaselineManager
from aura_longitudinal.domain import ObservationPoint, Signal, SignalKey
from aura_longitudinal.drift import assess_drift, DriftKind
from aura_simulation.life import LifePlan, generate, load_effects


def generate_quiet(plan, seed, start, effects, noise_multiplier):
    rows=generate(plan,seed=seed,patient_id='synthetic-quiet',start=start,
                  profile=effects['profile'],effects=effects,notes=False)
    # The simulation generator's skin-temperature deviation uses a fixed
    # uniform(-0.08, 0.08), outside effects['noise']; scale it here as part of
    # this evaluation-only measurement profile.
    for row in rows:
        value=row['values'].get(Signal.SKIN_TEMPERATURE_DEVIATION.value)
        if value is not None:
            row['values'][Signal.SKIN_TEMPERATURE_DEVIATION.value]=round(value*noise_multiplier,3)
    return rows


def measure(seed, noise_multiplier=1.0):
    manager=BaselineManager();effects=deepcopy(load_effects())
    effects['noise']={key:value*noise_multiplier for key,value in effects['noise'].items()}
    rows=generate(LifePlan(days=28,events=[]),seed=seed,patient_id='synthetic-quiet',
                  start='2026-01-01',profile=effects['profile'],effects=effects,notes=False)
    for row in rows:
        key=Signal.SKIN_TEMPERATURE_DEVIATION.value
        row['values'][key]=round(row['values'][key]*noise_multiplier,3)
    signals=[Signal.RESTING_HEART_RATE,Signal.HRV,Signal.RESPIRATORY_RATE,Signal.SKIN_TEMPERATURE_DEVIATION]
    keys=[SignalKey(signal,'synthetic_wearable') for signal in signals]
    at=datetime(2026,1,29,tzinfo=timezone.utc)
    for key in keys:
        points=tuple(ObservationPoint(key,date.fromisoformat(row['date']),row['values'][key.signal.value],1,1) for row in rows)
        for point in points:manager.ingest(point)
        manager.apply_anchor_command(AnchorCommand(AnchorAction.CREATE_PROVISIONAL_ANCHOR,key,at,points))
        manager.apply_anchor_command(AnchorCommand(AnchorAction.TRUST_ANCHOR,key,at,reviewed_by='synthetic-fixture-review'))
    counts={key.signal.value:0 for key in keys}
    quiet=generate_quiet(LifePlan(days=30,events=[]),seed,'2026-01-29',effects,noise_multiplier)
    for row in quiet:
        for key in keys:
            point=ObservationPoint(key,date.fromisoformat(row['date']),row['values'][key.signal.value],1,1)
            manager.ingest(point)
            drift=assess_drift(manager.rolling(key,point.day),manager.anchor(key),manager.config_for(key),manager.trust_state(key))
            if drift.kind==DriftKind.TRANSIENT_DEVIATION:counts[key.signal.value]+=1
    return {'seed':seed,'transient_channel_days':counts,'any_transient':any(counts.values())}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default='docs/evidence/final-dash-quiet-noisy.json')
    parser.add_argument('--noise-multiplier',type=float,default=3.0,
                        help='scale simulator noise for the noisy cohort (default: 3.0)')
    parser.add_argument('--seeds',type=int,default=20)
    args=parser.parse_args()
    if args.noise_multiplier<1 or args.seeds<1:
        parser.error('--noise-multiplier must be >= 1 and --seeds must be >= 1')
    original=[measure(seed) for seed in range(args.seeds)]
    noisy=[measure(seed,args.noise_multiplier) for seed in range(args.seeds)]
    report={'scope':'synthetic stable profile; each cohort uses a 28-day explicit anchor and 30 observed quiet days',
            'generator_profile_assumption':'aura_simulation life_effects profile; no life events; simulator uniform noise scaled from the same profile during anchor and observation; skin-temperature deviation uniform noise is scaled in this evaluation-only harness',
            'engine_changed':False,'registry_version':BaselineManager().registry.version,
            'original_noise_multiplier':1.0,'original_seeds':original,
            'original_seeds_with_any_transient':sum(row['any_transient'] for row in original),
            'noisy_noise_multiplier':args.noise_multiplier,'noisy_seeds':noisy,
            'noisy_seeds_with_any_transient':sum(row['any_transient'] for row in noisy),
            'interpretation':'Counts are outputs from the existing longitudinal engine for these synthetic profiles; this measurement does not tune thresholds and is not a false-positive rate or clinical claim.'}
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))


if __name__=='__main__':main()
