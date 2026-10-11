"""Twenty-seed measurement of unchanged engine behavior, not clinical validation."""
import argparse
from datetime import date, datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from aura_longitudinal.baseline import AnchorAction, AnchorCommand, BaselineManager
from aura_longitudinal.domain import ObservationPoint, Signal, SignalKey
from aura_longitudinal.drift import assess_drift, DriftKind
from aura_simulation.life import LifePlan, generate, load_effects


def measure(seed):
    manager=BaselineManager();effects=load_effects()
    rows=generate(LifePlan(days=28,events=[]),seed=seed,patient_id='synthetic-quiet',
                  start='2026-01-01',profile=effects['profile'],notes=False)
    signals=[Signal.RESTING_HEART_RATE,Signal.HRV,Signal.RESPIRATORY_RATE,Signal.SKIN_TEMPERATURE_DEVIATION]
    keys=[SignalKey(signal,'synthetic_wearable') for signal in signals]
    at=datetime(2026,1,29,tzinfo=timezone.utc)
    for key in keys:
        points=tuple(ObservationPoint(key,date.fromisoformat(row['date']),row['values'][key.signal.value],1,1) for row in rows)
        for point in points:manager.ingest(point)
        manager.apply_anchor_command(AnchorCommand(AnchorAction.CREATE_PROVISIONAL_ANCHOR,key,at,points))
        manager.apply_anchor_command(AnchorCommand(AnchorAction.TRUST_ANCHOR,key,at,reviewed_by='synthetic-fixture-review'))
    counts={key.signal.value:0 for key in keys}
    quiet=generate(LifePlan(days=30,events=[]),seed=seed,patient_id='synthetic-quiet',
                   start='2026-01-29',profile=effects['profile'],notes=False)
    for row in quiet:
        for key in keys:
            point=ObservationPoint(key,date.fromisoformat(row['date']),row['values'][key.signal.value],1,1)
            manager.ingest(point)
            drift=assess_drift(manager.rolling(key,point.day),manager.anchor(key),manager.config_for(key),manager.trust_state(key))
            if drift.kind==DriftKind.TRANSIENT_DEVIATION:counts[key.signal.value]+=1
    return {'seed':seed,'transient_channel_days':counts,'any_transient':any(counts.values())}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default='docs/evidence/final-dash-quiet.json')
    args=parser.parse_args();rows=[measure(seed) for seed in range(20)]
    report={'scope':'synthetic stable profile; 28-day explicit anchor, 30 observed quiet days',
            'engine_changed':False,'registry_version':BaselineManager().registry.version,
            'seeds':rows,'seeds_with_any_transient':sum(row['any_transient'] for row in rows)}
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))


if __name__=='__main__':main()
