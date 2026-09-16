#!/usr/bin/env bash
# Create a goalworld task issue from the server with owner labels.
#
#   create-task.sh <owner> <priority> <title> <objective>
#   create-task.sh --source ceo <owner> <priority> <title> <objective>
#
# --source only changes the "## Context" line (who requested it).
# create-task-ceo.sh is a shim that passes --source ceo.
set -euo pipefail

SOURCE="manager"
ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --source) SOURCE="${2:-manager}"; shift 2 ;;
    --source=*) SOURCE="${1#*=}"; shift ;;
    *) ARGS+=("$1"); shift ;;
  esac
done
set -- ${ARGS[@]+"${ARGS[@]}"}

if [[ $# -lt 4 ]]; then
  cat <<EOF
Usage: $0 [--source manager|ceo] <owner:cursor|antigravity|hermes|code|grok> <priority:P0|P1|P2> <title> <objective>
Example:
  $0 cursor P1 "Webapp devnet bets" "Wire real place_bet tx in webapp"
  $0 --source ceo hermes P0 "[DRAFT] Finish PR #32" "Finish consolidation"
EOF
  exit 1
fi

# config.env lives in the ops dir, NOT the Hermes Agent profile dir.
# Do NOT use $HERMES_HOME here — on a profile it points at the agent's home.
CONFIG_ENV=""
for candidate in \
  "${GOALWORLD_OPS_HOME:-$HOME/hermes}/config.env" \
  "$HOME/hermes/config.env" \
  /home/goalworld/hermes/config.env; do
  if [[ -f "$candidate" ]]; then
    CONFIG_ENV="$candidate"
    break
  fi
done
if [[ -z "$CONFIG_ENV" ]]; then
  echo "ERROR: config.env not found (looked in GOALWORLD_OPS_HOME, \$HOME/hermes, /home/goalworld/hermes)" >&2
  exit 1
fi
# shellcheck disable=SC1090
source "$CONFIG_ENV"

OWNER="$1"
PRIORITY="$2"
TITLE="$3"
OBJECTIVE="$4"

case "$OWNER" in
  code|opencode) OWNER="hermes" ;;
  cursor|antigravity|hermes|grok) ;;
  *)
    echo "ERROR: owner must be one of: cursor|antigravity|hermes|code|grok" >&2
    exit 1
    ;;
esac

case "$PRIORITY" in
  P0|P1|P2) ;;
  *)
    echo "ERROR: priority must be P0, P1, or P2" >&2
    exit 1
    ;;
esac

if ! command -v gh >/dev/null 2>&1; then
  echo "ERROR: gh CLI not found" >&2
  exit 1
fi

case "$SOURCE" in
  ceo) REQUESTED_BY="Requested by Nico via Manager (hermes-ceo profile)." ;;
  *)   REQUESTED_BY="Requested by Nico via Manager (WhatsApp/OpenClaw)." ;;
esac

# Ensure canonical labels exist (ignore if already present).
for spec in \
  "agent:${OWNER}|1f6feb|Task owner ${OWNER}" \
  "priority:${PRIORITY}|d73a4a|Priority ${PRIORITY}" \
  "status:ready|0e8a16|Ready to start" \
  "source:manager|5319e7|Created by Manager/OpenClaw"; do
  IFS='|' read -r label color desc <<<"$spec"
  gh label create "$label" --repo "$GITHUB_REPO" --color "$color" --description "$desc" >/dev/null 2>&1 || true
done

ISSUE_TITLE="[${OWNER^^}] ${TITLE}"
ISSUE_BODY="$(cat <<EOF
## Objective
${OBJECTIVE}

## Owner
${OWNER}

## Priority
${PRIORITY}

## Context
${REQUESTED_BY} Keep scope tight and aligned with goalworld orchestration rules.

## Required output
- Proposed file list
- Risks/regressions + rollback
- Exact test commands

## Workflow
- One implementer only
- Branch naming:
  - cursor: \`feat/*\` or \`fix/*\`
  - antigravity: \`exp/antigravity-*\`
  - hermes: \`exp/hermes-*\`
  - grok: \`exp/grok-*\`
- Draft PR for Antigravity/Nico review — no direct merge to \`main\` unless \`cambio urgente\`
EOF
)"

ISSUE_URL="$(gh issue create \
  --repo "$GITHUB_REPO" \
  --title "$ISSUE_TITLE" \
  --body "$ISSUE_BODY" \
  --label "agent:${OWNER}" \
  --label "priority:${PRIORITY}" \
  --label "status:ready" \
  --label "source:manager")"

echo "Created issue: $ISSUE_URL"
