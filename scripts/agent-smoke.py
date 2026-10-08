"""Explicit paid synthetic-only smoke through the running production agent boundary.

Never reads API keys/admin tokens, and never prints browser cookies.
"""

import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

import httpx


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8017")
    parser.add_argument("--host-header", help="operator-approved HTTP demo host, if needed")
    parser.add_argument("--skill", choices=["clinician_brief", "record_qa", "patient_insight", "visit_prep", "question_ranker"], default="clinician_brief")
    parser.add_argument("--confirm-synthetic-live-call", action="store_true")
    parser.add_argument("--save", type=Path)
    args = parser.parse_args()
    if not args.confirm_synthetic_live_call:
        parser.error("explicit confirmation required; this small synthetic call may incur model charges")
    if urlsplit(args.base_url).hostname not in {"localhost", "127.0.0.1"}:
        parser.error("local operator smoke only")
    headers = {"Host": args.host_header} if args.host_header else {}
    with httpx.Client(base_url=args.base_url, headers=headers, trust_env=False, timeout=90) as client:
        status = client.get("/system/status"); status.raise_for_status()
        if not status.json().get("live_enabled"):
            raise SystemExit("Live synthetic provider is disabled; no model call attempted")
        catalog = client.get("/demo/scenarios"); catalog.raise_for_status()
        if not catalog.json().get("synthetic_only"):
            raise SystemExit("Synthetic boundary not confirmed")
        patient = next(row["patient_id"] for row in catalog.json()["scenarios"] if row["id"] == "B")
        request = {"run_id": str(uuid4()), "query_id": "sleep_change" if args.skill == "record_qa" else None,
                   "window_days": 56, "client_offline": False}
        route = f"/patients/{patient}/agent/{args.skill}"
        response = client.post(route, json=request); response.raise_for_status()
        result = response.json()
        retry = client.post(route, json=request); retry.raise_for_status()
        report = {"synthetic_only": True, "skill": args.skill, "status": result["status"],
                  "model_id": result["model_id"], "generation_used": result["generation_used"],
                  "reason": result["reason"], "claim_count": len(result["draft"]["claims"]),
                  "tool_steps": [step["tool"] for step in result["trace"] if "tool" in step],
                  "validation": [step for step in result["trace"] if step.get("action") == "VALIDATION"],
                  "elapsed_ms": result["elapsed_ms"], "retry_same_draft": retry.json()["draft"] == result["draft"],
                  "retry_idempotent": retry.json().get("idempotent_replay", False)}
        if args.save: args.save.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
        return 0 if result["generation_used"] and report["retry_idempotent"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
