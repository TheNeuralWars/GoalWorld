#!/usr/bin/env bash
# omniroute-exit-setup.sh
# Routes ONLY the OmniRoute container's egress through a Tailscale sidecar
# whose exit node is Nico's Windows machine (100.101.209.8). The rest of the
# VPS keeps its normal public IP. Isolation via a dedicated docker bridge net.
#
# USAGE:
#   TS_AUTHKEY=tskey-auth-xxxxx ./omniroute-exit-setup.sh up      # activate
#   ./omniroute-exit-setup.sh down                                # revert to host net
#   ./omniroute-exit-setup.sh status                              # show state
#
# PREREQUISITES (Nico, on Windows PowerShell, machine already in tailnet):
#   tailscale up --advertise-exit-node
# (no auth key needed on the Windows side)
set -euo pipefail

NET="omni-exit"
SUBNET="172.30.0.0/16"
SIDECAR="omniroute-ts"
APP="omniroute"
APP_IMG="diegosouzapw/omniroute:latest"
APP_VOL="/data/docker/volumes/omniroute-data/_data:/app/data"
EXIT_NODE="100.101.209.8"   # windows tailscale IP
APP_PORT="20128"

TS_AUTHKEY="${TS_AUTHKEY:-$(cat /data/hermes-home/.tailscale_authkey 2>/dev/null || echo)}"

case "${1:-status}" in
  up)
    if [ -z "$TS_AUTHKEY" ]; then
      echo "ERROR: TS_AUTHKEY not set. Export it or put it in /data/hermes-home/.tailscale_authkey"
      echo "Get one at https://login.tailscale.com -> Settings -> Keys (ephemeral+reusable)"
      exit 1
    fi
    echo "=== [1/5] create isolated bridge network ==="
    docker network inspect "$NET" >/dev/null 2>&1 || docker network create --subnet "$SUBNET" "$NET"

    echo "=== [2/5] start tailscale sidecar (exit node = windows) ==="
    docker rm -f "$SIDECAR" >/dev/null 2>&1 || true
    docker run -d --name "$SIDECAR" --restart unless-stopped \
      --network "$NET" \
      -e TS_AUTHKEY="$TS_AUTHKEY" \
      -e TS_EXTRA_ARGS="--advertise-exit-node=false --exit-node=$EXIT_NODE --exit-node-allow-lan-access" \
      tailscale/tailscale:stable

    echo "=== [3/5] wait for sidecar to join tailnet + use exit node ==="
    for i in $(seq 1 30); do
      if docker exec "$SIDECAR" tailscale status >/dev/null 2>&1; then break; fi
      sleep 2
    done
    docker exec "$SIDECAR" tailscale up --exit-node="$EXIT_NODE" --exit-node-allow-lan-access || true
    sleep 5
    echo "sidecar egress check:"; docker exec "$SIDECAR" curl -s -m 8 https://api.ipify.org; echo

    echo "=== [4/5] relaunch omniroute attached to sidecar network (port on 127.0.0.1) ==="
    docker rm -f "$APP" >/dev/null 2>&1 || true
    docker run -d --name "$APP" --restart unless-stopped \
      --network "container:$SIDECAR" \
      -p 127.0.0.1:$APP_PORT:$APP_PORT \
      -v "$APP_VOL" \
      "$APP_IMG"
    # re-apply OmniRoute prefix/alias patches (preserve container behavior)
    sleep 6
    bash "$(dirname "$0")/reapply-omniroute-patches.sh" || echo "(patch script warning, non-fatal)"

    echo "=== [5/5] verify ==="
    sleep 4
    curl -s -m 8 -o /dev/null -w "OmniRoute API (127.0.0.1): HTTP %{http_code}\n" "http://127.0.0.1:$APP_PORT/api/combos"
    echo "DONE. OmniRoute now egresses via Windows Tailscale exit node."
    ;;
  down)
    echo "=== revert: relaunch omniroute in host network ==="
    docker rm -f "$APP" >/dev/null 2>&1 || true
    docker run -d --name "$APP" --restart unless-stopped \
      --network host \
      -v "$APP_VOL" \
      "$APP_IMG"
    sleep 6
    bash "$(dirname "$0")/reapply-omniroute-patches.sh" || true
    docker rm -f "$SIDECAR" >/dev/null 2>&1 || true
    docker network rm "$NET" >/dev/null 2>&1 || true
    curl -s -m 8 -o /dev/null -w "OmniRoute API (host net): HTTP %{http_code}\n" "http://127.0.0.1:$APP_PORT/api/combos"
    echo "REVERTED to host networking."
    ;;
  status)
    echo "=== omniroute network mode ==="
    docker inspect "$APP" --format '{{.HostConfig.NetworkMode}}' 2>/dev/null
    echo "=== sidecar present? ==="
    docker ps --filter name="$SIDECAR" --format '{{.Names}} {{.Status}}' 2>/dev/null || echo "(no sidecar)"
    echo "=== omniroute egress IP (via sidecar) ==="
    docker exec "$APP" curl -s -m 8 https://api.ipify.org 2>/dev/null; echo
    echo "=== banned providers (cloudflare 1010) ==="
    sudo python3 - <<'PY' 2>/dev/null
import sqlite3,sys
db=sqlite3.connect('/data/docker/volumes/omniroute-data/_data/storage.sqlite'); db.row_factory=sqlite3.Row
cur=db.cursor()
for p in ['groq','cerebras','cloudflare-ai','mistral','sambanova']:
    cur.execute("SELECT COUNT(*) t, SUM(CASE WHEN rate_limited_until IS NOT NULL THEN 1 ELSE 0 END) b FROM provider_connections WHERE provider=?",(p,))
    r=cur.fetchone(); print(f"  {p}: banned={r['b']}/{r['t']}")
PY
    ;;
  *) echo "usage: $0 {up|down|status}"; exit 1 ;;
esac
