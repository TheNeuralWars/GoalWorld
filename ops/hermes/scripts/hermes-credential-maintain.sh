#!/usr/bin/env bash
# Scheduled maintenance: Hermes Vault oauth refresh + xAI/Nous auth.json refresh.
#
# Single canonical implementation. This file used to exist twice, as two
# drifted generations: this copy had the profile-safe HOME resolution, the
# revoked-token pre-check and the alert() webhook but no fleet sync; the
# copy at ops/hermes/hermes-credential-maintain.sh had fleet sync (xai+nous)
# but had lost the HOME fix and re-inlined the same xai-refresh block twice.
# Neither was a superset, so both behaviours are kept here, once.
#
# ops/hermes/hermes-credential-maintain.sh is now a shim to this file.
set -euo pipefail

# Resolve the real home: HERMES profile sessions override $HOME to
# ~/.hermes/profiles/<p>/home, which would put the vault and logs in the
# wrong place.
_real_home() {
  if command -v getent >/dev/null 2>&1; then
    getent passwd "$(whoami)" | cut -d: -f6
    return
  fi
  case "$HOME" in
    */.hermes/profiles/*/home) echo "/home/$(whoami)" ;;
    *) echo "$HOME" ;;
  esac
}

REAL_HOME="$(_real_home)"
export PATH="${REAL_HOME}/.local/bin:/usr/local/bin:${PATH}"
HERMES_AGENT_HOME="${HERMES_AGENT_HOME:-$REAL_HOME/.hermes}"
HERMES_HOME="${HERMES_HOME:-$REAL_HOME/hermes}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HERMES_PYTHON="${HERMES_PYTHON:-$HERMES_AGENT_HOME/hermes-agent/venv/bin/python3}"
GOALWORLD_DIR="${GOALWORLD_DIR:-/data/apps/GoalWorld}"

PASSPHRASE_FILE="${HERMES_VAULT_PASSPHRASE_FILE:-$HERMES_AGENT_HOME/vault.env}"
[[ -f "${PASSPHRASE_FILE}" ]] || PASSPHRASE_FILE="${HERMES_AGENT_HOME}/vault.passphrase"
VAULT_HOME="${HERMES_VAULT_HOME:-$HERMES_AGENT_HOME/hermes-vault-data}"

LOG="${HERMES_HOME}/logs/credential-maintain.log"
mkdir -p "$(dirname "${LOG}")"
ts() { date -u '+%F %T UTC'; }
log() { printf '[%s] %s\n' "$(ts)" "$*" | tee -a "${LOG}"; }
alert() { printf '[%s] ALERT: %s\n' "$(ts)" "$*" | tee -a "${LOG}"; }

# --- vault passphrase ---------------------------------------------------------
export HERMES_VAULT_HOME="${VAULT_HOME}"
if [[ -f "${PASSPHRASE_FILE}" ]]; then
  # shellcheck disable=SC1090
  source "${PASSPHRASE_FILE}" 2>/dev/null || true
fi
if [[ -z "${HERMES_VAULT_PASSPHRASE:-}" && -f "${HERMES_AGENT_HOME}/vault.passphrase" ]]; then
  export HERMES_VAULT_PASSPHRASE
  HERMES_VAULT_PASSPHRASE="$(tr -d '\n\r' < "${HERMES_AGENT_HOME}/vault.passphrase")"
fi

# --- helpers ------------------------------------------------------------------
# Was inlined twice in the older copy; now one function.
refresh_xai_oauth() {
  local refresh_py="${HERMES_HOME}/scripts/hermes-xai-oauth-refresh.py"
  [[ -f "${refresh_py}" ]] || refresh_py="${SCRIPT_DIR}/hermes-xai-oauth-refresh.py"
  if [[ ! -x "${HERMES_PYTHON}" || ! -f "${refresh_py}" ]]; then
    log "skip xai-oauth refresh (python or script missing)"
    return 0
  fi
  if "${HERMES_PYTHON}" "${refresh_py}" --all-agent-profiles >> "${LOG}" 2>&1; then
    log "xai-oauth refresh (default + agent profiles): OK"
  else
    log "WARN xai-oauth refresh: exit $?"
  fi
}

maintain_vault() {
  if command -v hermes-vault >/dev/null 2>&1 && [[ -n "${HERMES_VAULT_PASSPHRASE:-}" ]]; then
    if timeout 120 hermes-vault --no-banner maintain --format json >> "${LOG}" 2>&1; then
      log "hermes-vault maintain: OK"
    else
      log "WARN hermes-vault maintain: exit $?"
    fi
  else
    log "skip hermes-vault maintain (CLI or passphrase missing)"
  fi
}

# Keep Super Grok + Nous grants + picker caches identical across all profiles.
# Nous agent keys expire ~1h; without this, HERMPro 404s while Grok still works.
sync_fleet_oauth() {
  local fleet_sync
  for candidate in \
    "${GOALWORLD_DIR}/ops/hermes/sync-xai-oauth-fleet.py" \
    "${SCRIPT_DIR}/sync-xai-oauth-fleet.py"; do
    [[ -f "$candidate" ]] && { fleet_sync="$candidate"; break; }
  done
  if [[ -z "${fleet_sync:-}" || ! -x "${HERMES_PYTHON}" ]]; then
    log "skip fleet oauth sync (python or script missing)"
    return 0
  fi
  if timeout 180 "${HERMES_PYTHON}" "${fleet_sync}" >> "${LOG}" 2>&1; then
    log "fleet oauth sync (xai + nous): OK"
  else
    log "WARN fleet oauth sync: exit $?"
  fi
}

# Refreshing a revoked grant just burns attempts and can log the profile out.
xai_token_revoked() {
  local auth_json="${HERMES_AGENT_HOME}/auth.json"
  [[ -f "${auth_json}" ]] || return 1
  command -v jq >/dev/null 2>&1 || return 1
  local relogin code
  relogin="$(jq -r '.providers["xai-oauth"].last_auth_error.relogin_required // false' "${auth_json}" 2>/dev/null || echo false)"
  code="$(jq -r '.providers["xai-oauth"].last_auth_error.code // "none"' "${auth_json}" 2>/dev/null || echo none)"
  [[ "${relogin}" == "true" || "${code}" == "xai_refresh_failed" ]]
}

notify_revoked() {
  [[ -n "${goalworld_ALPHA_WEBHOOK:-}" ]] || return 0
  curl -s -X POST "${goalworld_ALPHA_WEBHOOK}" \
    -H "Content-Type: application/json" \
    -d '{"message":"🚨 xAI OAuth token revoked! Run `bash ~/hermes/scripts/xai-oauth-reauth.sh` to re-authenticate."}' \
    >/dev/null 2>&1 || true
}

# --- run ----------------------------------------------------------------------
log "credential-maintain start"

if xai_token_revoked; then
  alert "xai-oauth relogin_required detected"
  alert "Run: bash ${HERMES_HOME}/scripts/xai-oauth-reauth.sh"
  notify_revoked
  log "Skipping xai-oauth refresh due to revoked token. Manual re-auth required."
else
  refresh_xai_oauth
fi

maintain_vault
sync_fleet_oauth

log "credential-maintain done"