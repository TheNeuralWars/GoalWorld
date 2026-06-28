#!/usr/bin/env bash
# Deploy goalworld_api on Hermes VPS (Docker, same network as Caddy).
# Idempotent: safe to re-run after git pull on ~/hermes/workspace/goalworld.
set -euo pipefail

REPO="${goalworld_REPO_PATH:-$HOME/hermes/workspace/goalworld}"
TWENTY_DIR="${TWENTY_DIR:-$HOME/twenty}"

echo "==> Pull + build"
cd "${REPO}"
git stash push -u -m "pre-api-deploy-$(date +%s)" 2>/dev/null || true
git checkout main
git pull --ff-only origin main
cd "${REPO}/goalworld-sdk" && npm ci --no-audit --no-fund && npm run build
cd "${REPO}/goalworld_api" && npm ci --no-audit --no-fund && npm run build

echo "==> Ensure docker service + Caddy routes"
python3 - <<PY
from pathlib import Path
compose = Path("${TWENTY_DIR}/docker-compose.yml")
text = compose.read_text()
if "goalworld-api:" not in text:
    block = """
  goalworld-api:
    image: node:24-bookworm-slim
    container_name: goalworld-api
    restart: unless-stopped
    working_dir: /repo/goalworld_api
    volumes:
      - ${REPO}:/repo:ro
    environment:
      PORT: 3001
      RPC_URL: https://api.devnet.solana.com
    command: node dist/index.js
    networks:
      - twenty-net

"""
    text = text.replace("\nvolumes:\n", block + "\nvolumes:\n")
    compose.write_text(text)
    print("patched docker-compose.yml")
PY

cat > "${TWENTY_DIR}/Caddyfile" <<EOF
crm.goalworld.fun {
    handle /goalworld-api/* {
        uri strip_prefix /goalworld-api
        reverse_proxy goalworld-api:3001
    }
    reverse_proxy twenty-app:3000
}

api.goalworld.fun {
    handle /pilot/* {
        uri strip_prefix /pilot
        file_server {
            root /srv/pilot
        }
    }
    reverse_proxy goalworld-api:3001
}
EOF

cd "${TWENTY_DIR}"
docker compose up -d goalworld-api caddy

echo "==> Smoke"
sleep 4
curl -sf "http://127.0.0.1:3001/api/ops/status" >/dev/null 2>&1 || \
  docker exec goalworld-api wget -qO- http://127.0.0.1:3001/api/ops/status >/dev/null
curl -sf "https://crm.goalworld.fun/goalworld-api/api/ops/status" | head -c 120
echo ""
echo "Done. Set Vercel VITE_API_BASE_URL=https://crm.goalworld.fun/goalworld-api (or https://api.goalworld.fun after DNS A record)."
