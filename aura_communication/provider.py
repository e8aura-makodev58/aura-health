"""Optional HTTP wording adapter and deterministic development fixtures. No detector."""

from dataclasses import dataclass, field
import json
import os
from time import monotonic
from typing import Protocol
from urllib.parse import urlsplit

import httpx

from .config import CommunicationConfig


class ProviderUnavailable(Exception):
    pass


class GenerationProvider(Protocol):
    model_id: str
    def generate(self, contract: dict) -> object: ...


class DisabledProvider:
    model_id = "disabled"

    def generate(self, contract):
        raise ProviderUnavailable("generation is not configured")


class HTTPGenerationProvider:
    """POST the documented neutral JSON contract to an explicitly configured model gateway."""

    def __init__(self, endpoint: str, model_id: str, config: CommunicationConfig,
                 *, token: str | None = None, transport=None):
        parts = urlsplit(endpoint)
        if (parts.username or parts.password or parts.query or parts.fragment
                or not parts.hostname or not model_id
                or (parts.scheme != "https" and not
                    (parts.scheme == "http" and parts.hostname in {"localhost", "127.0.0.1", "::1"}))):
            raise ValueError("provider requires HTTPS (or local development HTTP) without URL credentials")
        self.endpoint, self.model_id, self.config = endpoint, model_id, config
        self._token, self._transport = token, transport

    def generate(self, contract):
        headers = {"Authorization": f"Bearer {self._token}"} if self._token else {}
        deadline = monotonic() + self.config.provider_timeout_seconds
        try:
            with httpx.Client(timeout=self.config.provider_timeout_seconds, transport=self._transport,
                              follow_redirects=False, trust_env=False) as client:
                with client.stream("POST", self.endpoint, json={**contract, "model": self.model_id},
                                   headers=headers) as response:
                    response.raise_for_status()
                    body = bytearray()
                    for chunk in response.iter_bytes():
                        if monotonic() > deadline:
                            raise TimeoutError("model gateway exceeded total engineering deadline")
                        body.extend(chunk)
                        if len(body) > self.config.max_provider_response_bytes:
                            raise ProviderUnavailable("provider response exceeded engineering limit")
            if monotonic() > deadline:
                raise TimeoutError("model gateway exceeded total engineering deadline")
            return json.loads(body)
        except httpx.TimeoutException as exc:
            raise TimeoutError("model gateway timeout") from exc
        except (httpx.HTTPError, ValueError) as exc:
            # Do not persist provider response, URL/token, prompt, or error details.
            raise ProviderUnavailable("model gateway unavailable or returned invalid JSON") from exc


def provider_from_environment(config: CommunicationConfig) -> GenerationProvider:
    endpoint = os.environ.get("AURA_COMMUNICATION_ENDPOINT")
    if not endpoint:
        return DisabledProvider()
    return HTTPGenerationProvider(endpoint, os.environ.get("AURA_COMMUNICATION_MODEL", "configured-gateway"),
                                  config, token=os.environ.get("AURA_COMMUNICATION_TOKEN"))


@dataclass
class FixtureProvider:
    """Development/test-only fixed replies, explicitly not a live generative model."""

    behavior: str = "valid"
    model_id: str = "fixture-wording-v1"
    calls: list[dict] = field(default_factory=list)

    def generate(self, contract):
        self.calls.append(contract)
        if self.behavior == "timeout":
            raise TimeoutError("fixture timeout")
        if self.behavior == "error":
            raise ProviderUnavailable("fixture unavailable")
        candidate = dict(contract["request"]["candidates"][-1])
        if self.behavior == "invalid":
            candidate["message"] = "Your sleep proves depression and relapse. Stop your medication."
        return candidate
