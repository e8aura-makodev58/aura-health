"""Exercise existing synthetic checkpoints; never generate or expose latent truth."""

import argparse
import json
from pathlib import Path

from aura_app.agent import AgentService
from aura_app.demo import create_demo_app
from .roles import AgentRole


def main():
    parser = argparse.ArgumentParser(description="AURA read-only agent offline engineering evaluation")
    parser.add_argument("--db", type=Path, required=True, help="explicit synthetic development database")
    parser.add_argument("--save", type=Path)
    args = parser.parse_args()
    app = create_demo_app(args.db)
    service = AgentService(app.state.service)
    results = []
    from uuid import uuid4
    for case in "ABCDEF":
        for role in AgentRole:
            result = service.execute(f"demo-{case}-7", role, run_id=str(uuid4()),
                query_id="sleep_change" if role == AgentRole.RECORD_QA else None)
            results.append({"evaluation_case": case, "skill": role.value, "status": result["status"],
                            "generation_used": result["generation_used"], "claim_count": len(result["draft"]["claims"]),
                            "reason": result["reason"]})
    report = {"synthetic_only": True, "clinical_validation": False,
              "provider": "offline-rule-based-v1", "results": results}
    if args.save:
        args.save.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
