#!/usr/bin/env bash
# Shared GBrain installer core for macOS/Linux (goalworld repo).
#
# Sourced by ops/hermes/install-gbrain.sh — never executed directly.
# Requires before sourcing:
#   REPO_ROOT  absolute path to the goalworld repo
#   GBRAIN_IDE cursor | antigravity   (used for log prefix + MCP resolution)
#
# Previously this body existed twice, byte-identical for ~90 lines, in
# install-gbrain-cursor.sh and install-gbrain-antigravity.sh.

: "${REPO_ROOT:?REPO_ROOT must be set before sourcing gbrain-install-common.sh}"
: "${GBRAIN_IDE:?GBRAIN_IDE must be set before sourcing gbrain-install-common.sh}"

BRAIN_REPO="${GBRAIN_BRAIN_REPO:-$HOME/brain}"
SEARCH_MODE="${GBRAIN_SEARCH_MODE:-balanced}"
PATH="$HOME/.bun/bin:${PATH:-}"
export PATH

log() { printf '[gbrain-%s] %s\n' "${GBRAIN_IDE}" "$*"; }

install_bun() {
  if command -v bun >/dev/null 2>&1; then
    log "bun: $(bun --version)"
    return 0
  fi
  log "installing bun..."
  curl -fsSL https://bun.sh/install | bash
  PATH="$HOME/.bun/bin:$PATH"
  export PATH
}

install_gbrain() {
  if command -v gbrain >/dev/null 2>&1; then
    log "gbrain: $(gbrain --version 2>/dev/null || true)"
    return 0
  fi
  bun install -g github:garrytan/gbrain
  gbrain --version
}

load_keys() {
  set -a
  [[ -f "${REPO_ROOT}/.env" ]] && source "${REPO_ROOT}/.env" 2>/dev/null || true
  set +a
}

init_brain() {
  load_keys
  if [[ ! -d "${HOME}/.gbrain" ]]; then
    if [[ -n "${ZEROENTROPY_API_KEY:-}" || -n "${OPENAI_API_KEY:-}" ]]; then
      gbrain init --pglite
    else
      log "init --pglite --no-embedding (add ZEROENTROPY_API_KEY or OPENAI_API_KEY to .env for vectors)"
      gbrain init --pglite --no-embedding || gbrain init --pglite
    fi
  fi
  gbrain config set search.mode "${SEARCH_MODE}" 2>/dev/null || true
  gbrain doctor --fast 2>/dev/null || gbrain doctor || true
}

setup_brain_repo() {
  mkdir -p "${BRAIN_REPO}"/{projects,operations,concepts,people,companies}
  [[ -d "${BRAIN_REPO}/.git" ]] || git -C "${BRAIN_REPO}" init -q 2>/dev/null || true
}

import_goalworld() {
  log "importing goalworld context..."
  for sub in ai_context docs/intake docs/proposals; do
    [[ -d "${REPO_ROOT}/${sub}" ]] || continue
    gbrain import "${REPO_ROOT}/${sub}" --no-embed 2>/dev/null || gbrain import "${REPO_ROOT}/${sub}" || true
  done
  for f in IMPLEMENTATION_STATUS.md FRONTEND_ROUTING.md PLAY_DEPLOY_GUIDE.md; do
    [[ -f "${REPO_ROOT}/docs/${f}" ]] && gbrain import "${REPO_ROOT}/docs/${f}" --no-embed 2>/dev/null || true
  done
  if [[ -n "${ZEROENTROPY_API_KEY:-}" || -n "${OPENAI_API_KEY:-}" ]]; then
    gbrain embed --stale 2>/dev/null || log "WARN: embed skipped"
  fi
}

# Resolve the MCP config path this IDE actually reads.
resolve_ide_mcp() {
  case "${GBRAIN_IDE}" in
    cursor)
      MCP_CONFIG="${CURSOR_MCP:-${REPO_ROOT}/.cursor/mcp.json}"
      mkdir -p "$(dirname "${MCP_CONFIG}")"
      ;;
    antigravity)
      local candidate
      for candidate in \
        "${ANTIGRAVITY_MCP:-$HOME/.gemini/config/mcp_config.json}" \
        "${HOME}/.gemini/antigravity-ide/mcp_config.json" \
        "${HOME}/.gemini/antigravity/mcp_config.json"; do
        if [[ -f "${candidate}" ]]; then
          MCP_CONFIG="${candidate}"
          break
        fi
      done
      MCP_CONFIG="${MCP_CONFIG:-$HOME/.gemini/config/mcp_config.json}"
      mkdir -p "$(dirname "${MCP_CONFIG}")"
      ;;
    *)
      log "ERROR: unknown GBRAIN_IDE '${GBRAIN_IDE}' (expected cursor|antigravity)"
      return 1
      ;;
  esac
}

# Both IDEs consume the same {"mcpServers":{"gbrain":{...}}} shape.
# The GUI has no shell PATH, and gbrain's shebang uses `env bun`,
# so invoke bun explicitly with the gbrain script as its argument.
wire_mcp() {
  local bun_bin gbrain_bin
  bun_bin="$(command -v bun)"
  gbrain_bin="$(command -v gbrain)"
  python3 - "${MCP_CONFIG}" "${bun_bin}" "${gbrain_bin}" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
data = {}
if path.exists():
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        data = {}
servers = data.setdefault("mcpServers", {})
servers["gbrain"] = {"command": sys.argv[2], "args": [sys.argv[3], "serve"]}
path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
print("wrote", path)
PY
  log "MCP wired: ${MCP_CONFIG}"
}

summary() {
  cat <<EOF

=== GBrain ready for ${GBRAIN_IDE} ===
CLI:     $(command -v gbrain)
Brain:   ~/.gbrain
Repo:    ${BRAIN_REPO}
MCP:     ${MCP_CONFIG}

Test: gbrain query "goalworld Hermes FCC pipeline"
Reload the ${GBRAIN_IDE} window/IDE — MCP does not hot-reload.

EOF
}

gbrain_install_main() {
  install_bun
  install_gbrain
  init_brain
  setup_brain_repo
  import_goalworld
  resolve_ide_mcp
  wire_mcp
  summary
}
