"""Fixed-host vendor transport. No safety detection or product-policy ownership."""

import json
from time import monotonic
import httpx

from .config import load_config
from .provider import ProviderUnavailable

PROVIDERS = {
    "openrouter": {"label":"OpenRouter", "endpoints":{"default":"https://openrouter.ai/api/v1"}},
    "openai": {"label":"OpenAI", "endpoints":{"default":"https://api.openai.com/v1"}},
    "deepseek": {"label":"DeepSeek", "endpoints":{"default":"https://api.deepseek.com/v1"}},
    "tencent": {"label":"Tencent", "endpoints":{
        "singapore":"https://tokenhub-intl.tencentcloudmaas.com/v1",
        "guangzhou":"https://tokenhub.tencentcloudmaas.com/v1",
        "hunyuan":"https://api.hunyuan.cloud.tencent.com/v1"}},
}


# Operator-selected reasoning level for agent calls. "none" keeps the fastest behaviour.
REASONING_LEVELS = ("none", "low", "medium", "high")


def _output_kind(result):
    """Short non-sensitive label for an unusable provider reply."""
    try:
        choice = result["choices"][0]
        if choice["message"].get("refusal"):
            return "refusal"
        reason = str(choice.get("finish_reason") or "")
        if reason and reason not in {"stop", "tool_calls"}:
            return "finish_" + "".join(c for c in reason if c.isalnum() or c == "_")[:30]
        if not (choice["message"].get("content") or choice["message"].get("tool_calls")):
            return "empty_content"
    except (KeyError, IndexError, TypeError, AttributeError):
        return "bad_shape"
    return "bad_output"


class VendorProvider:
    def __init__(self, provider, model, api_key, *, variant=None, config=None, transport=None, reasoning="none"):
        self.provider, self.model = provider, model
        self.reasoning = reasoning if reasoning in REASONING_LEVELS else "none"
        self.base = PROVIDERS[provider]["endpoints"][variant or next(iter(PROVIDERS[provider]["endpoints"]))]
        self.model_id = f"{provider}:{model}"
        self._key, self.config, self._transport = api_key, config or load_config(), transport

    def _request(self, method, path, payload=None):
        deadline = monotonic() + self.config.provider_timeout_seconds
        try:
            with httpx.Client(timeout=self.config.provider_timeout_seconds, follow_redirects=False,
                              trust_env=False, transport=self._transport) as client:
                with client.stream(method,self.base+path,json=payload,
                                   headers={"Authorization":f"Bearer {self._key}"}) as response:
                    response.raise_for_status()
                    body=bytearray()
                    # Model catalogs are larger than generation replies; both are bounded.
                    limit=1048576 if path=="/models" else self.config.max_provider_response_bytes
                    for chunk in response.iter_bytes():
                        if monotonic()>deadline: raise TimeoutError("Provider deadline exceeded")
                        body.extend(chunk)
                        if len(body)>limit: raise ProviderUnavailable("Provider response too large", kind="too_large")
            if monotonic()>deadline: raise TimeoutError("Provider deadline exceeded")
            return json.loads(body)
        except httpx.TimeoutException as exc:
            raise TimeoutError("Provider timed out") from exc
        except httpx.HTTPStatusError as exc:
            raise ProviderUnavailable("Provider request failed", kind=f"http_{exc.response.status_code}") from exc
        except json.JSONDecodeError as exc:
            raise ProviderUnavailable("Provider request failed", kind="bad_json") from exc
        except (httpx.HTTPError,ValueError) as exc:
            raise ProviderUnavailable("Provider request failed", kind="request_error") from exc

    def models(self):
        data=self._request("GET","/models")
        rows=data.get("data",[]) if isinstance(data,dict) else []
        return sorted({row["id"] for row in rows if isinstance(row,dict) and
                       isinstance(row.get("id"),str) and 0<len(row["id"])<=160
                       and not any(word in row["id"].lower() for word in
                                   ("embedding","whisper","tts","dall-e","moderation"))})[:500]

    def generate(self, contract):
        payload={"model":self.model,"stream":False,"messages":[
            {"role":"system","content":contract["instructions"]+" Return JSON only. Copy one authorized candidate exactly."},
            {"role":"user","content":json.dumps(contract)}]}
        if self.provider=="openai":
            payload.update(max_completion_tokens=1024,store=False,response_format={"type":"json_object"})
        else:
            payload.update(max_tokens=1024)
            # Legacy Hunyuan has no assumed JSON-mode support; exact validation still wins.
            if not (self.provider=="tencent" and self.base.endswith("hunyuan.cloud.tencent.com/v1")):
                payload["response_format"]={"type":"json_object"}
            if self.provider=="deepseek":
                # Reasoning tokens would use the 1024-token budget and the short communication deadline.
                payload["thinking"]={"type":"disabled"}
        result=self._request("POST","/chat/completions",payload)
        try:
            choice=result["choices"][0]
            if choice.get("finish_reason")!="stop" or choice["message"].get("refusal"):
                raise ValueError("Incomplete or refused output")
            return json.loads(choice["message"]["content"])
        except (KeyError,IndexError,TypeError,ValueError) as exc:
            raise ProviderUnavailable("Invalid provider output", kind=_output_kind(result)) from exc

    def agent_step(self, messages, tools):
        """Native function calling, separate from unchanged M5 candidate wording."""
        payload = {"model": self.model, "messages": messages, "stream": False}
        if tools:
            payload.update(tools=tools, tool_choice="auto")
            if self.provider == "openai":
                payload["parallel_tool_calls"] = True
        if not (self.provider=='tencent' and self.base.endswith('hunyuan.cloud.tencent.com/v1')):
            payload["response_format"] = {"type": "json_object"}
            # JSON mode providers (DeepSeek) reject a request whose prompt never says "json".
            if not any("json" in str(m.get("content") or "").lower() for m in messages):
                payload["messages"] = [dict(messages[0], content=str(messages[0].get("content") or "") + "\nReturn plain JSON only."), *messages[1:]]
        if self.provider=='deepseek':
            payload['thinking']={'type':'disabled' if self.reasoning=='none' else 'enabled'}
            # Stable endpoint: local strict validation remains authoritative.
            if tools:payload['tools']=[{'type':spec['type'],'function':{key:value for key,value in spec['function'].items() if key!='strict'}} for spec in tools]
        # Reasoning tokens share the output budget, so allow more when reasoning is on.
        budget = 4096 if self.reasoning == "none" else 16384
        if self.provider == "openai":
            payload.update(max_completion_tokens=budget, store=False, reasoning_effort=self.reasoning)
        else:
            payload.update(max_tokens=budget)
            if self.provider == "openrouter" and self.reasoning != "none":
                payload["reasoning"] = {"effort": self.reasoning}
        result = self._request("POST", "/chat/completions", payload)
        try:
            choice = result["choices"][0]
            message = choice["message"]
            if choice["finish_reason"] not in {"stop", "tool_calls"} or message.get("refusal"):
                raise ValueError()
            return {"role": "assistant", "content": message.get("content"),
                    "tool_calls": message.get("tool_calls", [])}
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ProviderUnavailable("Invalid agent provider output", kind=_output_kind(result)) from exc
