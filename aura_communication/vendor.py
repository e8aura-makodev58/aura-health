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


class VendorProvider:
    def __init__(self, provider, model, api_key, *, variant=None, config=None, transport=None):
        self.provider, self.model = provider, model
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
                        if len(body)>limit: raise ProviderUnavailable("Provider response too large")
            if monotonic()>deadline: raise TimeoutError("Provider deadline exceeded")
            return json.loads(body)
        except httpx.TimeoutException as exc:
            raise TimeoutError("Provider timed out") from exc
        except (httpx.HTTPError,ValueError) as exc:
            raise ProviderUnavailable("Provider request failed") from exc

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
        result=self._request("POST","/chat/completions",payload)
        try:
            choice=result["choices"][0]
            if choice.get("finish_reason")!="stop" or choice["message"].get("refusal"):
                raise ValueError("Incomplete or refused output")
            return json.loads(choice["message"]["content"])
        except (KeyError,IndexError,TypeError,ValueError) as exc:
            raise ProviderUnavailable("Invalid provider output") from exc
