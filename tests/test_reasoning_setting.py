"""Operator reasoning level: stored per provider (default medium), mapped per provider. Mock only."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import httpx

from aura_app.models import AppError
from aura_app.system_settings import SystemSettings
from aura_communication.vendor import VendorProvider


def capture(provider, reasoning, variant=None):
    sent = {}
    def handler(request):
        sent.update(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {"content": "{}"}}]})
    VendorProvider(provider, "fixture-model", "fixture-key", reasoning=reasoning, variant=variant,
                   transport=httpx.MockTransport(handler)).agent_step([{"role": "user", "content": "json"}], [])
    return sent


TOOL = {"type": "function", "function": {"name": "get_x", "description": "x", "parameters": {"type": "object", "properties": {}}}}


class ReasoningSettingTests(unittest.TestCase):
    def test_rs1_payload_per_provider(self):
        self.assertEqual(capture("openai", "medium")["reasoning_effort"], "medium")
        self.assertEqual(capture("openai", "none")["reasoning_effort"], "none")
        self.assertEqual(capture("deepseek", "medium")["thinking"], {"type": "enabled"})
        self.assertEqual(capture("deepseek", "none")["thinking"], {"type": "disabled"})
        self.assertEqual(capture("openrouter", "high")["reasoning"], {"effort": "high"})
        self.assertNotIn("reasoning", capture("openrouter", "none"))
        self.assertGreater(capture("openai", "medium")["max_completion_tokens"], capture("openai", "none")["max_completion_tokens"])
        self.assertEqual(capture("openai", "bogus")["reasoning_effort"], "none")
        # Tencent TokenHub (Hy4 preview): thinking off for "none", else the effort level; legacy Hunyuan untouched.
        self.assertEqual(capture("tencent", "none", "singapore")["thinking"], {"type": "disabled"})
        self.assertEqual(capture("tencent", "medium", "singapore")["reasoning_effort"], "medium")
        self.assertNotIn("thinking", capture("tencent", "medium", "singapore"))
        legacy = capture("tencent", "medium", "hunyuan")
        self.assertNotIn("thinking", legacy); self.assertNotIn("reasoning_effort", legacy)

    def test_rs2_settings_default_medium_validate_and_persist(self):
        with TemporaryDirectory() as root:
            settings = SystemSettings(Path(root) / "system")
            self.assertEqual(settings.snapshot()["models"]["openai"]["reasoning"], "medium")
            settings.credential({"provider": "openai", "api_key": "fixture-key-123"})
            settings.update({"provider": "openai", "model": "fixture-text", "variant": "default", "enabled": True, "reasoning": "high"})
            self.assertEqual(settings._options()[5], "high")
            self.assertEqual(settings.public_status()["reasoning"], "high")
            # Saving without a reasoning field keeps the stored level.
            settings.update({"provider": "openai", "model": "fixture-text", "variant": "default", "enabled": True})
            self.assertEqual(SystemSettings(settings.root)._options()[5], "high")
            with self.assertRaises(AppError):
                settings.update({"provider": "openai", "model": "fixture-text", "variant": "default", "enabled": True, "reasoning": "max"})

    def test_rs3_openai_tools_with_reasoning_use_responses_api(self):
        sent = {}
        def handler(request):
            sent["path"] = request.url.path; sent["body"] = json.loads(request.content)
            return httpx.Response(200, json={"status": "completed", "tools": [TOOL["function"]] * 200, "output": [
                {"type": "reasoning", "summary": []},
                {"type": "function_call", "call_id": "c2", "name": "get_x", "arguments": "{}"}]})
        history = [{"role": "system", "content": "Return json"}, {"role": "user", "content": "q"},
                   {"role": "assistant", "content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {"name": "get_x", "arguments": "{}"}}]},
                   {"role": "tool", "name": "get_x", "tool_call_id": "c1", "content": "{\"v\": 1}"}]
        reply = VendorProvider("openai", "fixture-model", "fixture-key", reasoning="medium",
                               transport=httpx.MockTransport(handler)).agent_step(history, [TOOL])
        self.assertTrue(sent["path"].endswith("/responses"))
        body = sent["body"]
        self.assertEqual(body["reasoning"], {"effort": "medium"})
        self.assertEqual(body["tools"][0]["name"], "get_x")
        self.assertEqual([item.get("type", item.get("role")) for item in body["input"]],
                         ["system", "user", "function_call", "function_call_output"])
        self.assertEqual(reply["tool_calls"][0]["id"], "c2")
        self.assertEqual(reply["tool_calls"][0]["function"]["name"], "get_x")
        # Without reasoning the chat completions path is kept.
        VendorProvider("openai", "fixture-model", "fixture-key", reasoning="none",
                       transport=httpx.MockTransport(lambda r: (sent.update(path=r.url.path),
                       httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {"content": "{}"}}]}))[1])).agent_step(history, [TOOL])
        self.assertTrue(sent["path"].endswith("/chat/completions"))


if __name__ == "__main__":
    unittest.main()
