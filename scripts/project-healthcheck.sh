#!/usr/bin/env bash
# scripts/project-healthcheck.sh
# Verifies compile-time health of all goalworld components.

set -euo pipefail

PRIMARY_ROOT="/Users/NicoPez/goalworld"
if [ ! -d "$PRIMARY_ROOT" ]; then
  PRIMARY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi

log() { printf '[%s] [HEALTHCHECK] %s\n' "$(date -u '+%F %T UTC')" "$*"; }

failed=0

log "Starting goalworld components healthcheck..."

# 1. Check SDK
log "Checking goalworld-sdk..."
if (cd "$PRIMARY_ROOT/goalworld-sdk" && npm run build) >/dev/null 2>&1; then
  log "✓ goalworld-sdk build: OK"
else
  log "✗ goalworld-sdk build: FAILED"
  failed=1
fi

# 2. Check API
log "Checking goalworld_api..."
if (cd "$PRIMARY_ROOT/goalworld_api" && npx tsc --noEmit) >/dev/null 2>&1; then
  log "✓ goalworld_api typecheck: OK"
else
  log "✗ goalworld_api typecheck: FAILED"
  failed=1
fi

# 3. Check Webapp
log "Checking goalworld_webapp..."
if (cd "$PRIMARY_ROOT/goalworld_webapp" && npx tsc --noEmit && npm run build) >/dev/null 2>&1; then
  log "✓ goalworld_webapp build: OK"
else
  log "✗ goalworld_webapp build: FAILED"
  failed=1
fi

# 4. Check Program
log "Checking goalworld_program..."
if (cd "$PRIMARY_ROOT/goalworld_program" && cargo check) >/dev/null 2>&1; then
  log "✓ goalworld_program check: OK"
else
  log "✗ goalworld_program check: FAILED"
  failed=1
fi

if [ $failed -eq 0 ]; then
  log "🎉 All healthchecks PASSED!"
  exit 0
else
  log "🚨 Healthcheck FAILED for one or more components."
  exit 1
fi
