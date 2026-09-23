#!/usr/bin/env bash
# /goal loop: grinds docs/intake/ backlog into tracked GitHub issues (agent:hermes).
# Idempotent: files get a marker comment after dispatch; skipped on next run.
# DRYRUN=1 -> print what would dispatch, make no changes.
set -uo pipefail
REPO="${GOALWORLD_REPO_PATH:-/data/apps/GoalWorld}"
INTAKE="$REPO/docs/intake"
SCRIPT="$REPO/ops/hermes/create-task.sh"
MARKER="goalworld-dispatched"
MAX="${MAX:-3}"
DRYRUN="${DRYRUN:-0}"
cd "$REPO" || exit 1

count=0
# oldest unprocessed top-level md first (skip README/TEMPLATE)
while IFS= read -r f; do
  [ -z "$f" ] && continue
  if grep -q "$MARKER" "$f" 2>/dev/null; then continue; fi
  title=$(grep -m1 '^# ' "$f" | sed 's/^# //' | cut -c1-60)
  [ -z "$title" ] && title=$(basename "$f" .md)
  rel="docs/intake/$(basename "$f")"
  prompt="$(head -40 "$f" | sed '/goalworld-dispatched/d')
---
Source file: $rel (auto-dispatched by intake_goal_loop.sh). Prioritize according to GoalWorld queue freeze rules. Close the linked intake file marker once implemented."

  if [ "$DRYRUN" = "1" ]; then
    echo "[dryrun] would dispatch: $title  ($rel)"
    count=$((count+1)); [ "$count" -ge "$MAX" ] && break; continue
  fi

  out=$("$SCRIPT" hermes P1 "[intake] $title" "$prompt" 2>&1) || { echo "DISPATCH_FAIL: $title :: $out"; continue; }
  url=$(printf '%s' "$out" | grep -oE 'https://github.com/[^ ]*issues/[0-9]+' | head -1)
  if [ -n "$url" ]; then
    printf '\n<!-- %s: %s -->\n' "$MARKER" "$url" >> "$f"
    echo "DISPATCHED: $title -> $url"
    count=$((count+1))
  else
    echo "DISPATCH_FAIL_NO_URL: $title :: $out"
  fi
  [ "$count" -ge "$MAX" ] && break
done < <(find "$INTAKE" -maxdepth 1 -name '*.md' -type f ! -name 'README*' ! -name 'TEMPLATE*' -printf '%T@ %p\n' | sort -n | awk '{print $2}')

[ "$count" -eq 0 ] && echo "NO_PENDING_INTAKE"
exit 0
