#!/usr/bin/env bash
# Morning digest for WhatsApp (no LLM) — cron delivers stdout.
set -euo pipefail

HERMES_HOME="${HERMES_HOME:-$HOME/hermes}"
REPO="${goalworld_REPO_PATH:-$HERMES_HOME/workspace/goalworld}"
API_BASE="${API_BASE_URL:-https://crm.goalworld.fun/goalworld-api}"
API_BASE="${API_BASE%/}"
DATE="$(date -u +%F)"
DIGEST="${HERMES_HOME}/memory/goalworld/daily/${DATE}.md"

if [[ ! -f "${DIGEST}" && -x "${HERMES_HOME}/scripts/daily-digest.sh" ]]; then
  bash "${HERMES_HOME}/scripts/daily-digest.sh" >> "${HERMES_HOME}/logs/digest.log" 2>&1 || true
fi

echo "☀️ goalworld — resumen $(date -u '+%H:%M UTC')"

if [[ -f "${DIGEST}" ]]; then
  echo ""
  echo "Digest:"
  head -n 18 "${DIGEST}" | sed 's/^/  /'
fi

export API_BASE
python3 - <<PY
import json, urllib.request, os
from pathlib import Path

api = os.environ.get("API_BASE", "https://crm.goalworld.fun/goalworld-api").rstrip("/")
try:
    h = json.loads(urllib.request.urlopen(f"{api}/api/economy/health", timeout=15).read())
    print(f"\nEconomía: {h.get('status','?')}")
    fail = h.get("failing_checks") or []
    if fail:
        print("  Checks:", ", ".join(fail[:5]))
except Exception as e:
    print(f"\nEconomía: (sin datos: {e})")

docs = Path.home() / ".hermes/workspace/docs"
radars = sorted(docs.glob("ai-radar-*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
if radars:
    t = radars[0].read_text(encoding="utf-8", errors="ignore").splitlines()
    title = next((ln.lstrip("# ").strip() for ln in t if ln.startswith("#")), radars[0].name)
    print(f"\nÚltimo radar: {title[:70]}")
PY

echo ""
echo "Play: https://play.goalworld.fun · Foro: active-research"
