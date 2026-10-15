#!/usr/bin/env bash
# Blue/green switch for the public AURA demo: exactly one server runs the Cloudflare tunnel connector.
#
#   deploy/switch.sh status          which side is live, and what the public URL answers
#   deploy/switch.sh blue|green      health-gate the target, stop the other connector FIRST, start the
#                                    target, then confirm every public answer comes from the target
#   deploy/switch.sh blue --force    continue even if the other side can't be reached (risk: both live)
#   deploy/switch.sh help            plain-language guide (deploy/SWITCH_HELP.md), incl. rules for bots
#
# Demo sessions live in one server's memory, so a switch ends current visitors' sessions (they reload).
# Machine details live outside the public repo, in ~/.config/aura/switch.env:
#   BLUE_SSH=user@host  BLUE_KEY=~/.ssh/key  BLUE_DIR=aura-health   (remote, relative to home)
#   GREEN_SSH=          GREEN_KEY=           GREEN_DIR=/abs/path     (empty SSH = this machine)
#   PUBLIC_URL=https://example.org
set -euo pipefail
CONFIG="${AURA_SWITCH_CONFIG:-$HOME/.config/aura/switch.env}"
[ -r "$CONFIG" ] || { echo "Missing $CONFIG (see the header of this script)."; exit 2; }
# shellcheck disable=SC1090
. "$CONFIG"
CONNECTOR=aura-health-cloudflared-1
APP=aura-health-app-1

on() {  # on <side> <command…>: run a command in that side's AURA folder
  local side=$1; shift
  local ssh_var="${side^^}_SSH" key_var="${side^^}_KEY" dir_var="${side^^}_DIR"
  local ssh="${!ssh_var:-}" key="${!key_var:-}" dir="${!dir_var}"
  if [ -z "$ssh" ]; then (cd "$dir" && bash -c "$*")
  else ssh -o BatchMode=yes -o ConnectTimeout=10 ${key:+-i "${key/#\~/$HOME}" -o IdentitiesOnly=yes} "$ssh" "cd $dir && $*"; fi
}
reachable() { on "$1" true >/dev/null 2>&1; }
connector_running() { [ "$(on "$1" "docker inspect -f '{{.State.Running}}' $CONNECTOR 2>/dev/null || echo false")" = true ]; }

public_nodes() {  # sample the public URL; prints one node name per answer ('-' when it failed)
  for _ in $(seq 1 "${1:-20}"); do
    curl -s -m 8 "$PUBLIC_URL/health" | python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("node","?"))
except Exception: print("-")' || echo "-"
    sleep 0.5
  done
}

status() {
  for side in blue green; do
    if ! reachable "$side"; then echo "$side: NOT REACHABLE"; continue; fi
    local health live
    health=$(on "$side" "docker inspect -f '{{.State.Health.Status}}' $APP 2>/dev/null || echo missing")
    live=$(on "$side" "curl -s -m 5 127.0.0.1:\${AURA_DEMO_PORT:-8017}/system/status" 2>/dev/null | python3 -c 'import json,sys
try: d=json.load(sys.stdin); print("AI live" if d.get("live_enabled") else "AI off")
except Exception: print("AI status unknown")')
    echo "$side: app $health, $live, connector $(connector_running "$side" && echo RUNNING || echo stopped)"
  done
  echo "public answers: $(public_nodes 10 | sort | uniq -c | xargs)"
}

switch() {
  local target=$1 force=${2:-} other
  [ "$target" = blue ] && other=green || other=blue
  echo "== Health gate: $target"
  reachable "$target" || { echo "ABORT: $target is not reachable."; exit 1; }
  local health node live
  health=$(on "$target" "docker inspect -f '{{.State.Health.Status}}' $APP 2>/dev/null || echo missing")
  [ "$health" = healthy ] || { echo "ABORT: $target app is '$health', not healthy."; exit 1; }
  node=$(on "$target" "curl -s -m 5 127.0.0.1:\${AURA_DEMO_PORT:-8017}/health" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("node"))')
  [ "$node" = "$target" ] || { echo "ABORT: $target says it is '$node' (set AURA_NODE_NAME=$target in its .env)."; exit 1; }
  live=$(on "$target" "curl -s -m 5 127.0.0.1:\${AURA_DEMO_PORT:-8017}/system/status" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("live_enabled"))')
  if [ "$live" != True ] && [ "$force" != --force ]; then echo "ABORT: live AI is off on $target (add --force to switch anyway)."; exit 1; fi
  on "$target" "grep -q '^AURA_TUNNEL_TOKEN_FILE=' .env && test -r \$(grep '^AURA_TUNNEL_TOKEN_FILE=' .env | cut -d= -f2-)" \
    || { echo "ABORT: $target has no readable tunnel token file in .env."; exit 1; }

  echo "== Stop $other's connector first (never two live)"
  if reachable "$other"; then
    on "$other" "docker stop $CONNECTOR >/dev/null 2>&1 || true"
    if connector_running "$other"; then echo "ABORT: $other's connector is still running."; exit 1; fi
    echo "$other: connector stopped"
  elif [ "$force" = --force ]; then
    echo "WARNING: $other is unreachable. If it can still reach Cloudflare, both may be live; the check below will tell."
  else
    echo "ABORT: $other is unreachable, so its connector can't be confirmed stopped. Re-run with --force if it is down."; exit 1
  fi

  echo "== Start $target's connector"
  on "$target" "docker compose -f compose.yaml -f compose.tunnel.yaml up -d cloudflared >/dev/null 2>&1"
  connector_running "$target" || { echo "FAILED: $target's connector did not start. Bring $other back with: $0 $other"; exit 1; }

  echo "== Confirm the public URL answers only from $target"
  local answers ok=0
  for attempt in 1 2 3 4 5 6; do
    answers=$(public_nodes 20 | sort | uniq -c | xargs)
    echo "  check $attempt: $answers"
    if [[ "$answers" =~ ^20\ $target$ ]]; then ok=1; break; fi
    if [[ "$answers" == *"$other"* ]]; then
      echo "ALERT: answers came from $other too: both connectors may be live. Stopping $other again."
      reachable "$other" && on "$other" "docker stop $CONNECTOR >/dev/null 2>&1 || true"
    fi
    sleep 5
  done
  [ "$ok" = 1 ] && echo "DONE: $target is live; $other is standby." || { echo "NOT CONFIRMED: check '$0 status'."; exit 1; }
}

case "${1:-}" in
  help|-h|--help) cat "$(dirname "$0")/SWITCH_HELP.md"; exit 0 ;;
  status) status ;;
  blue|green) switch "$1" "${2:-}" ;;
  *) sed -n '2,14p' "$0"; exit 2 ;;
esac
