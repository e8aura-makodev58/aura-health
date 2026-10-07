"""Bounded scenario-planning agent; numeric generation/policy are separate.

The default planner is an inspectable offline template adapter, not a claimed LLM.
An optional synthetic-only JSON gateway may supply a plan; all output is validated.
No patient context, application object or write-capable repository enters a prompt.
"""

from dataclasses import asdict, dataclass
import json
import math
import re

import httpx


SIGNALS = {"SLEEP_MIDPOINT", "SLEEP_DURATION", "ACTIVITY", "RESTING_HEART_RATE"}


@dataclass(frozen=True)
class ScenarioPlan:
    case: str = "A"
    seed: int = 7
    days: int = 70
    changes: tuple[dict, ...] = ()
    gaps: tuple[dict, ...] = ()
    checkins: tuple[dict, ...] = ()
    explanation_day: int | None = None
    messages: tuple[dict, ...] = ()

    def data(self):
        return asdict(self)


def validate_plan(raw):
    if not isinstance(raw, dict) or set(raw) - set(ScenarioPlan.__dataclass_fields__):
        raise ValueError("Unknown scenario-plan fields (policy/ground truth do not belong here)")
    data = {**ScenarioPlan().data(), **raw}
    if not isinstance(data["case"], str) or data["case"] not in "ABCDEF" or len(data["case"]) != 1:
        raise ValueError("Unknown base fixture")
    if type(data["seed"]) is not int or not 0 <= data["seed"] < 2**31:
        raise ValueError("Invalid engineering seed")
    if type(data["days"]) is not int or not 14 <= data["days"] <= 365:
        raise ValueError("Timeline outside the engineering size budget")
    if data["explanation_day"] is not None and (type(data["explanation_day"]) is not int or not 14 <= data["explanation_day"] < data["days"]):
        raise ValueError("Invalid explicit explanation event day")
    shapes = {"changes":{"signal","start_day","end_day","delta","delta_per_day"},
              "gaps":{"start_day","end_day"}, "checkins":{"start_day","end_day","state"},
              "messages":{"day","fixture"}}
    for family, keys in shapes.items():
        rows = data[family]
        if not isinstance(rows, (tuple, list)) or len(rows) > 32:
            raise ValueError("Scenario event budget exceeded")
        for row in rows:
            if not isinstance(row, dict) or set(row) != keys:
                raise ValueError("Unexpected scenario event fields")
            dates = [row["day"]] if family == "messages" else [row["start_day"], row["end_day"]]
            if any(type(day) is not int or not 0 <= day < data["days"] for day in dates) or dates[-1] < dates[0]:
                raise ValueError("Invalid scenario time window")
            if family == "changes":
                if not isinstance(row["signal"],str) or row["signal"] not in SIGNALS or any(type(row[k]) not in {int,float} or not math.isfinite(row[k]) or abs(row[k]) > 100000 for k in ("delta","delta_per_day")):
                    raise ValueError("Invalid synthetic signal change")
            if family == "checkins" and (not isinstance(row["state"],str) or row["state"] not in {"Good","Okay","Rough"}):
                raise ValueError("Invalid check-in fixture")
            if family == "messages" and (not isinstance(row["fixture"],str) or row["fixture"] not in {"ORDINARY","SAFETY_CONCERN","FIGURATIVE","GATE_TIMEOUT"}):
                raise ValueError("Only curated synthetic message fixtures are permitted")
        data[family] = tuple(dict(row) for row in rows)
    return ScenarioPlan(**data)


class TemplatePlanner:
    """Offline, explicitly rule-based adapter for fixture requests; no semantic claim."""
    model_id = "offline-template-planner-v1"

    def propose(self, description, seed):
        text = description.lower()
        case_match = re.search(r"\bcase\s+([a-f])\b", text)
        case = case_match.group(1).upper() if case_match else (
            "D" if "benign schedule" in text else "B" if "slow drift" in text else
            "F" if "safety handoff" in text else "E" if "wearable gap" in text else "A")
        length = re.search(r"\b(\d+)[ -]day", text)
        days = int(length.group(1)) if length else 70
        result = {"case":case,"seed":seed,"days":days}
        if "illness" in text and "independent" in text:
            result["case"] = "C"
        if "worsening check-in" in text:
            result["checkins"] = [{"start_day":min(40,days-1),"end_day":days-1,"state":"Rough"}]
        if "missing wearable" in text:
            result["gaps"] = [{"start_day":min(40,days-1),"end_day":min(54,days-1)}]
        if "new signal after explanation" in text:
            result.update(case="D", explanation_day=30,
                          changes=[{"signal":"RESTING_HEART_RATE","start_day":40,"end_day":days-1,"delta":10,"delta_per_day":0}])
        if "figurative language" in text:
            result["messages"] = [{"day":days-1,"fixture":"FIGURATIVE"}]
        if "detector failure" in text:
            result["messages"] = [{"day":days-1,"fixture":"GATE_TIMEOUT"}]
        return result


class JSONGatewayPlanner:
    """Optional synthetic-spec provider, distinct from the patient communication model."""

    def __init__(self, endpoint, model_id, *, timeout=5, transport=None):
        from urllib.parse import urlsplit
        url = urlsplit(endpoint)
        if url.username or url.password or url.query or url.fragment or not url.hostname or (
                url.scheme != "https" and not (url.scheme == "http" and url.hostname in {"localhost","127.0.0.1","::1"})):
            raise ValueError("Scenario gateway must be HTTPS or loopback without URL credentials")
        self.endpoint, self.model_id, self.timeout, self.transport = endpoint, model_id, timeout, transport

    def propose(self, description, seed):
        contract = {"contract":"synthetic-scenario-plan-v1", "model":self.model_id,
                    "description":description, "seed":seed,
                    "example":ScenarioPlan().data(),
                    "allowed_signals":sorted(SIGNALS), "allowed_cases":list("ABCDEF"),
                    "instructions":"Generate only synthetic observable scenario parameters. No policy state, diagnosis, medication instructions, or hidden truth. JSON only."}
        with httpx.Client(timeout=self.timeout, follow_redirects=False, trust_env=False, transport=self.transport) as client:
            with client.stream("POST", self.endpoint, json=contract) as response:
                response.raise_for_status()
                content = bytearray()
                for chunk in response.iter_bytes():
                    content.extend(chunk)
                    if len(content) > 32768:
                        raise ValueError("Scenario output exceeds engineering budget")
        return json.loads(content)


class SimulationDataAgent:
    def __init__(self, planner=None):
        self.planner = planner or TemplatePlanner()

    def plan(self, description, seed=7):
        if not isinstance(description, str) or not 1 <= len(description) <= 2000:
            raise ValueError("Use a bounded synthetic-only description")
        # No retry loop/self-correction. Invalid provider output is rejected, never run.
        return validate_plan(self.planner.propose(description, seed))
