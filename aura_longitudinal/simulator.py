"""CLI for synthetic A–E longitudinal evaluation and exact trace replay."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from .comparators import load_comparator_config, parse_comparator_config
from .config import load_config, parse_config
from .evaluation import METHODS, aggregate, run_timeline
from .synthetic import CASE_NAMES, generate_case


def run_cases(cases: tuple[str, ...], seed: int) -> dict:
    engineering = load_config()
    comparator = load_comparator_config()
    timelines = {case: generate_case(case, seed) for case in cases}
    results = {case: run_timeline(timeline, engineering, comparator)
               for case, timeline in timelines.items()}
    return {"schema_version": 1, "seed": seed, "cases": list(cases),
            "engineering_config": asdict(engineering),
            "comparator_config": asdict(comparator),
            "timelines": timelines, "results": results,
            "aggregate": aggregate(results)}


def replay(record: dict) -> dict:
    engineering = parse_config(record["engineering_config"])
    comparator = parse_comparator_config(record["comparator_config"])
    for case in record["cases"]:
        if generate_case(case, record["seed"]) != record["timelines"][case]:
            raise AssertionError(f"generated timeline diverged for Case {case}")
    results = {case: run_timeline(record["timelines"][case], engineering, comparator)
               for case in record["cases"]}
    if results != record["results"] or aggregate(results) != record["aggregate"]:
        raise AssertionError("longitudinal policy trace or metrics diverged")
    return record


def _print_metrics(record: dict) -> None:
    print("Synthetic engineering comparison; no clinical efficacy claim")
    columns = ("patient_interruptions", "unnecessary_notifications",
               "persistent_drift_detection_latency_days", "missed_persistent_drift",
               "duplicate_notifications_for_explained_drift", "data_coverage",
               "stay_quiet_proportion", "clinician_review_items")
    for case in record["cases"]:
        print(f"\nCase {case}: {CASE_NAMES[case]}")
        for method in METHODS:
            values = record["results"][case]["metrics"][method]
            print(f"  {method}: " + ", ".join(f"{name}={values[name]}" for name in columns))
    print("\nAggregate")
    for method in METHODS:
        values = record["aggregate"][method]
        print(f"  {method}: " + ", ".join(f"{name}={values[name]}" for name in columns))


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="AURA synthetic longitudinal evaluation")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--case", choices=(*CASE_NAMES, "ALL"), default="ALL")
    run.add_argument("--seed", type=int, default=7)
    run.add_argument("--save-timeline", type=Path)
    run.add_argument("--save-trace", type=Path)
    replay_parser = sub.add_parser("replay")
    replay_parser.add_argument("trace", type=Path)
    args = parser.parse_args(argv)
    if args.command == "run":
        cases = tuple(CASE_NAMES) if args.case == "ALL" else (args.case,)
        record = run_cases(cases, args.seed)
        _print_metrics(record)
        if args.save_timeline:
            args.save_timeline.write_text(json.dumps(record["timelines"], indent=2) + "\n")
            print(f"Saved synthetic timeline: {args.save_timeline}")
        if args.save_trace:
            args.save_trace.write_text(json.dumps(record, indent=2) + "\n")
            print(f"Saved evaluation trace: {args.save_trace}")
    else:
        record = json.loads(args.trace.read_text())
        replay(record)
        print(f"Replay matched {len(record['cases'])} case(s), timelines, decisions, and metrics")
        _print_metrics(record)


if __name__ == "__main__":
    main()
