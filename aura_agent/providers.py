"""Provider abstraction. Offline execution is explicitly rule-based, never AI."""

from typing import Protocol


class AgentProvider(Protocol):
    model_id: str
    live: bool
    def step(self, messages: list[dict], tools: list[dict]) -> dict: ...


class ScriptedAgentProvider:
    model_id = "offline-rule-based-v1"
    live = False

    def step(self, messages, tools):
        called = {message["name"] for message in messages if message["role"] == "tool"}
        for tool in tools:
            name = tool["function"]["name"]
            if name not in called:
                return {"role": "assistant", "content": None, "tool_calls": [{"id": f"offline-{name}", "type": "function", "function": {"name": name, "arguments": "{}"}}]}
        raise ValueError("OFFLINE_EXTRACTION_COMPLETE")
