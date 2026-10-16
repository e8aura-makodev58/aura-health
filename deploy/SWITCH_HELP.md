# deploy/switch.sh — help

## What this script is for

The public AURA demo (the domain judges open) can be served by **one of two servers**:

| Name | Machine | Normal role |
|---|---|---|
| **blue** | Tencent Cloud Lighthouse, Singapore | Live: serves the public site |
| **green** | The original self-hosted machine | Warm standby: running and up to date, but not serving |

Both servers run the same AURA code with live AI. Which one the public reaches depends only on
which one runs its **Cloudflare tunnel connector**. This script moves the public site from one
server to the other **safely**, so that:

- the target is checked first (healthy, correctly named, live AI on, tunnel token present);
- the old server's connector is **stopped first**, so the two are **never live at the same time**
  (each visitor's demo session lives in one server's memory; two live servers would break sessions);
- afterwards it asks the public site 20 times and confirms **every** answer came from the target.

If any check fails, it stops and says why. Nothing is switched halfway.

## Commands

Run from the AURA folder on the green machine (`deploy/switch.sh …`).

| Command | What it does | Safe to run any time? |
|---|---|---|
| `status` | Shows each server (app health, AI on/off, connector running/stopped) and which server 10 public requests came from | Yes, it changes nothing |
| `blue` | Make blue (Lighthouse) the live server | Ends current demo sessions |
| `green` | Make green (self-hosted) the live server | Ends current demo sessions |
| `blue --force` / `green --force` | Switch even if the *other* server can't be reached (it may be down) | Only when the other server is really down |
| `help` | Shows this file | Yes |

## Reading the output

`status`, normal state:

```
blue: app healthy, AI live, connector RUNNING
green: app healthy, AI live, connector stopped
public answers: 10 blue
```

- Exactly one `connector RUNNING`, and public answers all from that server: correct.
- Two `RUNNING`: **wrong**; run the switch to the one you want and the script stops the other.
- `NOT REACHABLE`: the script couldn't log in to that server (it may be down or off the network).
- Public answers with `-`: requests that failed (normal for a few seconds during a switch).

A switch ends with `DONE: blue is live; green is standby.` Anything else (`ABORT`, `FAILED`,
`NOT CONFIRMED`, `ALERT`) means read the line above it; the public site stays on the server that
was working unless the message says otherwise.

## When to switch

- The live server is down, slow or showing errors and the other one is healthy (`status` first).
- Deploying a change: update the standby server, check it, switch to it, update the other, switch back.
- **Not during a judge's demo**: a switch ends the demo sessions in progress (visitors reload and
  start fresh). The header light on the site shows which server answers: blue or green dot, red = offline.

## Rules for assistants and bots (e.g. the Telegram agent)

- Use **only** this script, with exactly `status`, `blue`, `green`, `blue --force`, `green --force` or `help`.
- `status` and `help` may be run freely. Before `blue` or `green`, show the current status and
  **ask the owner to confirm**. Use `--force` only when the owner explicitly says "force".
- Never start or stop AURA containers or the tunnel any other way, never edit `.env`, the token
  files or `~/.config/aura/switch.env`. Doing so can put both servers live at once.
- Report the script's output word for word.

## Setup the script relies on (already done)

- `~/.config/aura/switch.env` on the green machine: how to reach each server and the public URL
  (kept out of the public repo).
- Each server's `.env` names it (`AURA_NODE_NAME=blue|green`) and points to its own copy of the
  tunnel token file. The Cloudflare side needs no change: both servers use the same tunnel.

## If the green machine itself is down

The script runs on green, so it is unavailable. An assistant on another machine that reaches green
over SSH (such as the owner's Telegram agent) will report green as NOT REACHABLE; it must **not**
start blue's connector itself. Blue keeps serving on its own. If blue's connector must be started by
hand, the **owner** uses the Tencent Lighthouse web terminal (as user `ubuntu`):

```
cd ~/aura-health && docker compose -f compose.yaml -f compose.tunnel.yaml up -d cloudflared
```

Only do this when green is down: there are no safety checks on this path.
