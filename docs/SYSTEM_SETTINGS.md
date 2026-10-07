# AI provider settings

Click the header gear. Following Compass, keys are write-only, server-side and
stored separately from provider/model settings. This is demo operator control,
not production authentication or a production secrets-management system.

## Unlock and configure

Use HTTPS or a localhost SSH forward. Plain LAN HTTP deliberately cannot submit
credentials. On your laptop you can run:

```sh
ssh -L 8017:127.0.0.1:8017 makodev58@192.168.80.193
# Open http://localhost:8017
```

The server creates a private administrator token on first startup. Retrieve it
yourself on the server, paste it into the administrator field, and unlock:

```sh
docker compose exec app python -c "from pathlib import Path; print(Path('/data/workspaces/system/admin.token').read_text())"
```

Never put tokens or keys in chat, Git, logs or screenshots. The dialog clears its
in-memory unlock token on close/lock; there is no browser-storage credential copy.

1. Select OpenRouter, OpenAI, DeepSeek or Tencent and save its API key.
2. Select endpoint/region. Tencent offers TokenHub Singapore, TokenHub Guangzhou
   and legacy Hunyuan. Their keys are not interchangeable; Cloud SecretID/SecretKey
   is not the API key requested here.
3. Enter an exact text-model ID or refresh the model list. Catalog presence does
   not guarantee JSON-output compatibility.
4. Check **Enable live wording for this synthetic demo** and save provider settings.
5. Optionally test the saved connection. The confirmation sends one small synthetic
   request and may incur a charge. Saving a key does not run a connection test.

One provider is active; there is no automatic cross-provider failover. Remove its
key or disable live wording to use fixed output. UI response labels distinguish
actual validated generation from fixed wording/fallback.

## Boundaries and storage

- Only allowlisted hosted synthetic workspaces can use this provider. The ordinary
  patient API remains disabled. Arbitrary public text does not reach generation.
- Models select exact approved wording candidates. Existing deterministic validator,
  safety containment, resource separation, race checks and audit remain authoritative.
  Accepted safety/longitudinal algorithms are unchanged.
- Fixed HTTPS endpoints, no redirects/environment proxies, 5-second timeout,
  1,024-token cap, 16-KiB generation response cap and 1-MiB model catalog cap.
  Engineering budget: 10 calls/minute and 60/hour per single-worker process,
  including discovery/tests. It resets on restart and is not a billing limit.
- Docker persists `system/provider-settings.json`, `system/provider-credentials.json`
  and `system/admin.token` under `/data/workspaces`. Directory 0700, files 0600,
  atomic replacement. Keys are **plaintext at rest**, not encrypted; protect host,
  volume and backups. Keys do not enter patient databases, prompts or audit records.
- Provider/key changes invalidate cached wording through a revision identifier.
- This is single-worker development/demo infrastructure, not institutional readiness
  or clinical validation. Future institution-managed on-prem/private-cloud deployment
  remains intended direction, not an implemented deployment claim.

## Sources and verification

Official API references: [OpenAI Chat Completions](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create),
[OpenRouter](https://openrouter.ai/docs/quickstart),
[DeepSeek JSON mode](https://api-docs.deepseek.com/guides/json_mode/),
[Tencent TokenHub](https://intl.cloud.tencent.com/ind/document/product/1300/80632),
[legacy Hunyuan](https://main.qcloudimg.com/raw/document/product/pdf/1729_111006_cn.pdf).
Unsupported model options, timeout or invalid output fall back to fixed wording.
Automated transport tests use mocks: no actual paid call or clinical efficacy is
claimed. Supply credentials and run a synthetic smoke test to verify your model.
