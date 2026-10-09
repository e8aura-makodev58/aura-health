"""OR-combined proposals: neither layer can clear stronger evidence or policy state."""

import json
import os
from pathlib import Path
import re

from aura_agent.tasks import structured_task
from aura_safety.domain import DetectorOutput, Mode
from aura_app.safety import SafetyGateUnavailable


class LayeredSafetyGate:
    def __init__(self, provider, *, fixtures=None, policy=None):
        self.provider, self.fixtures = provider, fixtures
        self.policy = policy or json.loads(Path(os.environ.get("AURA_DETECTOR_POLICY") or
            Path(__file__).with_name("engineering_policy.json")).read_text())
        if set(self.policy) != {"version", "semantic_targets", "rules"} or not self.policy["version"].endswith("not-clinically-validated"):
            raise ValueError("invalid detector configuration")
        if set(self.policy["semantic_targets"]) != {"none", "possible", "likely"}:
            raise ValueError("invalid semantic proposals")
        self.targets = {key: Mode[value] for key, value in self.policy["semantic_targets"].items()}
        if self.targets["none"] != Mode.NORMAL or not Mode.NORMAL < self.targets["possible"] <= self.targets["likely"]:
            raise ValueError("semantic proposals must be raise-only")
        if not isinstance(self.policy['rules'],list) or not 1<=len(self.policy['rules'])<=128 or any(set(row)!={'pattern','proposal'} or Mode[row['proposal']]<=Mode.NORMAL for row in self.policy['rules']):
            raise ValueError('at least one curated raise-only detector rule required')
        self.rules = [(re.compile(row["pattern"], re.I), Mode[row["proposal"]]) for row in self.policy["rules"]]

    def resolve(self, event, source_episode_id, source_sequence):
        if self.fixtures:
            try:
                return self.fixtures.resolve(event, source_episode_id, source_sequence)
            except SafetyGateUnavailable:
                pass
        payload = event.payload
        texts = [payload[key] for key in ("text", "question", "explanation") if isinstance(payload.get(key), str)]
        answers = payload.get("structured_answers", {})
        texts.extend(str(value) for value in answers.values())
        if not texts:
            # Only reviewed categorical shapes bypass semantic free-text detection.
            if ((set(payload) == {"state"} and payload["state"] in {"Good", "Okay", "Rough"}) or
                (set(payload) == {"scheduled_time", "status"} and payload["status"] in {"ACKNOWLEDGED", "MISSED", "UNKNOWN"})):
                return ()
            raise SafetyGateUnavailable("unresolved structured safety input")
        text = "\n".join(texts)
        outputs = tuple(DetectorOutput("D2", tier, event.event_id,
                                      source_episode_id, source_sequence)
                        for pattern, tier in self.rules if pattern.search(text))
        try:
            if len(text) > 4000: raise ValueError("DETECTOR_TEXT_BUDGET")
            result = structured_task(self.provider, "detect", {"quoted_input": text})
            if not isinstance(result, dict) or set(result) != {"concern"} or result["concern"] not in self.targets:
                raise ValueError("INVALID_DETECTOR_OUTPUT")
            tier = self.targets[result["concern"]]
            return outputs + (DetectorOutput("D4", tier, event.event_id,
                                            source_episode_id, source_sequence),)
        except Exception as error:
            code=str(error) if isinstance(error,ValueError) and str(error) in {'INVALID_DETECTOR_OUTPUT','DETECTOR_TEXT_BUDGET','TASK_TOOL_CALL_FORBIDDEN'} else type(error).__name__
            raise SafetyGateUnavailable("semantic safety evaluation unavailable", outputs=outputs,failure_code=code) from None
