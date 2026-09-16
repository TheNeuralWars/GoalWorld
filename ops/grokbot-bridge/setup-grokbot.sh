#!/usr/bin/env bash
# Grokbot-side bootstrap for the Hermes bridge.
# Run this ON THE GROKBOT HOST (jefe-gabinete). It is safe and idempotent.
#
#   bash setup-grokbot.sh relay     # SSH relay MCP (works with only SSH access)
#   bash setup-grokbot.sh api       # native API client config (:8642)
#   bash setup-grokbot.sh test      # verify whichever you installed
#
# Neither method needs inbound access to this host: the relay SSHs out, and the
# API client dials the Tailscale IP. No Funnel, no public bind.

set -euo pipefail

HERMES_HOST="${HERMES_HOST:-100.101.211.44}"      # goalchain, Tailscale IP
HERMES_SSH_TARGET="${HERMES_SSH_TARGET:-ubuntu@100.101.211.44}"
HERMES_API_PORT="${HERMES_API_PORT:-8642}"
IDENTITY_NAME="${IDENTITY_NAME:-hermes-goalchain}"
BRIDGE_DIR="${BRIDGE_DIR:-$HOME/hermes-grok-bridge}"
BRIDGE_REPO="https://github.com/shagghiesuperstar/hermes-grok-bridge"
# Key staged on the Hermes side, pulled by scp before running the api path.
HERMES_STAGE_ENV="${HERMES_STAGE_ENV:-$HOME/grokbot-bridge/.staged/hermes-api.env}"

say() { printf '\033[1m%s\033[0m\n' "$*"; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

preflight() {
  say "== preflight"
  command -v python3 >/dev/null || die "python3 is required"
  command -v ssh    >/dev/null || die "ssh is required"
  if ! ssh -o BatchMode=yes -o ConnectTimeout=8 "$HERMES_SSH_TARGET" true 2>/dev/null; then
    die "cannot SSH to $HERMES_SSH_TARGET — check the key and Tailscale membership"
  fi
  echo "  ssh to $HERMES_SSH_TARGET: OK"
  if ssh -o BatchMode=yes -o ConnectTimeout=8 "$HERMES_SSH_TARGET" 'command -v hermes' >/dev/null 2>&1; then
    echo "  hermes CLI on the far side: OK"
  else
    die "hermes CLI not found on $HERMES_SSH_TARGET (the relay needs it)"
  fi
}

install_relay() {
  say "== SSH relay (stdio MCP)"
  if [ -d "$BRIDGE_DIR" ]; then
    git -C "$BRIDGE_DIR" pull --ff-only || true
  else
    git clone --depth 1 "$BRIDGE_REPO" "$BRIDGE_DIR"
  fi
  local entry="$BRIDGE_DIR/ssh-relay/src/hermes_grok_relay/server.py"
  [ -f "$entry" ] || die "relay entrypoint missing: $entry"

  say "== MCP config to paste into the Grok Bot app"
  cat <<EOF
{
  "mcpServers": {
    "$IDENTITY_NAME": {
      "command": "python3",
      "args": ["$entry"],
      "env": {
        "HERMES_RELAY_SSH_TARGET": "$HERMES_SSH_TARGET",
        "HERMES_RELAY_IDENTITY_NAME": "$IDENTITY_NAME"
      }
    }
  }
}
EOF
  say "== relay smoke test (asks Hermes one question over SSH)"
  ssh -o BatchMode=yes "$HERMES_SSH_TARGET" \
    'hermes -z "reply with exactly the word RELAY_OK"' 2>&1 | tail -5
}

install_api() {
  say "== native API client (:8642)"
  local envfile="$HOME/.hermes-api-${HERMES_HOST//./_}.env"
  if [ -f "$HERMES_STAGE_ENV" ]; then
    install -m 600 "$HERMES_STAGE_ENV" "$envfile"
    echo "  wrote $envfile (mode 600)"
  elif [ ! -f "$envfile" ]; then
    die "no key file. Copy the staged env from the Hermes host first:
      scp $HERMES_SSH_TARGET:$HERMES_STAGE_ENV_DEFAULT $envfile
    then re-run."
  fi
  set -a; . "$envfile"; set +a
  say "== connector config (base URL + key from env, never inline)"
  cat <<EOF
{
  "mcpServers": {
    "${IDENTITY_NAME}-api": {
      "url": "http://$HERMES_HOST:$HERMES_API_PORT/v1",
      "headers": { "Authorization": "Bearer \$HERMES_API_KEY" }
    }
  }
}
EOF
  echo "  API key source: $envfile"
  echo "  endpoint:       http://$HERMES_HOST:$HERMES_API_PORT/v1"
}

test_all() {
  say "== /health"
  curl -fsS --max-time 10 "http://$HERMES_HOST:$HERMES_API_PORT/health" && echo || \
    echo "  /health unreachable — the API server may not be enabled on the Hermes side yet"
  say "== authenticated /v1/models (needs the key)"
  if [ -f "$HOME/.hermes-api-${HERMES_HOST//./_}.env" ]; then
    set -a; . "$HOME/.hermes-api-${HERMES_HOST//./_}.env"; set +a
    curl -fsS --max-time 15 "http://$HERMES_HOST:$HERMES_API_PORT/v1/models" \
      -H "Authorization: Bearer $HERMES_API_KEY" | head -c 400
    echo
  else
    echo "  no key file, skipping"
  fi
}

case "${1:-}" in
  relay) preflight; install_relay ;;
  api)   install_api ;;
  test)  test_all ;;
  *)     echo "usage: $0 {relay|api|test}"; exit 2 ;;
esac
