import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from .agent import SimulationDataAgent, validate_plan
from .timeline import generate
from .driver import drive, observable_events, configuration_fingerprint


def main():
    parser = argparse.ArgumentParser(description="Synthetic-only scenario agent → deterministic generator → accepted engines")
    parser.add_argument("--description", default="Case B slow drift")
    parser.add_argument("--seed",type=int,default=7)
    parser.add_argument("--spec",type=Path)
    parser.add_argument("--save",type=Path)
    parser.add_argument("--replay",type=Path)
    args = parser.parse_args()
    with TemporaryDirectory(prefix="aura-scenario-") as temporary:
        if args.replay:
            prior = json.loads(args.replay.read_text())
            if prior["configuration_fingerprint"] != configuration_fingerprint():
                raise ValueError("Replay configuration changed; refusing to claim an identical replay")
            replay = drive(prior["events"],Path(temporary)/"replay.sqlite3")
            if replay != prior:
                raise ValueError("Semantic replay mismatch")
            print(f"Replay matched all {len(replay['trace'])} semantic state/action entries exactly")
            return
        plan = validate_plan(json.loads(args.spec.read_text())) if args.spec else SimulationDataAgent().plan(args.description,args.seed)
        timeline = generate(plan)
        record = drive(observable_events(timeline),Path(temporary)/"scenario.sqlite3")
        if args.save:
            args.save.write_text(json.dumps(record,indent=2)+"\n")
            args.save.with_suffix(".timeline.json").write_text(json.dumps(timeline,indent=2)+"\n")
            args.save.with_suffix(".plan.json").write_text(json.dumps(plan.data(),indent=2)+"\n")
        final = record["trace"][-1]
        print(f"{len(record['trace'])} events; final decision={final['communication_decision']}; "
              f"held={len(final['longitudinal']['held'])}; no live model")


if __name__ == "__main__":
    main()
