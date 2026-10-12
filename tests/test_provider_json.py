"""JSON-mode requests must say "json"; provider failures carry a safe kind. Mock only."""
import json
import unittest

import httpx

from aura_agent.roles import AgentRole
from aura_agent.runtime import run
from aura_agent.tools import RecordTools
from aura_communication.provider import ProviderUnavailable
from aura_communication.vendor import VendorProvider
from tests.test_final_dash import HeadlineProvider, evidence


class RecordingProvider(HeadlineProvider):
    def __init__(self):
        super().__init__()
        self.first = None

    def step(self, messages, specs):
        if self.first is None:
            self.first = [dict(m) for m in messages]
        return super().step(messages, specs)


def deepseek(handler):
    return VendorProvider("deepseek", "fixture-model", "fixture-key", transport=httpx.MockTransport(handler))


class ProviderJsonTests(unittest.TestCase):
    def test_pj1_every_presentation_prompt_says_json(self):
        for role in (AgentRole.CLINICIAN_BRIEF, AgentRole.PATIENT_INSIGHT):
            with self.subTest(role=role.value):
                provider = RecordingProvider()
                tools = RecordTools(evidence(), role)
                run(role, None, tools, provider, presentation=True)
                self.assertIsNotNone(provider.first)
                self.assertTrue(any("json" in str(m.get("content") or "").lower() for m in provider.first))

    def test_pj2_agent_step_adds_json_word_when_missing(self):
        seen = []

        def handler(request):
            seen.append(json.loads(request.content))
            return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {"content": "{}"}}]})
        deepseek(handler).agent_step([{"role": "system", "content": "Be brief."}, {"role": "user", "content": "hello"}], [])
        payload = seen[0]
        self.assertEqual(payload["response_format"], {"type": "json_object"})
        self.assertTrue(any("json" in m["content"].lower() for m in payload["messages"]))
        self.assertEqual(len(payload["messages"]), 2)

    def test_pj3_deepseek_generate_disables_thinking(self):
        seen = []

        def handler(request):
            seen.append(json.loads(request.content))
            return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {"content": "{}"}}]})
        deepseek(handler).generate({"instructions": "Return JSON", "request": {}})
        self.assertEqual(seen[0]["thinking"], {"type": "disabled"})

    def test_pj4_failure_kinds_are_safe_labels(self):
        def status(code):
            return lambda request: httpx.Response(code, json={"error": {"message": "secret-ish detail"}})
        with self.assertRaises(ProviderUnavailable) as caught:
            deepseek(status(400)).agent_step([{"role": "system", "content": "json"}], [])
        self.assertEqual(caught.exception.kind, "http_400")
        self.assertNotIn("secret", str(caught.exception))
        with self.assertRaises(ProviderUnavailable) as caught:
            deepseek(status(429)).agent_step([{"role": "system", "content": "json"}], [])
        self.assertEqual(caught.exception.kind, "http_429")
        length = lambda request: httpx.Response(200, json={"choices": [{"finish_reason": "length", "message": {"content": "{"}}]})
        with self.assertRaises(ProviderUnavailable) as caught:
            deepseek(length).agent_step([{"role": "system", "content": "json"}], [])
        self.assertEqual(caught.exception.kind, "finish_length")
        empty = lambda request: httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {"content": ""}}]})
        with self.assertRaises(ProviderUnavailable) as caught:
            deepseek(empty).generate({"instructions": "Return JSON", "request": {}})
        self.assertEqual(caught.exception.kind, "empty_content")

    def test_pj5_fallback_trace_records_failure_kind_only(self):
        class Failing(RecordingProvider):
            def step(self, messages, specs):
                raise ProviderUnavailable("raw upstream text must not persist", kind="http_400")
        tools = RecordTools(evidence(), AgentRole.PATIENT_INSIGHT)
        result = run(AgentRole.PATIENT_INSIGHT, None, tools, Failing(), presentation=True)
        fallback = [t for t in result["trace"] if t.get("action") == "FALLBACK"]
        self.assertEqual(fallback[-1]["provider_failure"], "http_400")
        self.assertNotIn("raw upstream", json.dumps(result["trace"]))


if __name__ == "__main__":
    unittest.main()
