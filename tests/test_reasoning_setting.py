"""Operator reasoning level: stored per provider (default medium), mapped per provider. Mock only."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import httpx

from aura_app.models import AppError
from aura_app.system_settings import SystemSettings
from aura_communication.vendor import VendorProvider


def capture(provider, reasoning):
    sent = {}
    def handler(request):
        sent.update(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {"content": "{}"}}]})
    VendorProvider(provider, "fixture-model", "fixture-key", reasoning=reasoning,
                   transport=httpx.MockTransport(handler)).agent_step([{"role": "user", "content": "json"}], [])
    return sent


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


if __name__ == "__main__":
    unittest.main()
