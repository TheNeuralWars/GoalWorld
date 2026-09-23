#!/usr/bin/env bash
# omniroute-egress-monitor.sh  (host-based hybrid egress)
# Nico's design:
#   - DEFAULT: OmniRoute egress via SERVER IP (89.168.20.135) -> 22/27 providers.
#   - WHEN Windows (100.101.209.8) is ONLINE + offering exit node:
#       set host Tailscale exit-node -> Windows residential IP -> 27/27.
#   - WHEN Windows drops: auto-revert host exit-node to NONE (server IP) so the
#     whole VPS does NOT lose internet. OmniRoute keeps working on server IP.
# Runs every minute via cron. Safe: never leaves host without internet.
set -uo pipefail

WIN_IP="100.101.209.8"
MODE_FILE="/tmp/omniroute_egress_mode"
LOG="/var/log/omniroute_egress.log"
PATCH="$(dirname "$0")/reapply-omniroute-patches.sh"

log(){ echo "$(date -u +%FT%TZ) $*" >>"$LOG"; }

# ---- is Windows up + offering exit node (per host tailscale view)? ----
win_exit_ready(){
  local st; st=$(tailscale status 2>/dev/null) || return 1
  local win; win=$(echo "$st" | grep "$WIN_IP") || return 1   # windows line only
  echo "$win" | grep -qE "offline" && return 1
  echo "$win" | grep -qE "exit node" || return 1
  return 0
}

current_mode(){ cat "$MODE_FILE" 2>/dev/null || echo server; }

# check active exit node on local host
if sudo tailscale status --json 2>/dev/null | python3 -c "import sys, json; data=json.load(sys.stdin); sys.exit(0 if data.get('ExitNodeStatus') else 1)"; then
  HAS_EXIT_NODE=true
else
  HAS_EXIT_NODE=false
fi

if win_exit_ready; then
  MODE=$(current_mode)
  if [ "$MODE" != "windows" ] || [ "$HAS_EXIT_NODE" = false ]; then
    log "SWITCH -> windows exit node (residential egress)"
    sudo tailscale up --reset --exit-node="$WIN_IP" --exit-node-allow-lan-access --accept-routes >/dev/null 2>&1 || true
    sleep 4
    # confirm residential egress
    IP=$(curl -s -m 10 https://api.ipify.org 2>/dev/null)
    if [ "$IP" != "89.168.20.135" ] && [ -n "$IP" ]; then
      log "egress now via windows: $IP"
      # clear 1010 bans so the 5 providers retry via residential IP
      sudo python3 - <<'PY' 2>/dev/null
import sqlite3
db=sqlite3.connect('/data/docker/volumes/omniroute-data/_data/storage.sqlite'); c=db.cursor()
for p in ('groq','cerebras','cloudflare-ai','mistral','sambanova'):
    c.execute("UPDATE provider_connections SET rate_limited_until=NULL,backoff_level=0,test_status='active' WHERE provider=?",(p,))
db.commit()
PY
      echo windows >"$MODE_FILE"
    else
      log "exit node set but egress still server IP ($IP) - reverting"
      sudo tailscale up --reset --accept-routes >/dev/null 2>&1 || true
    fi
  fi
else
  MODE=$(current_mode)
  if [ "$MODE" != "server" ] || [ "$HAS_EXIT_NODE" = true ]; then
    log "SWITCH -> server (windows down): clearing exit node settings (HAS_EXIT_NODE=$HAS_EXIT_NODE)"
    sudo tailscale up --reset --accept-routes >/dev/null 2>&1 || true
    sleep 4
    echo server >"$MODE_FILE"
  fi
fi

# OmniRoute health ping
curl -s -m 8 -o /dev/null -w "omni-api HTTP %{http_code}\n" "http://127.0.0.1:20128/api/combos" >>"$LOG" 2>&1
