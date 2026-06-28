#!/usr/bin/env bash
# Register OpenClaw cron jobs for goalworld (run on server as goalworld user)
set -euo pipefail

if ! command -v openclaw >/dev/null 2>&1; then
  echo "ERROR: openclaw CLI not found"
  exit 1
fi

openclaw cron add \
  --name "goalworld-morning-digest" \
  --cron "0 9 * * *" \
  --session isolated \
  --message "goalworld morning digest. Run: bash ~/hermes/scripts/openclaw-context.sh and bash ~/hermes/scripts/sync.sh. Summarize open PRs, intake briefs, blocked items. Append summary to ~/.openclaw/workspace/memory/YYYY-MM-DD.md (today UTC). Spanish preferred." \
  --description "Daily goalworld ops digest via Hermes agent" \
  2>/dev/null || echo "WARN: morning digest job may already exist"

openclaw cron add \
  --name "goalworld-repo-sync" \
  --cron "0 */6 * * *" \
  --session main \
  --system-event "Run bash ~/hermes/scripts/sync.sh on goalworld repo. No reply unless sync failed." \
  --description "Periodic git fetch/pull for goalworld clone" \
  2>/dev/null || echo "WARN: repo sync job may already exist"

openclaw cron list
echo "Done."

# --- goalworld economy crank dry-run refresh (issue #811) ---
# Re-source this installer to register the periodic dry-run that refreshes
# docs/data/burn_tracker.json. Idempotent.
(cd "$(dirname "${BASH_SOURCE[0]}")" && bash ./install-economy-crank-cron.sh) || echo "WARN: economy-crank cron installer skipped"
