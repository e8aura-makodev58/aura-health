# Synthetic demo deployment

Local Docker verified; public URL **pending** hostname/tunnel configuration. This is
demo infrastructure, not production deployment or authenticated patient care.

## Server demo

```sh
AURA_SECURE_COOKIE=false docker compose up -d --build app
docker compose ps
curl -fsS http://127.0.0.1:8017/health
```

Port 8017 is published on `0.0.0.0` by explicit user decision. Open
`http://<server-ip>:8017` from the network (subject to firewall); local access remains
`http://127.0.0.1:8017`. Set `AURA_DEMO_BIND=127.0.0.1` to restore loopback-only
hosting. Use only synthetic data; direct HTTP is unencrypted and unauthenticated.
Seeding builds nine accepted checkpoints privately and
publishes the baseline only when complete. Existing complete seeds are verified and
preserved; incomplete databases are rejected, not silently skipped. Default fixed
seed: 7. Startup may take a minute; health start grace is 120 seconds. One worker is
required for this development session store.

Only labelled synthetic taps/text/explanations are accepted. No sign-up, arbitrary
free-text storage, public anchor command, live model, remote font or tracker. The
read-only, non-root app has a persistent named volume, configurable published port, CPU/memory limits,
and explicit static-asset allowlist. API docs are disabled rather than weakening CSP.

## Cloudflare (operator configuration required)

Configure a dedicated remotely managed tunnel/public hostname in Cloudflare. Point its
HTTP service to `http://app:8000` on this Compose network. Save its token in a protected
local file outside the repository. Provide only that path, never paste/commit the token.
Copy `.env.example` to ignored `.env` and set `AURA_TUNNEL_TOKEN_FILE` to that file path;
set `AURA_SECURE_COOKIE=true` for HTTPS. Pin `AURA_CLOUDFLARED_IMAGE` to a reviewed image
digest when provisioning (the current `latest` placeholder is not an immutable lock).

```sh
docker compose -f compose.yaml -f compose.tunnel.yaml up -d --build
docker compose -f compose.yaml -f compose.tunnel.yaml ps
```

The sidecar receives a file-backed Compose secret and uses `--token-file`; no token
value is in YAML or the process command. Supported cloudflared versions are documented
by [Cloudflare run parameters](https://developers.cloudflare.com/tunnel/reference/run-parameters/).
File mounting follows [Docker Compose secrets](https://docs.docker.com/compose/how-tos/use-secrets/).
Keep tunnel logs at warn, not debug. Do not print environment/secret contents.

Before recording the public URL: verify HTTPS, cookie Secure/HttpOnly/SameSite,
Cases A–F, two-browser isolation/reset, unknown input rejection, health and fallback.
**Public reachability has not been tested; M7 is not complete.**

## Reset, restart and limitations

Explore demo → Reset synthetic session replaces only that browser's synthetic clone.
It is not a safety downgrade. Old clone is retained until session expiry; other
visitors are unchanged. Engineering limits: 16 concurrent sessions, 3600-second idle
TTL, 4 resets/session, 8192-byte input body. These are not clinical parameters.

Restart preserves the verified baseline. Session mappings are in memory; existing
cookies receive fresh workspaces after restart. Orphaned files from an abrupt restart
are retained, not silently deleted. Operator storage cleanup/rate-limiting remains
open; do not treat this as hardened unlimited public infrastructure. Restrict access
or stop the tunnel if abused. Do not remove the volume with `down -v` to reset sessions.

Local operator reset for an explicit verified synthetic DB (stop its server first):

```sh
.venv/bin/python -m aura_app.demo --db /tmp/demo.sqlite3 --reset-from /tmp/baseline.sqlite3 --confirm-synthetic-reset
```

This archives the old DB at a printed exact path. It rejects unknown patient profiles.
No production patient data should exist. Offline fallback requires an already-loaded
page; there is no cold-start offline app or durable encrypted pending queue.
